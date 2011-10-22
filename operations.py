import values

def traceback_register(context, reg_spec):
    instructions, index, memory = context
    index = index - 1 

    while index >= 0:
        try:
            instruction = instructions[index]
            if reg_spec in instruction.get_modified_regs():
                return instruction.get_value((instructions, index, memory), reg_spec)

            index -= 1
        except NotImplementedError:
            print instruction.mnemonic, 'is not supported yet'
            return values.UnknownValue(reg_spec)
    return values.UnknownValue(reg_spec)


class Registers:
    REGISTERS = ['$r' + str(num) for num in range(16)]
    def __init__(self):
        self.gp = [values.UnknownValue(reg_name) for reg_name in self.REGISTERS]
    
    def get(self, name):
        return self.gp[int(name[2:])]

    def set(self, name, value):
        self.gp[int(name[2:])] = value


class MachineState:
    def __init__(self, memory_structure):
        self.regs = Registers()
        self.memory = memory_structure
    
    def read_mem(self, base, offset, size):
        size = int(size[1:]) / 8
        cell = self.memory.get_memory(base, offset, size)
        if cell is None:
            return values.MemoryRead(base, offset, size)
        return cell

    def write_mem(self, base, offset, size, value):
        pass

    def read_reg(self, reg_spec):
        return self.regs.get(reg_spec)
    
    def write_reg(self, reg_spec, value):
        return self.regs.set(reg_spec, value)
    

class DummyMachineState:
    """A machine state that only tracks reads and writes"""
    def __init__(self):
        self.read_places = set()
        self.written_places = set()

    def read_reg(self, reg_spec):
        self.read_places.add(reg_spec)
        return values.UnknownValue(None)

    def write_reg(self, reg_spec, value):
        self.written_places.add(reg_spec)

    def read_mem(self, base, offset, size):
        return values.UnknownValue

    def write_mem(self, base, offset, size, value):
        pass

    def get_read_places(self):
        return self.read_places
    
    def get_written_places(self):
        return self.written_places


class MemoryAssignment:
    def __init__(self, instructions, data_SRAM, store_index):
        self.instruction = instructions[store_index]
        self.index = store_index
        
        self.base = self.instruction.base
        self.offset = self.instruction.offset
 
        self.value = self.instruction.source
        self.memory = None

        self.instructions = instructions
        self.affected_instructions = []
        self.data_SRAM = data_SRAM

    def mark_complete(self):
        for instruction in self.affected_instructions:
            instruction.mark_chain(self.instruction.addr)

        self.instruction.replaced_by = self

    def get_memory_size(self):
        return int(self.instruction.size[1:]) / 8
    
    def traceback(self):
        self.base = self.instruction.get_value((self.instructions, self.index, self.data_SRAM), self.instruction.base)

        if not isinstance(self.instruction.offset, int):
            self.offset = self.instruction.get_value((self.instructions, self.index, self.data_SRAM), self.instruction.offset)
        
        size = self.get_memory_size()
        self.memory = self.data_SRAM.get_memory(self.base, self.offset, size)
        self.value = self.instruction.get_value((self.instructions, self.index, self.data_SRAM), self.instruction.source)
    
    def __str__(self):
        value = self.value
        if isinstance(value, int):
            value = hex(value)
        return '{0} = {1};'.format(self.memory, value)