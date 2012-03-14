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
#        print 'next from', hex(self.instructions[index].address) + ':' + str(index % 4)
#        raw_input()
        def will_jump():
            if machine_jump_fresh: # check first obligatory delay slot
                return False
            
            next_index = current_index + 1

            in_bundle_index = next_index % 4
            if in_bundle_index == 0: # check inter-bundle boundary
                return True
                
            next_insn_bundle = self.get_bundle(next_index)
            exec_unit = self.instructions[next_index].exec_unit
            for instruction in next_insn_bundle[:in_bundle_index]: # check if execution unit was already used
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
     #           print 'jump from', hex(instruction.address) + ':' + str(current_index % 4)
                if not (isinstance(jump_target, int) or isinstance(jump_target, long)):
                    raise EmulationUnsupported("Function can't be traced, contains a dynamic jump at 0x{0:x}.".format(instruction.address))
                if machine_jump_reason:
                    raise InvalidCodeError("Trying to jump but there's already a jump in progress: " + str(instruction))
                machine_jump_target = jump_target
                machine_jump_reason = instruction
                machine_jump_fresh = True
            elif instruction.is_return():
                if machine_jump_reason:
                    raise InvalidCodeError("Trying to jump but there's already a jump in progress: " + str(instruction))                   
                machine_jump_reason = instruction
                machine_jump_fresh = True
            elif instruction.is_exit():
                subflow = self.commit_flow(source, index, current_index)
                add_edge(subflow, self._end)
#                print subflow, 'is *FINISH*ed'
                return
            
            # jump is checked _before_ next instruction. It's possible there is no more instructions
            if machine_jump_reason is not None and will_jump():
    #            print 'leaving after', hex(instruction.address) + ':' + str(current_index % 4)
   #             print  machine_jump_reason,  machine_jump_reason.get_branch_condition()
                if machine_jump_reason.is_return():
                    subflow = self.commit_flow(source, index, current_index)
                    add_edge(subflow, self._end)
                elif machine_jump_reason.get_branch_condition() is None:
  #                  print 'single'
                    subflow = self.commit_flow(source, index, current_index)
                    self.find_subflow(subflow, self.get_index(machine_jump_target))
                else:
 #                   print 'multi'
                    subflow = self.commit_flow(source, index, current_index)
                    self.find_subflow(subflow, current_index + 1)
#                    print 'again after', hex(instruction.address) + ':' + str(current_index % 4)
                    self.find_subflow(subflow, self.get_index(machine_jump_target))
                return

            post_subflow = self.find_existing_subflow(current_index + 1)
            if post_subflow:
#                print '*CRASH*es with', post_subflow
                subflow = self.commit_flow(source, index, current_index)
                add_edge(subflow, post_subflow)
                return
    #        print 'crashes not'

            current_index += 1
