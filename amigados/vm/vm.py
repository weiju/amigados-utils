from amigados.hunktools.dalf import *
from capstone import *


class AddressSpace:
    def __init__(self, size):
        self.mem = [0] * size

    def value_at(self, addr, size):
        return self.mem[addr]

    def set_value_at(self, addr, size, value):
        self.mem[addr] = value


class CpuState:

    def __init__(self, addr_space):
        self.d = [0] * 8
        self.a = [0] * 8
        self.pc = 0
        self.sr = 0
        self.addr_space = addr_space

    def value_at(self, addr, size):
        return self.addr_space.value_at(addr, size)

    def set_value_at(self, addr, size, value):
        self.addr_space.set_value_at(addr, size, value)

    def __repr__(self):
        out = ""
        print(self.a)
        for index, aval in enumerate(self.a):
            out += "a%d: %d\t\td%d: %d\n" % (index, aval, index, self.d[index])

        return out

################################
# Code execution functions
#######

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
        start_offset = None

        # skip over data at the begining of the code
        for i in md.disasm(code_block[1], 0):
            print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
            if index == 0 and i.mnemonic.startswith('bra'):
                start_offset = int(i.op_str.replace('$', ''), 16)
                print("(skip %d bytes)" % start_offset)
            break

        running = True
        while running:
            do_continue = False
            for i in md.disasm(code_block[1][start_offset:], start_offset):
                do_continue = execute_instruction(vm_state, i)
            running = False


def execute_move(vm_state, size, operands):
    print("MOVE SIZE: %s operands: %s" % (size, str(operands)))


def execute_instruction(vm_state, i):
    if i.mnemonic.startswith("move."):
        operands = [op.strip() for op in i.op_str.split(",")]
        execute_move(vm_state, i.mnemonic[-1], operands)
    else:
        print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    return True
