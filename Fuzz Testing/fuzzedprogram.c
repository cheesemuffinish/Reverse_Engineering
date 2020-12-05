#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

typedef struct __attribute__((packed,aligned(1)))  _ldata {

	char type;
	unsigned int len;
	char val[0];

} ldata;

int process_data( char * d, unsigned int len )
{

	//
	// Expecting TLV style

	unsigned int i = 0;
	unsigned char *stackBuffer = malloc(64);
	unsigned int numToRead = 0;
	char * end = d + len;
	char * curr = d;
	ldata * pTLV;

	while( curr < end )
	{
	
		pTLV = (ldata *)curr;
		//printf("================================\n");
		//printf("Type: %02x\n", pTLV->type );
		//printf("Len: %08x\n", pTLV->len );
		//printf("Val:\n");
		if((int)pTLV->type == 0xffffffaa){
			//printf("Hello my people! %d \n",numToRead);
			printf("!!!!!!!!!!!!!!!!Type: %02x\n", pTLV->type );
			if((int)pTLV->len == 4){
				numToRead = (unsigned int)pTLV->val;
				printf("Hello my people! %d \n",numToRead);

			}
		}
		else if((int)pTLV->type == 0xffffffbb){
			//printf("Hello my people! %d \n",numToRead);
			printf("!!!!!!!!!!!!!!!!Type: %02x\n", pTLV->type );
			if(numToRead != 0){
				memcpy(stackBuffer, &numToRead, 4);
				printf("Hello my bkit! %d \n",numToRead);
			}
		}		
			
		for( i = 0; i < pTLV->len; ++i )
		{
			printf("%02x ", (int)pTLV->val[i] & 0xff );
			if( ((i+1)%16) == 0 )
				printf("\n");	
		}
		printf("\n");

		curr += sizeof(ldata);
		curr += pTLV->len;
	}


}


int main( int argc, char ** argv )
{

	int fd = -1;
	struct stat buf;
	char * data = NULL;

	if( argc != 2 )
	{
		return -1;
	}


	fd = open( argv[1], O_RDONLY );

	fstat( fd, &buf );

	data = (char *)malloc( buf.st_size );

	read( fd, data, buf.st_size );

	process_data( data, buf.st_size );

	free( data );

	return 0;

}