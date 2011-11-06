from common import instructions
import machine


def parse_imm(operand):
    if operand.startswith('0x'):
        return int(operand[2:], 16)
    elif operand.startswith('-0x'):
        return -int(operand[3:], 16)
    else:
        return int(operand)


def parse_reg(operand):
    if not operand.startswith("$a"):
        raise ValueError("Register type unsupported " + operand)
    else:
        return operand


def parse_memory_address(operand):
    if not (operand.startswith('[') and operand.endswith(']')):
        raise ValueError("Memory access format unknown " + operand)
    else:
        operand = operand[1:-1]
        if "+" in operand:
            base, offset = operand.split("+")
            base = parse_reg(base)
            offset = parse_imm(offset)
        else:
            base = parse_reg(operand)
            offset = 0
        return base, offset


class BranchInstruction(instructions.GenericInstruction):
    def __init__(self, arch, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, mnemonic, operands)
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
    def __init__(self, arch, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, mnemonic, operands)
        self.target = parse_imm(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return False


class JumpDynamicInstruction(instructions.GenericInstruction):
    def __init__(self, arch, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, mnemonic, operands)
        self.target = parse_reg(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return False


class RetInstruction(instructions.GenericInstruction):
    def breaks_function(self):
        return True


class CallInstruction(instructions.GenericInstruction):
    """Doesn't support the 0x8 thing (first mnemonic)"""
    def __init__(self, arch, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, mnemonic, operands)
        self.function = parse_imm(operands[1])

    def calls_function(self):
        return True


class StoreInstruction(instructions.GenericInstruction):
    def __init__(self, arch, address, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, mnemonic, operands)
        self.source = parse_reg(operands[0])
        self.base, self.offset = parse_memory_address(operands[1])
        self.size = 4

    def stores_memory(self):
        return True

    def evaluate(self, machine_state):
        value = machine_state.read_register(self.source)
        machine_state.write_memory(self.base, self.offset, 32, value)


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
                   'jx': JumpDynamicInstruction,
                   's32i': StoreInstruction,
                   's32i.n': StoreInstruction}


def Instruction(address, mnemonic, operands):
    return instructions.Instruction(machine.Architecture, address, mnemonic, operands, instruction_map)