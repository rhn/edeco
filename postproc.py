#!/usr/bin/env python

import sys
from flow import Function, FunctionBoundsException, ControlStructure
import memory
import operations
import argparse


class ParsingError(ValueError): pass


def parse_line_envydis(arch, disasmline):
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
    return arch.Instruction(addr, mnemonic, operands)


def parse_functions_cmap_envydis(cmapline):
    if cmapline.startswith('C'):
        typ, addr, name = cmapline.split()
        if name == '?':
            name = None
        addr = int(addr, 16)
        return addr, name


def find_functions(instructions, function_addrs, code_memory):
    instr_index = 0
    for address in sorted(function_addrs):
        if start_vram <= address <= end_vram:
            while instructions[instr_index].address != address:
                instr_index += 1
            try:
                code_memory.add_function(Function(instructions, instr_index))
            except FunctionBoundsException, e:
                print e
        else:
            print 'function not in this segment:', hex(address)
    return functions


def parse_instructions(arch, lines):
    # filter out instructions and parse them
    instructions = []
    for line in lines:
        line = line.strip()
        if not line.startswith('//') and not line == '' and not line.startswith('['):
            try:
                instructions.append(parse_line_envydis(arch, line))
            except ParsingError, e:
                #print e, 'line skipped'
                pass
    return instructions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="decompile fuc")
    parser.add_argument('-m', '--microcode', type=str, choices=['fuc', 'xtensa'], required=True, help='microcode name')
    parser.add_argument('--cmap', type=str, help='code space map file')
    parser.add_argument('-g', '--greedy', action='store_true', default=False, help='try to encapsulate all code in functions')
    parser.add_argument('-d', '--diagrams', action='store_true', default=False, help='Generate control flow diagrams for unresolved control patterns. Requires pydot and graphviz')
    parser.add_argument('-x', '--no-autodetect', action='store_true', default=False, help="Don't autodetect functions")
    parser.add_argument('deasm', type=str, help='input deasm file')
    parser.add_argument('deco', type=str, help='output decompiled file')
    parser.add_argument('-f', '--function', action="append", help="Function address")
    args = parser.parse_args()

    # input file
    with open(args.deasm) as deasm:
        data = deasm.readlines()


    ControlStructure.diagrams = args.diagrams
        

    if args.microcode == 'fuc':
        import fuc as arch
    elif args.microcode == 'xtensa':
        import xtensa as arch
    else:
        raise ValueError("ISA {0} unsupported".format(args.microcode))
    

    instructions = parse_instructions(arch, data)

    functions = {}
    if args.cmap:
        with open(args.cmap) as cmap:
            for line in cmap:
                result = parse_functions_cmap_envydis(line.strip())
                if result:
                    address, name = result
                    functions[address] = name

    code_memory = memory.CodeMemory(functions)

    # set globals
    start_vram = instructions[0].addrtoint()
    end_vram = instructions[-1].addrtoint()

    # find functions
    if args.greedy:
        index = 0
        try:
            while index < len(instructions):
                f = Function(instructions, index)
                code_memory.add_function(f)
                index += len(f.instructions)
        except FunctionBoundsException, e:
            print e
    else:
        addrs = functions.keys()
        if args.function:
            for addr in args.function:
                if addr.startswith('0x'):
                    addr = int(addr[2:], 16)
                else:
                    addr = int(addr)
                addrs.append(addr)
        
        function_addrs = set(addrs)
        if not args.no_autodetect:
            function_addrs.update(arch.find_function_addresses(instructions))
        find_functions(instructions, function_addrs, code_memory)


    # should be: first, evaluate memory accesses. Second, gather data from instructions
    memory_analyzer = arch.MemoryStructureInstructionAnalyzer()
    memory_structure = memory_analyzer.find_memory_structures(code_memory.functions)


    with open(args.deco, 'w') as output:
        output.write(str(memory_structure))
        output.write(str(code_memory))
