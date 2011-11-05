from instructions import Instruction


def find_function_addresses(parsed_code):
    '''returns ints'''
    function_addrs = []

    for instruction in parsed_code:
        if hasattr(instruction, 'function'):
            function_addrs.append(instruction.function)
    return set(function_addrs)