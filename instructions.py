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

    def get_read_regs(self):
        raise NotImplementedError

    def get_modified_regs(self):
        raise NotImplementedError

    def emulate(self, regs):
        raise NotImplementedError


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
        if not base.startswith('$r'):
            raise Exception('wrong base ' + base + ' of ' + GenericInstruction.str(self))
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
        if not base.startswith('$r'):
            raise Exception('wrong base ' + base + ' of ' + GenericInstruction.str(self))
        else:
            self.base = base
        
        self.offset = parse_reg_or_imm(offset)

    def get_read_regs(self):
        regs = [self.base, self.source]
        if isinstance(self.offset, str):
            regs.append(self.offset)
        return regs
    
    def get_modified_regs(self):
        return []


class MOVInstruction(GenericInstruction):
    def __init__(self, address, mnemonic, operands):
        GenericInstruction.__init__(self, address, mnemonic, operands)
        self.source = parse_reg_or_imm(operands[1])
        self.destination = operands[0]

    def get_read_regs(self):
        if isinstance(self.source, str):
            return [self.source]
        return []

    def get_modified_regs(self):
        return [self.destination]

    def emulate(self, regs):
        regs.set_(self.destination, self.source)


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