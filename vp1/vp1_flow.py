from flow.emulator import *
from flow.exceptions import *


ADDRESS_UNIT = '$a_u'
VECTOR_UNIT = '$v_u'
SCALAR_UNIT = '$r_u'
BRANCH_UNIT = 'br_u'


class Emulator:
    """Finds flow graph by emulating instructions. Specific to vp1 and its model of branch delays.
    """
    def __init__(self, instructions, start_address):
        self.instructions = instructions
        self.flow = StartNode()
        self._end = EndNode()
        self.find(self.get_index(start_address))

    def get_index(self, address):
        for i, instr in enumerate(self.instructions):
            if instr.address == address:
                return i
        raise FunctionBoundsException("Address 0x{0:x} out of this code block.".format(address))

    def find_existing_subflow(self, index):
        """BFS over the whole graph to find the subflow node containing instruction indexed with index."""
        nodes = [self.flow]
        traversed_nodes = set()
        while nodes:
            new_nodes = []
            for node in nodes:
                if not isinstance(node, StartNode) and not isinstance(node, EndNode):
                    if node.instructions.start_index <= index < node.instructions.end_index:
                        return node
                if not isinstance(node, EndNode):
                    followers = frozenset(node.following).difference(traversed_nodes)
                    traversed_nodes.update(followers)
                    new_nodes.extend(list(followers))
            nodes = new_nodes
        return None

    def find(self, start_index):
        self.find_subflow(self.flow, start_index)

    def get_bundle(self, index):
        bundle_index = index / 4
        return self.instructions[bundle_index * 4:(bundle_index + 1) * 4]

    def commit_flow(self, source_node, start_index, end_index):
        """Adds executed instructions to the graph."""
        instructions = Instructions(self.instructions[start_index:end_index + 1], start_index, end_index + 1)
        subflow = Subflow(instructions)
        add_edge(source_node, subflow)
        return subflow

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

        executed_instructions = []
        current_index = index
        
        machine_jump_target = None
        machine_jump_reason = None
        machine_jump_fresh = False
        
        for instruction in self.instructions[current_index:]:
            machine_jump_fresh = False
            executed_instructions.append(instruction)
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

    def find_subflow(self, source, start_index):
#        print 'subflow after', source, 'starting', hex(self.instructions[start_index].address)
        subflow = self.find_existing_subflow(start_index)
        if subflow is None:
            self.follow_subflow(source, start_index)
        else:
            # joins back with already traversed branch
#            print 'this comes back into', subflow

            # if joins into the beginning od a branch, only add edge
            # if joins into the middle of a branch, perform some splitting
            if start_index != subflow.instructions.start_index:
                presubflow = subflow.copy_before_index(start_index)
                for preceding in subflow.preceding:
                    preceding.following.remove(subflow)
                    preceding.following.append(presubflow)
                subflow.cut_before_index(start_index)
                add_edge(presubflow, subflow)
                    
#                print 'rips it apart, results:', presubflow, subflow
    #            print 'sf', source.following
   #             print 'pp', presubflow.preceding
  #              print 'pf', presubflow.following
 #               print 'fp', subflow.preceding
#                print 'ff', subflow.following
            add_edge(source, subflow)
