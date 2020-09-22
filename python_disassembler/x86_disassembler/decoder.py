import utils
from x86.constants import *

UNKNOWN_INSTRUCTION = "UNKNOWN"

class DecoderState:
    contents = None     # original object source as a python string

    _hasDecoded = None   # bool array, indicates which bytes have been decoded. None is an error
    objectSource = None  # bytearry of the object source

    _currentIdx = 0      # The current index to be decoded

    instructions = None  # mapping of index to instructions
    instructionKeys = None
    instructionLens = None

    runningErrorIdx = None  # keep track of error bytes indexes

    labelAddresses = None

    deferAddresses = None

    def __init__(self, objectFile=None, objectStr=None):
        self.instructions = {}
        self.instructionKeys = []
        self.instructionLens = {}
        self.labelAddresses = []
        self.deferAddresses = []

        if objectFile:
            with open(objectFile,'rb') as fh:
                self.contents = fh.read()
        elif objectStr:
            self.contents = objectStr

        else:
            RuntimeError("Must provide either a file or string containing object code.")

        self.objectSource = bytearray(self.contents)
        self._hasDecoded = [False]*len(self.objectSource)


    def markDecoded(self, startIdx, byteLen, instruction):
        # don't do anything if this has already been decoded!
        decodedPath = set()
        for idx in range(startIdx, startIdx+byteLen ):
            decodedPath.add(self._hasDecoded[idx])
        if True in decodedPath:
            return None

        self._currentIdx = startIdx+byteLen
        for idx in range(startIdx, startIdx+byteLen ):
            self._hasDecoded[idx] = True

        if self.runningErrorIdx != None:
            startErr = self.runningErrorIdx[0]
            byteLenErr = len(self.runningErrorIdx)
            self.instructions[ (startErr, byteLenErr) ] = UNKNOWN_INSTRUCTION
            self.instructionKeys.append( (startErr, byteLenErr) )
            self.runningErrorIdx = None

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
                    self.labelAddresses.append(hex(labelAddr))
                    label = "label_%s"%hex(labelAddr)
                    instruction = "%-15s ; %s" % (instructionOp+" "+label, "%s = %s signed = addr[%s]" % (repr(fields[1]), repr(hex(offset)), repr(hex(labelAddr))))

        self.instructions[ (startIdx, byteLen) ] = instruction
        self.instructionKeys.append( (startIdx, byteLen) )
        self.instructionLens[startIdx] = byteLen

        return labelAddr

    def doLinearSweep(self):
        pass

    


    def markError(self, startIdx=None, byteLen=1):
        if startIdx == None:
            startIdx = self._currentIdx
        self._currentIdx = startIdx+byteLen
        for idx in range(startIdx, startIdx+byteLen ):
            self._hasDecoded[idx] = None
            if self.runningErrorIdx == None:
                self.runningErrorIdx = []
            self.runningErrorIdx.append(idx)

    def getCurIdx(self):
        return self._currentIdx

    def hasDecoded(self, idx):
        return self._hasDecoded[idx]

    def isComplete(self):
        return self._hasDecoded.count(False) == 0 and self._hasDecoded.count(None) == 0

    def isSweepComplete(self):
        return self._currentIdx >= int(len(self.objectSource))

    def _showUnknownBytes(self, startIdx, endIdx, color=utils.colors.YELLOW):
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
        if detail:
            utils.logger.info( utils.hexdump(self.contents, hasDecoded=self._hasDecoded) )

        percDecoded = (self._hasDecoded.count(True) / float(len(self._hasDecoded)))*100.0
        utils.logger.info("")
        utils.logger.info("%3.3f %% Decoded"%percDecoded)
        utils.logger.info("")
        utils.logger.info("Inst#  Addr    Bytes                                Assembly")

        sortedInstructionKeys = sorted(self.instructionKeys)
        for idx, instKey in enumerate(sortedInstructionKeys):
            startIdx, instLen = instKey

            # check if there are skipped bytes...

            if idx > 0:
                lastStartIdx, lastInstLen = sortedInstructionKeys[idx-1]
                if False in self._hasDecoded[lastStartIdx+lastInstLen:startIdx]:
                    self._showUnknownBytes(lastStartIdx+lastInstLen, startIdx)

            instruction = self.instructions[instKey]
            #instructionBytes = repr(self.contents[startIdx:startIdx+instLen])
            instructionBytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[startIdx:startIdx+instLen])
            prefix, postfix = utils.colors.NORMAL, utils.colors.NORMAL
            if instruction == UNKNOWN_INSTRUCTION:
                prefix = utils.colors.RED
            addr = hex(startIdx)
            if addr in self.labelAddresses:
                label = "label_%s"%addr
                utils.logger.info("       %-5s   %-30s   %s:" % ( "", "", label) )
            utils.logger.info(" %s%-3s   %-5s   %-30s      %s%s" % ( prefix, idx+1, addr, instructionBytes, instruction, postfix) )

        if self.runningErrorIdx != None:
            startIdx, instLen = self.runningErrorIdx[0], len(self.runningErrorIdx)
            self._showUnknownBytes(startIdx, startIdx+instLen, utils.colors.RED)
        elif False in self._hasDecoded:
            startIdx, instLen = sortedInstructionKeys[-1]
            unknownStartIdx = startIdx+instLen
            endIdx = len(self.objectSource)
            self._showUnknownBytes(unknownStartIdx, endIdx, utils.colors.YELLOW)

