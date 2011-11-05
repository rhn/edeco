#!/usr/bin/env python

import sys
from flow import Function, FunctionBoundsException
import memory
import operations
import argparse


class ParsingError(ValueError): pass


def get_bra_address(operands):
  if len(operands) == 1:
    return operands[0]
  else:
    return operands[1]

def get_first_operand(operands):
    return operands[1]

branch_address_extractors = {'bra': get_bra_address,
                             'call': get_first_operand,
                             }

def get_instr_index(address, instructions):
    instr_index = 0
    first_addr = instructions[0].addrtoint()
    last_addr = instructions[-1].addrtoint()
    if first_addr <= address <= last_addr:
        while instructions[instr_index].addrtoint() != address:
            instr_index += 1
        if instr_index > len(instructions):
            raise NotFound
        return instr_index
    else:
        raise NotFound


def parse_line_envydis(disasmline):
    """Typical format:
    012345: 01 23 45 67  BC mnemonic operand1 operand2
    address: opcode  FLAGS mnemonic operand1 operand2
    flags: uppercase, instruction: lowercase
    """
    addr, rest = disasmline.split(':', 1)
    try:
        opcode, rest = rest.strip().split("  ", 1)
    except ValueError, e:
        raise ParsingError("line {0} invalid".format(repr(disasmline)))
    
    # destroy flags, stupid way:
    flags = 'ABCDEFGHIJKLMNOPQRSTUWVXYZ'
    
    instruction = rest
    for flag in flags:
        instruction = instruction.replace(flag, '')
    spl = instruction.strip().split()
    mnemonic = spl[0]
    operands = spl[1:]
    return Instruction(addr, mnemonic, operands)


def find_functions(instructions, function_addrs):
    functions = []
    instr_index = 0
    for address in sorted(function_addrs):
        if start_vram <= address <= end_vram:
            while instructions[instr_index].address != address:
                instr_index += 1
            try:
                functions.append(Function(instructions, instr_index))
            except FunctionBoundsException, e:
                print e
        else:
            print 'function not in this segment:', hex(address)
    return functions


class MemoryStructureInstructionAnalyzer:
    def __init__(self):
        self.data_SRAM = memory.FucMemoryLayout()
        self.analyzed_operations = None

    def find_memory_structures(self, functions):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="decompile fuc")
    parser.add_argument('-m', '--microcode', type=str, choices=['fuc', 'xtensa'], required=True, help='microcode name')
    parser.add_argument('-g', '--greedy', action='store_true', default=False, help='try to encapsulate all code in functions')
    parser.add_argument('deasm', type=str, help='input deasm file')
    parser.add_argument('deco', type=str, help='output decompiled file')
    parser.add_argument('-f', '--function', action="append", help="Function address")
    args = parser.parse_args()

    # input file
    with open(args.deasm) as deasm:
        data = deasm.readlines()

    if args.microcode == 'fuc':
        from fuc import *
    elif args.microcode == 'xtensa':
        from xtensa import *
    else:
        raise ValueError("ISA {0} unsupported".format(args.microcode))
    

    # filter out instructions and parse them
    instructions = []
    for line in data:
        line = line.strip()
        if not line.startswith('//') and not line == '' and not line.startswith('['):
            try:
                instructions.append(parse_line_envydis(line))
            except ParsingError, e:
                #print e, 'line skipped'
                pass

    # set globals
    start_vram = instructions[0].addrtoint()
    end_vram = instructions[-1].addrtoint()

    # find functions
    if args.greedy:
        functions = []
        index = 0
        try:
            while index < len(instructions):
                f = Function(instructions, index)
                functions.append(f)
                index += len(f.instructions)
        except FunctionBoundsException, e:
            print e
    else:
        addrs = []
        if args.function:
            for addr in args.function:
                if addr.startswith('0x'):
                    addrs.append(int(addr[2:], 16))
                else:
                    addrs.append(int(addr))
        
        function_addrs = find_function_addresses(instructions).union(set(addrs))
        functions = find_functions(instructions, function_addrs)

    memory_analyzer = MemoryStructureInstructionAnalyzer()
    memory_structure = memory_analyzer.find_memory_structures(functions)

    '''
    if len(sys.argv) > 3:
        with open(sys.argv[2]) as debook:
            known_functions = find_known_functions(debook)
    '''

    with open(args.deco, 'w') as output:
        output.write(str(memory_structure))
        for function in functions:
            output.write(str(function))
