

import logging
from constants import *
import modrm
import utils

#######################################
###            Setup                ###
#######################################
class Invalid_Opcode_Provided(Exception): pass
class Invalid_Operator_Value(Exception): pass
class Invalid_Value(Exception): pass

#########################################
####     Class Intel Disassembler    ####
#########################################
class Intel_Disassembler:
    def __init__(self, decoderState):
        self.state = decoderState

    def sequential_instruction(self):
        assembly_instruction = []
        current_index        = self.state.get_current_index()
        instruction_length   = 1
        instruction_offset   = 0
        current_byte         = self.state.objectSource[current_index]
        instruction_prefix   = None
        modrm_byte           = None 
        sib_byte             = None

        try:
            if current_byte in g_instruction_prefix_dictionary:
                instruction_prefix  = current_byte
                instruction_offset  = 1
                instruction_length += 1
                current_byte = self.state.objectSource[current_index + instruction_offset]

            dictionary_operator = g_find_opcode[(instruction_prefix, current_byte)]
            if (current_index + 1 + instruction_offset) < len(self.state.objectSource):
                modrm_byte = self.state.objectSource[current_index + 1 + instruction_offset]
            if (current_index + 2 + instruction_offset) < len(self.state.objectSource):
                sib_byte = self.state.objectSource[current_index + 2 + instruction_offset]
            if modrm_byte != None:
                dict_register = modrm.getRegVal(modrm_byte)
                if dict_register in dictionary_operator:
                    dict_operator = dictionary_operator[dict_register]
                else:
                    dict_operator = dictionary_operator[None]
            else:
                dict_operator = dictionary_operator[None]

        except:
            raise Invalid_Opcode_Provided("Error: Opcode Invalid !! %s" % hex(current_byte))

        assembly_instruction.append(dict_operator)
        try:
            opEnc, rem_operations, ops = g_find_operand[ (dict_operator, current_byte) ]
        except:

            raise Invalid_Operator_Value("Error: Opcode Invalid !! %s" % hex(current_byte))

        machine_code = []
        if opEnc.hasModrm:
            if modrm_byte == None:
                raise RuntimeError("Error: No bytes left !!")

            instruction_length += 1
            modrm_value, modrm_translation = modrm.translate(modrm_byte)

        if opEnc.hasModrm and modrm_translation.hasSib:
            if sib_byte == None:
                raise RuntimeError("Error:  No bytes left !")

            sib_value, sib_translation = sib.translate(sib_byte)
            instruction_length += 1

        disp8, disp32 = None, None

        if opEnc.hasModrm and modrm_translation.hasDisp8 or opEnc.hasModrm and modrm_translation.hasSib and sib_translation.hasDisp8 or \
            opEnc.hasModrm and modrm_translation.hasSib and modrm_value.mod == 1 and sib_value.base == 5:

            disp8 = self.state.objectSource[current_index+instruction_length]
            instruction_length += 1

        elif opEnc.hasModrm and modrm_translation.hasDisp32 or opEnc.hasModrm and modrm_translation.hasSib and sib_translation.hasDisp32 or \
             opEnc.hasModrm and modrm_translation.hasSib and modrm_value.mod in (0,2) and sib_value.base == 5:

            disp32 = self.state.objectSource[current_index+instruction_length:current_index+instruction_length+4]
            disp32.reverse()
            instruction_length += 4

        imm = None
        for i in ops:

            decoded_value = None
            if i == None:
                break
            if i == OpUnit.eax:
                decoded_value = 'eax'
            if i.name in (OpUnit.rm.name, OpUnit.reg.name):
                if opEnc.hasModrm:
                    decoded_value = getattr(modrm_translation, i.name)
                else:
                    decoded_value = REGISTER[ rem_operations[0] ]
            elif i.name in (OpUnit.imm32.name):
                imm = self.state.objectSource[current_index + instruction_length:current_index + instruction_length + 4]
                imm.reverse()
                instruction_length += 4
                decoded_value = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif i.name in (OpUnit.imm16.name):
                imm = self.state.objectSource[current_index + instruction_length:current_index + instruction_length + 2]
                imm.reverse()
                instruction_length += 2
                decoded_value = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif i.name in (OpUnit.imm8.name):
                imm = self.state.objectSource[current_index + instruction_length:current_index+instruction_length + 1]
                instruction_length += 1
                decoded_value = "0x"+''.join('{:02x}'.format(x) for x in imm)

            elif i.name in (OpUnit.one.name, ):
                instruction_length += 0
                decoded_value = '1'

            if opEnc.hasModrm and modrm_translation.hasSib:
                sibInst = sib_translation.scaledIndexBase

                if not modrm_translation.hasDisp8:
                    if modrm_value.mod == 1:
                        sibInst = sibInst + ' + disp8 + [ebp]'

                elif not modrm_translation.hasDisp32:
                    if modrm_value.mod == 0:
                        sibInst = sibInst + ' + disp32'
                    elif modrm_value.mod == 2:
                        sibInst = sibInst + ' + disp32 + [ebp]'

                decoded_value = decoded_value.replace(modrm.SIB_TEMPLATE, sibInst)

            if disp8 != None:
                hexVal =   "0x"+''.join('{:02x}'.format(x) for x in (disp8,))
                decoded_value = decoded_value.replace("disp8",hexVal)

            if disp32 != None:
                hexVal =  "0x"+''.join('{:02x}'.format(x) for x in disp32)
                decoded_value = decoded_value.replace("disp32",hexVal)

            machine_code.append(decoded_value)

        if None in machine_code:
            raise Invalid_Value()
        assembly_instruction.append(", ".join(machine_code))
        assembly_instructionStr = " ".join(assembly_instruction)
        return_address = self.state.has_been_decoded(current_index, instruction_length, assembly_instructionStr)
        return operator, return_address

###################################
####     Opcode Lookup Func    ####
###################################
def opcode_lookup(operator, current_opcode):

    global g_find_opcode
    current_instruction_prefix   = None
    current_register = None

    if isinstance(current_opcode, tuple):
        if len(current_opcode) == 2:
            temp_opcode, current_register = current_opcode[0], ord(current_opcode[1])
        elif len(current_opcode) == 3:
            instruction_prefix, temp_opcode, current_register = ord(current_opcode[0]), current_opcode[1], current_opcode[2]
            if current_register != None:
                current_register = ord(current_register)
    else:
        temp_opcode = current_opcode

    if isinstance(temp_opcode, str):
        key = (current_instruction_prefix,ord(temp_opcode))
    else:
        key = (current_instruction_prefix,temp_opcode)

    if key not in g_find_opcode:
        g_find_opcode[key] = {}

    g_find_opcode[key][current_register] = operator

g_find_opcode    = {}
g_find_operand   = {}
g_find_operator  = set()
g_instruction_prefix_operand = {
    ord('\x0F'): ("JNZ","JZ","IMUL"),
    ord('\xF0'): ("LOCK",),
    ord('\xF2'): ("REPNZ", "REPNE"),
    ord('\xF3'): ("REPZ","REPE", "REP")
}
g_instruction_prefix_dictionary = g_instruction_prefix_operand.keys()

############################################
####    OPCODES NEEDE FOR THIS PROJECT  ####
############################################


#############################
####      Add OpCode     ####
#############################
operator = "ADD"
for op in ('\x01', '\x03','\x05', ('\x81','\x00'), ('\x83','\x00')):
    opcode_lookup(operator, op) 
g_find_operand[(operator,ord('\x01'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x03'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,    None, None))
g_find_operand[(operator,ord('\x05'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8,  None, None))

#############################
####      And OpCode     ####
#############################
operator = "AND"
for op in ('\x21', '\x23','\x25', ('\x81','\x04'), ('\x83','\x04')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x21'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x23'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,    None, None))
g_find_operand[(operator,ord('\x25'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8,  None, None))


#############################
####     Call OpCode     ####
#############################
operator = "CALL"
for op in ('\x9A','\xE8', ('\xFF','\x02'), ('\xFF','\x03')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x9A'))] = (OpEnc.D, ('cp'), (OpUnit.imm32,  None, None, None))
g_find_operand[(operator,ord('\xE8'))] = (OpEnc.D, ('cd'), (OpUnit.imm32,  None, None, None)) 
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,     None, None, None))
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,     None, None, None))

#############################
####     Call CLFLUSH    ####
#############################
operator = "CLFLUSH"
for op in ('\xAE','\x07'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xAE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None))

#############################
####      CMP OpCode     ####
#############################
operator = "CMP"
for op in ('\x39', '\x3B','\x3D', ('\x81','\x07'), ('\x83','\x07')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x39'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,    None, None))
g_find_operand[(operator,ord('\x3B'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,     None, None))
g_find_operand[(operator,ord('\x3D'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32,  None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32,  None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8,   None, None))

#############################
####      DEC OpCode     ####
#############################
operator = "DEC"
for op in (('\xFE','\x01'), ('\xFF','\x01')):
    opcode_lookup(operator, op)
for reg in range(8):
    opcode_lookup(operator, ord('\x48')+reg )
g_find_operand[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None))
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None))

#############################
####      IDIV OpCode    ####
#############################
operator = "IDIV"
for op in (('\xF7','\x07')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None))

#############################
####      IMUL OpCode    ####
#############################
operator = "IMUL"
for op in (('\xF7','\x05'), ('\x0F','\xAF', None), '\x6B', '\x69' ):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x6B'))] = (OpEnc.RMI, tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm8, None))
g_find_operand[(operator,ord('\x69'))] = (OpEnc.RMI, tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm32, None))
g_find_operand[(operator,ord('\xF7'))] = (OpEnc.M,   tuple(), (OpUnit.rm, None, None, None))
g_find_operand[(operator,ord('\xAF'))] = (OpEnc.RM,  tuple(), (OpUnit.reg, OpUnit.rm, None, None))


#############################
####      INC OpCode     ####
#############################
operator = "INC"
for op in (('\xFE','\x00'), ('\xFF','\x00')):
    opcode_lookup(operator, op)
for reg in range(8):
    opcode_lookup(operator, ord('\x40')+reg )
g_find_operand[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None))
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None))
for reg in range(8):
    g_find_operand[(operator, ord('\x40')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None))

#############################
####      JMP OpCode     ####
#############################
operator = "JMP"
for op in ('\xEB','\xE9', ('\xFF','\x04')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xEB'))] = (OpEnc.D, ('cd'),  (OpUnit.imm8,  None, None, None))
g_find_operand[(operator,ord('\xE9'))] = (OpEnc.D, ('cd'),  (OpUnit.imm32, None, None, None))
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm,    None, None, None))

#############################
####      JZ OpCode      ####
#############################
operator = "JZ"
for op in (('\x0F','\x84',None), '\x74'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x84'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None))
g_find_operand[(operator,ord('\x74'))] = (OpEnc.D, ('cb'), (OpUnit.imm8,  None, None, None))

#############################
####      JNZ OpCode     ####
#############################
operator = "JNZ"
for op in (('\x0F','\x85',None), '\x75'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x85'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None))
g_find_operand[(operator,ord('\x75'))] = (OpEnc.D, ('cb'), (OpUnit.imm8,  None, None, None))

#############################
####      LEA OpCode     ####
#############################
operator = "LEA"
for op in ('\x8D',):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x8D'))] = (OpEnc.RM,  ('/r'), (OpUnit.reg, OpUnit.rm, None, None))

#############################
####      MOV OpCode     ####
#############################
operator = "MOV"
for op in ('\x89', '\x8B', '\xA1', '\xA3', ('\xC7','\x00'),):
    opcode_lookup(operator, op)
for reg in range(8):
    opcode_lookup(operator, ord('\xB8')+reg )
g_find_operand[(operator,ord('\x89'))] = (OpEnc.MR, ('/r'), (OpUnit.rm, OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x8B'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,   None, None))
g_find_operand[(operator,ord('\xC7'))] = (OpEnc.MI, ('id'), (OpUnit.rm, OpUnit.imm32, None, None))
for reg in range(8):
    g_find_operand[(operator, ord('\xB8')+reg)] = (OpEnc.OI, (reg,), (OpUnit.reg, OpUnit.imm32, None, None))

#############################
####    MOVSD OpCode     ####
#############################
operator = "MOVSD"
for op in ('\xA5',):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xA5'))] = (OpEnc.NP, tuple(), (None, None, None, None))

#############################
####      MUL OpCode     ####
#############################
operator = "MUL"
for op in (('\xF7','\x04')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None))

#############################
####      NEG OpCode     ####
#############################
operator = "NEG"
for op in (('\xF7','\x03')):
    opcode_lookup(operator, op)

g_find_operand[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None))

#############################
####      NOP OpCode     ####
#############################
operator = "NOP"
for op in ('\x90', ('\x0F','\x1F','\x00')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x90'))] = (OpEnc.NP, tuple(),      (None, None, None, None))
g_find_operand[(operator,ord('\x1F'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None))

#############################
####      NOT OpCode     ####
#############################
operator = "NOT"
for op in (('\xF7','\x02')):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xF7'))] = (OpEnc.RM,  tuple(), (OpUnit.rm, None, None, None))

#############################
####      OR OpCode      ####
#############################
operator = "OR"
for op in ('\x0D',('\x81','\x01'),('\x83','\x01'),'\x09','\x0B'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x0D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8,  None, None))
g_find_operand[(operator,ord('\x09'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x0B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm,    None, None))

#############################
####      OUT OpCode     #### TODO
#############################
operator = "Out"
for op in ('\xE7'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xE7'))] = (OpEnc.I, ('id',), (OpUnit.eax, OpUnit.imm32, None, None))

#############################
####      POP OpCode     ####
#############################
operator = "POP"
for op in (('\x8F','\x00')):
    opcode_lookup(operator, op)
for reg in range(8):
    opcode_lookup(operator, ord('\x58') + reg )
g_find_operand[(operator,ord('\x8F'))] = (OpEnc.M, ('/x00'), (OpUnit.rm,  None, None, None))
for reg in range(8):
    g_find_operand[(operator, ord('\x58')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None))

#############################
####      PUSH OpCode    ####
#############################
operator = "PUSH"
for op in (('\xFF','\x06'), '\x68'):
    opcode_lookup(operator, op)
for reg in range(8):
    opcode_lookup(operator, ord('\x50') + reg)
g_find_operand[(operator,ord('\xFF'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,          None, None, None))
g_find_operand[(operator,ord('\x68'))] = (OpEnc.I,  ('id'), (OpUnit.imm32,       None, None, None))
for reg in range(8):
    g_find_operand[(operator, ord('\x50')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None))

###################################
####    REPNE CMPSD OpCode     ####
###################################

operator = "REPNE CMPSD"
for op in (('\xF2','\xA7',None)):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xA7'))] = (OpEnc.NP, tuple(), (None, None, None, None))

#############################
####      RETF OpCode    ####
#############################
operator = "RETF"
for op in ('\xCB', '\xCA'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xCB'))] = (OpEnc.NP, tuple(),       (None, None, None, None))
g_find_operand[(operator,ord('\xCA'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None))

#############################
####      RETN OpCode    ####
#############################
operator = "RETN"
for op in ('\xC3', '\xC2'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\xC3'))] = (OpEnc.NP, tuple(),       (None, None, None, None))
g_find_operand[(operator,ord('\xC2'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None))

#############################
####      SAL OpCode     ####
#############################
operator = "SAL"
opcode_lookup(operator, ('\xD1','\x04'))
g_find_operand[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None))

#############################
####      SAR OpCode     ####
#############################
operator = "SAR"
opcode_lookup(operator, ('\xD1','\x07'))
g_find_operand[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None))

#############################
####      SBB OpCode     ####
#############################
operator = "SBB"
for op in ('\x1D',('\x81','\x03'),('\x83','\x03'),'\x19','\x1B'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x1D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8,  None, None))
g_find_operand[(operator,ord('\x19'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x1B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm,    None, None))

#############################
####      SHR OpCode     ####
#############################
operator = "SHR"
opcode_lookup(operator, ('\xD1','\x05'))
g_find_operand[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None))

#############################
####      SUB OpCode     ####
#############################
operator = "SUB"
for op in ('\x2D',('\x81','\x05'),('\x83','\x05'),'\x29','\x2B'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x2D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8,  None, None))
g_find_operand[(operator,ord('\x29'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x2B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm,    None, None))

#############################
####      TEST OpCode    ####
#############################
operator = "TEST"
for op in ('\xA9', ('\xF7','\x00'),'\x85'):
    opcode_lookup(operator, op)

g_find_operand[(operator,ord('\xA9'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\xF7'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x85'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,   None, None))

#############################
####      XOR OpCode     ####
#############################
operator = "XOR"
for op in ('\x35', ('\x81','\x06'), '\x31', '\x33'):
    opcode_lookup(operator, op)
g_find_operand[(operator,ord('\x35'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None))
g_find_operand[(operator,ord('\x31'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,   None, None))
g_find_operand[(operator,ord('\x33'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,    None, None))
for operator, opcode in list(g_find_operand.keys()):
    g_find_operator.add(operator)

