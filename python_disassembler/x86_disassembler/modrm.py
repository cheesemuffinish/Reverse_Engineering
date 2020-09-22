import collections

from constants import *

ModRMVal   = collections.namedtuple("ModRMVal",  "mod reg rm")
ModRMTrans = collections.namedtuple("ModRMTrans","reg rm hasDisp8 hasDisp32 hasSib")

MODRM_PARSE_LOOKUP = {}
MODRM_TRANSLATION_LOOKUP = {}

SIB_TEMPLATE = "[--][--]"

def translate(modrmByte):
    return _getModrmValues(modrmByte), _getModRmTranslation(modrmByte)

def _getModrmValues(modrm):
    if isinstance(modrm, str) or isinstance(modrm, bytes):
        if len(modrm) > 1:
            raise RuntimeError("Can only parse a single byte for MODRM.")
        modrm = ord(modrm)

    return MODRM_PARSE_LOOKUP[modrm]

def _getModRmTranslation(modrm):
    if isinstance(modrm, ModRMVal) and isinstance(modrm[0], int):
        modrm = _assembleModRmByte(modrm.mod, modrm.reg, modrm.rm)

    if isinstance(modrm, int):
        return MODRM_TRANSLATION_LOOKUP[modrm]

    raise RuntimeError("Must provide either a modrm byte or an ModRMVal object.")

def _assembleModRmByte(mod, reg, rm):
    return ((mod<<6)+(reg<<3)+rm)

def getRegVal(modrmByte):
    return (modrmByte>>3)&0x7

def showModRMTable():
    for modIdx, mod in enumerate(MOD):
        for rmIdx, rm in enumerate(RM):
            for regIdx, reg in enumerate(REGISTER):
                val = _assembleModRmByte(modIdx, regIdx, rmIdx)
                #mod_val, reg_val, rm_val, hasSib_val = MODRM_PARSE_LOOKUP[val]
                #mod_trans, reg_trans, rm_trans, hasSib_trans = MODRM_TRANSLATION_LOOKUP[val]
                print( hex(val)+"\t"+str(MODRM_PARSE_LOOKUP[val]) +"\t"+ str(MODRM_TRANSLATION_LOOKUP[val]) )

# Initialize lookup table...

for modIdx, mod in enumerate(MOD):
    for rmIdx, rm in enumerate(RM):
        for regIdx, reg in enumerate(REGISTER):

            hasSib = False
            tmpMod = mod

            # make exceptions for SIB byte follows
            if modIdx in (0,1,2) and rmIdx in (4,):
                hasSib = True
                #tmpMod = mod.replace("[","").replace("]","").replace("reg",SIB_TEMPLATE)
                tmpMod = mod.replace("reg",SIB_TEMPLATE)

            # note there is an exception for mod 0 rm 5
            elif modIdx in (0,) and rmIdx in (5,):
                # note that displacement implies [], since you can only displace
                # a memory address. An immediate value has no brackets.
                tmpMod = '[disp32]'

            # Store the effective address
            tmpRm = tmpMod.replace("reg",rm)


            #rm = rm.replace("reg",rm)

            val = _assembleModRmByte(modIdx, regIdx, rmIdx)
            MODRM_PARSE_LOOKUP[val] = ModRMVal(modIdx, regIdx, rmIdx)
            hasDisp8 = "disp8" in tmpRm
            hasDisp32 = "disp32" in tmpRm
            MODRM_TRANSLATION_LOOKUP[val] = ModRMTrans(reg, tmpRm, hasDisp8, hasDisp32, hasSib)


#showModRMTable()