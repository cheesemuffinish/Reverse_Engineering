#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import shutil
import sys
import os

import utils
from decoderState import DecoderState
from decoder import X86Decoder
import logging

class InvalidOpcode(Exception): pass
class InvalidOperatorTranslation(Exception): pass
class InvalidTranslationValue(Exception): pass

utils.setupLogging()


def decode(decoder, continueOnError=True,  verbose=False, detail=False):

	if not verbose:
	    utils.logger.setLevel(logging.INFO)
	else:
	    utils.logger.setLevel(logging.DEBUG)
	    terminalSize = shutil.get_terminal_size((80, 20))

	instCount = 1

	while not decoder.state.isSweepComplete():
	    try:
	        if verbose:
	            title = "Instruction %d" % instCount
	            utils.logger.debug(title + " "*(terminalSize.columns-len(title)))

	        operator, _ = decoder.decodeSingleInstruction()

	        instCount += 1
	        if verbose:
	            decoder.state.showDecodeProgress(detail)

	        decoder.state.doLinearSweep()

	    except InvalidTranslationValue:
	        location = decoder.state.getCurIdx()
	        try:
	            location = hex(location)
	        except:
	            location = repr(location)

	        try:
	            theByte = hex(decoder.state.contents[decoder.state.getCurIdx()])
	        except:
	            theByte = repr("???")

	        message = 'Unable to parse byte as an operand @ position %s (byte:%s).' % (location, theByte)
	        utils.logger.info(message)
	        decoder.state.markError()

	        if not continueOnError:
	            break

	    except InvalidOpcode:
	        location = decoder.state.getCurIdx()
	        try:
	            location = hex(location)
	        except:
	            location = repr(location)

	        try:
	            theByte = hex(decoder.state.contents[decoder.state.getCurIdx()])
	        except:
	            theByte = repr("???")

	        message = 'Unable to parse byte as an opcode @ position %s (byte:%s).' % (location, theByte)
	        utils.logger.info(message)
	        decoder.state.markError()

	        if not continueOnError:
	            break
	    except:
	        location = decoder.state.getCurIdx()
	        try:
	            location = hex(location)
	        except:
	            location = repr(location)

	        try:
	            theByte = hex(decoder.state.contents[decoder.state.getCurIdx()])
	        except:
	            theByte = repr("???")

	        message = 'Unrecoverable Error: Unable to parse byte @ position %s (byte:%s).' % (location, theByte)
	        utils.logger.info(message)
	        break

	return decoder.state.isComplete()



#######################################
###     Command Line Arguments      ###
#######################################
def parseArgs():

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input_file", nargs=1, help="Please enter a valid binary! ")
    parser.add_argument("--linear-sweep", action="store_true", help="Use the linear sweep method. ")
    args = parser.parse_args()
    return args


def main(input_file, verbose, detail):
    if not os.path.exists(input_file):
        utils.logger.info("Could not find the given file: %s" %repr(input_file))
        sys.exit(1)

    terminalSize = shutil.get_terminal_size((80, 20))

    decoderState = DecoderState(input_file=input_file)
    decoderSpec = X86Decoder(decoderState)
    decoder = decode(decoderSpec,verbose=verbose, detail=detail)
    decoderState.showDecodeProgress(detail=True)

    if not decoderState.isComplete() and decoderState.isSweepComplete():

        utils.logger.info(" "*(terminalSize.columns))
        title = "Almost completed disassembly of %s. A few bytes remain encoded when using Linear Sweep method."%repr(input_file)
        utils.logger.info(title + " "*(terminalSize.columns-len(title)))
        utils.logger.info(" "*(terminalSize.columns))

    else:

        utils.logger.info("Could not finish processing %s" %repr(input_file))

if __name__ == "__main__":
    args = parseArgs()



    if args.input_file:
        main( args.input_file[0], verbose= False, detail = False)

