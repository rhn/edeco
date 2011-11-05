from common import instructions

instruction_map = {}

def Instruction(address, mnemonic, operands):
    return instructions.Instruction(address, mnemonic, operands, instruction_map)