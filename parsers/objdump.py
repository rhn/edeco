from common import *


def parse_line(arch, disasmline):
    """Format:
    1234:   56 78 90      mnemonic operand1,operand2
    addr:   op co de      mnemonic operand1,operand2
    """
    addr, rest = disasmline.split(':', 1)
    try:
        str_opcode, rest = rest.strip().split("  ", 1)
    except ValueError, e:
        raise ParsingError("line {0} invalid".format(repr(disasmline)))
    opcode = tuple(int(charpair[0], 16) * 16 + int(charpair[1], 16) for charpair in str_opcode.strip().split())
    
    instruction = rest

    spl = instruction.strip().split()
    
    # FIXME: fond out the format and parse it properly
    mnemonic = spl[0]
    operands = spl[1:]
    return arch.Instruction(addr, opcode, mnemonic, operands)
