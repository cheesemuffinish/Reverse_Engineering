from enum import Enum

CALL_INST = ('CALL',)
FUNC_END = ('RET','RETN','RETF')
JUMP_INST = ('JMP',)
JCC_INST = ('JZ','JNZ')

REGISTER    = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
RM          = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
MOD         = ['[reg]','[reg + disp8]','[reg + disp32]','reg']

# note: the MOD values already contain the address brackets [], so they are not needed here.
SCALE       = ['index + base','index*2 + base','index*4 + base','index*8 + base']
INDEX       = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
BASE        = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']

class OpUnit(Enum):
    #imm8  = 'imm8'
    #imm32 = 'imm32'
    one = 'one'
    imm8 = 'imm8'
    imm32 = 'imm32'
    imm16 = 'imm16'
    reg   = 'reg'
    rm    = 'rm'
    eax   = 'eax'
    moff  = 'moff'   # ???

class OpEnc(Enum):
    I   = ('I',   False)
    D   = ('D',   False)
    M   = ('M',   True)
    O   = ('O',   False)
    NP  = ('NP',  False)
    MI  = ('MI',  True)
    M1  = ('M1',  True) # second operand is just '1'
    MR  = ('MR',  True)
    RM  = ('RM',  True)
    RMI = ('RMI', True)
    OI  = ('OI',  False)

    def __init__(self, opEnc, hasModrm):
        self.opEnc = opEnc
        self.hasModrm = hasModrm