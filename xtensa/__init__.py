from instructions import Instruction 
import memory
import operations
import common


def find_function_addresses(parsed_code):
    '''returns ints'''
    function_addrs = []

    for instruction in parsed_code:
        if instruction.mnemonic == "entry":
            function_addrs.append(instruction.address)
        elif instruction.calls_function():
            function_addrs.append(instruction.function)
    return set(function_addrs)


class MemoryStructureInstructionAnalyzer(common.MemoryStructureInstructionAnalyzer):
    def __init__(self):
        common.MemoryStructureInstructionAnalyzer.__init__(self)
        self.data_memory = memory.FucMemoryLayout()