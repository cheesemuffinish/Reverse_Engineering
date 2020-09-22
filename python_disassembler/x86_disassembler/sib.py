import collections

from constants import *

SibVal   = collections.namedtuple("SibVal",  "scale index base")
SibTrans = collections.namedtuple("SibTrans","scaledIndexBase hasDisp8 hasDisp32")

SIB_PARSE_LOOKUP = {}
SIB_TRANSLATION_LOOKUP = {}

def translate(sibByte):
    return _getSibValues(sibByte), _getSibTranslation(sibByte)

def _getSibValues(sib):
    if isinstance(sib, str) or isinstance(sib, bytes):
        if len(sib) > 1:
            raise RuntimeError("Can only parse a single byte for SIB.")
        sib = ord(sib)

    return SIB_PARSE_LOOKUP[sib]

def _getSibTranslation(sib):
    if isinstance(sib, SibVal) and isinstance(sib[0], int):
        sib = _assembleSibByte(sib.scale, sib.base, sib.index)

    if isinstance(sib, int):
        return SIB_TRANSLATION_LOOKUP[sib]

    raise RuntimeError("Must provide either a sib byte or an SibVal object.")

def _assembleSibByte(scale, index, base):
    return ((scale<<6)+(index<<3)+base)


def showSibTable():
    for scaleIdx, scale in enumerate(MOD):
        for indexIdx, index in enumerate(INDEX):
            for baseIdx, base in enumerate(BASE):
                val = _assembleSibByte(scaleIdx, baseIdx, indexIdx)
                print( hex(val)+"\t"+str(SIB_PARSE_LOOKUP[val]) +"\t"+ str(SIB_TRANSLATION_LOOKUP[val]) )

# Initialize lookup table...

for scaleIdx, scale in enumerate(SCALE):
    for indexIdx, index in enumerate(INDEX):
        for baseIdx, base in enumerate(BASE):

            scaledIndexBase = scale

            # make exceptions for SIB byte follows
            if scaleIdx in (0,1,2,3) and indexIdx in (4,):
                # There is no scale, however, the correct index register should
                # be used instead (this is ESP)

                #scaledIndexBase = "none"
                scaledIndexBase = INDEX[indexIdx]

            # note there is an exception for base 5, there should be no base

            if baseIdx in (5,):
                scaledIndexBase = scaledIndexBase.replace(" + base","")
                """
                # this is wrong... it should be in reference to the MOD bits in the MODRM byte, not the scale in the SIB byte
                if scaleIdx == 0:
                    scaledIndexBase = scaledIndexBase + ' + disp32'
                elif scaleIdx == 1:
                    scaledIndexBase = scaledIndexBase + ' + disp8 + [ebp]'
                elif scaleIdx == 2:
                    scaledIndexBase = scaledIndexBase + ' + disp32 + [ebp]'
                """
            # Store the effective address
            scaledIndexBase = scaledIndexBase.replace("index", index)
            scaledIndexBase = scaledIndexBase.replace("base", base)

            #index = index.replace("base",index)

            val = _assembleSibByte(scaleIdx, indexIdx, baseIdx)
            SIB_PARSE_LOOKUP[val] = SibVal(scaleIdx, indexIdx, baseIdx)
            hasDisp8 = "disp8" in scaledIndexBase
            hasDisp32 = "disp32" in scaledIndexBase
            SIB_TRANSLATION_LOOKUP[val] = SibTrans(scaledIndexBase, hasDisp8, hasDisp32)

#showSibTable()