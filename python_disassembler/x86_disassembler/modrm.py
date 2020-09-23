import collections

from constants import *

ModRM_byte   = collections.namedtuple("ModRM_byte",  "mod reg rm")
ModRM_translation = collections.namedtuple("ModRM_translation","reg rm hasDisp8 hasDisp32 hasSib")
ModRM_Table_Lookup = {}
ModRM_Translation_Table_Lookup = {}


def translate(modrmByte):
    return _getModRM_byteues(modrmByte), _getModRmTranslation(modrmByte)

def _getModRM_byteues(modrm):
    if isinstance(modrm, str) or isinstance(modrm, bytes):
        if len(modrm) > 1:
            raise RuntimeError("Can only parse a single byte for MODRM.")
        modrm = ord(modrm)

    return ModRM_Table_Lookup[modrm]

def _getModRmTranslation(modrm):
    if isinstance(modrm, ModRM_byte) and isinstance(modrm[0], int):
        modrm = _assembleModRmByte(modrm.mod, modrm.reg, modrm.rm)

    if isinstance(modrm, int):
        return ModRM_Translation_Table_Lookup[modrm]

    raise RuntimeError("modrm byte not provided")

def _assembleModRmByte(mod, reg, rm):
    return ((mod<<6)+(reg<<3)+rm)

def getRegVal(modrmByte):
    return (modrmByte>>3)&0x7

for modIdx, mod in enumerate(MOD):
    for rmIdx, rm in enumerate(RM):
        for regIdx, reg in enumerate(REGISTER):

            tmpMod = mod

            if modIdx in (0,1,2) and rmIdx in (4,):
                tmpMod = 'reg'

            elif modIdx in (0,) and rmIdx in (5,):
                tmpMod = '[disp32]'

            tmpRm = tmpMod.replace("reg",rm)
            val = _assembleModRmByte(modIdx, regIdx, rmIdx)
            ModRM_Table_Lookup[val] = ModRM_byte(modIdx, regIdx, rmIdx)
            hasDisp8 = "disp8" in tmpRm
            hasDisp32 = "disp32" in tmpRm
            ModRM_Translation_Table_Lookup[val] = ModRM_translation(reg, tmpRm, hasDisp8, hasDisp32, False)

