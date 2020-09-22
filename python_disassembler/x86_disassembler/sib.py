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
for scale
Idx, scale in enumerate(SCALE):
    for indexIdx, index in enumerate(INDEX):
        for baseIdx, base in enumerate(BASE):
            scaledIndexBase = scale

            if scaleIdx in (0,1,2,3) and indexIdx in (4,):
                scaledIndexBase = INDEX[indexIdx]

            if baseIdx in (5,):
                scaledIndexBase = scaledIndexBase.replace(" + base","")

            scaledIndexBase = scaledIndexBase.replace("index", index)
            scaledIndexBase = scaledIndexBase.replace("base", base)

            val = _assembleSibByte(scaleIdx, indexIdx, baseIdx)
            SIB_PARSE_LOOKUP[val] = SibVal(scaleIdx, indexIdx, baseIdx)
            hasDisp8 = "disp8" in scaledIndexBase
            hasDisp32 = "disp32" in scaledIndexBase
            SIB_TRANSLATION_LOOKUP[val] = SibTrans(scaledIndexBase, hasDisp8, hasDisp32)

