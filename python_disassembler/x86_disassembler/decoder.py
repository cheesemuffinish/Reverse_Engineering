import logging

from constants import *
from error import *
from operatorTable import OP_LOOKUP, OPERAND_LOOKUP, PREFIX_SET, PREFIX_OP
import modrm

#sib.showSibTable()
#import sys
#sys.exit(0)
import utils

class X86Decoder:
    # has a reference to the DecoderState instance

    # knows how do decode x86 at the given byte and return an instruction with
    # params + the length of the decoded instruction (None means no valid decoding was found).

    def __init__(self, decoderState):
        self.state = decoderState

    # Instruction fields (bit len):
    # prefix(8), opcode(8), modrm(8=2|3|3), sib(8=2|3|3), displacement(8 or 16 or 32), immediate(32)
    def decodeSingleInstruction(self):
        utils.logger.debug("Next instruction...")
        # Step 1: get the operation. One of two possibilities:

        # { opcode : Operator   } ... assume no MODRM value,
        # { opcode : { /r : Operator }  }  ... assume MODRM, get reg value for key lookup

        # Step 2: given the specific operation (XOR, opcode, [modrm]), parse the rest

        # { (operator, opcode) : ( OpEnc, remaining Opcode values, operands) }
        #      operands = (operand1, operand2, operand3, operand4)

        assemblyInstruction = []
        startIdx = self.state.getCurIdx()

        utils.logger.debug("   StartIdx: %s" %str(startIdx))

        instructionLen = 1
        prefixOffset = 0

        opcodeByte = self.state.objectSource[startIdx]

        prefix, modrmByte, sibByte = None, None, None

        try:

            if opcodeByte in PREFIX_SET:

                prefix = opcodeByte
                prefixOffset = 1
                instructionLen += 1
                opcodeByte =  self.state.objectSource[startIdx+prefixOffset]


            operatorDict = OP_LOOKUP[(prefix, opcodeByte)]



            # Grab the modrm...
            if (startIdx+1+prefixOffset) < len(self.state.objectSource):
                #utils.logger.debug("Has ModRM...")
                modrmByte  = self.state.objectSource[startIdx+1+prefixOffset]

            # Grab the sib...
            if (startIdx+2+prefixOffset) < len(self.state.objectSource):
                #utils.logger.debug("Has Sib...")
                sibByte    = self.state.objectSource[startIdx+2+prefixOffset]

            #print("prefix %s opcodeByte %s modrm %s : dict %s" % (repr(prefix), hex(opcodeByte), str(modrmByte), repr(operatorDict)))

            if modrmByte != None:
                reg = modrm.getRegVal(modrmByte)
                if reg in operatorDict:
                    operator = operatorDict[reg]
                else:
                    operator = operatorDict[None]
            else:
                operator = operatorDict[None]
        except:
            raise InvalidOpcode("Opcode: %s" % hex(opcodeByte))

        assemblyInstruction.append(operator)

        try:
            opEnc, remOps, operands = OPERAND_LOOKUP[ (operator, opcodeByte) ]
        except:

            raise InvalidOperatorTranslation("Operator: %s Opcode: %s" % (operator, hex(opcodeByte)))

        """
        if operator in ('LEA',):
            utils.logger.setLevel(logging.DEBUG)
        else:
            utils.logger.setLevel(logging.INFO)
        """
        log = "   Op[%s:%s] Prefix[%s] Enc[%s] remOps[%s] Operands%s" % (
            operator, hex(opcodeByte), str(prefix), str(opEnc), str(remOps), str(operands)
            )
        utils.logger.debug(log)

        assemblyOperands = []

        # Process the MODRM
        if opEnc.hasModrm:
            if modrmByte == None:
                raise RuntimeError("Expected ModRM byte but there arn't any bytes left.")

            instructionLen += 1
            modRmVals, modRmTrans = modrm.translate(modrmByte)

            utils.logger.debug("   MODRM: %s" %str(modRmVals))
            utils.logger.debug("   MODRM: %s" %str(modRmTrans))

        # Process the SIB
        if opEnc.hasModrm and modRmTrans.hasSib:
            if sibByte == None:
                raise RuntimeError("Expected SIB byte but there arn't any bytes left.")

            sibVals, sibTrans = sib.translate(sibByte)

            utils.logger.debug("   SIB: %s" %str(sibVals))
            utils.logger.debug("   SIB: %s" %str(sibTrans))
            instructionLen += 1


        # parse displacement
        disp8, disp32 = None, None

        # check for if there is an explicit disp8 in modrm and sib bytes, or...
        # check if this is the base=EBP exception in the sib byte
        if opEnc.hasModrm and modRmTrans.hasDisp8 or opEnc.hasModrm and modRmTrans.hasSib and sibTrans.hasDisp8 or \
            opEnc.hasModrm and modRmTrans.hasSib and modRmVals.mod == 1 and sibVals.base == 5:

            utils.logger.debug("   Getting disp8...")
            disp8 = self.state.objectSource[startIdx+instructionLen]
            instructionLen += 1

        # check for if there is an explicit . disp32 in modrm and sib bytes, or...
        # check if this is the base=EBP exception in the sib byte
        elif opEnc.hasModrm and modRmTrans.hasDisp32 or opEnc.hasModrm and modRmTrans.hasSib and sibTrans.hasDisp32 or \
             opEnc.hasModrm and modRmTrans.hasSib and modRmVals.mod in (0,2) and sibVals.base == 5:

            utils.logger.debug("   Getting disp32...")
            disp32 = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+4]
            # note: flip to little endian
            disp32.reverse()
            instructionLen += 4

        # parse immediate
        """
        if 'id' in remOps:
            utils.logger.debug("   Getting imm32...")
            imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+4]
            # note: flip to little endian
            imm.reverse()
            instructionLen += 4
        """
        imm = None

        # Add all of the processed arguments to the assembly instruction
        for operand in operands:

            decodedTranslatedValue = None

            if operand == None:
                break

            # This is an exception... eax *is* the operand
            if operand == OpUnit.eax:
                decodedTranslatedValue = 'eax'

            if operand.name in (OpUnit.rm.name, OpUnit.reg.name, ):
                # operand is from MODRM
                if opEnc.hasModrm:
                    decodedTranslatedValue = getattr(modRmTrans, operand.name)
                # operand is derived from the opcode
                else:
                    decodedTranslatedValue = REGISTER[ remOps[0] ]

            # operand is an immediate value
            elif operand.name in (OpUnit.imm32.name, ):

                utils.logger.debug("   Getting imm32...")
                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+4]
                # note: flip to little endian
                imm.reverse()
                instructionLen += 4

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.imm16.name, ):

                utils.logger.debug("   Getting imm16...")
                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+2]
                # note: flip to little endian
                imm.reverse()
                instructionLen += 2

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.imm8.name, ):

                utils.logger.debug("   Getting imm8...")
                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+1]
                instructionLen += 1

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.one.name, ):

                utils.logger.debug("   Setting one...")
                instructionLen += 0

                decodedTranslatedValue = '1'

            # replace any sib templates with the actual sib operation
            if opEnc.hasModrm and modRmTrans.hasSib:
                sibInst = sibTrans.scaledIndexBase

                # note, there is an exception for the SIB for a base of ESP
                # only if the modrm has not already specified to use the displacement
                if not modRmTrans.hasDisp8:
                    #utils.logger.debug("   SIB base=5 disp8 exception...")
                    if modRmVals.mod == 1:
                        sibInst = sibInst + ' + disp8 + [ebp]'

                elif not modRmTrans.hasDisp32:
                    #utils.logger.debug("   SIB base=5 disp32 exception...")
                    if modRmVals.mod == 0:
                        sibInst = sibInst + ' + disp32'
                    elif modRmVals.mod == 2:
                        sibInst = sibInst + ' + disp32 + [ebp]'

                decodedTranslatedValue = decodedTranslatedValue.replace(modrm.SIB_TEMPLATE, sibInst)

            # Note, only the correct operands will have the necessary
            # string template to insert the displacement

            if disp8 != None:
                #utils.logger.debug("   Adding disp8...")
                hexVal =   "0x"+''.join('{:02x}'.format(x) for x in (disp8,))
                decodedTranslatedValue = decodedTranslatedValue.replace("disp8",hexVal)

            if disp32 != None:
                #utils.logger.debug("   Adding disp32...")
                hexVal =  "0x"+''.join('{:02x}'.format(x) for x in disp32)

                decodedTranslatedValue = decodedTranslatedValue.replace("disp32",hexVal)

            assemblyOperands.append(decodedTranslatedValue)


        if None in assemblyOperands:

            raise InvalidTranslationValue()

        assemblyInstruction.append(", ".join(assemblyOperands))
        assemblyInstructionStr = " ".join(assemblyInstruction)

        #print(assemblyInstructionStr)
        utils.logger.debug("   Final Instruction: %s"% repr(assemblyInstructionStr))
        targetAddr = self.state.markDecoded(startIdx, instructionLen, assemblyInstructionStr)

        return operator, targetAddr

    #def