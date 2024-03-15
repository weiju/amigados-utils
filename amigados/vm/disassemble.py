import struct
from collections import deque
from amigados.vm.cpu import *




def print_instruction(address, instr):
    print("$%08x:\t%s" % (address, instr))


def disassemble(code):
    """Disassembling a chunk of code works on this assumptions:

    the first address in the block contains a valid instruction from here
      a. branches: add the branch target to the list of continue points
      b. if the instruction is an absolute jump/branch, we can't safely
         assume the code after the instruction is valid -> continue at branch
         target
      c. conditional branch -> add the address after the instruction as a valid
         ass valid decoding location
      d. rts: we can't assume the code after this instruction is valid

    In order to achieve an ordered sequence of instructions, we store the
    disassembled instructions and their addresses in a list and sort them
    in ascending order after completion
    """
    reachable = deque([0])
    seen = set()
    result = []
    while len(reachable) > 0:  # offset < len(code):
        offset = reachable.popleft()
        #print("offset is now: %d" % offset)
        seen.add(offset)
        instr = decode(code, offset)
        result.append((offset, instr))

        if instr.is_return():
            continue  # we can't assume any valid code to come after a return

        # enqueue the address after the instruction
        if not instr.is_absolute_branch():
            new_dest = offset + instr.size
            if new_dest < len(code) and new_dest not in seen:
                reachable.append(new_dest)

        # following jumps and branches is non-trivial the problem is that we need to be
        # able to tell local from global branches. For now, only branch instructions
        # are recognized as local branches.
        # TODO: jumps can be local as well, if the destination is to a relocatable
        # address, we need to include that information, too
        if instr.is_local_branch():
            # note that the branch target is computed based on the address after the
            # 16 bit opcode, ignoring additional extension words in the displacement
            branch_dest = offset + 2 + instr.displacement
            if not branch_dest in seen:
                reachable.append(branch_dest)

    result.sort(key=lambda x: x[0])
    for addr, instr in result:
        print_instruction(addr, instr)
