[BITS 32] ; <--- BITS directive

; These next two instructions help build a stack frame using
; EDP as the Base Frame pointer


swap_bytes:
	xor	eax, ebx
	xor	ebx, eax
	xor eax, ebx
	pop edx
	cmp eax, 0x41424344
	ret

push	1
push	2
call	swap_bytes
