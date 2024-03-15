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
