from parsers.common import *
import re

# TODO: implement as objects to utilize inheritance

class objdump:
    function_header = re.compile('^(?P<address>[a-f0-9]*) ' + re.escape('<') + '(?P<name>.+)' + re.escape('>: ') + '*$')
    """Compatible with -Mintel"""
    
    @classmethod
    def parse_instructions(cls, arch, lines):
        return parse_instructions(cls, arch, lines)

    @staticmethod
    def parse_line(arch, disasmline):
        """Format:
        1234:   56 78 90      mnemonic dest,src
        addr:   op co de      mnemonic destination,source
        """
        addr, rest = disasmline.split(':', 1)
        try:
            str_opcode, rest = rest.strip().split("  ", 1)
        except ValueError, e:
            raise ParsingError("line {0} invalid".format(repr(disasmline)))
        opcode = tuple(int(charpair[0], 16) * 16 + int(charpair[1], 16) for charpair in str_opcode.strip().split())
        
        instruction = rest

        spl = instruction.strip(',').split()
        
        # FIXME: find out the format and parse it properly
        mnemonic = spl[0]
        operands = spl[1:]
        return arch.Instruction(addr, opcode, mnemonic, operands)
        
    @classmethod
    def parse_functions_cmap(cls, cmapline):
        matches = re.match(cls.function_header, cmapline)
        if matches:
            addr, name = matches.groupdict()['address'], matches.groupdict()['name']
            return int(addr, 16), name
