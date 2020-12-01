import argparse
import binascii
import logging
import sys

logging.basicConfig()
log = logging.getLogger('disasm')
log.setLevel(logging.ERROR)     # enable CRITICAL and ERROR messages by default


def format_line(hexbytes, text):
    hexstr = ''.join(['{:02x}'.format(x) for x in hexbytes])
    return '{:<24}{}'.format(hexstr, text)


def format_unknown(hexbyte):
    return format_line([hexbyte], 'db 0x{:02x}'.format(hexbyte))


def format_label(address):
    return 'offset_{:08x}h:\n'.format(address)


def format_instr(hexbytes, mnemonic, op1=None, op2=None, op3=None):
    line = format_line(hexbytes, mnemonic)
    if op1:
        line = '{} {}'.format(line, op1)
        if op2:
            line = '{}, {}'.format(line, op2)
            if op3:
                line = '{}, {}'.format(line, op3)

    return line

def parse_int3(instr):
    if 1 == len(instr) and b'\xcc' == instr:
        log.info('Found int3!')
        return format_line(instr, 'int3')
    return None


def parse_cpuid(instr):
    if 2 == len(instr) and b'\x0f\x31' == instr:
        log.info('Found cpuid!')
        return format_line(instr, 'cpuid')
    return None


# This is not really "mov eax, eax", only an example of a formatted instruction
def parse_fake_mov(instr):
    if 2 == len(instr) and b'\xd0\x0d' == instr:
        log.info('Found fake mov!')
        return format_instr(instr, 'mov', 'eax', 'eax')


def parse(instruction):
    parsers = [parse_int3, parse_cpuid, parse_fake_mov]
    for p in parsers:
        result = p(instruction)
        if result:
            return result
    return None


if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Input file', dest='infile',
                        required=True)
    parser.add_argument('-v', '--verbose', help='Enable verbose output',
                        action='store_true', default=False)
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    log.debug('Attempting to read input file')
    try:
        with open(args.infile, 'rb') as fd:
            inbytes = bytearray(fd.read())
            if not inbytes:
                log.error('Input file was empty')
                sys.exit(-1)
    except (IOError, OSError) as e:
        log.error('Failed to open {}'.format(args.infile))
        sys.exit(-1)

    log.debug('Parsing instructions')
    offset = 0
    instr = bytearray()
    instructions = []
    for b in inbytes:
        instr.append(b)
        log.debug('Testing instruction: {}'.format(binascii.hexlify(instr)))
        result = parse(instr)
        if result:
            instr_offset = offset + 1 - len(instr)
            log.info('Adding instruction for offset {}'.format(instr_offset))
            instructions.append((instr_offset, result))
            instr = bytearray()

        offset += 1

    log.debug('Creating output data')
    output = ''
    for (offset, text) in instructions:
        output += '{:08x}:   {}\n'.format(offset, text)

    log.debug('Attempting to write output')
    print(output)
