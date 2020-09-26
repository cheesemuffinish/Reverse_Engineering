


from enum import Enum

#######################################
###       Project Constants         ###
#######################################

REGISTER    = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
RM          = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
MOD         = ['[reg]','[reg + disp8]','[reg + disp32]','reg']

############################
###      OPCode Units    ###
############################
class opcode_units(Enum):
    one   = 'one'
    imm8  = 'imm8'
    imm32 = 'imm32'
    imm16 = 'imm16'
    reg   = 'reg'
    rm    = 'rm'
    eax   = 'eax'
    moff  = 'moff'   

###############################
###       OPCode Encoding   ###
###############################
class opcode_encoding(Enum):
    I   = ('I',  False)
    D   = ('D',  False)
    M   = ('M',  True)
    O   = ('O',  False)
    NP  = ('NP', False)
    MI  = ('MI', True)
    M1  = ('M1', True) 
    MR  = ('MR', True)
    RM  = ('RM', True)
    RMI = ('RMI',True)
    OI  = ('OI', False)

    def __init__(self, opcode_encoding, hasModrm):
        self.opcode_encoding = opcode_encoding
        self.hasModrm = hasModrm