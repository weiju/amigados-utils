from .cpu import *
from amigados.hunktools.dalf import *
from capstone import *


def read_blocks(infile, is_loadfile):
    result = []
    block = read_block(infile, is_loadfile)
    while block is not None:
        result.append(block)
        block = read_block(infile, is_loadfile)
    return result


def group_blocks(blocks):
    """group the blocks into relocation groups"""
    groups = []
    for block in blocks:
        if block[0] in {'NAME', 'UNIT'}:
            continue
        elif block[0] in {'BSS', 'CODE', 'DATA'}:
            current_group = []

        if block[0] == 'END':
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(block)
    return groups


def run(hunkfile):
    """Top level parsing function"""
    with open(hunkfile, 'rb') as infile:
        id = infile.read(4)

        # can be Header or Unit
        is_loadfile = True
        if id == HUNK_BLOCK_HEADER:
            print("Hunk Header (03f3)")
            library_names = read_string_list(infile)
            print("\tLibraries: ", library_names)
            hunk_table_size = read_int32(infile)
            first_slot = read_int32(infile)
            last_slot = read_int32(infile)
            print("\t%d hunks (%d-%d)\n" % (hunk_table_size, first_slot, last_slot))
            num_hunk_sizes = last_slot - first_slot + 1
            """
            print("first slot: %d, last slot: %d, # hunk sizes: %d" % (first_slot,
                                                                       last_slot,
                                                                       num_hunk_sizes))
            """
            hunk_sizes = [read_int32(infile) for i in range(num_hunk_sizes)]
            #print("hunk sizes: ", hunk_sizes)
        elif id == HUNK_BLOCK_UNIT:
            strlen = read_int32(infile) * 4
            #print("# name: %d" % strlen)
            unit_name = str(infile.read(strlen))
            print("Hunk unit (03e7)")
            print("\tName: %s\n" % unit_name)
        else:
            is_loadfile = False
            raise Exception('Unsupported header type')

        blocks = read_blocks(infile, is_loadfile)
        hunks = group_blocks(blocks)
        hunk0 = hunks[0]
        code_block = hunk0[0]

        addr_space = AddressSpace(65536)
        vm_state = CpuState(addr_space)
        addr_space.set_value_at(4, 'l', 1234)

        md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)

        # What do we do with data at the start of the code block ???
        # If it starts with an absolute branch, it means
        # there is data at the start of the code block,
        # so we skip the data and start decoding after that
        index = 0
        new_offset = None
        for i in md.disasm(code_block[1], 0):
            print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
            if index == 0 and i.mnemonic.startswith('bra'):
                new_offset = int(i.op_str.replace('$', ''), 16)
                print("(skip %d bytes)" % new_offset)
            break

        # skip the data block at the start of the code if there is one
        start_offset = new_offset if new_offset is not None else 0

        for i in md.disasm(code_block[1][start_offset:], start_offset):
            print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
