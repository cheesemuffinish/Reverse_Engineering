#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import shutil
import sys
import os
import utils
from decoderState import Linear_Sweep_State
from decoder import Decoder_x86
import logging

class InvalidOpcode(Exception): pass
class InvalidOperatorTranslation(Exception): pass
class InvalidTranslationValue(Exception): pass
utils.setupLogging()

#######################################
###     Linear Sweep Algorithm      ###
#######################################
def linear_sweep(decoder, continueOnError=True,  verbose=False, detail=False):
	utils.logger.setLevel(logging.INFO)
	instCount = 1

	while not decoder.state.isSweepComplete():
	    try:
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

	        message = 'Error could not pase binary at the location %s (byte:%s).' % (location, theByte)
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

#######################################
###     Main Program                ###
#######################################
def main(input_file, verbose, detail):
    if not os.path.exists(input_file):
        utils.logger.info("Please enter a valid file: %s" %repr(input_file))
        sys.exit(1)

    decoderState = Linear_Sweep_State(input_file=input_file)
    decoderSpec = Decoder_x86(decoderState)
    decoder = linear_sweep(decoderSpec,verbose=verbose, detail=detail)
    decoderState.showDecodeProgress(detail=True)


if __name__ == "__main__":
    args = parseArgs()
    if args.input_file:
        main( args.input_file[0], verbose= False, detail = False)

