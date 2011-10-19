class Registers:
    def __init__(self):
        self.gp = range(16)
    
    def get(self, name):
        return self.gp[int(name[2:])]

    def set(self, name, value):
        self.gp[int(name[2:])] = value


class MachineState:
    def __init__(self):
        self.regs = Registers()

    def read_reg(self, reg_spec):
        return self.regs.get(reg_spec)
    
    def write_reg(self, reg_spec, value):
        return self.regs.set(reg_spec, value)
    

class TrackingMachineState(MachineState):
    """A MachineState that in addition to normal emulation capabilities additionally tracks reads and writes.
    """
    def __init__(self):
        MachineState.__init__(self)
        self.read_places = set()
        self.written_places = set()

    def read_reg(self, reg_spec):
        self.read_places.add(reg_spec)
        return MachineState.read_reg(self, reg_spec)

    def write_reg(self, reg_spec, value):
        self.written_places.add(reg_spec)
        return MachineState.write_reg(self, reg_spec, value)

    def get_read_places(self):
        return self.read_places
    
    def get_written_places(self):
        return self.written_places


class MemoryAssignment:
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

        while index > 0 and required_registers:
            try:
                instruction = self.code[index]
                satisfied_regs = set(instruction.get_modified_regs()).intersection(required_registers)
                instruction.get_modified_regs()

                if satisfied_regs: # relevant to getting the data
                    required_registers.difference_update(satisfied_regs)
                    required_registers.update(set(instruction.get_read_regs()))
                    instructions.insert(0, instruction)
                index -= 1
            except NotImplementedError:
                print instruction.mnemonic, 'is not supported yet'
                return

        if len(required_registers) == 0:
            state = MachineState()
            for instruction in instructions:
                instruction.evaluate(state)
            self.base = state.regs.get(self.store.base)
            size = int(self.store.size[1:]) / 8
            self.memory = self.data_SRAM.get_memory(self.base, self.offset, size)
            self.affected_instructions = instructions[:-1]
    
    def __str__(self):
        if self.value == None:
            value = self.store.source
        else:
            value = self.value
        return '{0} = {1};'.format(str(self.memory), value)