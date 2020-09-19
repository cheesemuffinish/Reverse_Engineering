import logging
import shutil

import utils
from error import *
from strategy.decoderStrategy import DecoderStrategy

CALL_INST = ('CALL',)
FUNC_END = ('RET','RETN','RETF')
JUMP_INST = ('JMP','JZ','JNZ')
JCC_INST = ('JZ','JNZ')

class RecursiveDescent(DecoderStrategy):

    addressDefer = None

    def __init__(self, *args, **kwargs):
        super(RecursiveDescent, self).__init__(*args, **kwargs)
        self.addressDefer = []

    def decode(self, continueOnError=True,  verbose=False, detail=False):

        if not verbose:
            utils.logger.setLevel(logging.INFO)
        else:
            utils.logger.setLevel(logging.DEBUG)
            terminalSize = shutil.get_terminal_size((80, 20))

        instCount = 1

        while not self.decoder.state.isRecursiveDescentComplete():
            try:
                if verbose:
                    title = "Instruction %d" % instCount
                    utils.logger.debug(utils.colors.INVERT+(title + " "*(terminalSize.columns-len(title)))+utils.colors.NORMAL)

                operator, targetAddr = self.decoder.decodeSingleInstruction()

                instCount += 1
                if verbose:
                    self.decoder.state.showDecodeProgress(detail)

                self.decoder.state.doRecursiveDescent(operator, targetAddr)

            except InvalidTranslationValue:
                location = self.decoder.state.getCurIdx()
                try:
                    location = hex(location)
                except:
                    location = repr(location)

                try:
                    theByte = hex(self.decoder.state.contents[self.decoder.state.getCurIdx()])
                except:
                    theByte = repr("???")

                message = 'Unable to parse byte as an operand @ position %s (byte:%s).' % (location, theByte)
                utils.logger.info(utils.colors.RED+utils.colors.BOLD +message+utils.colors.NORMAL)
                self.decoder.state.markError()

                if not continueOnError:
                    break

            except InvalidOpcode:
                location = self.decoder.state.getCurIdx()
                try:
                    location = hex(location)
                except:
                    location = repr(location)

                try:
                    theByte = hex(self.decoder.state.contents[self.decoder.state.getCurIdx()])
                except:
                    theByte = repr("???")

                message = 'Unable to parse byte as an opcode @ position %s (byte:%s).' % (location, theByte)
                utils.logger.info(utils.colors.RED+utils.colors.BOLD +message+utils.colors.NORMAL)
                self.decoder.state.markError()

                if not continueOnError:
                    break
            except:
                location = self.decoder.state.getCurIdx()
                try:
                    location = hex(location)
                except:
                    location = repr(location)

                try:
                    theByte = hex(self.decoder.state.contents[self.decoder.state.getCurIdx()])
                except:
                    theByte = repr("???")

                message = 'Unrecoverable Error: Unable to parse byte @ position %s (byte:%s).' % (location, theByte)
                utils.logger.info(utils.colors.RED+utils.colors.BOLD +message+utils.colors.NORMAL)
                break

        return self.decoder.state.isComplete()