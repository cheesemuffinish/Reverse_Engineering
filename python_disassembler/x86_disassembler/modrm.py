
import collections
from constants import *

####################
###   Setup      ###
####################
ModRM_byte         = collections.namedtuple("ModRM_byte",  "mod reg rm")
ModRM_translation  = collections.namedtuple("ModRM_translation","reg rm hasDisp8 hasDisp32 hasSib")
ModRM_Table_Lookup             = {}
ModRM_Translation_Table_Lookup = {}

#######################################
###   Translate MODRM Byte Handler  ###
#######################################
def tranlate_modrm_byte(modrm_byte):
    return get_modrm_byte(modrm_byte), get_modrm_translation(modrm_byte)

#######################################
###   Get MODRM Byte Handler        ###
#######################################
def get_modrm_byte(modrm):
    if isinstance(modrm, str) or isinstance(modrm, bytes):
        if len(modrm) > 1:
            raise RuntimeError("Please provide just one byte")
        modrm = ord(modrm)
    return ModRM_Table_Lookup[modrm]

################################################
###   Get MODRM Byte Translation Handler     ###
################################################
def get_modrm_translation(modrm):
    if isinstance(modrm, ModRM_byte) and isinstance(modrm[0], int):
        modrm = get_modrm_assembly(modrm.mod, modrm.reg, modrm.rm)
    if isinstance(modrm, int):
        return ModRM_Translation_Table_Lookup[modrm]
    raise RuntimeError("Expected modrm byte")

################################################
###   Get MODRM Byte Assembly Handler        ###
################################################
def get_modrm_assembly(mod, reg, rm):
    return ((mod<<6)+(reg<<3)+rm)

################################################
###   Get MODRM Byte Translation Handler     ###
################################################
def get_register_value(modrm_byte):
    return (modrm_byte>>3)&0x7

for modIdx, mod in enumerate(MOD):
    for rmIdx, rm in enumerate(RM):
        for regIdx, reg in enumerate(REGISTER):

            tmpMod = mod

            if modIdx in (0,1,2) and rmIdx in (4,):
                tmpMod = 'reg'

            elif modIdx in (0,) and rmIdx in (5,):
                tmpMod = '[disp32]'

            tmpRm = tmpMod.replace("reg",rm)
            val = get_modrm_assembly(modIdx, regIdx, rmIdx)
            ModRM_Table_Lookup[val] = ModRM_byte(modIdx, regIdx, rmIdx)
            hasDisp8 = "disp8" in tmpRm
            hasDisp32 = "disp32" in tmpRm
            ModRM_Translation_Table_Lookup[val] = ModRM_translation(reg, tmpRm, hasDisp8, hasDisp32, False)

