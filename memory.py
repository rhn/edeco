class MemoryStructure:
    """represents some memory space"""
    def __init__(self, size=None):
        """size=None means infinite, counted in bytes"""
        self.members = {} # {(address rel begining of structure):member}
        self.size = size

    def get_member(self, member_address):
        return self.members[member_address]

    def add_member(self, member_address, member):
        if member_address in self.members:
            raise ValueError('Member already here')

        self.members[member_address] = member

    def get_name(self, addr):
       return self.members[addr].DEFAULT_PREFIX + hex(addr)


class DataSpace(MemoryStructure):
    def to_str(self):
        member_strings = []
        for addr, member in sorted(self.members.items()): # sorted wrt address
            name = member.DEFAULT_PREFIX + hex(addr)
            member_strings.append('// {0}\n'
                                  '{1}'.format(hex(addr), member.to_str(name)))

        return '\n'.join(member_strings) + '\n\n'
    
    def get_access_name(self, base, offset):
        struct = self.members[base]
        return self.get_name(base) + '.' + struct.get_name(offset)


class Variable:
    DEFAULT_PREFIX = 'var_'
    def __init__(self, size):
        self.size = size
    
    def to_str(self, name):
        size = 'b' + str(self.size * 8)
        return size + ' ' + name + ';'


class Structure(MemoryStructure):
    DEFAULT_PREFIX = 'str_'
    def to_str(self, name):
        member_strings = []
        for addr, member in sorted(self.members.items()): # sorted wrt address
            member_name = member.DEFAULT_PREFIX + hex(addr)
            member_strings.append('    // +{0}\n'
                                  '    {1}'.format(hex(addr), member.to_str(member_name)))

        struct_string = 'struct {0} {{\n{1}\n}};'

        return struct_string.format(name, '\n'.join(member_strings))