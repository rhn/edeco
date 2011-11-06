import memory
import values
import common.machine as machine


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
        return values.UnknownValue(None)

    def write_mem(self, base, offset, size, value):
        pass

    def get_read_places(self):
        return self.read_places
    
    def get_written_places(self):
        return self.written_places


class MemoryStructure:
    def __init__(self):
        self.data_SRAM = memory.FucMemoryLayout()
        self.analyzed_operations = None

    def get_unknown_state(self, name):
        return MachineState(self.data_SRAM, name)

    def analyze(self, functions):
        self.analyzed_operations = []
        for function in functions:
            function.apply_instruction_analyzer(self.scan_instruction_block)

        memory_structure = self.data_SRAM.find_structure()
        
        for candidate in self.analyzed_operations:
            if candidate.memory is not None:
                candidate.mark_complete()
        return memory_structure
    
    def scan_instruction_block(self, instructions):
        """This function sucks. should be split into finding memory layout and then finding roles, naming structures and whatnot.
        """
        write_candidates = []
        for i, instruction in enumerate(instructions):
            if instruction.mnemonic == 'st':
                write_candidates.append(operations.MemoryAssignment(instructions, self.data_SRAM, i))
        
        for candidate in write_candidates:
            candidate.traceback()
        self.analyzed_operations.extend(write_candidates)


class Architecture:
    DummyMachineState = DummyMachineState
    MachineState = MachineState