from instructions import Instruction
import vp1_flow

def find_function_addresses(instructions):
    addresses = []
    for instruction in instructions:
        call_target = instruction.get_call_target()
        if call_target is not None:
            addresses.append(call_target)
    return set(addresses)
    
    
def detect_flow(instructions, start_address):
    flow_emulator = vp1_flow.Emulator(instructions, start_address)
    return flow_emulator.flow
