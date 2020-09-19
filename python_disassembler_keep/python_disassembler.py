import argparse
import sqlite3
import binascii
import csv
from bitstring import BitArray

parser = argparse.ArgumentParser(description='Disassemble using linear sweep.')
parser.add_argument('file', metavar='file', help='The file you want to disassemble')
parser.add_argument('--showinvalid', dest='showInvalid', action='store_true', default=False, help='Display the invalid opcodes. Default is to suppress them')
args = parser.parse_args()
file = args.file

class Instruction:
    def __init__(self,opcode,mnemonic,prefix,operands):
        self.opcode = opcode
        self.mnemonic = mnemonic
        self.dst = ''
        self.src = ''
        self.prefix = prefix
        self.fullinstruction = opcode
        self.displacement_on = 0
        self.displacement = ''
        self.operands = operands
        self.offset = ''
    
# Simple funciton to open the source file for reading in binary mode
def openFile(file):
    return open(file, mode='rb')
    
# Create a sqlite database  with what we consider valid opcodes
def makeLookup():
    db = sqlite3.connect(':memory:')
    cur = db.cursor()
    cur.execute('CREATE TABLE opcodes (opcode blob, mnemonic text, length int, modrm int, reg text, extension int, operands int)')
    reader = csv.reader(open('opcodes.txt','r'))
    for row in reader:
        cur.execute("INSERT INTO opcodes VALUES (?, ?, ?, ?, ?, ?, ?)", (binascii.a2b_hex(row[0]), row[1], row[2], row[3], row[4], row[5], row[6]))        
    db.commit()
    return db
    
# Create a sqlite database to lookup registers found in modr/m bytes
def makeRegLookup():
    db = sqlite3.connect(':memory:')
    cur = db.cursor()
    cur.execute('CREATE TABLE regs (bincode text, reg text)')
    reader = csv.reader(open('regs.txt','r'))
    for row in reader:
        cur.execute("INSERT INTO regs VALUES (?,?)", (row[0], row[1]))
    db.commit()
    return db
    
# This function performs a query against our opcode table to determine if it's valid
# If the code is not in the database, add it to our list of invalid codes
def lookup(byte):
    opcodeTable.row_factory = sqlite3.Row
    cur = opcodeTable.cursor()
    cur.execute("SELECT * FROM opcodes WHERE opcode = ?",(byte,))
    code = cur.fetchone()
    if code != None:
        decode(code)
    else:
        pcode = binascii.b2a_hex(byte).decode('utf8')
        invalidCodes.append(pcode)
        pass
        
# Instantiate an Instruction object and read the rest of the instruction, if applicable
def decode(code):
    global offset
    
    # If the code is 0x0f, we have a prefix
    # Save the prefix, read another byte, and continue processing
    prefix = ''
    if code['opcode'] == b'\x0f':
        prefix = code['opcode']
        byte = program.read(1)
        opcodeTable.row_factory = sqlite3.Row
        cur = opcodeTable.cursor()
        cur.execute("SELECT * FROM opcodes WHERE opcode = ?",(byte,))
        code = cur.fetchone()
        if code != None:
            decode(code)
        else:
            pcode = binascii.b2a_hex(byte).decode('utf8')
            invalidCodes.append(pcode)
            pass
        
    instruction = Instruction(code['opcode'],code['mnemonic'],prefix,code['operands'])

    # If the instruction uses the modr/m byte, read it and parse it
    if code['modrm'] == 1:
        modrmbyte = program.read(1)
        offset += 1
        instruction.fullinstruction += modrmbyte
        parse_modrm(instruction,modrmbyte)
    args = program.read(code['length'])
    instruction.fullinstruction += args
        
    if instruction.src == '':
        instruction.src = binascii.b2a_hex(args).decode('utf8')
        if code['length'] == 4:
            instruction.src = hex(int.from_bytes(args,'little'))
    elif instruction.dst == '':
        instruction.dst = binascii.b2a_hex(args).decode('utf8')
        if code['length'] == 4:
            instruction.dst = hex(int.from_bytes(args,'little'))
    
        
    if instruction.mnemonic == 'jmp' or instruction.mnemonic == 'call' or instruction.mnemonic == 'jz' or instruction.mnemonic == 'jnz':
        instruction.offset = hex(code['length'] + 1 + offset + int.from_bytes(args,'little'))
        offsetlist.append(instruction.offset)
        instruction.src = 'offset_' + str(instruction.offset)
        
    # A few checks for where destination registers are implicit
    # Multiple ifs for readability
    if hex(63) < hex(int.from_bytes(instruction.opcode,'little')) < hex(75):
        instruction.dst = code['reg']
    if hex(183) < hex(int.from_bytes(instruction.opcode,'little')) < hex(191):
        instruction.dst = code['reg']
    if hex(79) < hex(int.from_bytes(instruction.opcode,'little')) < hex(95):
        instruction.dst = code['reg']
    offset += code['length']
    print_instruction(instruction)
    
# Determine the mode, reg, and r/m of an instruction
def parse_modrm(instruction,modrmbyte):
    modrmbits = BitArray(bytes=modrmbyte)
    mode = modrmbits.bin[0:2]
    reg = modrmbits.bin[2:5]
    rm = modrmbits.bin[5:8]
    regTable.row_factory = sqlite3.Row
    opbits = BitArray(bytes=instruction.opcode)
    dest_or_src = opbits.bin[6:7]
    cur = regTable.cursor()
    if instruction.operands == 2:
        cur.execute("SELECT * FROM regs WHERE bincode = ?",(rm,))
        rmcode = cur.fetchone()
        cur.execute("SELECT * FROM regs WHERE bincode = ?",(reg,))
        regcode = cur.fetchone()
        if dest_or_src == '0':
            instruction.src = regcode['reg']
            instruction.dst = rmcode['reg']
        else:
            instruction.dst = regcode['reg']
            instruction.src = rmcode['reg']
    if instruction.operands == 1:
        cur.execute("SELECT * FROM regs WHERE bincode = ?",(rm,))
        rmcode = cur.fetchone()
        if dest_or_src == '0':
            instruction.dst = rmcode['reg']
        else:
            instruction.src = rmcode['reg']
    
    # A few checks for opcode extensions
    # If the instruction uses an extension, find it and make sure we have the right mnemonic
    if (instruction.opcode == b'\x81') or (instruction.opcode == b'\xd3') or (instruction.opcode == b'\xc1') or (instruction.opcode == b'\x83') or (instruction.opcode == b'\xf7') or (instruction.opcode == b'\xf7') or (instruction.opcode == b'\xff'):
         cur = opcodeTable.cursor()
         cur.execute("SELECT * FROM opcodes WHERE opcode = ? AND extension = ?",(instruction.opcode,int(reg,2)))
         extension = cur.fetchone()
         instruction.opcode = extension['opcode']
    # register to register addressing  
    if mode == '11':
        cur = regTable.cursor()
        cur.execute("SELECT * FROM regs WHERE bincode = ?",(reg,))
        reg = cur.fetchone()
        cur.execute("SELECT * FROM regs WHERE bincode = ?",(rm,))
        rm = cur.fetchone()
        # compare the dest bit from opcode
        if dest_or_src == '0':
            instruction.src = reg['reg']
            instruction.dst = rm['reg']
        else:
            instruction.dst = reg['reg']
            instruction.src = rm['reg']
    # memory, 0 displacement
    elif mode == '00':
        instruction.displacement_on = 1
        instruction.displacement = 0    
        if dest_or_src == '0':
            tmp = instruction.dst
            instruction.dst =  '[' + tmp  + ']'
        else:
            tmp = instruction.src
            instruction.src = '[' + tmp  + ']' 
    # memory, 8 bit displacement
    elif mode == '01':
        instruction.displacement_on = 8
        instruction.displacement = program.read(1)
        instruction.fullinstruction += instruction.displacement
        if dest_or_src == '0':
            tmp = instruction.dst
            dispvalue = hex(int.from_bytes(instruction.displacement,'little'))
            instruction.dst = '[' + tmp + '+' + str(dispvalue) + ']'
        else:
            tmp = instruction.src
            dispvalue = hex(int.from_bytes(instruction.displacement,'little'))
            instruction.src = '[' + tmp + '+' + str(dispvalue) + ']'
    # memory, 32bit displacement
    elif mode == '10':
        instruction.displacement_on = 32
        instruction.displacement = program.read(4)
        instruction.fullinstruction += instruction.displacement
        if dest_or_src == '0':
            tmp = instruction.dst
            dispvalue = hex(int.from_bytes(instruction.displacement,'little'))
            instruction.dst = '[' + tmp + '+' + str(dispvalue) + ']'
        else:
            tmp = instruction.src
            dispvalue = hex(int.from_bytes(instruction.displacement,'little'))
            instruction.src = '[' + tmp + '+' + str(dispvalue) + ']'
    
# Print the Instruction object
def print_instruction(instruction):
    hex_code = binascii.b2a_hex(instruction.fullinstruction).decode('utf8')
    if instruction.prefix != '':
        tmpcode = hex_code
        hex_code = binascii.b2a_hex(instruction.prefix).decode('utf8') + tmpcode
         
    code_length = len(hex_code)
    code_space = ' ' * (20 - code_length)
    mnem_length = len(instruction.mnemonic)
    if hex(offset) in offsetlist:
        print('offset_' + str(hex(offset)))
    print('  ', end="")
    print('{0:0>8}'.format(hex(offset).replace("x","")), end=': ')
    print(hex_code,code_space,instruction.mnemonic,instruction.dst,instruction.src)
 
        
def main():
    # Create global variables
    global opcodeTable 
    opcodeTable = makeLookup()
    global regTable
    regTable = makeRegLookup()
    global invalidCodes 
    invalidCodes = []
    global offset
    offset = -1
    global offsetlist
    offsetlist = []

    print('Opening file: %s\n'%file)
    global program
    program = openFile(file)
    
    # Loop through each byte of the file and see if it's a valid instruction
    length = 1
    while True:
        byte = program.read(length)
        offset += length
        if not byte:
            break
        lookup(byte)
        
    
    # If specified via commandline, show the invalid opcodes
    if args.showInvalid:
        print('\nFound the following invalid codes:\n')
        for i in invalidCodes:
            print(i,end=" ")
        
    

if __name__ == "__main__":
    main()