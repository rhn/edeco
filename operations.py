class Registers:
    def __init__(self):
        self.gp = range(16)
    
    def get(self, name):
        return self.gp[int(name[2:])]

    def set_(self, name, value):
        self.gp[int(name[2:])] = value


class Emulator:
    def __init__(self, instructions):
        self.instructions = instructions
        self.regs = Registers()

    def go(self):
        for instruction in self.instructions:
            instruction.emulate(self.regs)


class MemoryAssignment:
    TRACEBACK_LIMIT = 10 # instructions
    def __init__(self, instructions, data_SRAM, store_index):
        self.store = instructions[store_index]
        self.index = store_index
        
        # those two won't be needed
        self.base = None # first one
        # second one
        if isinstance(self.store.offset, int):
            self.offset = self.store.offset
        else:
            self.offset = None

        self.value = None
        self.memory = None

        self.code = instructions
        self.affected_instructions = []
        self.data_SRAM = data_SRAM

    def mark_complete(self):
        for instruction in self.affected_instructions:
            instruction.mark_chain(self.store.addr)

        self.store.replaced_by = self

    def get_memory_size(self):
        return int(self.store.size[1:]) / 4
    
    def traceback_base(self):
        if self.offset is None:
            raise NeedProperTracing
        required_registers = set([self.store.base])
        instructions = [self.store]

        index = self.index - 1

        while index > 0 and self.index - self.TRACEBACK_LIMIT <= index and required_registers:
            try:
                instruction = self.code[index]
                satisfied_regs = set(instruction.get_modified_regs()).intersection(required_registers)
                if satisfied_regs: # relevant to getting the data
                    required_registers.difference_update(satisfied_regs)
                    required_registers.update(set(instruction.get_read_regs()))
                    instructions.insert(0, instruction)
                index -= 1
            except NotImplementedError:
                print instruction.mnemonic, 'is not supported yet'
                return
        if len(required_registers) == 0:
            emul = Emulator(instructions[:-1])
            emul.go()
            self.base = emul.regs.get(self.store.base)
            size = int(self.store.size[1:]) / 8
            self.memory = self.data_SRAM.get_memory(self.base, self.offset, size)
            self.affected_instructions = instructions[:-1]
    
    def __str__(self):
        if self.value == None:
            value = self.store.source
        else:
            value = self.value
        return '{0} = {1};'.format(str(self.memory), value)