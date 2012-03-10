from instructions import Instruction
import vp1_flow

def find_function_addresses(instructions):
    print 'finding functions is a stub'
    return set()
    
    
def detect_flow(instructions, start_address):
    flow_emulator = vp1_flow.Emulator(instructions, start_address)
    return flow_emulator.flow
