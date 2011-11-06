from instructions import Instruction
import memory
import operations


def find_function_addresses(parsed_code):
    '''returns ints'''
    function_addrs = []

    for instruction in parsed_code:
        if instruction.calls_function():
            function_addrs.append(instruction.function)
    return set(function_addrs)


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