from common import instructions


def parse_imm(operand):
    if operand.startswith('0x'):
        return int(operand[2:], 16)
    elif operand.startswith('-0x'):
        return -int(operand[3:], 16)
    else:
        try:
            return int(operand)
        except ValueError:
            return operand


class BranchInstruction(instructions.GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, address, mnemonic, operands)
        if mnemonic.endswith('z'):
            target = operands[1]
        else:
            target = operands[2]
        
        self.target = parse_imm(target)

    def jumps(self):
        return True

    def is_conditional(self):
        return True


class JumpInstruction(instructions.GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, address, mnemonic, operands)
        self.target = parse_imm(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return False


class RetInstruction(instructions.GenericInstruction):
    def breaks_function(self):
        return True


class CallInstruction(instructions.GenericInstruction):
    """Doesn't support the 0x8 thing (first mnemonic)"""
    def __init__(self, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, address, mnemonic, operands)
        self.function = parse_imm(operands[1])

    def calls_function(self):
        return True


instruction_map = {'retw': RetInstruction,
                   'retw.n': RetInstruction,
                   'call': CallInstruction,
                   'beqz': BranchInstruction,
                   'bnez': BranchInstruction,
                   'bgez': BranchInstruction,
                   'bltz': BranchInstruction,
                   'beqi': BranchInstruction,
                   'bnei': BranchInstruction,
                   'bgei': BranchInstruction,
                   'blti': BranchInstruction,
                   'bgeui': BranchInstruction,
                   'bltui': BranchInstruction,
                   'bbci': BranchInstruction,
                   'bbsi': BranchInstruction,
                   'beq': BranchInstruction,
                   'bne': BranchInstruction,
                   'bge': BranchInstruction,
                   'blt': BranchInstruction,
                   'bgeu': BranchInstruction,
                   'bltu': BranchInstruction,
                   'bany': BranchInstruction,
                   'bnone': BranchInstruction,
                   'ball': BranchInstruction,
                   'bnall': BranchInstruction,
                   'bbc': BranchInstruction,
                   'bbs': BranchInstruction,
                   'j': JumpInstruction,
                   'jx': JumpInstruction}


def Instruction(address, mnemonic, operands):
    return instructions.Instruction(address, mnemonic, operands, instruction_map)