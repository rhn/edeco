import common.instructions as instructions


GenericInstruction = instructions.GenericInstruction


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


class BRAInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.target = parse_imm(operands[-1])
        if len(operands) == 1:
            self.condition = ''
        else:
            self.condition = parse_imm(operands[0])


class CALLInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.function = parse_imm(operands[0])

    def calls_function(self):
        return True


class RETInstruction(GenericInstruction):
    def breaks_function(self):
        return True


class LDInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.size = operands[0]
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
            offset = machine_state.read_reg(self.offset)
        base = machine_state.read_reg(self.base)
        value = machine_state.read_mem(base, offset, self.size)
        machine_state.write_reg(self.destination, value)


class STInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.size = operands[0]
        self.source = operands[2]
        
        base, offset = parse_address(operands[1])
        if not (base.startswith('$r') or base.startswith('$sp')):
            raise Exception('unsupported base ' + base + ' of ' + GenericInstruction.__str__(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)

    def evaluate(self, machine_state):
        source = machine_state.read_reg(self.source)
        offset = self.offset
        if not isinstance(self.offset, int):
            offset = machine_state.read_reg(self.offset)
        base = machine_state.read_reg(self.base)
        machine_state.write_mem(base, offset, self.size, source)


class MOVInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.source = parse_reg_or_imm(operands[1])
        self.destination = operands[0]

    def evaluate(self, machine_state):
        if not isinstance(self.source, int):
            value = machine_state.read_reg(self.source)
        else:
            value = self.source
        machine_state.write_reg(self.destination, value)


class CLEARInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.size = operands[0]
        self.destination = operands[1]

    def evaluate(self, machine_state):
        if self.size == 'b32':
            value = 0
        else:
            reg = machine_state.read_reg(self.destination)
            if self.size == 'b16':
                value = reg & 0xffff0000
            else: # b8
                value = reg & 0xffffff00
        machine_state.write_reg(self.destination, value)


class ANDInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.destination = operands[0]
        self.source1 = operands[-2]
        self.source2 = parse_reg_or_imm(operands[-1])

    def evaluate(self, machine_state):
        s1 = machine_state.read_reg(self.source1)
        if isinstance(self.source2, int):
            s2 = self.source2
        else:
            s2 = machine_state.read_reg(self.source2)
        machine_state.write_reg(self.destination, s1 & s2)


class SETHIInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.destination = operands[0]
        self.source = parse_imm(operands[1])

    def evaluate(self, machine_state):
        value = machine_state.read_reg(self.destination)
        value = value & 0xFFFF | self.source
        machine_state.write_reg(self.destination, value)


instruction_map = {'ld': LDInstruction,
                   'st': STInstruction,
                   'mov': MOVInstruction,
                   'bra': BRAInstruction,
                   'clear': CLEARInstruction,
                   'and': ANDInstruction,
                   'sethi': SETHIInstruction,
                   'call': CALLInstruction,
                   'ret': RETInstruction}


def Instruction(address, mnemonic, operands):
    return instructions.Instruction(address, mnemonic, operands, instruction_map)