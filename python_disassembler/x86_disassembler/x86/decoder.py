import logging

from x86.constants import *
from error import *
from x86.operatorTable import OP_LOOKUP, OPERAND_LOOKUP, PREFIX_SET, PREFIX_OP
from x86 import modrm, sib
import utils

class X86Decoder:

    def __init__(self, decoderState):
        self.state = decoderState


    def decodeSingleInstruction(self):


        assemblyInstruction = []
        startIdx = self.state.getCurIdx()

        

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
                
                modrmByte  = self.state.objectSource[startIdx+1+prefixOffset]

            # Grab the sib...
            if (startIdx+2+prefixOffset) < len(self.state.objectSource):
                
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

        log = "   Op[%s:%s] Prefix[%s] Enc[%s] remOps[%s] Operands%s" % (
            operator, hex(opcodeByte), str(prefix), str(opEnc), str(remOps), str(operands)
            )
       

        assemblyOperands = []

        # Process the MODRM
        if opEnc.hasModrm:
            if modrmByte == None:
                raise RuntimeError("Expected ModRM byte but there arn't any bytes left.")

            instructionLen += 1
            modRmVals, modRmTrans = modrm.translate(modrmByte)

        # Process the SIB
        if opEnc.hasModrm and modRmTrans.hasSib:
            if sibByte == None:
                raise RuntimeError("Expected SIB byte but there arn't any bytes left.")

            sibVals, sibTrans = sib.translate(sibByte)

       
            instructionLen += 1


        # parse displacement
        disp8, disp32 = None, None

        # check for if there is an explicit disp8 in modrm and sib bytes, or...
        # check if this is the base=EBP exception in the sib byte
        if opEnc.hasModrm and modRmTrans.hasDisp8 or opEnc.hasModrm and modRmTrans.hasSib and sibTrans.hasDisp8 or \
            opEnc.hasModrm and modRmTrans.hasSib and modRmVals.mod == 1 and sibVals.base == 5:

            
            disp8 = self.state.objectSource[startIdx+instructionLen]
            instructionLen += 1

        # check for if there is an explicit . disp32 in modrm and sib bytes, or...
        # check if this is the base=EBP exception in the sib byte
        elif opEnc.hasModrm and modRmTrans.hasDisp32 or opEnc.hasModrm and modRmTrans.hasSib and sibTrans.hasDisp32 or \
             opEnc.hasModrm and modRmTrans.hasSib and modRmVals.mod in (0,2) and sibVals.base == 5:

            
            disp32 = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+4]
            # note: flip to little endian
            disp32.reverse()
            instructionLen += 4

        # parse immediate

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

                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+4]
                # note: flip to little endian
                imm.reverse()
                instructionLen += 4

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.imm16.name, ):

                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+2]
                # note: flip to little endian
                imm.reverse()
                instructionLen += 2

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.imm8.name, ):

                imm = self.state.objectSource[startIdx+instructionLen:startIdx+instructionLen+1]
                instructionLen += 1

                decodedTranslatedValue = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif operand.name in (OpUnit.one.name, ):

                instructionLen += 0

                decodedTranslatedValue = '1'

            # replace any sib templates with the actual sib operation
            if opEnc.hasModrm and modRmTrans.hasSib:
                sibInst = sibTrans.scaledIndexBase

                # note, there is an exception for the SIB for a base of ESP
                # only if the modrm has not already specified to use the displacement
                if not modRmTrans.hasDisp8:
                    if modRmVals.mod == 1:
                        sibInst = sibInst + ' + disp8 + [ebp]'

                elif not modRmTrans.hasDisp32:
                    if modRmVals.mod == 0:
                        sibInst = sibInst + ' + disp32'
                    elif modRmVals.mod == 2:
                        sibInst = sibInst + ' + disp32 + [ebp]'

                decodedTranslatedValue = decodedTranslatedValue.replace(modrm.SIB_TEMPLATE, sibInst)

            # Note, only the correct operands will have the necessary
            # string template to insert the displacement

            if disp8 != None:
                hexVal =   "0x"+''.join('{:02x}'.format(x) for x in (disp8,))
                decodedTranslatedValue = decodedTranslatedValue.replace("disp8",hexVal)

            if disp32 != None:
                hexVal =  "0x"+''.join('{:02x}'.format(x) for x in disp32)

                decodedTranslatedValue = decodedTranslatedValue.replace("disp32",hexVal)

            assemblyOperands.append(decodedTranslatedValue)


        if None in assemblyOperands:

            raise InvalidTranslationValue()

        assemblyInstruction.append(", ".join(assemblyOperands))
        assemblyInstructionStr = " ".join(assemblyInstruction)

        #print(assemblyInstructionStr)
        targetAddr = self.state.markDecoded(startIdx, instructionLen, assemblyInstructionStr)

        return operator, targetAddr

    #def