import machine
import common.instructions as instructions
import flow.emulator


def parse_size(operand):
    if operand.startswith("b") and int(operand[1:]) % 8 == 0:
        return int(operand[1:]) / 8
    raise ValueError("Unrecognized size: " + operand)


def parse_reg_or_imm(operand):
    if operand.startswith('$'):
        return operand
    else:
        return parse_imm(operand)


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


def parse_address(addr):
    if not (addr.startswith('[') and addr.endswith(']')):
        raise ValueError("Address format unsupported " + addr)
    addr = addr[1:-1]
    if '+' in addr:
        return addr.split('+')
    return addr, '0'


class FucInstruction(instructions.GenericInstruction, flow.emulator.FlowInstructionMixIn):
    def calls_function(self):
        raise NotImplementedError


class SimpleInstruction(FucInstruction):
    def jumps(self):
        return False
    
    def breaks_function(self):
        return False

    def calls_function(self):
        return False


class BRAInstruction(FucInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        FucInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.target = parse_imm(operands[-1])
        if len(operands) == 1:
            self.condition = ''
        else:
            self.condition = parse_imm(operands[0])

    def jumps(self):
        return True

    def is_conditional(self):
        return self.condition
        
    def breaks_function(self):
        return False

    def calls_function(self):
        return False


class CALLInstruction(FucInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        FucInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.function = parse_imm(operands[0])

    def jumps(self):
        return False
    
    def breaks_function(self):
        return False
    
    def calls_function(self):
        return True


class RETInstruction(FucInstruction):
    def jumps(self):
        return False

    def breaks_function(self):
        return True
        
    def calls_function(self):
        return False


class LDInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.size = parse_size(operands[0])
        self.destination = operands[1]
        
        base, offset = parse_address(operands[2])
        if not (base.startswith('$r') or base.startswith('$sp')):
            raise Exception('unsupported base ' + base + ' of ' + GenericInstruction.__str__(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)

    def evaluate(self, machine_state):
        offset = self.offset
        if not isinstance(self.offset, int):
            offset = machine_state.read_register(self.offset)
        base = machine_state.read_register(self.base)
        value = machine_state.read_memory(base, offset, self.size)
        machine_state.write_register(self.destination, value)


class STInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.size = parse_size(operands[0])
        self.source = operands[2]
        
        base, offset = parse_address(operands[1])
        if not (base.startswith('$r') or base.startswith('$sp')):
            raise Exception('unsupported base ' + base + ' of ' + GenericInstruction.__str__(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)

    def evaluate(self, machine_state):
        source = machine_state.read_register(self.source)
        offset = self.offset
        if not isinstance(self.offset, int):
            offset = machine_state.read_register(self.offset)
        base = machine_state.read_register(self.base)
        machine_state.write_memory(base, offset, self.size, source)

    def stores_memory(self):
        return True


class MOVInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.source = parse_reg_or_imm(operands[1])
        self.destination = operands[0]

    def evaluate(self, machine_state):
        if not isinstance(self.source, int):
            value = machine_state.read_register(self.source)
        else:
            value = self.source
        machine_state.write_register(self.destination, value)


class CLEARInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.size = operands[0]
        self.destination = operands[1]

    def evaluate(self, machine_state):
        if self.size == 'b32':
            value = 0
        else:
            reg = machine_state.read_register(self.destination)
            if self.size == 'b16':
                value = reg & 0xffff0000
            else: # b8
                value = reg & 0xffffff00
        machine_state.write_register(self.destination, value)


class ANDInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.destination = operands[0]
        self.source1 = operands[-2]
        self.source2 = parse_reg_or_imm(operands[-1])

    def evaluate(self, machine_state):
        s1 = machine_state.read_register(self.source1)
        if isinstance(self.source2, int):
            s2 = self.source2
        else:
            s2 = machine_state.read_register(self.source2)
        machine_state.write_register(self.destination, s1 & s2)


class SETHIInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        SimpleInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.destination = operands[0]
        self.source = parse_imm(operands[1])

    def evaluate(self, machine_state):
        value = machine_state.read_register(self.destination)
        value = value & 0xFFFF | self.source
        machine_state.write_register(self.destination, value)


instruction_map = {'ld': LDInstruction,
                   'st': STInstruction,
                   'mov': MOVInstruction,
                   'bra': BRAInstruction,
                   'clear': CLEARInstruction,
                   'and': ANDInstruction,
                   'sethi': SETHIInstruction,
                   'call': CALLInstruction,
                   'ret': RETInstruction}


def Instruction(address, opcode, mnemonic, operands):
    return instructions.Instruction(machine.Architecture, address, opcode, mnemonic, operands, instruction_map, SimpleInstruction)
