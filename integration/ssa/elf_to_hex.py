#!/usr/bin/env python3
"""Emit the reversed-byte lines expected by this Chipyard SimDRAM loadmem.

Input must be a flat image produced with objcopy -O binary, starting at DRAM
base 0x80000000. ELF itself is not a supported +loadmem format in this tree.
"""
import pathlib, sys
src, dst = map(pathlib.Path, sys.argv[1:])
b = src.read_bytes()
dst.write_text('\n'.join(b[i:i+16].ljust(16,b'\0')[::-1].hex()
                         for i in range(0,len(b),16))+'\n')
