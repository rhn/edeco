import operations


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
    if '+' in addr:
        return addr.split('+')
    return addr, '0'


class GenericInstruction:
    def __init__(self, address, mnemonic, operands):
        self.addr = address
        self.address = self.addrtoint()
        self.mnemonic = mnemonic
        self.operands = operands

        # a little bridge to make an Instruction closer to a small Operation
        self.operation_result = None

        # get rid of these eventually. replacement will be handled in a structured manner
        self.used_in = [] # list of addresses of final instructions this one contributed to
        self.replaced_by = None # an Operation that completely replaces this instruction

    def addrtoint(self):
        return int(self.addr, 16)

    def mark_chain(self, address):
        self.used_in.append(address)

    def __str__(self):
        ins = ' '.join([self.addr + ':   ', self.mnemonic] + self.operands)
        if self.used_in:
            ins = ins + ' // ' + ' '.join(self.used_in)
        if self.replaced_by is not None:
            ins = '// ' + ins + '\n' + str(self.replaced_by) + '\n'
        return ins

    def evaluate(self, machine_state):
        """Changes the machine state to the best of out knowledge. no return value.
        """
        raise NotImplementedError

    def get_read_regs(self):
        state = operations.TrackingMachineState()
        self.evaluate(state)
        return state.get_read_places()

    def get_modified_regs(self):
        state = operations.TrackingMachineState()
        self.evaluate(state)
        return state.get_written_places()

    def get_value(self, context, reg_spec):
        state = operations.MachineState()
        for reg in self.get_read_regs():
            value = operations.traceback_register(context, reg)
            state.regs.set(reg, value)
        self.evaluate(state)
        return state.regs.get(reg_spec)


class BRAInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.target = parse_imm(operands[-1])
        if len(operands) == 1:
            self.condition = ''
        else:
            self.condition = parse_imm(operands[0])


class LDInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.size = operands[0]
        self.destination = operands[1]
        addr = operands[2][2:-1]
        
        base, offset = parse_address(addr)
        if not (base.startswith('$r') or base.startswith('$sp')):
            raise Exception('unsupported base ' + base + ' of ' + GenericInstruction.__str__(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)


class STInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.size = operands[0]
        self.source = operands[2]
        addr = operands[1][2:-1]
        
        base, offset = parse_address(addr)
        if not (base.startswith('$r') or base.startswith('$sp')):
            raise Exception('unsupported base ' + base + ' of ' + GenericInstruction.__str__(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)

    def evaluate(self, machine_state):
        """Unfinished - memory write"""
        machine_state.read_reg(self.source)
        if not isinstance(self.offset, int):
            machine_state.read_reg(self.offset)
        machine_state.read_reg(self.base)


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


instruction_map = {'ld': LDInstruction,
                   'st': STInstruction,
                   'mov': MOVInstruction,
                   'bra': BRAInstruction}

def Instruction(address, mnemonic, operands):
    try:
        cls = instruction_map[mnemonic]
    except KeyError:
        cls = GenericInstruction
    try:
        return cls(address, mnemonic, operands)
    except:
        print GenericInstruction(address, mnemonic, operands)
        raise