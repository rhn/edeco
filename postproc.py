#!/usr/bin/env python

import sys
from instructions import Instruction
import memory
import operations
import argparse

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

def parse_line(disasmline):
    addr = disasmline[:8]
    code = disasmline[instruction_offset:]
    spl = code.split(' ')
    mnemonic = spl[0]
    operands = spl[1:]
    return Instruction(addr, mnemonic, operands)

def find_functions(parsed_code):
    '''returns ints'''
    function_addrs = []

    for instruction in parsed_code:
        if instruction.mnemonic == 'call':
            function_addrs.append(int(instruction.operands[0][2:], 16))
    return set(function_addrs)


def mark_flow(instructions, function_addrs):
    instr_index = 0
    for address in sorted(function_addrs):
        if start_vram <= address <= end_vram:
            while instructions[instr_index].addrtoint() != address:
                instr_index += 1
            instr = instructions[instr_index]
            instr.set_function_entry()
        else:
            print 'function not in this segment:', hex(address)


def find_memory_structures(instructions, data_SRAM):
    """This function sucks. should be split into finding memory layout and then finding roles, naming structures and whatnot.
    """
    write_candidates = []
    for i, instruction in enumerate(instructions):
        if instruction.mnemonic == 'st':
            write_candidates.append(operations.MemoryAssignment(instructions, data_SRAM, i))
    
    for candidate in write_candidates:
        candidate.traceback_base()

    memory_structure = data_SRAM.find_structure()
    
    for candidate in write_candidates:
        if candidate.memory is not None:
            candidate.mark_complete()
    return memory_structure


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="decompile fuc")
    parser.add_argument('-o', '--asmoffset', type=int, default=28, help='asm instruction offset')
    parser.add_argument('-g', '--greedy', action='store_true', default=True, help='try to encapsulate all code in functions')
    parser.add_argument('deasm', type=str, help='input deasm file')
    parser.add_argument('deco', type=str, help='output decompiled file')
    args = parser.parse_args()
    with open(args.deasm) as deasm:
        data = deasm.readlines()

    instruction_offset = args.asmoffset
    
    instructions = []
    for line in data:
        line = line.strip()
        if not line.startswith('//') and not line == '':
            instructions.append(parse_line(line))


    start_vram = instructions[0].addrtoint()
    end_vram = instructions[-1].addrtoint()
    print 'start', hex(start_vram), 'end', hex(end_vram)
    function_addrs = find_functions(instructions)

    mark_flow(instructions, function_addrs)

    data_SRAM = memory.FucMemoryLayout()

    memory_structure = find_memory_structures(instructions, data_SRAM)

    '''
    if len(sys.argv) > 3:
        with open(sys.argv[2]) as debook:
            known_functions = find_known_functions(debook)
    '''

    with open(args.deco, 'w') as output:
        output.write(str(memory_structure))
        strings = [str(instr) for instr in instructions]
        output.write('\n'.join(strings))