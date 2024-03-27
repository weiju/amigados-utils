"""
cpu.py - 68000 CPU module
"""
import struct


ADDR_MODES = {
    '000': 'Dn', '001': 'An', '010': '(An)', '011': '(An)+', '100': '-(An)',
    '101': '(d16,An)', '110': '(d8,An,Xn)', '111': 'EXT'  # -> ADDR_MODES_EXT
}

ADDR_MODES_EXT = {
    '000': '(xxx).W', '001': '(xxx).L', '100': '#<data>',
    '010': '(d16,PC)', '011': '(d8,PC,Xn)'
}

OPCODE_CATEGORIES = {
    '0000': 'bitops_movep_imm', '0001': 'move.b', '0010': 'move.l', '0011': 'move.w',
    '0100': 'misc', '0101': 'addq_subq', '1001': 'sub_subx', '1011': 'cmp_eor',
    '0110': 'bcc_bsr_bra', '0111': 'moveq',
    '1101': 'add_addx', '1110': 'shift_rotate'
}

OPMODES = {
    '000': ('b', 'ea,dn->dn'), '001': ('w', 'ea,dn->dn'),'010': ('l', 'ea,dn->dn'),
    '100': ('b', 'dn,ea->ea'), '101': ('w', 'dn,ea->ea'),'110': ('l', 'dn,ea->ea')
}

SIZES = ['b', 'w', 'l']

CONDITION_CODES = [
    't', 'f', 'hi', 'ls',
    'cc', 'cs', 'ne', 'eq',
    'vc', 'vs', 'pl', 'mi',
    'ge', 'lt', 'gt', 'le'
]


######################################################################
#### Operand classes / Addressing modes
######################################################################

class IntConstant:
    def __init__(self, value):
        self.val = value  # don't call it "value", naming clash !!

    def value(self, vm_state, size):
        return self.val

    def __repr__(self):
        return '#%02x' % self.val


class AbsoluteAddress:
    def __init__(self, addr, size):
        self.addr = addr
        self.size = size

    def value(self, vm_state, size):
        # size parameter is ignored
        return vm_state.value_at(self.addr, self.size)

    def __repr__(self):
        return '#%02x.%s' % (self.addr, self.size)


class PCIndirectDisplacement:
    def __init__(self, disp16):
        self.disp16 = disp16

    def __repr__(self):
        return "%02x(PC)" % self.disp16



class DataRegister:
    def __init__(self, regnum):
        self.regnum = regnum

    def value(self, vm_state, size):
        return vm_state.d[self.regnum]

    def set_value(self, vm_state, size, value):
        vm_state.d[self.regnum] = value

    def __repr__(self):
        return 'd%d' % self.regnum


class AddressRegister:
    def __init__(self, regnum):
        self.regnum = regnum

    def value(self, vm_state, size):
        return vm_state.a[self.regnum]

    def set_value(self, vm_state, size, value):
        vm_state.a[self.regnum] = value

    def __repr__(self):
        return 'a%d' % self.regnum


class AddressRegisterIndirect:
    def __init__(self, regnum):
        self.regnum = regnum

    def __repr__(self):
        return '(a%d)' % self.regnum


class AddressRegisterIndirectPost:
    def __init__(self, regnum):
        self.regnum = regnum

    def __repr__(self):
        return '(a%d)+' % self.regnum


class AddressRegisterIndirectPre:
    def __init__(self, regnum):
        self.regnum = regnum

    def __repr__(self):
        return '-(a%d)' % self.regnum


class AddressRegisterIndirectDisplacement:
    def __init__(self, regnum, displacement):
        self.regnum = regnum
        self.displacement = displacement

    def __repr__(self):
        return '%02x(a%d)' % (self.displacement, self.regnum)


class AddressRegisterIndirectDisplacementIndex:
    def __init__(self, regnum, displacement, index):
        self.regnum = regnum
        self.displacement = displacement
        self.index = iindex

    def __repr__(self):
        return '(%02x,a%d,%02x)' % (self.displacement, self.regnum, self.index)


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


######################################################################
#### Opcode classes
######################################################################

class Opcode(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def is_branch(self):
        return False

    def is_absolute_branch(self):
        return False

    def is_local_branch(self):
        return False

    def is_return(self):
        return self.name == 'rts'

    def execute(self, vm_state):
        vm_state.pc += self.size

    def __repr__(self):
        return "%s" % self.name


class Operation2(Opcode):
    def __init__(self, name, size, src, dest):
        Opcode.__init__(self, name, size)
        self.src = src
        self.dest = dest

    def __repr__(self):
        return "%s\t%s,%s" % (self.name, self.src, self.dest)


class MoveInstruction(Operation2):
    def __init__(self, name, size, src, dest):
        Operation2.__init__(self, name, size, src, dest)

    def execute(self, vm_state):
        srcval = self.src.value(vm_state, self.size)
        self.dest.set_value(vm_state, self.size, srcval)
        Operation2.execute(self, vm_state)


class Operation1(Opcode):
    """A single operand operation"""

    def __init__(self, name, size, dest):
        Opcode.__init__(self, name, size)
        self.dest = dest

    def __repr__(self):
        return "%s\t%s" % (self.name, self.dest)


class Jump(Opcode):
    def __init__(self, name, pc, size, displacement):
        Opcode.__init__(self, name, size)
        self.displacement = displacement
        self.pc = pc

    def is_branch(self):
        return True

    def is_absolute_branch(self):
        return self.name == 'bra'

    def is_local_branch(self):
        """a very simplified model assumption of a local branch for now, which
        excludes jumps. An improved version will also look at the relocation
        addresses, since a relocation target is likely a local address"""
        return self.name.startswith('b')

    def __repr__(self):
        # TODO: branches currently are displayed using their offset
        # and not their destination
        # jump locations are defined correctly
        # To adjust the branch destination, we need to actually
        # add the displacement to the address after the instruction
        if self.is_local_branch():
            if self.size == 2:
                return "%s.s\t%x" % (self.name, self.pc + self.size + self.displacement)
            else:
                return "%s\t%x" % (self.name, self.pc + self.size + self.displacement)
        else:
            return "%s\t%s" % (self.name, self.displacement)


def is_move(category):
    return category in {'move.b', 'move.w', 'move.l'}


def next_word(size, data, data_offset):
    if size == 'L':
        value = struct.unpack('>i', data[data_offset:data_offset+4])[0]
        added = 4
    elif size == 'W':
        data[data_offset:data_offset+2]
        value = struct.unpack('>h', data[data_offset:data_offset+2])[0]
        added = 2
    elif size == 'B':
        data[data_offset:data_offset+2]
        value = (struct.unpack('>h', data[data_offset:data_offset+2])[0]) & 0xff
        added = 2
    else:
        raise Exception('unsupported size: ', size)
    return (value, added)


def operand(size, mode_bits, reg_bits, data, offset, skip=0):
    """Creates an operand from the given information"""
    result = ""
    added = 0
    mode = ADDR_MODES[mode_bits]
    size = size.upper()

    if mode == 'EXT':
        mode = ADDR_MODES_EXT[reg_bits]
        regnum = int(reg_bits, 2)
        # TODO: immediate operands are currently only string, might be
        # better to make them class instances
        if mode == '#<data>':
            imm_value, added = next_word(size, data, offset + 2 + skip)
            result = IntConstant(imm_value)
        elif mode in {'(xxx).L', '(xxx).W'}:  # absolute
            addr, added = next_word(mode[-1], data, offset + 2 + skip)
            result = AbsoluteAddress(addr, mode[-1])
        elif mode == '(d16,PC)':
            disp16, added = next_word('W', data, offset + 2 + skip)
            #result = "%02x(PC)" % disp16
            result = PCIndirectDisplacement(disp16)
        else:
            raise Exception("unsupported ext mode: '%s'" % mode)
    elif mode == '(d16,An)':
        regnum = int(reg_bits, 2)
        disp16, added = next_word('W', data, offset + 2 + skip)
        result = AddressRegisterIndirectDisplacement(regnum, disp16)
    elif mode == 'An':
        result = AddressRegister(int(reg_bits, 2))
    elif mode == '(An)':
        result = AddressRegisterIndirect(int(reg_bits, 2))
    elif mode == '(An)+':
        result = AddressRegisterIndirectPost(int(reg_bits, 2))
    elif mode == '-(An)':
        result = AddressRegisterIndirectPre(int(reg_bits, 2))
    elif mode == '(d8,An,Xn)':
        #result = AddressRegisterIndirectDisplacementIndex(int(reg_bits, 2))
        raise Exception('unsupported mode: ', mode)
    elif mode == 'Dn':
        result = DataRegister(int(reg_bits, 2))
    else:
        raise Exception('unsupported mode: ', mode)
    return result, added

def decode_move(bits, data, offset):
    category = OPCODE_CATEGORIES[bits[0:4]]
    total_added = 2
    # dst: reg|mode
    dst_op, added = operand(category[-1], bits[7:10], bits[4:7], data, offset)
    total_added += added

    # src: mode|reg
    src_op, added = operand(category[-1], bits[10:13], bits[13:16], data, offset)
    total_added += added
    return MoveInstruction(category, total_added, src_op, dst_op)

def decode_add_sub(name, bits, data, offset):
    total_added = 2
    reg = "D%d" % int(bits[4:7], 2)
    size, operation = OPMODES[bits[7:10]]
    ea, added = operand(size, bits[10:13], bits[13:16], data, offset)
    total_added += added

    if operation == 'ea,dn->dn':
        src = ea
        dst = reg
    elif operation == 'dn,ea->ea':
        src = reg
        dst = ea
    else:
        raise Exception('Unknown operation for %s' % name)

    return Operation2('%s.%s' % (name, size), total_added, src, dst)


def decode_misc(bits, data, offset):
    #print("misc bits: " + bits)
    if bits == '0100111001110101':  # rts
        return Opcode('rts', 2)
    elif bits == '0100111001110001':  # nop
        return Opcode('nop', 2)
    elif bits == '0100101011111100': # illegal
        return Opcode('illegal', 2)
    elif bits[7:10] == '111':  # lea
        regnum = int(bits[4:7], 2)
        ea, added = operand('l', bits[10:13], bits[13:16], data, offset)
        return Operation2('lea', added + 2, ea, AddressRegister(regnum))
    elif bits.startswith('0100111010'):  # jsr
        ea, added = operand('l', bits[10:13], bits[13:16], data, offset)
        return Jump('jsr', offset, added + 2, ea)
    elif bits.startswith('0100111011'):  # jmp
        ea, added = operand('l', bits[10:13], bits[13:16], data, offset)
        return Jump('jmp', added + 2, ea)
    elif bits.startswith('01001010'):  # tst.x
        size = SIZES[int(bits[8:10], 2)]
        ea, added = operand('l', bits[10:13], bits[13:16], data, offset)
        return Operation1('tst.%s' % size, added + 2, ea)
    else:
        print("unrecognized misc: %s" % bits)
        raise Exception('TODO Misc')


def signed8(value):
    return -(256 - value) if value > 127 else value


def branch_displacement(bits, data, offset):
    """disp, added = read displacement"""
    disp = signed8(int(bits[8:16], 2))
    if disp == 0:  # 16 bit displacement
        return next_word('W', data, offset + 2)
    elif disp == -1:  # 32 bit displacement
        return next_word('L', data, offset + 2)
    else:
        return disp, 0


def decode(data, offset):
    bits = "{0:016b}".format(struct.unpack(">H", data[offset:offset+2])[0])
    # first step categorize by looking at bits 15-12
    opcode = bits[0:4]
    category = OPCODE_CATEGORIES[opcode]
    print(bits)

    if is_move(category):
        instr = decode_move(bits, data, offset)
    elif category in {'add_addx', 'sub_subx'}:
        if bits[7] == 1 and bits[10:12] == '11':  # extended
            raise Exception('addx/subx not supported yet')
        else:
            instr = decode_add_sub(category[0:3], bits, data, offset)
    elif category == 'misc':
        instr = decode_misc(bits, data, offset)
    elif category == 'moveq':
        regnum = int(bits[4:7], 2)
        value = signed8(int(bits[8:16], 2))
        #instr = Operation2('moveq', 2, IntConstant(value), DataRegister(regnum))
        instr = MoveInstruction("moveq", 2, IntConstant(value), DataRegister(regnum))
    elif category == 'bcc_bsr_bra':
        if bits[0:8] == '01100000':  # bra
            disp, added = branch_displacement(bits, data, offset)
            instr = Jump('bra', offset, added + 2, disp)
        elif bits[0:8] == '01100001':  # bsr
            disp, added = branch_displacement(bits, data, offset)
            instr = Jump('bsr', offset, added + 2, disp)
        else:
            cond = CONDITION_CODES[int(bits[4:8], 2)]
            disp, added = branch_displacement(bits, data, offset)
            instr = Jump('b%s' % cond, offset, added + 2, disp)
    elif category == 'addq_subq':
        if bits[7] == '0':  # addq
            ea, added = operand('l', bits[10:13], bits[13:16], data, offset)
            value = int(bits[4:7], 2)
            instr = Operation2('addq', added + 2, IntConstant(value), ea)
        else:
            raise Exception('TODO addq_subq etc')
    elif category == 'bitops_movep_imm':
        if bits[0:10] == '0000100000':
            ea, added1 = operand('l', bits[10:13], bits[13:16], data, offset, skip=2)
            bitnum, added2 = next_word('W', data, offset + 2)
            instr = Operation2('btst', added1 + added2 + 2, IntConstant(bitnum & 0xff), ea)
        elif bits[0:8] == '00001100':
            size = SIZES[int(bits[8:10], 2)]
            immdata, added1 = next_word(size.upper(), data, offset + 2)
            ea, added2 = operand(size, bits[10:13], bits[13:16], data, offset, skip=added1)
            instr = Operation2('cmpi.' + size, added1 + added2 + 2, IntConstant(immdata), ea)
        else:
            detail = bits[8:11]
            print("bits at offset: %d -> %s" % (offset, bits))
            raise Exception('TODO: bitops, detail: ' + detail)
    elif category == 'cmp_eor':
        regnum = int(bits[4:7], 2)
        opmode = bits[7:10]
        addr_mode = OPMODES[opmode]
        size = addr_mode[0]
        if addr_mode[1] == 'ea,dn->dn':
            ea, added = operand(size, bits[10:13], bits[13:16], data, offset)
            instr = Operation2('cmp.' + size, added + 2, ea, DataRegister(regnum))
        else:
            raise Exception('TODO: cmp_eor')
    else:
        print("\nUnknown instruction\nCategory: ", category, " Bits: ", bits)
        raise Exception('TODO')
    #print("%d: %s" % (offset, instr))
    return instr
