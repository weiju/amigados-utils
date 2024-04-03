import struct
from collections import deque

from capstone import *


def disassemble(code):
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
    # What do we do with data at the start of the code block ???
    # If it starts with an absolute branch, it means
    # there is data at the start of the code block,
    # so we skip the data and start decoding after that
    index = 0
    new_offset = None
    for i in md.disasm(code, 0):
        print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
        if index == 0 and i.mnemonic.startswith('bra'):
            new_offset = int(i.op_str.replace('$', ''), 16)
            print("(skip %d bytes)" % new_offset)
        break

    # skip the data block at the start of the code if there is one
    start_offset = new_offset if new_offset is not None else 0

    for i in md.disasm(code[start_offset:], start_offset):
        print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
