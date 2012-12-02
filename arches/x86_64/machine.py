import values
import memory


class Registers:
    REGISTERS = ['$a' + str(num) for num in range(16)]
    def __init__(self):
        self.gp = [values.UnknownValue(reg_name) for reg_name in self.REGISTERS]
    
    def get(self, name):
        return self.gp[int(name[2:])]

    def set(self, name, value):
        self.gp[int(name[2:])] = value


class MachineState:
    def __init__(self, memory, name=None):
        self.memory = memory
        self.name = name
        self.regs = Registers()

    def copy(self, name):
        return MachineState(self.memory.copy(), name)

    def read_register(self, reg_spec):
        return self.regs.get(reg_spec)
    
    def write_register(self, reg_spec, value):
        return self.regs.set(reg_spec, value)

    def read_memory(self, base, offset, size):
        cell = self.memory.get_memory(base, offset, size)
        if cell is None:
            return values.MemoryRead(base, offset, size)
        return cell

    def write_memory(self, base, offset, size, value):
        pass

    def get_memory(self, base, offset, size):
        return self.memory.get_cell_untracked(base, offset, size)


class DummyMachineState:
    """A machine state that only tracks reads and writes"""
    def __init__(self):
        self.read_places = set()
        self.written_places = set()

    def read_register(self, reg_spec):
        self.read_places.add(reg_spec)
        return values.UnknownValue(None)

    def write_register(self, reg_spec, value):
        self.written_places.add(reg_spec)

    def read_memory(self, base, offset, size):
        return values.UnknownValue(None)

    def write_memory(self, base, offset, size, value):
        pass

    def get_read_places(self):
        return self.read_places
    
    def get_written_places(self):
        return self.written_places


class Memory:
    def __init__(self, structure):
        self.structure = structure

    def copy(self):
        return Memory(self.structure)

    def get_cell_untracked(self, base, offset, size):
        return values.MemoryRead(base, offset, size)


class Environment:
    def __init__(self):
        self.memory_structure = memory.MemoryStructure()

    def get_unknown_state(self, name):
        return MachineState(self.get_empty_memory(), name)

    def get_dummy_state(self):
        return DummyMachineState()

    def get_empty_memory(self):
        return Memory(self.memory_structure)


class Architecture:
    DummyMachineState = DummyMachineState
    MachineState = MachineState
