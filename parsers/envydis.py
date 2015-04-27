from parsers.common import *


def parse_line(arch, disasmline):
    """Typical format:
    012345: 01234567  BC mnemonic operand1 operand2
    address: opcode  FLAGS mnemonic operand1 operand2
    flags: uppercase, instruction: lowercase
    """
    addr, rest = disasmline.split(':', 1)
    try:
        opcode, rest = rest.strip().split("  ", 1)
    except ValueError, e:
        raise ParsingError("line {0} invalid".format(repr(disasmline)))
    
    # make opcode a X-int tuple, to be similar to py3k bytes
    opcode.strip()
    if len(opcode) % 2:
        opcode = '0' + opcode
    
    opcode = tuple((int(first, 16) * 16 + int(second, 16) for first, second in zip(opcode[::2], opcode[1::2])))
    
    # destroy flags, stupid way:
    flags = 'ABCDEFGHIJKLMNOPQRSTUWVXYZ'
    
    instruction = rest
    for flag in flags:
        instruction = instruction.replace(flag, '')
    spl = instruction.strip().split()
    mnemonic = spl[0]
    operands = spl[1:]
    return arch.Instruction(addr, opcode, mnemonic, operands)


def parse_functions_cmap(cmapline):
    if cmapline.startswith('C'):
        typ, addr, name = cmapline.split()
        if name == '?':
            name = None
        addr = int(addr, 16)
        return addr, name

