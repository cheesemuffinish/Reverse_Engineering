
#include <limits.h>
#include <stdint.h>
#include <stdio.h>

#define IS_BIG_ENDIAN (*(uint16_t *)"\0\xff" < 0x100)

unsigned char endianness_checker( void )
{
    int temp = 1;
    unsigned char *endianness_checker = (unsigned char*)&temp;

    return (endianness_checker[0] == 0);
}

static inline is_big_endian() {
const uint16_t endianness = 256;
return *(const uint8_t *)&endianness;
}

///////////////////////////////////////////////////////////////////////////////
//                  Main
///////////////////////////////////////////////////////////////////////////////
int main() {
	int result = 0;
	result = endianness_checker();
	printf("The result is: %u \n", result );
	
	
	int result2 = 1;
	result2 = endianness_checker();
	printf("The result is: %u \n", result2 );
	
	int result3 = 0;
	result3 = is_big_endian();
	printf("The result3: %u \n", result3 );

	
	printf("The IS_BIG_ENDIAN: %u \n", IS_BIG_ENDIAN );
}