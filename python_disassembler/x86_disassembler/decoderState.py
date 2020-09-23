

import utils
import modrm
import logging


UNKNOWN_INSTRUCTION = "invalid_opcode"

###################################################
###       State of Linear Sweep Function        ###
###################################################
class Linear_Sweep_State:

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
                    pass

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
                    label = "offsettt_"
                    instruction = "%-15s ; %s" % (instructionOp+" "+label, "%s" %  hex(labelAddr))

        self.machine_code[ (startIdx, byteLen) ] = instruction
        self.inst_keys.append( (startIdx, byteLen) )
        self.inst_length[startIdx] = byteLen

        return labelAddr

    def linear_sweeper(self):
        pass

    def markError(self, startIdx=None, byteLen=1):
        if startIdx == None:
            startIdx = self.index
        self.index = startIdx+byteLen
        for idx in range(startIdx, startIdx+byteLen ):
            self.decoded[idx] = None
            if self.error_index == None:
                self.error_index = []
            self.error_index.append(idx)

    def get_current_index(self):
        return self.index

    def linear_sweep_complete(self):
        return self.decoded.count(False) == 0 and self.decoded.count(None) == 0

    def linear_sweep_finished(self):
        return self.index >= int(len(self.objectSource))

    def _showUnknownBytes(self, startIdx, endIdx):
        lastInstructionBytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[startIdx:endIdx])

        byteSections = []
        secLen = 27
        byteLen = 9
        for rowNum, blkIdx in enumerate(range(0, len(lastInstructionBytes), secLen)):
            subAddr = hex(startIdx+(rowNum*byteLen))
            byteSections.append( (subAddr, lastInstructionBytes[blkIdx:blkIdx+secLen]))

        for row in byteSections:
            addr, partialBytes = row
            utils.logger.info(" %-3s   %-5s   %-30s ▏     %s" % ( '--', addr, partialBytes, UNKNOWN_INSTRUCTION))

    def linear_sweep_progression(self, detail=False):
        utils.logger.info("")

        percDecoded = (self.decoded.count(True) / float(len(self.decoded)))*100.0
        utils.logger.info("")
        utils.logger.info("  Address     Machine Code                        Disassembly Instruction ")
        utils.logger.info("  _______     ____________                        ________________________")
        utils.logger.info("                               ")


        sortedinst_keys = sorted(self.inst_keys)
        for idx, instKey in enumerate(sortedinst_keys):
            startIdx, instLen = instKey

            if idx > 0:
                lastStartIdx, lastInstLen = sortedinst_keys[idx-1]
                if False in self.decoded[lastStartIdx+lastInstLen:startIdx]:
                    self._showUnknownBytes(lastStartIdx+lastInstLen, startIdx)

            instruction = self.machine_code[instKey]
            instructionBytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[startIdx:startIdx+instLen])
            addr = hex(startIdx)
            if addr in self.label_addr:
                label = "offset_%s"%addr
                utils.logger.info(label)
            utils.logger.info(" %-5s       %-30s      %s" % ( addr, instructionBytes, instruction))

        if self.error_index != None:
            startIdx, instLen = self.error_index[0], len(self.error_index)
            self._showUnknownBytes(startIdx, startIdx+instLen)
        elif False in self.decoded:
            startIdx, instLen = sortedinst_keys[-1]
            unknownStartIdx = startIdx+instLen
            endIdx = len(self.objectSource)
            self._showUnknownBytes(unknownStartIdx, endIdx)

       