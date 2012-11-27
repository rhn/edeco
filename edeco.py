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
            print 'finding function at', hex(address)
            functions.append(detect_function(arch, instructions, address))
        except FlowDetectionError, e:
            print e
    return functions


def parse_instructions(parser, arch, lines):
    # TODO: move to parsers
    # filter out instructions and parse them
    instructions = []
    for line in lines:
        line = line.strip()
        if not line.startswith('//') and not line == '' and not line.startswith('['):
            try:
                instructions.append(parser.parse_line(arch, line))
            except parsers.ParsingError, e:
                #print e, 'line skipped'
                pass
    return instructions


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Detects control flow in assembly files.")
    arg_parser.add_argument('-m', '--microcode', type=str, choices=['fuc', 'xtensa', 'vp1', 'x86_64'], required=True, help='microcode name')
    arg_parser.add_argument('--cmap', type=str, help='code space map file')
    arg_parser.add_argument('-x', '--no-autodetect', action='store_true', default=False, help="Don't autodetect functions")
    arg_parser.add_argument('deasm', type=str, help='input deasm file')
    arg_parser.add_argument('deco', type=str, help='output decompiled file')
    arg_parser.add_argument('-f', '--function', action="append", help="Function address: decimal (123) or hex (0x12ab)")
    args = arg_parser.parse_args()

    # input file
    with open(args.deasm) as deasm:
        data = deasm.readlines()

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
        import x86_64 as arch
        import parsers.objdump as insn_parser
    else:
        raise ValueError("ISA {0} unsupported".format(args.microcode))
    

    instructions = parse_instructions(insn_parser, arch, data)

    function_mapping = {}
    if args.cmap:
        with open(args.cmap) as cmap:
            for line in cmap:
                result = insn_parser.parse_functions_cmap(line.strip())
                if result:
                    address, name = result
                    function_mapping[address] = name

    # find functions
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
