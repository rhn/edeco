from exceptions import *

def add_edge(from_, to):
    from_.following.append(to)
    to.preceding.append(from_)


class Instructions:
    def __init__(self, instructions, start_index, end_index):
        self.instructions = instructions
        self.start_index = start_index
        self.end_index = end_index

    def copy_before(self, index):
        relative_index = index - self.start_index
        instructions = self.instructions[:relative_index]
        return Instructions(instructions, self.start_index, index)

    def copy_after(self, index):
        relative_index = index - self.start_index
        instructions = self.instructions[relative_index:]
        return Instructions(instructions, index, self.end_index)


class Node:
    pass


class Subflow(Node):
    def __init__(self, instructions):
        self.instructions = instructions
        self.following = []
        self.preceding = []

    def copy_before_index(self, index):
        new_flow = Subflow(self.instructions.copy_before(index))
        new_flow.preceding = self.preceding[:]
        return new_flow

    def cut_before_index(self, index):
        self.instructions = self.instructions.copy_after(index)
        self.preceding = []

    def __str__(self):
        return hex(self.instructions.instructions[0].address) + ":" + hex(self.instructions.instructions[-1].address)

    __repr__=__str__

    def other_neighbors(self, excluded):
        neighbors = set(self.preceding).union(set(self.following))
        neighbors.remove(excluded)
        return neighbors


class StartNode(Node):
    def __init__(self):
        self.following = []
        self.preceding = []

    def __str__(self):
        return 'start'

    def other_neighbors(self, excluded):
        neighbors = set(self.following)
        if excluded is not None:
            neighbors.remove(excluded)
        return neighbors


class EndNode(Node):
    def __init__(self):
        self.preceding = []
        self.following = []

    def __str__(self):
        return 'end'

    def other_neighbors(self, excluded):
        neighbors = set(self.preceding)
        neighbors.remove(excluded)
        return neighbors


class FunctionFlowEmulator:
    """Finds flow graph by emulating instructions.
    For future reference: ditching all results on a jump into parsed code should be acceptable.
    """
    """Notes:
    store Subflow tree self.currently_detected_flow
    pass current leaf to find_subflow, ALWAYS must be attached to stored root
    finish and append a leaf as soon as jump is detected
    after jump is detected, look for its target in root. If found, what to do?
        break branch into pieces and reevaluate? could chop off itself. how to evaluate jumpback?
            how to store jumpback?
                full reference to code? if code is chopped off, it will be evaluated again
        break branch into pieces and insert full reference to code?

    how to store backwardflows?
        full link to code? easy to parse
        full link and remove forwardflow? how to tell them apart in complex code? and consecutive normal flows will merge
        full link with backwardflow/forwardflow annotation? forwardflows must be annotated. looks good, preserves sortable graph structure
    """
    """Chosen: store subflows normally, separate following (splits) and preceding (joins) flows, make no exception for "straight" flow.
    """
    def __init__(self, arch, instructions, start_address):
        self.arch = arch
        self.instructions = instructions
        self.flow = StartNode()
        self._end = EndNode()
        self.find(self.get_index(start_address))

    def get_index(self, address):
        for i, instr in enumerate(self.instructions):
            if instr.address == address:
                return i

    def find_containing_subflow(self, index):
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

    def find_subflow(self, source, start_index):
#        print 'subflow after', source, 'starting', hex(self.instructions[start_index].address)
        def commit_flow(end_index):
            instructions = Instructions(self.instructions[start_index:end_index + 1], start_index, end_index + 1)
            subflow = Subflow(instructions)
            add_edge(source, subflow)
            return subflow

        subflow = self.find_containing_subflow(start_index)
        if subflow:
#            print 'this comes back into', subflow

            if start_index != subflow.instructions.start_index:
        #        print 'sf', source.following
       #         print 'fp', subflow.preceding
      #          print 'ff', subflow.following
            
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
            return
   #     print 'node starts fresh'
        current_index = start_index
        
        newest_instructions = []

        # for instruction in self.instructions indexed by current_index:
        for instruction in self.instructions[current_index:]:
            newest_instructions.append(instruction)
            if instruction.jumps():
#                print 'leaving', hex(self.instructions[start_index].address), 'from', hex(instruction.address)
                if not (isinstance(instruction.target, int) or isinstance(instruction.target, long)):
                    raise EmulationUnsupported("Function can't be traced, contains a dynamic jump at 0x{0:x}.".format(instruction.address))
                if instruction.is_conditional():
                    subflow = commit_flow(current_index)
                    self.find_subflow(subflow, current_index + 1)
#                    print 'again from', hex(instruction.address)
                    self.find_subflow(subflow, self.get_index(instruction.target))
                    return
                else:
                    subflow = commit_flow(current_index)
                    self.find_subflow(subflow, self.get_index(instruction.target))
                    return
            elif instruction.breaks_function():
                subflow = commit_flow(current_index)
                add_edge(subflow, self._end)
#                print subflow, 'is *FINISH*ed'
                return
            
            post_subflow = self.find_containing_subflow(current_index + 1)
            if post_subflow:
#                print '*CRASH*es with', post_subflow
                subflow = commit_flow(current_index)
                add_edge(subflow, post_subflow)
                return
    #        print 'crashes not'

            current_index += 1    


def emulate_flow(arch, instructions, start_index):
    return FunctionFlowEmulator(arch, instructions, start_index).flow
