import common.instructions as instructions
import vp1_flow as flow

def parse_imm(operand):
    if operand.startswith('0x'):
        return int(operand[2:], 16)
    elif operand.startswith('-0x'):
        return -int(operand[3:], 16)
    else:
        return int(operand)


def get_exec_unit(opcode):
    oc = opcode[0]
    if oc > 0xff:
        raise ValueError("Impossible byte value")
    for start, unit in reversed([(0x00, flow.ADDRESS_UNIT),
                                 (0x80, flow.VECTOR_UNIT),
                                 (0xc0, flow.SCALAR_UNIT),
                                 (0xe0, flow.BRANCH_UNIT)]):
        if oc > start:
            return unit
    raise Exception("Execution unit table is messed up.")


class VP1Instruction(instructions.GenericInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        instructions.GenericInstruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.exec_unit = get_exec_unit(opcode)
    
    def __str__(self):
        return ' '.join([self.addr + ':  ({0})'.format(self.exec_unit), self.mnemonic] + self.operands)
    
    def get_branch_target(self):
        raise NotImplementedError
    
    def is_exit(self):
        raise NotImplementedError

    def is_return(self):
        raise NotImplementedError
        

class SimpleInstruction(VP1Instruction):
    def get_branch_target(self):
        return None

    def is_exit(self):
        return False
        
    def is_return(self):
        return False
        
    def get_call_target(self):
        return None


class BRAInstruction(VP1Instruction):
    """Both loop and regular"""
    def __init__(self, arch, address, opcode, mnemonic, operands):
        VP1Instruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.condition = operands[1:-1]
        self.target = parse_imm(operands[-1])
    
    def get_branch_target(self):
        return self.target
    
    def is_exit(self):
        return False
        
    def is_return(self):
        return False
        
    def get_call_target(self):
        return None        

class EXITInstruction(VP1Instruction):
    def get_branch_target(self):
        return None
        
    def is_exit(self):
        return True

    def is_return(self):
        return False

    def get_call_target(self):
        return None


class RETInstruction(VP1Instruction):
    def get_branch_target(self):
        return None
        
    def is_exit(self):
        return False

    def is_return(self):
        return True
    
    def get_call_target(self):
        return None


class CALLInstruction(SimpleInstruction):
    def __init__(self, arch, address, opcode, mnemonic, operands):
        VP1Instruction.__init__(self, arch, address, opcode, mnemonic, operands)
        self.target = parse_imm(operands[-1])

    def get_call_target(self):
        return self.target
        
        
instruction_map = {'bra': BRAInstruction,
                   'ret': RETInstruction,
                   'exit': EXITInstruction,
                   'call': CALLInstruction}


def Instruction(address, opcode, mnemonic, operands):
    # Machine emulation architecture not developed - therefore passing Null
    return instructions.Instruction(None, address, opcode, mnemonic, operands, instruction_map, SimpleInstruction)
