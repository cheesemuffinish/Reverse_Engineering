import logging

from constants import *

import modrm
import utils

class InvalidOpcode(Exception): pass
class InvalidOperatorTranslation(Exception): pass
class InvalidTranslationValue(Exception): pass

def setOpLookup(operator, op):
    global OP_LOOKUP

    prefix, reg = None, None
    if isinstance(op, tuple):
        #print(repr(op))
        if len(op) == 2:
            opcode, reg = op[0], ord(op[1])
        elif len(op) == 3:
            prefix, opcode, reg = ord(op[0]), op[1], op[2]

            if reg != None:
                reg = ord(reg)
    else:
        opcode = op

    #if operator == "MOV":
    #    print(repr(reg), repr(op))

    if isinstance(opcode, str):
        key = (prefix,ord(opcode))
    else:
        key = (prefix,opcode)

    if key not in OP_LOOKUP:
        OP_LOOKUP[key] = {}

    OP_LOOKUP[key][reg] = operator


# { opcode : Operator   } ... assume no MODRM value,
# { opcode : { /r val : Operator }  }  ... assume MODRM, get reg value for key lookup
OP_LOOKUP = {}

# { (operator, opcode) : ( OpEnc, remaining Opcode values, operands) }
#      where: operands = (operand1, operand2, operand3, operand4)
OPERAND_LOOKUP = {}

# this is tallied at the end
SUPPORTED_OPERATORS = set()

# LOCK = 0xF0
# REPNE/REPNZ = 0xF2
# REP/REPE/REPZ = 0xF3
PREFIX_OP = {
    ord('\x0F'): ("IMUL","JZ","JNZ"),
    ord('\xF0'): ("LOCK",),
    ord('\xF2'): ("REPNE", "REPNZ"),
    ord('\xF3'): ("REP", "REPE", "REPZ")
}

PREFIX_SET = PREFIX_OP.keys()

#############################
####      Add OpCode     ####
#############################
operator = "ADD"
for op in ('\x05', ('\x81','\x00'), ('\x83','\x00'), '\x01', '\x03',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x05'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x01'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x03'))] = (OpEnc.RM, ('/r'),  (OpUnit.reg, OpUnit.rm,  None, None) )


#############################
####      And OpCode     ####
#############################
operator = "AND"
for op in ('\x25', ('\x81','\x04'), ('\x83','\x04'), '\x21', '\x23',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x25'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x21'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x23'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,  None, None) )

#############################
####     Call OpCode     ####
#############################
operator = "CALL"
for op in ('\xE8', ('\xFF','\x02'), '\x9A', ('\xFF','\x03'), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xE8'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) ) 
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,    None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x9A'))] = (OpEnc.D, ('cp'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,    None,  None, None) )

#############################
####     Call CLFLUSH    ####
#############################
operator = "CLFLUSH"
for op in ('\xAE','\x07'):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xAE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )


#############################
####      CMP OpCode     ####
#############################
operator = "CMP"
for op in ('\x3D', ('\x81','\x07'), ('\x83','\x07'), '\x39', '\x3B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x3D'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x39'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x3B'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,  None, None) )

#############################
####      DEC OpCode     ####
#############################
operator = "DEC"
for op in (('\xFE','\x01'), ('\xFF','\x01'),):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x48')+reg )

OPERAND_LOOKUP[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

#############################
####      IDIV OpCode    ####
#############################
operator = "IDIV"
for op in ( ('\xF7','\x07'), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

#############################
####      IMUL OpCode    ####
#############################
operator = "IMUL"
for op in ( ('\xF7','\x05'), ('\x0F','\xAF', None), '\x6B', '\x69' ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xAF'))] = (OpEnc.RM,  tuple(), (OpUnit.reg, OpUnit.rm, None, None) )
OPERAND_LOOKUP[(operator,ord('\x6B'))] = (OpEnc.RMI,  tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm8, None) )
OPERAND_LOOKUP[(operator,ord('\x69'))] = (OpEnc.RMI,  tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm32, None) )

#############################
####      INC OpCode     ####
#############################
operator = "INC"
for op in (('\xFE','\x00'), ('\xFF','\x00'),):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x40')+reg )

OPERAND_LOOKUP[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x40')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

#############################
####      JMP OpCode     ####
#############################
operator = "JMP"
for op in ('\xEB','\xE9', ('\xFF','\x04'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xEB'))] = (OpEnc.D, ('cd'),  (OpUnit.imm8, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xE9'))] = (OpEnc.D, ('cd'),  (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

#############################
####      JZ OpCode      ####
#############################
operator = "JZ"
for op in (('\x0F','\x84',None), '\x74'):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x84'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x74'))] = (OpEnc.D, ('cb'), (OpUnit.imm8, None, None, None) )

#############################
####      JNZ OpCode     ####
#############################
operator = "JNZ"
for op in (('\x0F','\x85',None), '\x75'):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x85'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x75'))] = (OpEnc.D, ('cb'), (OpUnit.imm8, None, None, None) )

#############################
####      LEA OpCode     ####
#############################
operator = "LEA"
for op in ('\x8D',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x8D'))] = (OpEnc.RM,  ('/r'), (OpUnit.reg, OpUnit.rm, None, None) )

#############################
####      MOV OpCode     ####
#############################
operator = "MOV"
for op in ('\x89', '\x8B', '\xA1', '\xA3', ('\xC7','\x00'),):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\xB8')+reg )

OPERAND_LOOKUP[(operator,ord('\x89'))] = (OpEnc.MR, ('/r'), (OpUnit.rm, OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x8B'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm, None, None) )
OPERAND_LOOKUP[(operator,ord('\xC7'))] = (OpEnc.MI, ('id'), (OpUnit.rm, OpUnit.imm32, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\xB8')+reg)] = (OpEnc.OI, (reg,), (OpUnit.reg, OpUnit.imm32, None, None) )

#############################
####    MOVSD OpCode     ####
#############################
operator = "MOVSD"
for op in ('\xA5',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA5'))] = (OpEnc.NP, tuple(), (None, None, None, None) )

#############################
####      MUL OpCode     ####
#############################
operator = "MUL"
for op in (('\xF7','\x04'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

#############################
####      NEG OpCode     ####
#############################
operator = "NEG"
for op in (('\xF7','\x03'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

#############################
####      NOP OpCode     ####
#############################
operator = "NOP"
for op in ('\x90', ('\x0F','\x1F','\x00'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x90'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x1F'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

#############################
####      NOT OpCode     ####
#############################
operator = "NOT"
for op in (('\xF7','\x02'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.RM,  tuple(), (OpUnit.rm, None, None, None) )

#############################
####      OR OpCode      ####
#############################
operator = "OR"
for op in ('\x0D',('\x81','\x01'),('\x83','\x01'),'\x09','\x0B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x0D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x09'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x0B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

#############################
####      OUT OpCode     #### TODO
#############################
operator = "Out"
for op in ('\xE7'):
    setOpLookup(operator, op)
OPERAND_LOOKUP[(operator,ord('\xE7'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )

#############################
####      POP OpCode     ####
#############################
operator = "POP"
for op in ( ('\x8F','\x00'), ):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x58')+reg )

OPERAND_LOOKUP[(operator,ord('\x8F'))] = (OpEnc.M, ('/x00'), (OpUnit.rm,  None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x58')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

#############################
####      PUSH OpCode    ####
#############################
operator = "PUSH"
for op in ( ('\xFF','\x06'), '\x68' ):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x50')+reg )

OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x68'))] = (OpEnc.I,  ('id'), (OpUnit.imm32, None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x50')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

###################################
####    REPNE CMPSD OpCode     ####
###################################

operator = "REPNE CMPSD"
for op in ( ('\xF2','\xA7',None), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA7'))] = (OpEnc.NP, tuple(), (None, None, None, None) )

#############################
####      RETF OpCode    ####
#############################
operator = "RETF"
for op in ( '\xCB', '\xCA', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xCB'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xCA'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None) )

#############################
####      RETN OpCode    ####
#############################
operator = "RETN"
for op in ( '\xC3', '\xC2', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xC3'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xC2'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None) )

#############################
####      SAL OpCode     ####
#############################
operator = "SAL"
setOpLookup(operator, ('\xD1','\x04'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

#############################
####      SAR OpCode     ####
#############################
operator = "SAR"
setOpLookup(operator, ('\xD1','\x07'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

#############################
####      SBB OpCode     ####
#############################
operator = "SBB"
for op in ('\x1D',('\x81','\x03'),('\x83','\x03'),'\x19','\x1B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x1D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x19'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x1B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

#############################
####      SHR OpCode     ####
#############################
operator = "SHR"
setOpLookup(operator, ('\xD1','\x05'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )


#############################
####      SUB OpCode     ####
#############################
operator = "SUB"
for op in ('\x2D',('\x81','\x05'),('\x83','\x05'),'\x29','\x2B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x2D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x29'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x2B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

#############################
####      TEST OpCode    ####
#############################
operator = "TEST"
for op in ('\xA9', ('\xF7','\x00'),'\x85',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA9'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x85'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,  None, None) )

#############################
####      XOR OpCode     ####
#############################
operator = "XOR"
for op in ('\x35', ('\x81','\x06'), '\x31', '\x33', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x35'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x31'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x33'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,  None, None) )


# Gather a list of supported operators
for operator, opcode in list(OPERAND_LOOKUP.keys()):
    SUPPORTED_OPERATORS.add(operator)

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