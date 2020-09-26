


import modrm
import logging
import utils

g_unknown_opcode = "invalid_opcode"

###################################################
###       State of Linear Sweep Function        ###
###################################################
class Linear_Sweep_State:

    #############################
    ###       Vairbles        ###
    #############################

    input              = None    
    decoded            = None   
    objectSource       = None 
    index              = 0     
    machine_code       = None  
    inst_keys          = None
    inst_length        = None
    error_index        = None  
    label_addr         = None
    postpone_addr      = None

    #############################
    ###       Initilzation    ###
    #############################
    def __init__(self, input_file=None):
        self.machine_code = {}
        self.inst_keys = []
        self.inst_length = {}
        self.label_addr = []
        self.postpone_addr = []

        if input_file:
            with open(input_file,'rb') as fh:
                self.input = fh.read()
        else:
            RuntimeError("Please provide a valid file")
        self.objectSource = bytearray(self.input)
        self.decoded = [False]*len(self.objectSource)

    ########################################
    ###      Decoded Opcodes Handler     ###
    ########################################
    def has_been_decoded(self, starting_index, byte_length, instruction):
       
        path_of_decode = set()
        for i in range(starting_index, starting_index+byte_length):
            path_of_decode.add(self.decoded[i])
        if True in path_of_decode:
            return None

        self.index = starting_index + byte_length
        for j in range(starting_index, starting_index + byte_length):
            self.decoded[j] = True

        if self.error_index != None:
            error_start = self.error_index[0]
            error_length = len(self.error_index)
            self.machine_code[(error_start, error_length)] = g_unknown_opcode
            self.inst_keys.append((error_start, error_length))
            self.error_index = None

        offset_address = None
        opcode = instruction.split(" ")[0]
        if opcode.lower() in ("jmp","jz","jnz","call"):
            value = instruction.split()
            if len(value) > 1:
                opcode_instruction = value[0]
                valid_offset = False
                try:
                    offset_value = int(value[1], 16)
                    valid_offset = True
                except ValueError:
                    pass
                if valid_offset:
                    if len(value[1].replace("0x","")) == 8:
                        if offset_value > 0x7FFFFFFF:
                            offset_value -= 0x100000000
                    elif len(value[1].replace("0x","")) == 4:
                        if offset_value > 0x7FFF:
                            offset_value -= 0x10000
                    elif len(value[1].replace("0x","")) == 2:
                        if offset_value > 0x7F:
                            offset_value -= 0x100
                    offset_address = starting_index + byte_length + offset_value
                    self.label_addr.append(hex(offset_address))
                    offset = "offset_"
                    instruction = "%s%s" % (opcode_instruction + " " + offset, "%s" %  hex(offset_address))
        self.machine_code[ (starting_index, byte_length) ] = instruction
        self.inst_keys.append( (starting_index, byte_length) )
        self.inst_length[starting_index] = byte_length
        return offset_address

    ####################################
    ###       Linear Sweep Handler   ###
    ####################################
    def linear_sweeper(self):
        pass

    ##########################################
    ###       Linear Sweep Error Handler   ###
    ##########################################
    def throw_error(self, starting_index = None, byte_length = 1):
        if starting_index == None:
            starting_index = self.index
        self.index = starting_index + byte_length
        for i in range(starting_index, starting_index + byte_length):
            self.decoded[i] = None
            if self.error_index == None:
                self.error_index = []
            self.error_index.append(i)

    ##################################################
    ###       Linear Sweep Current Index Handler   ###
    ##################################################
    def get_current_index(self):
        return self.index

    #############################################
    ###       Linear Sweep Complete Handler   ###
    #############################################
    def linear_sweep_complete(self):
        return self.decoded.count(False) == 0 and self.decoded.count(None) == 0

    #############################################
    ###       Linear Sweep Finished Handler   ###
    #############################################
    def linear_sweep_finished(self):
        return self.index >= int(len(self.objectSource))

    ##################################################
    ###       Linear Sweep Uknown Bytes Haandler   ###
    ##################################################
    def unknown_bytes_handler(self, starting_index, ending_index):
        last_byte = ' '.join('{:02x}'.format(x) for x in self.objectSource[starting_index:ending_index])
        section = []
        length = 27
        byte_length = 9
        for i, j in enumerate(range(0, len(last_byte), length)):
            address = hex(starting_index+(i * byte_length))
            section.append((address, last_byte[j:j+length]))
        for j in section:
            address, partial = j
            utils.logger.info(" %s   %s   %s      %s" % ( '--', address, partial, g_unknown_opcode))

    ################################################
    ###       Linear Sweep Progression Handler   ###
    ################################################
    def linear_sweep_progression(self):
        utils.logger.info("")
        utils.logger.info("")
        utils.logger.info("  Address     Machine Code                        Disassembly Instruction ")
        utils.logger.info("  _______     ____________                        ________________________")
        utils.logger.info("                               ")

        sorted_keys = sorted(self.inst_keys)
        for i, j in enumerate(sorted_keys):
            starting_index, length = j
            if i > 0:
                last_index, last_length = sorted_keys[i - 1]
                if False in self.decoded[last_index+last_length:starting_index]:
                    self.unknown_bytes_handler(last_index + last_length, starting_index)

            instruction = self.machine_code[j]
            instruction_bytes = ' '.join('{:02x}'.format(x) for x in self.objectSource[starting_index:starting_index + length])
            address = hex(starting_index)
            if address in self.label_addr:
                offset = "offset_%s"%address
                utils.logger.info(offset)
            utils.logger.info(" %-5s       %-30s      %s" % ( address, instruction_bytes, instruction))

        if self.error_index != None:
            starting_index, length = self.error_index[0], len(self.error_index)
            self.unknown_bytes_handler(starting_index, starting_index + length)
        elif False in self.decoded:
            starting_index, length = sorted_keys[-1]
            unknown_index = starting_index+length
            ending_index = len(self.objectSource)
            self.unknown_bytes_handler(unknown_index, ending_index)

       