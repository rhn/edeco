class MemoryCell:
    def __init__(self, size):
        self.size = size
        self.owner = None

    def __str__(self):
        if not self.owner:
            raise ValueError("Cell unprocessed, role unknown")
        return self.owner.get_access_name()


class MemoryLayout:
    """Represents a memory space and its accesses structured in a way specific to the arch.
    """
    def find_structure(self):
        """Returns MemoryStructure"""
        raise NotImplementedError


class FucMemoryLayout(MemoryLayout):
    """Memory access model for fuc. Assumes no unions"""
    def __init__(self):
        self.accesses = {} # (base, offset), MemoryCell
    
    def get_memory(self, base, offset, size):
        if (base, offset) in self.accesses:
            memory_cell = self.accesses[base, offset]
            if memory_cell.size != size:
                raise ValueError("Memory sizes don't match. Looks like an union or a bug")
        else:
            memory_cell = MemoryCell(size)
            self.accesses[base, offset] = memory_cell
        return memory_cell

    def find_structure(self):
        def find_offsets_of(addr, i):
            offsets = []
            for baseaddr, offset in sorted_addrs[i:]:
                if baseaddr == addr:
                    offsets.append(offset)
                else:
                    break
            return offsets

        memory_structure = DataSpace()
        sorted_addrs = list(sorted(self.accesses.keys()))
        for i, (baseaddr, offset) in enumerate(sorted_addrs):
            all_offsets = find_offsets_of(baseaddr, i)
            cell = self.accesses[baseaddr, offset]
            if len(all_offsets) == 1 and list(sorted(all_offsets))[0] == 0:
                memory_structure.add_member(baseaddr, Variable(cell))
            else:
                try:
                    struct = memory_structure.get_member(baseaddr)
                except KeyError:
                    struct = Structure()
                    memory_structure.add_member(baseaddr, struct)
                struct.add_member(offset, Variable(cell))

        return memory_structure


class MemoryStructure:
    """Decompiled and analyzed version of the layout"""
    def __init__(self):
        """size=None means infinite, counted in bytes"""
        self.members = {} # {(address rel begining of structure):member}
        self.parent = None

    def get_member(self, member_address):
        return self.members[member_address]

    def add_member(self, member_address, member):
        if member_address in self.members:
            raise ValueError('Member already here ' + str(member_address))

        member.parent = self
        self.members[member_address] = member
        member.set_name(self.get_name(member_address))

    def get_name(self, addr):
        return self.members[addr].DEFAULT_PREFIX + hex(addr)            


class DataSpace(MemoryStructure):
    def __str__(self):
        member_strings = []
        for addr, member in sorted(self.members.items()): # sorted wrt address
            member_strings.append('// {0}\n'
                                  '{1}'.format(hex(addr), member))

        return '\n'.join(member_strings) + '\n\n'

    def get_access_prefix(self):
        return ''


class Variable:
    DEFAULT_PREFIX = 'var_'
    def __init__(self, cell):
        self.size = cell.size
        cell.owner = self
        self.name = None
        self.parent = None
    
    def __str__(self):
        size = 'b' + str(self.size * 8)
        return size + ' ' + self.name + ';'

    def set_name(self, name):
        self.name = name

    def get_access_name(self):
        return self.parent.get_access_prefix() + self.name


class Structure(MemoryStructure):
    DEFAULT_PREFIX = 'str_'
    def __init__(self):
        MemoryStructure.__init__(self)
        self.name = None
        self.parent = None

    def set_name(self, name):
        self.name = name

    def get_access_prefix(self):
        return self.parent.get_access_prefix() + self.name + '.'

    def __str__(self):
        member_strings = []
        for addr, member in sorted(self.members.items()): # sorted wrt address
            member_strings.append('    // +{0}\n'
                                  '    {1}'.format(hex(addr), member))

        struct_string = 'struct {0} {{\n{1}\n}};'

        return struct_string.format(self.name, '\n'.join(member_strings))