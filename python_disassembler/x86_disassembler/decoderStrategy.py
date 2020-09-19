class DecoderStrategy:
    # has a reference to the DecoderState instance

    # driver, iterates through the source and passes the decoder class the current
    # index to decode. Depending on the implementation this can be linear sweep
    # or recursive descent.

    def __init__(self, decoder):
        self.decoder = decoder

    def decode(self):
        pass