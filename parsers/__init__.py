from parsers.common import *
import re

# TODO: implement as objects to utilize inheritance

class objdump:
    function_header = re.compile('^(?P<address>[a-f0-9]*) ' + re.escape('<') + '(?P<name>.+)' + re.escape('>: ') + '*$')
    """Compatible with -Mintel"""
    
    @classmethod
    def parse_deasm(cls, arch, lines):
        instructions = []
        function_mapping = {}
        
        for line in lines:
            line = line.strip('\n')
            if line:
                if line.lstrip() != line:
                    instructions.append(cls.parse_instruction(arch, line))
                elif re.match(cls.function_header, line):
                    addr, name = cls.parse_functions_cmap(line)
                    if addr in function_mapping:
                        raise ValueError('Function at 0x{0:x} with name {0} already defined as {1}'.format(addr, function_mapping[addr], name))
                    function_mapping[addr] = name
                else:
                    # some comment...
                    pass
        return instructions, function_mapping
    
    @classmethod
    def parse_instructions(cls, arch, lines):
        # TODO: deprecated, deasm file will contain more than instructions
        return cls.parse_deasm(arch, lines)[0]

    @staticmethod
    def parse_instruction(arch, disasmline):
        """Format:
        1234:   56 78 90      mnemonic dest,src
        addr:   op co de      mnemonic destination,source
        """
        addr, rest = disasmline.split(':', 1)
        try:
            ret = rest.strip().replace('\t', '  ').split("  ", 1)
            if len(ret) == 1:
                str_opcode, rest = ret[0], ''
            else:
                str_opcode, rest = ret
        except ValueError, e:
            raise ParsingError("line {0!r} invalid".format(repr(disasmline)))
        
        try:
            opcode = tuple(int(charpair[0], 16) * 16 + int(charpair[1], 16) for charpair in str_opcode.strip().split())
        except ValueError, e:
            raise ParsingError("opcode {0!r} invalid".format(str_opcode))
        
        instruction = rest

        spl = instruction.strip().split(' ', 1)

        mnemonic = spl[0]
        if len(spl) > 1:
            operands = spl[1].strip().split(',')
        else:
            operands = []
        return arch.Instruction(addr, opcode, mnemonic, operands)
        
    @classmethod
    def parse_functions_cmap(cls, cmapline):
        matches = re.match(cls.function_header, cmapline)
        if matches:
            addr, name = matches.groupdict()['address'], matches.groupdict()['name']
            return int(addr, 16), name
