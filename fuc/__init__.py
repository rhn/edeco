from instructions import Instruction
import memory
import operations
import common
import flow.emulator


def detect_flow(instructions, start_address):
    """Creates a flat flow graph."""
    flow_emulator = flow.emulator.SimpleEmulator(instructions, start_address)
    return flow_emulator.flow


def find_function_addresses(parsed_code):
    '''returns ints'''
    function_addrs = []

    for instruction in parsed_code:
        if instruction.calls_function() and (isinstance(instruction.function, int) or isinstance(instruction.function, long)):
            function_addrs.append(instruction.function)
    return set(function_addrs)


class MemoryStructureInstructionAnalyzer(common.MemoryStructureInstructionAnalyzer):
    def __init__(self):
        common.MemoryStructureInstructionAnalyzer.__init__(self)
        self.data_memory = memory.FucMemoryLayout()
