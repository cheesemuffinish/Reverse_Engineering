import utils
from constants import *

UNKNOWN_INSTRUCTION = "???"

class DecoderState:

    #############################
    ###       Vairbles        ###
    #############################

    input              = None    
    decoded            = None   
    objectSource       = None 
    index              = 0     
    machine_code       = None  
    inst_keys          = None
    inst_length        = None
    error_index        = None  
    label_addr         = None
    postpone_addr      = None

    #############################
    ###       Initilzation    ###
    #############################

    def __init__(self, input_file=None, objectStr=None):
        self.machine_code = {}
        self.inst_keys = []
        self.inst_length = {}
        self.label_addr = []
        self.postpone_addr = []

            
        if input_file:
            with open(input_file,'rb') as fh:
                self.input = fh.read()
        elif objectStr:
            self.input = objectStr

        else:
            RuntimeError("Must provide either a file or string containing object code.")

        self.objectSource = bytearray(self.input)
        self.decoded = [False]*len(self.objectSource)


    def markDecoded(self, startIdx, byteLen, instruction):
        # don't do anything if this has already been decoded!
        decodedPath = set()
        for idx in range(startIdx, startIdx+byteLen ):
            decodedPath.add(self.decoded[idx])
        if True in decodedPath:
            return None

        self.index = startIdx+byteLen
        for idx in range(startIdx, startIdx+byteLen ):
            self.decoded[idx] = True

        if self.error_index != None:
            startErr = self.error_index[0]
            byteLenErr = len(self.error_index)
            self.machine_code[ (startErr, byteLenErr) ] = UNKNOWN_INSTRUCTION
            self.inst_keys.append( (startErr, byteLenErr) )
            self.error_index = None

        # This is a jump/call command
        labelAddr = None
        operator = instruction.split(" ")[0]
        if operator.lower() in ("jmp","jz","jnz","call"):
            fields = instruction.split()
            if len(fields) > 1:
                instructionOp = fields[0]

                validOffset = False
                try:
                    offset = int(fields[1], 16)
                    validOffset = True
                except ValueError:
                    # Some calls do not have a direct offset (e.g. 'CALL [ebx + 0x0c]')
                    pass

                # Remember! jump immediate values are signed!
                if validOffset:
                    if len(fields[1].replace("0x","")) == 8:
                        if offset > 0x7FFFFFFF:
                            offset -= 0x100000000

                    elif len(fields[1].replace("0x","")) == 4:
                        if offset > 0x7FFF:
                            offset -= 0x10000

                    elif len(fields[1].replace("0x","")) == 2:
                        if offset > 0x7F:
                            offset -= 0x100

                    labelAddr = startIdx+byteLen+offset
                    self.label_addr.append(hex(labelAddr))
                    label = "label_%s"%hex(labelAddr)
                    instruction = "%-15s ; %s" % (instructionOp+" "+label, "%s = %s signed = addr[%s]" % (repr(fields[1]), repr(hex(offset)), repr(hex(labelAddr))))

        self.machine_code[ (startIdx, byteLen) ] = instruction
        self.inst_keys.append( (startIdx, byteLen) )
        self.inst_length[startIdx] = byteLen

        return labelAddr

    def doLinearSweep(self):
        pass

    def doRecursiveDescent(self, operator, addr):

        utils.logger.debug("Recursive Descent DeferAddr: %s" % repr([ hex(x) for x in self.postpone_addr]))

        #if self.index >= (len(self.objectSource)-1):
        #    self._completedRecursiveDescent = True

        if operator in FUNC_END:
            utils.logger.debug("   Func End!")
            # set counter to first deferred address and remove from list
            try:
                while True:
                    self.index = self.postpone_addr.pop()
                    utils.logger.debug("   Selected Idx: %s" %hex(self.index))
                    # So tricky! sometimes you start decoding once you return
                    # from a call and discover that you've already decoded this!
                    # in this case, treat it as an implicit return statement.
                    # This will keep you out of an infinite loop.
                    if not self.decoded[self.index]:
                        utils.logger.debug("      ...Commited")
                        break
            except:
                utils.logger.debug("   Completed Recursive Descent!")
                self._completedRecursiveDescent = True
        else:

            if operator in JUMP_INST:
                utils.logger.debug("   Jump...")
                # set counter to target
                self.index = addr
                # continue...
            elif operator in JCC_INST:
                utils.logger.debug("   Jcc...")
                # add target to defer list
                if len(self.decoded) <= self.index:
                    utils.logger.debug("      Last Byte!!!")
                elif not self.decoded[addr]:
                    self.postpone_addr.append(addr)
                # update counter by size of instruction (already done)
                # continue...
            elif operator in CALL_INST:
                utils.logger.debug("   Call... Addr: %s" % hex(addr))
                # add next instruction address to defer list
                # Note: the currentIdx has already been bumped by the current
                # instuction length (thus, is already pointing to the beginning of
                # the next instruction)
                if len(self.decoded) <= self.index:
                    utils.logger.debug("      Last Byte!!!")
                elif not self.decoded[self.index]:
                    utils.logger.debug("      New Byte! Keeping Addr: %s" % hex(self.index))
                    self.postpone_addr.append(self.index)
                else:
                    utils.logger.debug("      OLD Byte")
                # set counter to target
                self.index = addr
                # continue...
            else:
                utils.logger.debug("   Continue...")
                if len(self.decoded) <= self.index:
                    utils.logger.debug("      Last Byte!!!")
                elif not self.decoded[self.index]:
                    utils.logger.debug("      New Byte!")
                    # update counter by size of instruction (already done)
                else:
                    utils.logger.debug("      OLD Byte")
                    # update counter by size of instruction (NOT already done)
                    self.index = self.index + self.inst_length[self.index]

                # continue...

    def isRecursiveDescentComplete(self):
        utils.logger.debug("Recursive Descent Complete? %s  [%s and %s]" % (
            str(len(self.postpone_addr) == 0 and self._completedRecursiveDescent),
            str(len(self.postpone_addr) == 0),
            str(self._completedRecursiveDescent),
        ))
        return len(self.postpone_addr) == 0 and self._completedRecursiveDescent


    def markError(self, startIdx=None, byteLen=1):
        if startIdx == None:
            startIdx = self.index
        self.index = startIdx+byteLen
        for idx in range(startIdx, startIdx+byteLen ):
            self.decoded[idx] = None
            if self.error_index == None:
                self.error_index = []
            self.error_index.append(idx)

    def getCurIdx(self):
        return self.index

    def hasDecoded(self, idx):
        return self.decoded[idx]

    def isComplete(self):
        return self.decoded.count(False) == 0 and self.decoded.count(None) == 0

    def isSweepComplete(self):
        return self.index >= int(len(self.objectSource))

    def _showUnknownBytes(self, startIdx, endIdx):
        lastInstructionBytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[startIdx:endIdx])

        byteSections = []
        secLen = 27
        byteLen = 9
        for rowNum, blkIdx in enumerate(range(0, len(lastInstructionBytes), secLen)):
            subAddr = hex(startIdx+(rowNum*byteLen))
            byteSections.append( (subAddr, lastInstructionBytes[blkIdx:blkIdx+secLen]))

        prefix, postfix = utils.colors.YELLOW, utils.colors.NORMAL
        for row in byteSections:
            addr, partialBytes = row
            utils.logger.info(" %s%-3s   %-5s   %-30s ▏     %s%s" % ( prefix, '--', addr, partialBytes, UNKNOWN_INSTRUCTION, postfix) )

    def showDecodeProgress(self, detail=False):
        utils.logger.info("")

        percDecoded = (self.decoded.count(True) / float(len(self.decoded)))*100.0
        utils.logger.info("")
        utils.logger.info("  Address     Machine Code                        Disassembly Instruction ")
        utils.logger.info("  _______     ____________                        ________________________")
        utils.logger.info("                               ")


        sortedinst_keys = sorted(self.inst_keys)
        for idx, instKey in enumerate(sortedinst_keys):
            startIdx, instLen = instKey

            # check if there are skipped bytes...

            if idx > 0:
                lastStartIdx, lastInstLen = sortedinst_keys[idx-1]
                if False in self.decoded[lastStartIdx+lastInstLen:startIdx]:
                    self._showUnknownBytes(lastStartIdx+lastInstLen, startIdx)

            instruction = self.machine_code[instKey]
            #instructionBytes = repr(self.input[startIdx:startIdx+instLen])
            instructionBytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[startIdx:startIdx+instLen])
            prefix, postfix = utils.colors.NORMAL, utils.colors.NORMAL
            if instruction == UNKNOWN_INSTRUCTION:
                prefix = utils.colors.RED
            addr = hex(startIdx)
            if addr in self.label_addr:
                label = "label_%s"%addr
                utils.logger.info("         %-5s   %-30s   %s:" % ( "", "", label) )
            utils.logger.info(" %s %-5s       %-30s      %s%s" % (prefix, addr, instructionBytes, instruction, postfix) )

        if self.error_index != None:
            startIdx, instLen = self.error_index[0], len(self.error_index)
            self._showUnknownBytes(startIdx, startIdx+instLen, utils.colors.RED)
        elif False in self.decoded:
            startIdx, instLen = sortedinst_keys[-1]
            unknownStartIdx = startIdx+instLen
            endIdx = len(self.objectSource)
            self._showUnknownBytes(unknownStartIdx, endIdx, utils.colors.YELLOW)

       