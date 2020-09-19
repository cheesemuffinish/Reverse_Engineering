#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
a) Code starts at offset 0 in the given file.  This means you do not have to worry
about the headers that certain linkers add.
b) You only have to implement the given mnemonics.
c) If you hit an unknown opcode, your program should exit gracefully and give
feedback to the user as to the cause of the problem.
d) You must handle jumping/calling forwards and backwards.
e) This must work on the sample that is supplied, but it must also work on other
tests as well.
f) You must use either the recursive descent algorithm or linear sweep algorithm.
Supported Mnemonics
===================
* For all instructions below, do not worry about the ESP register being a destination
register.  ESP is sometimes handled differently and you are not expected to handle that.
* All register references will be 32-bit references.  For example, you do not need
to handle “mov dl, byte [ ebx ]”, you only need to handle “mov edx, dword [ ebx ]”.
An immediate will be a 32-bit value while the displacement may be 8-bit or 32-bit
in size. The only exception is the ‘retn 16-bit value’ instruction.
* You must implement labels (as seen in the Example 2):
    add nop and not call or cmp pop dec push idiv repne cmpsd imul retf inc retn
    jmp sal jz/jnz sar lea sbb mov shr movsd test mul xor neg
* Your output must be similar to the examples given.
    For the ‘repne cmpsd’, recall that the ‘d’ in ‘cmpsd’ refers to the data
    size. In this case, it is a DWORD or 32-bit value. Thus, in the Intel Manual
    we are looking for ‘repne cmps m32, m32’.
    For the 'sal'/'shr'/’sar’ instructions, you only need to support:
    Note that the shl/sal are the same opcode (Why is this?)
        sal r/m32, 1
        shr r/m32, 1
        shl r/m32, 1
    For the 'jz'/'jnz'/'jmp' you must implement:
        jz 32-bit displacement
        jz 8-bit displacement
        jnz 32-bit displacement
        jnz 8-bit displacement
        jmp 32-bit displacement
        jmp reg
        jmp [ reg ]
        jmp [ reg + 32-bit displacement]
    For the 'retn/retf' (listed as just ‘ret’ in the Intel Instruction Manual)
    instruction family, you must implement the following. Note that retn
    refers to ‘return near’ and ‘retf’ refers to ‘return far’:
        retn
        retn 16-bit value
        retf
        retf 16-bit value
    For the 'mov/add/and/not/or/pop/push' and similar, you must
    implement (where applicable): Note: displacement could be either 32-bit
    or 8-bit value.
        mov eax, edx
        mov [ eax ], edx
        mov [ eax + displacement], edx
        mov eax, [ edx ]
        mov eax , [ edx + displacement]
        mov eax, 0x12345678
        mov [ eax ], 0x12345678
        mov [ eax + displacement], 0x12345678
        mov [ 0x12345678 ], 0x12345678
        mov eax, [ 0x12345678 ]
"""
import argparse
import shutil
import sys
import os

import utils
from decoderState import DecoderState
from x86.decoder import X86Decoder
from strategy.linearSweep import LinearSweepDecoder
from strategy.recursiveDescent import RecursiveDescent

# Testers...
#from test import fromUnit
#from test import fromOnline   # not needed... blerg!
#from test import fromExample

utils.setupLogging()

def parseArgs():

    parser = argparse.ArgumentParser()
    #parser.add_argument("x", type=int, help="the base")
    #parser.add_argument("y", type=int, help="the exponent")

    parser.add_argument("-b", "--binary", nargs=1, help="Disassemble the given binary file.")

    parser.add_argument("-v", "--verbosity", action="count", default=0, help="Show verbosity. Add more -v's to show more detail")

    parser.add_argument("--recursive-descent", action="store_true", help="Use the recursive descent method. ")

    parser.add_argument("--linear-sweep", action="store_true", help="Use the linear sweep method. ")

    parser.add_argument("--test-examples", action="store_true", help="Disassemble the class examples (example1, example2, ex2)")
    parser.add_argument("--test-unit", action="store_true", help="Disassemble unit examples (one instruction at a time)")
    args = parser.parse_args()


    if not args.test_examples and not args.test_unit and not args.binary:
        print(utils.colors.RED+utils.colors.BOLD + "Must provide at least on of the following options:\n\t--test-examples \n\t--test-unit \n\t--binary <filepath>.\n"+ utils.colors.NORMAL)
        parser.print_help()
        sys.exit(1)

    if args.recursive_descent and args.linear_sweep:
        print(utils.colors.RED+utils.colors.BOLD + "Cannot provide both '--recursive-descent' and '--linear-sweep' options! Pick one.\n"+ utils.colors.NORMAL)
        parser.print_help()
        sys.exit(1)

    if not args.recursive_descent and not args.linear_sweep:
        print(utils.colors.RED+utils.colors.BOLD + "Must provide either '--recursive-descent' or '--linear-sweep' option!\n"+ utils.colors.NORMAL)
        parser.print_help()
        sys.exit(1)



    return args



def main(objectFile, StrategyClass, verbose, detail):
    if not os.path.exists(objectFile):
        utils.logger.info(utils.colors.RED+utils.colors.BOLD + ("Could not find the given file: %s" %repr(objectFile)) + utils.colors.NORMAL )
        sys.exit(1)

    terminalSize = shutil.get_terminal_size((80, 20))

    decoderState = DecoderState(objectFile=objectFile)
    decoderSpec = X86Decoder(decoderState)
    decoder = StrategyClass(decoderSpec)
    decoder.decode(verbose=verbose, detail=detail)
    decoderState.showDecodeProgress(detail=True)

    if decoderState.isComplete():

        utils.logger.info(utils.colors.GREEN+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)
        title = "Completed disassembly of %s"%repr(objectFile)
        utils.logger.info(utils.colors.GREEN+utils.colors.INVERT+(title + " "*(terminalSize.columns-len(title)))+utils.colors.NORMAL)
        utils.logger.info(utils.colors.GREEN+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)

    elif StrategyClass == LinearSweepDecoder and not decoderState.isComplete() and decoderState.isSweepComplete():

        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)
        title = "Almost completed disassembly of %s. A few bytes remain encoded when using Linear Sweep method."%repr(objectFile)
        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(title + " "*(terminalSize.columns-len(title)))+utils.colors.NORMAL)
        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)
    elif StrategyClass == RecursiveDescent and not decoderState.isComplete() and decoderState.isRecursiveDescentComplete():

        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)
        title = "Almost completed disassembly of %s. A few bytes remain encoded when using Recursive Descent method."%repr(objectFile)
        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(title + " "*(terminalSize.columns-len(title)))+utils.colors.NORMAL)
        utils.logger.info(utils.colors.YELLOW+utils.colors.INVERT+(" "*(terminalSize.columns))+utils.colors.NORMAL)
    else:

        utils.logger.info(utils.colors.YELLOW+utils.colors.BOLD + ("Could not finish processing %s" %repr(objectFile)) + utils.colors.NORMAL )

if __name__ == "__main__":
    args = parseArgs()

    # Determine the strategy
    if args.recursive_descent:
        StrategyClass = RecursiveDescent
    else:
        StrategyClass = LinearSweepDecoder

    # set verbosity

    if args.verbosity >= 2:
        verbose = True
        detail = True
    elif args.verbosity >= 1:
        verbose = True
        detail = False
    else:
        verbose = False
        detail = False

    # Run tests...
    if args.test_unit:
        fromUnit.test(StrategyClass, verbose=verbose, detail=detail)

    if args.test_examples:
        fromExample.test(StrategyClass, None, verbose=verbose, detail=detail)

    if args.binary:
        main( args.binary[0], StrategyClass, verbose=verbose, detail=detail)

    # TODO: accept arguments for generic file!

    #fromOnline.test()



    #main()