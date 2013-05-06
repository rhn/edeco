from common import instructions
import machine
import flow.emulator


# XXX: move to parser
def parse_target(operand):
    """Format: ab <function+0xcd>
    Format: absolute_address <function_name+0xfunction_offset>
    """
    return int(operand.split()[0], 16)


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


class BaseInstruction(instructions.GenericInstruction, flow.emulator.FlowInstructionMixIn):
    def calls_function(self):
        raise NotImplementedError


class SimpleInstruction(BaseInstruction):
    def jumps(self):
        return False
    
    def breaks_function(self):
        return False

    def calls_function(self):
        return False


class CondJumpInstruction(BaseInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        BaseInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        
        self.condition = mnemonic[1:]
        self.target = parse_target(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return True

    def calls_function(self):
        return False



class JumpInstruction(BaseInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        BaseInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.target = parse_target(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return False

    def calls_function(self):
        return False


class RetInstruction(BaseInstruction):
    def jumps(self):
        return False
        
    def breaks_function(self):
        return True

    def calls_function(self):
        return False


class CallInstruction(BaseInstruction):
    """Doesn't support the 0x8 thing (first operand)"""
    def __init__(self, arch, address, opcode, mnemonic, operands):
        BaseInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.function = parse_target(operands[0])
        
    def jumps(self):
        return False
    
    def breaks_function(self):
        return False

    def calls_function(self):
        return True


instruction_map = {'ret': RetInstruction,
                   'retq': RetInstruction,
                   'call': CallInstruction,
                   'jmp': JumpInstruction,
                   'jmpq': JumpInstruction,
                   'jne': CondJumpInstruction,
                   'jle': CondJumpInstruction,
                   'jbe': CondJumpInstruction,
                   'je': CondJumpInstruction,
                   'jl': CondJumpInstruction,
                   'ja': CondJumpInstruction}
                   

def Instruction(address, opcode, mnemonic, operands):
    return instructions.Instruction(machine.Architecture, address, opcode, mnemonic, operands, instruction_map, SimpleInstruction)
