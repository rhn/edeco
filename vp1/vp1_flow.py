from flow.emulator import *
from flow.exceptions import *


ADDRESS_UNIT = '$a_u'
VECTOR_UNIT = '$v_u'
SCALAR_UNIT = '$r_u'
BRANCH_UNIT = 'br_u'


class Emulator(FunctionFlowEmulator):
    """Finds flow graph by emulating instructions. Specific to vp1 and its model of branch delays.
    """
    def get_bundle(self, index):
        bundle_index = index / 4
        return self.instructions[bundle_index * 4:(bundle_index + 1) * 4]

    def follow_subflow(self, source, index):
        def will_jump():
            if machine_jump_fresh: # check first obligatory delay slot
                return False
            
            next_index = current_index + 1

            in_bundle_index = next_index % 4
            if in_bundle_index == 0: # check inter-bundle boundary
                return True
                
            next_bundle = self.get_bundle(next_index)
            exec_unit = self.instructions[next_index].exec_unit
            for instruction in next_bundle[:in_bundle_index]: # check if execution unit was already used
                if instruction.exec_unit == exec_unit:
                    return True
            return False

        current_index = index
        
        machine_jump_target = None
        machine_jump_reason = None
        machine_jump_fresh = False
        
        for instruction in self.instructions[current_index:]:
            machine_jump_fresh = False
            jump_target = instruction.get_branch_target()
            if jump_target is not None:
#                print 'leaving', hex(self.instructions[start_index].address), 'from', hex(instruction.address)
                if not (isinstance(jump_target, int) or isinstance(jump_target, long)):
                    raise EmulationUnsupported("Function can't be traced, contains a dynamic jump at 0x{0:x}.".format(instruction.address))
                    
                machine_jump_target = jump_target
                machine_jump_reason = instruction
                machine_jump_fresh = True
            elif instruction.is_exit():
                subflow = self.commit_flow(source, index, current_index)
                add_edge(subflow, self._end)
#                print subflow, 'is *FINISH*ed'
                return
            
            # jump is checked _before_ next instruction. It's possible there is no more instructions
            if machine_jump_target is not None and will_jump():
                # XXX: check jump reason
                if True:
                    subflow = self.commit_flow(source, index, current_index)
                    self.find_subflow(subflow, current_index + 1)
    #                    print 'again from', hex(instruction.address)
                    self.find_subflow(subflow, self.get_index(machine_jump_target))
                else:
                    subflow = self.commit_flow(source, index, current_index)
                    self.find_subflow(subflow, self.get_index(instruction.target))
                return

            post_subflow = self.find_existing_subflow(current_index + 1)
            if post_subflow:
#                print '*CRASH*es with', post_subflow
                subflow = self.commit_flow(source, index, current_index)
                add_edge(subflow, post_subflow)
                return
    #        print 'crashes not'

            current_index += 1
