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
        return self.instruction.size
    
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