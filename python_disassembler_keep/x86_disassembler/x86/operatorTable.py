from x86.constants import *

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

"""
# ADD
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    05 id               ADD EAX, imm32      I       Valid   Valid   Add imm32 to EAX.
    81 /0 id            ADD r/m32, imm32    MI      Valid   Valid   Add imm32 to r/m32.
    83 /0 ib            ADD r/m32, imm8     MI      Valid   Valid   Add sign-extended imm8 to r/m32.
    01 /r               ADD r/m32, r32      MR      Valid   Valid   Add r32 to r/m32.
    03 /r               ADD r32, r/m32      RM      Valid   Valid   Add r/m32 to r32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    RM      ModRM:reg (r, w)    ModRM:r/m (r)   NA          NA
    MR      ModRM:r/m (r, w)    ModRM:reg (r)   NA          NA
    MI      ModRM:r/m (r, w)    imm8            NA          NA
    I       EAX                 imm8            NA          NA
"""
operator = "ADD"
for op in ('\x05', ('\x81','\x00'), ('\x83','\x00'), '\x01', '\x03',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x05'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x01'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x03'))] = (OpEnc.RM, ('/r'),  (OpUnit.reg, OpUnit.rm,  None, None) )


"""
# AND
    Opcode          Instruction         Op/En   64-Bit  Compat  Description
    25 id           AND EAX, imm32      I       Valid   Valid   EAX AND imm32.
    81 /4 id        AND r/m32, imm32    MI      Valid   Valid   r/m32 AND imm32.
    83 /4 ib        AND r/m32, imm8     MI      Valid   Valid   r/m32 AND imm8 (sign-extended).
    21 /r           AND r/m32, r32      MR      Valid   Valid   r/m32 AND r32.
    23 /r           AND r32, r/m32      RM      Valid   Valid   r32 AND r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    RM      ModRM:reg (r, w)    ModRM:r/m (r)   NA          NA
    MR      ModRM:r/m (r, w)    ModRM:reg (r)   NA          NA
    MI      ModRM:r/m (r, w)    imm8            NA          NA
    I       EAX                 imm8            NA          NA
"""
operator = "AND"
for op in ('\x25', ('\x81','\x04'), ('\x83','\x04'), '\x21', '\x23',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x25'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x21'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x23'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,  None, None) )

"""
# CALL
    Opcode          Instruction         Op/En   64-Bit  Compat  Description
    E8 cd           CALL rel32          D       Valid   Valid   Call near, relative, displacement relative to
                                                                next instruction. 32-bit displacement sign
                                                                extended to 64-bits in 64-bit mode.
                                        ^--- Note: Changed from M to D... eratta?
    FF /2           CALL r/m32          M       N.E.    Valid   Call near, absolute indirect, address given in r/m32.
    9A cp           CALL ptr16:32       D       Invalid Valid   Call far, absolute, address given in operand.
    FF /3           CALL m16:32         M       Valid   Valid   In 64-bit mode: If selector points to a gate,
                                                                then RIP = 64-bit displacement taken from
                                                                gate; else RIP = zero extended 32-bit offset
                                                                from far pointer referenced in the instruction.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    D       Offset              NA              NA          NA
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "CALL"
for op in ('\xE8', ('\xFF','\x02'), '\x9A', ('\xFF','\x03'), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xE8'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) ) # Note: Changed from OpEnc.M to OpEnc.D... eratta?
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,    None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x9A'))] = (OpEnc.D, ('cp'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(),(OpUnit.rm,    None,  None, None) )


"""
# CMP
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    3D id               CMP EAX, imm32      I       Valid   Valid   Compare imm32 with EAX.
    81 /7 id            CMP r/m32, imm32    MI      Valid   Valid   Compare imm32 with r/m32.
    83 /7 ib            CMP r/m32, imm8     MI      Valid   Valid   Compare imm8 with r/m32.
    39 /r               CMP r/m32, r32      MR      Valid   Valid   Compare r32 with r/m32.
    3B /r               CMP r32, r/m32      RM      Valid   Valid   Compare r/m32 with r32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    RM      ModRM:reg (r)       ModRM:r/m (r)   NA          NA
    MR      ModRM:r/m (r)       ModRM:reg (r)   NA          NA
    MI      ModRM:r/m (r)       imm8            NA          NA
    I       EAX (r)             imm8            NA          NA
"""
operator = "CMP"
for op in ('\x3D', ('\x81','\x07'), ('\x83','\x07'), '\x39', '\x3B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x3D'))] = (OpEnc.I,  ('id'), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id'), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib'), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x39'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  OpUnit.reg,  None, None) )
OPERAND_LOOKUP[(operator,ord('\x3B'))] = (OpEnc.RM, ('/r'), (OpUnit.reg, OpUnit.rm,  None, None) )

"""
TODO: Test
# DEC
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    FE /1               DEC r/m8            M       Valid   Valid   Decrement r/m8 by 1.
    FF /1               DEC r/m32           M       Valid   Valid   Decrement r/m32 by 1.
    48+rd               DEC r32             O       N.E.    Valid   Decrement r32 by 1.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r, w)    NA              NA          NA
    O       opcode + rd (r, w)  NA              NA          NA
"""
operator = "DEC"
for op in (('\xFE','\x01'), ('\xFF','\x01'),):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x48')+reg )

OPERAND_LOOKUP[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x48')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

"""
# IDIV
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /7               IDIV r/m32          M       Valid   Valid   Signed divide EDX:EAX by r/m32, with result
                                                                    stored in EAX ← Quotient, EDX ← Remainder.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "IDIV"
for op in ( ('\xF7','\x07'), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

"""
# DIV
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /6               DIV r/m32           M       Valid   Valid   Unsigned divide EDX:EAX by r/m32, with
                                                                    result stored in EAX ← Quotient, EDX ←Remainder.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "DIV"
for op in ( ('\xF7','\x06'), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

"""
# IMUL
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /5               IMUL r/m32          M       Valid   Valid   EDX:EAX ← EAX ∗ r/m32.
    0F AF /r            IMUL r32, r/m32     RM      Valid   Valid   doubleword register ← doubleword register * r/m32.
    6B /r ib            IMUL r32, r/m32, imm8  RMI  Valid   Valid   doubleword register ← r/m32 ∗ sign-extended immediate byte.
    69 /r id            IMUL r32, r/m32, imm32 RMI  Valid   Valid   doubleword register ← r/m32 ∗ immediate doubleword.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r, w)    NA              NA          NA
    RM      ModRM:reg (r, w)    ModRM:r/m (r)   NA          NA
    RMI     ModRM:reg (r, w)    ModRM:r/m (r)   imm8/16/32  NA
"""
operator = "IMUL"
for op in ( ('\xF7','\x05'), ('\x0F','\xAF', None), '\x6B', '\x69' ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xAF'))] = (OpEnc.RM,  tuple(), (OpUnit.reg, OpUnit.rm, None, None) )
OPERAND_LOOKUP[(operator,ord('\x6B'))] = (OpEnc.RMI,  tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm8, None) )
OPERAND_LOOKUP[(operator,ord('\x69'))] = (OpEnc.RMI,  tuple(), (OpUnit.reg, OpUnit.rm, OpUnit.imm32, None) )

"""
# INC
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    FE /0               INC r/m8            M       Valid   Valid   Increment r/m byte by 1.
    FF /0               INC r/m32           M       Valid   Valid   Increment r/m doubleword by 1.
    40+ rd              INC r32             O       N.E.    Valid   Increment doubleword register by 1.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r, w)    NA              NA          NA
    O       opcode + rd (r, w)  NA              NA          NA
"""
operator = "INC"
for op in (('\xFE','\x00'), ('\xFF','\x00'),):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x40')+reg )

OPERAND_LOOKUP[(operator,ord('\xFE'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x40')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

"""
Note: from instructions
    jmp 32-bit displacement
    jmp reg
    jmp [ reg ]
    jmp [ reg + 32-bit displacement]
# JMP
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    EB cb               JMP rel8            D       Valid   Valid   Jump short, RIP = RIP + 8-bit displacement sign
                                                                    extended to 64-bits
    E9 cd               JMP rel32           D       Valid   Valid   Jump near, relative, RIP = RIP + 32-bit
                                                                    displacement sign extended to 64-bits
    FF /4               JMP r/m32           M       N.S.    Valid   Jump near, absolute indirect, address given in
                                                                    r/m32. Not supported in 64-bit mode.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    D       Offset              NA              NA          NA
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "JMP"
for op in ('\xEB','\xE9', ('\xFF','\x04'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xEB'))] = (OpEnc.D, ('cd'),  (OpUnit.imm8, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xE9'))] = (OpEnc.D, ('cd'),  (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.M, tuple(), (OpUnit.rm, None, None, None) )

"""
Note: from instructions
    jz 32-bit displacement
    jz 8-bit displacement
    jnz 32-bit displacement
    jnz 8-bit displacement
# JZ / JNZ
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    0F 84 cd            JZ rel32            D       Valid   Valid   Jump near if 0 (ZF=1).
    74 cb               JZ rel8             D       Valid   Valid   Jump short if zero (ZF = 1).
    0F 85 cd            JNZ rel32           D       Valid   Valid   Jump near if not zero (ZF=0).
    75 cb               JNZ rel8            D       Valid   Valid   Jump short if not zero (ZF=0).
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    D       Offset              NA              NA          NA
"""
operator = "JZ"
for op in (('\x0F','\x84',None), '\x74'):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x84'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x74'))] = (OpEnc.D, ('cb'), (OpUnit.imm8, None, None, None) )

operator = "JNZ"
for op in (('\x0F','\x85',None), '\x75'):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x85'))] = (OpEnc.D, ('cd'), (OpUnit.imm32, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x75'))] = (OpEnc.D, ('cb'), (OpUnit.imm8, None, None, None) )

"""
# LEA
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    8D /r               LEA r32,m           RM      Valid   Valid   Store effective address for m in register r32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    RM      ModRM:reg (w)       ModRM:r/m (r)   NA          NA
"""
operator = "LEA"
for op in ('\x8D',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x8D'))] = (OpEnc.RM,  ('/r'), (OpUnit.reg, OpUnit.rm, None, None) )

"""
# MOV
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    89 /r               MOV r/m32,r32       MR      Valid   Valid   Move r32 to r/m32.
    8B /r               MOV r32,r/m32       RM      Valid   Valid   Move r/m32 to r32.
    B8+ rd id           MOV r32, imm32      OI      Valid   Valid   Move imm32 to r32.
    C7 /0 id            MOV r/m32, imm32    MI      Valid   Valid   Move imm32 to r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    MR      ModRM:r/m (w)       ModRM:reg (r)   NA          NA
    RM      ModRM:reg (w)       ModRM:r/m (r)   NA          NA
    OI      opcode + rd (w)     imm8/16/32/64   NA          NA
    MI      ModRM:r/m (w)       imm8/16/32/64   NA          NA
"""
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

"""
# MOVSD
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    A5                  MOVSD               NP      Valid   Valid   For legacy mode, move dword from address
                                                                    DS:(E)SI to ES:(E)DI. For 64-bit mode move
                                                                    dword from address (R|E)SI to (R|E)DI.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
"""
operator = "MOVSD"
for op in ('\xA5',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA5'))] = (OpEnc.NP, tuple(), (None, None, None, None) )

"""
# MUL
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /4               MUL r/m32           M       Valid   Valid   Unsigned multiply (EDX:EAX ← EAX ∗ r/m32).
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "MUL"
for op in (('\xF7','\x04'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

"""
# NEG
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /3               NEG r/m32           M       Valid   Valid   Two's complement negate r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r, w)    NA              NA          NA
"""
operator = "NEG"
for op in (('\xF7','\x03'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )

"""
# NOP
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    90                  NOP                 NP      Valid   Valid   One byte no-operation instruction.
    0F 1F /0            NOP r/m32           M       Valid   Valid   Multi-byte no-operation instruction.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
    M       ModRM:r/m (r)       NA              NA          NA
"""
operator = "NOP"
for op in ('\x90', ('\x0F','\x1F','\x00'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x90'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x1F'))] = (OpEnc.M,  tuple(), (OpUnit.rm, None, None, None) )
"""
# NOT
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    F7 /2               NOT r/m32           M       Valid   Valid   Reverse each bit of r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r, w)    NA              NA          NA
"""
operator = "NOT"
for op in (('\xF7','\x02'),):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.RM,  tuple(), (OpUnit.rm, None, None, None) )

"""
# OR
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    0D id               OR EAX, imm32       I       Valid   Valid   EAX OR imm32.
    81 /1 id            OR r/m32, imm32     MI      Valid   Valid   r/m32 OR imm32.
    83 /1 ib            OR r/m32, imm8      MI      Valid   Valid   r/m32 OR imm8 (sign-extended).
    09 /r               OR r/m32, r32       MR      Valid   Valid   r/m32 OR r32.
    0B /r               OR r32, r/m32       RM      Valid   Valid   r32 OR r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    I       EAX                 imm8/16/32      NA          NA
    MI      ModRM:r/m (r, w)    imm8/16/32      NA          NA
    MR      ModRM:r/m (r, w)    ModRM:reg (r)   NA          NA
    RM      ModRM:reg (r, w)    ModRM:r/m (r)   NA          NA
"""
operator = "OR"
for op in ('\x0D',('\x81','\x01'),('\x83','\x01'),'\x09','\x0B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x0D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x09'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x0B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

"""
# POP
    Opcode      Instruction         Op/En   64-Bit  Compat  Description
    8F /0       POP r/m32           M       N.E     Valid   Pop top of stack into m32; increment stack pointer.
    58+ rd      POP r32             O       N.E.    Valid   Pop top of stack into r32; increment stack pointer.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (w)       NA              NA          NA
    O       opcode + rd (w)     NA              NA          NA
"""
operator = "POP"
for op in ( ('\x8F','\x00'), ):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x58')+reg )

OPERAND_LOOKUP[(operator,ord('\x8F'))] = (OpEnc.M, ('/x00'), (OpUnit.rm,  None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x58')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

"""
# PUSH
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    FF /6               PUSH r/m32          M       N.E.    Valid   Push r/m32.
    50+rd               PUSH r32            O       N.E.    Valid   Push r32.
    68 id               PUSH imm32          I       Valid   Valid   Push imm32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M       ModRM:r/m (r)       NA              NA          NA
    O       opcode + rd (r)     NA              NA          NA
    I       imm8/16/32          NA              NA          NA
"""
operator = "PUSH"
for op in ( ('\xFF','\x06'), '\x68' ):
    setOpLookup(operator, op)

for reg in range(8):
    setOpLookup(operator, ord('\x50')+reg )

OPERAND_LOOKUP[(operator,ord('\xFF'))] = (OpEnc.MR, ('/r'), (OpUnit.rm,  None, None, None) )
OPERAND_LOOKUP[(operator,ord('\x68'))] = (OpEnc.I,  ('id'), (OpUnit.imm32, None, None, None) )

for reg in range(8):
    OPERAND_LOOKUP[(operator, ord('\x50')+reg)] = (OpEnc.O, (reg,), (OpUnit.reg, None, None, None) )

"""
# CMPSD
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    A7                  CMPSD               NP      Valid   Valid   For legacy mode, compare dword at address
                                                                    DS:(E)SI with dword at address ES:(E)DI; For
                                                                    64-bit mode compare dword at address (R|E)SI
                                                                    with dword at address (R|E)DI. The status flags
                                                                    are set accordingly.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
"""

operator = "CMPSD"
for op in ( '\xA7', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA7'))] = (OpEnc.NP, tuple(), (None, None, None, None) )

"""
# REPNE CMPSD
    Opcode              Instruction          Op/En   64-Bit  Compat  Description
    F2 A7               REPNE CMPS m32, m32  NP      Valid   Valid   Find matching doublewords in ES:[(E)DI] and
                                                                     DS:[(E)SI].
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
"""
operator = "REPNE CMPSD"
for op in ( ('\xF2','\xA7',None), ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA7'))] = (OpEnc.NP, tuple(), (None, None, None, None) )

"""
# RETF
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    CB          RET                 NP      Valid   Valid   Far return to calling procedure.
    CA iw       RET imm16           I       Valid   Valid   Far return to calling procedure and pop imm16 bytes from stack.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
    I       imm16               NA              NA          NA
"""
operator = "RETF"
for op in ( '\xCB', '\xCA', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xCB'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xCA'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None) )

"""
# RETN
    Opcode      Instruction         Op/En   64-Bit  Compat  Description
    C3          RET                 NP      Valid   Valid   Near return to calling procedure.
    C2 iw       RET imm16           I       Valid   Valid   Near return to calling procedure and pop imm16 bytes from stack.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    NP      NA                  NA              NA          NA
    I       imm16               NA              NA          NA
"""
operator = "RETN"
for op in ( '\xC3', '\xC2', ):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xC3'))] = (OpEnc.NP, tuple(), (None, None, None, None) )
OPERAND_LOOKUP[(operator,ord('\xC2'))] = (OpEnc.I, ('iw'), (OpUnit.imm16, None, None, None) )

"""
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    # SAL
    D1 /4               SAL r/m32, 1        M1      Valid   Valid   Multiply r/m32 by 2, once.
    # SAR
    D1 /7               SAR r/m32, 1        M1      Valid   Valid   Signed divide* r/m32 by 2, once.
#    # SHL
#    D1 /4               SHL r/m32,1         M1      Valid   Valid   Multiply r/m32 by 2, once.
    # SHR
    D1 /5               SHR r/m32, 1        M1      Valid   Valid   Unsigned divide r/m32 by 2, once.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    M1      ModRM:r/m (r, w)    1               NA          NA
"""
# Note: The shift arithmetic left (SAL) and shift logical left (SHL) instructions perform the same operation; they shift the
# bits in the destination operand to the left (toward more significant bit locations).
# From: 4-340 Vol. 2B

operator = "SAL"
setOpLookup(operator, ('\xD1','\x04'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

operator = "SAR"
setOpLookup(operator, ('\xD1','\x07'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

#operator = "SHL"
#setOpLookup(operator, ('\xD1','\x04'))
#OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

operator = "SHR"
setOpLookup(operator, ('\xD1','\x05'))
OPERAND_LOOKUP[(operator,ord('\xD1'))] = (OpEnc.M1, tuple(), (OpUnit.rm, OpUnit.one, None, None) )

"""
# SBB
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    1D id               SBB EAX, imm32      I       Valid   Valid   Subtract with borrow imm32 from EAX.
    81 /3 id            SBB r/m32, imm32    MI      Valid   Valid   Subtract with borrow imm32 from r/m32
    83 /3 ib            SBB r/m32, imm8     MI      Valid   Valid   Subtract with borrow sign-extended imm8 from r/m32.
    19 /r               SBB r/m32, r32      MR      Valid   Valid   Subtract with borrow r32 from r/m32.
    1B /r               SBB r32, r/m32      RM      Valid   Valid   Subtract with borrow r/m32 from r32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    I       EAX                 imm8/16/32      NA          NA
    MI      ModRM:r/m (w)       imm8/16/32      NA          NA
    MR      ModRM:r/m (w)       ModRM:reg (r)   NA          NA
    RM      ModRM:reg (w)       ModRM:r/m (r)   NA          NA
"""
operator = "SBB"
for op in ('\x1D',('\x81','\x03'),('\x83','\x03'),'\x19','\x1B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x1D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x19'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x1B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

"""
# SUB
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    2D id               SUB EAX, imm32      I       Valid   Valid   Subtract imm32 from EAX.
    81 /5 id            SUB r/m32, imm32    MI      Valid   Valid   Subtract imm32 from r/m32
    83 /5 ib            SUB r/m32, imm8     MI      Valid   Valid   Subtract sign-extended imm8 from r/m32.
    29 /r               SUB r/m32, r32      MR      Valid   Valid   Subtract r32 from r/m32.
    2B /r               SUB r32, r/m32      RM      Valid   Valid   Subtract r/m32 from r32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    I       EAX                 imm8/16/32      NA          NA
    MI      ModRM:r/m (w)       imm8/16/32      NA          NA
    MR      ModRM:r/m (w)       ModRM:reg (r)   NA          NA
    RM      ModRM:reg (w)       ModRM:r/m (r)   NA          NA
"""
operator = "SUB"
for op in ('\x2D',('\x81','\x05'),('\x83','\x05'),'\x29','\x2B',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\x2D'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x81'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x83'))] = (OpEnc.MI, ('ib',), (OpUnit.rm,  OpUnit.imm8, None, None) )
OPERAND_LOOKUP[(operator,ord('\x29'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg, None, None) )
OPERAND_LOOKUP[(operator,ord('\x2B'))] = (OpEnc.RM, ('/r',), (OpUnit.reg, OpUnit.rm, None, None) )

"""
# TEST
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    A9 id               TEST EAX, imm32     I       Valid   Valid   AND imm32 with EAX; set SF, ZF, PF accordingto result.
    F7 /0 id            TEST r/m32, imm32   MI      Valid   Valid   AND imm32 with r/m32; set SF, ZF, PF according to result.
    85 /r               TEST r/m32, r32     MR      Valid   Valid   AND r32 with r/m32; set SF, ZF, PF according to result.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    I       EAX                 imm8/16/32      NA          NA
    MI      ModRM:r/m (r)       imm8/16/32      NA          NA
    MR      ModRM:r/m (r)       ModRM:reg (r)   NA          NA
"""
operator = "TEST"
for op in ('\xA9', ('\xF7','\x00'),'\x85',):
    setOpLookup(operator, op)

OPERAND_LOOKUP[(operator,ord('\xA9'))] = (OpEnc.I,  ('id',), (OpUnit.eax, OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\xF7'))] = (OpEnc.MI, ('id',), (OpUnit.rm,  OpUnit.imm32, None, None) )
OPERAND_LOOKUP[(operator,ord('\x85'))] = (OpEnc.MR, ('/r',), (OpUnit.rm,  OpUnit.reg,  None, None) )

"""
# XOR
    Opcode              Instruction         Op/En   64-Bit  Compat  Description
    35 id               XOR EAX, imm32      I       Valid   Valid   EAX XOR imm32.
    81 /6 id            XOR r/m32, imm32    MI      Valid   Valid   r/m32 XOR imm32.
    31 /r               XOR r/m32, r32      MR      Valid   Valid   r/m32 XOR r32.
    33 /r               XOR r32, r/m32      RM      Valid   Valid   r32 XOR r/m32.
    Op/En   Operand 1           Operand 2       Operand 3   Operand 4
    I       EAX                 imm8/16/32      NA          NA
    MI      ModRM:r/m (r, w)    imm8/16/32      NA          NA
    MR      ModRM:r/m (r, w)    ModRM:reg (r)   NA          NA
    RM      ModRM:reg (r, w)    ModRM:r/m (r)   NA          NA
"""
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