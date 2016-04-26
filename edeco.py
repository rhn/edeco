#!/usr/bin/env python

import sys
from flow import detect_function, FlowDetectionError
import memory
import argparse
import parsers


def find_functions(arch, instructions, function_addrs):
    functions = []
    for address in sorted(function_addrs):
        try:
            print('finding function at 0x{0:x}'.format(address))
            functions.append(detect_function(arch, instructions, address))
        except FlowDetectionError as e:
            print(e)
    return functions


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Detects control flow in assembly files.")
    arg_parser.add_argument('-m', '--microcode', type=str, choices=['fuc', 'xtensa', 'vp1', 'x86_64'], required=True, help='microcode name')
    arg_parser.add_argument('--cmap', type=str, help='code space map file')
    arg_parser.add_argument('-x', '--no-autodetect', action='store_true', default=False, help="Don't autodetect functions")
    arg_parser.add_argument('deasm', type=str, help='input deasm file')
    arg_parser.add_argument('deco', type=str, help='output decompiled file')
    arg_parser.add_argument('-f', '--function', action="append", help="Function address: decimal (123) or hex (0x12ab)")
    args = arg_parser.parse_args()

    if args.microcode == 'fuc':
        import fuc as arch
        import parsers.envydis as insn_parser
    elif args.microcode == 'xtensa':
        import xtensa as arch
        import parsers.envydis as insn_parser
    elif args.microcode == 'vp1':
        import vp1 as arch
        import parsers.envydis as insn_parser
    elif args.microcode == 'x86_64':
        if args.cmap:
            raise Exception("cmap file not supported on x86_64")
        if not args.no_autodetect:
            args.cmap = args.deasm
        import arches.x86_64 as arch
        from parsers import objdump as insn_parser
    else:
        raise ValueError("ISA {0} unsupported".format(args.microcode))
    
    # input file
    with open(args.deasm) as deasm:
        data = deasm.readlines()

    instructions = insn_parser.parse_instructions(insn_parser, arch, data)

    function_mapping = {}
    if args.cmap:
        with open(args.cmap) as cmap:
            for line in cmap:
                result = insn_parser.parse_functions_cmap(line.strip())
                if result:
                    address, name = result
                    function_mapping[address] = name

    # find functions in 3 steps
    # step 1: user-provided
    # step 2: disasm metadata
    # step 3: instructions themselves
    # TODO: define rules for overriding
    # TODO. implement as separate steps
    addrs = function_mapping.keys()
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
    functions = find_functions(arch, instructions, function_addrs)
    
    # functions are now basic nested graphs of flow

    code_memory = memory.CodeMemory(functions, function_mapping)

    with open(args.deco, 'w') as output:
        output.write(str(code_memory))
