#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import shutil
import sys
import os
import utils
from linear_sweep_state import Linear_Sweep_State
from linear_sweep_handlers import Intel_Disassembler
import logging
from error import *

#######################################
###            Setup                ###
#######################################
utils.logging_init()

#######################################
###     Linear Sweep Handler        ###
#######################################
def linear_sweep(decoder):
    utils.logger.setLevel(logging.INFO)

    while not decoder.state.linear_sweep_finished():
        try:
            operator_input, _ = decoder.sequential_instruction()
            decoder.state.linear_sweeper()

        except Invalid_Value:
            current_index = decoder.state.get_current_index()
            try:
                current_index = hex(current_index)
            except:
                current_index = repr(current_index)
            try:
                current_byte = hex(decoder.state.input[decoder.state.get_current_index()])
            except:
                current_byte = repr("invalid opcode!!")

            log_message = 'Unable to parse %s at %s.' % (current_byte, current_index)
            utils.logger.info(log_message)
            decoder.state.throw_error()

        except Invalid_Opcode_Provided:
            current_index = decoder.state.get_current_index()
            try:
                current_index = hex(current_index)
            except:
                current_index = repr(current_index)
            try:
                current_byte = hex(decoder.state.input[decoder.state.get_current_index()])
            except:
                current_byte = repr("invalid opcode!!")
            log_message = 'Unable to parse %s at %s.' % (current_byte, current_index)
            utils.logger.info(log_message)
            current_byte = repr("invalid opcode!!")
            decoder.state.throw_error()
           
        except:
            current_index = decoder.state.get_current_index()
            try:
                current_index = hex(current_index)
            except:
                current_index = repr(current_index)
            try:
                current_byte = hex(decoder.state.input[decoder.state.get_current_index()])
            except:
                current_byte = repr("invalid_opcode!!")
            log_message = 'Unable fucking to parse %s at %s.' % (current_byte, current_index)
            utils.logger.info(log_message)
            break
            

    return decoder.state.linear_sweep_complete()

#######################################
###     Command Line Arguments      ###
#######################################
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", nargs=1)
    args = parser.parse_args()
    return args

#######################################
###     Main Program                ###
#######################################
def main(input_file):
    if not os.path.exists(input_file):
        utils.logger.info("Please enter a valid file: %s !!" %repr(input_file))
        sys.exit(1)

    linear_state    = Linear_Sweep_State(input_file=input_file)
    linear_info     = Intel_Disassembler(linear_state)
    do_linear_sweep = linear_sweep(linear_info)
    linear_state.linear_sweep_progression()

if __name__ == "__main__":
    args = parse_arguments()
    if args.input_file:
        main( args.input_file[0])

