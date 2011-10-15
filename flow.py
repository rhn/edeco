# --- *coding=UTF-8* ---

flow_changing_mnemonics = ['bra'] # ret looks more like an instruction, call doesn't change the flow
finishing_mnemonics = ['ret']
if_mnemonics = ['bra']


def indent(text):
    return ''.join('\n    ' + se 
                   for se in
                   text.split('\n'))


class FunctionBoundsException(Exception):
    pass


class ControlStructure:
    def __init__(self, code, joinsplits):
        self.instructions = code
        self.flow = self.find_closures(joinsplits)

    def find_closures(self, joinsplits):
        return None

    def __repr__(self):
        return 'cs ' + self.instructions[0].addr + ' ' + self.instructions[-1].addr

    def __str__(self):
        if self.flow == None:
            return 'FlowPattern {{{{\n{0}\n}}}}'.format(indent(str(LinearCode(self.instructions))))

class LinearCode:
    def __init__(self, code):
        self.instructions = code

    def __repr__(self):
        return 'lc ' + self.instructions[0].addr + ' ' + self.instructions[-1].addr

    def __str__(self):
        return '\n'.join(map(str,self.instructions))


class Closure:
    """Closure: code, control, code, control, ..."""
    def find_flow_patterns(self, joinsplits):
        control_structures = []

        flow_control_joinsplit_index = None
        current_forward_references = []
        linear_start_index = 0

        print joinsplits

        for i, joinsplit in enumerate(joinsplits):
            print current_forward_references
            if linear_start_index is not None: # was in linear flow mode
                # commit results
                print 'linear', linear_start_index, joinsplit.index, self.instructions[linear_start_index]
                if linear_start_index != joinsplit.index:
                    control_structures.append(LinearCode(self.instructions[linear_start_index:joinsplit.index]))

                # switch modes
                linear_start_index = None
                flow_control_joinsplit_index = i
            
            # control flow find mode only
            if joinsplit.get_referenced_index() > joinsplit.index: # forward reference. add it
                current_forward_references.append(joinsplit)
            elif joinsplit.get_referenced_index() < joinsplit.index: # backward reference. remove the other one
                reference_index = None
                for y, reference in enumerate(current_forward_references):
                    try:
                        if reference.matches(joinsplit):
                            reference_index = y
                    except:
                        pass
                if reference_index is None:
                    raise FlowDetectError("A past jumpsplit referred to can't be found")
                current_forward_references.pop(reference_index)
            else:
                raise FlowDetectError("Found self jump, not sure what to do")

            if len(current_forward_references) == 0: # no jumps/splits: must be linear from now on
                print 'control', joinsplit.index
                # switch modes
                linear_start_index = joinsplit.index

                #commit results
                subjoinsplits = joinsplits[flow_control_joinsplit_index:i + 1]
                instructions_start_index = subjoinsplits[0].index
                instructions_end_index = subjoinsplits[-1].index
                subinstructions = self.instructions[instructions_start_index:instructions_end_index]

                for joinsplit in subjoinsplits:
                    joinsplit.index -= instructions_start_index

                cs = ControlStructure(subinstructions, subjoinsplits)
                control_structures.append(cs)

#            raw_input()

        if linear_start_index is None:
            raise FlowDetectError("After evalutaing joinsplits, some are left")
        
        if linear_start_index < len(self.instructions):
            control_structures.append(LinearCode(self.instructions[linear_start_index:]))

        print control_structures

        self.flow = control_structures


class Function(Closure):
    def __init__(self, code, index):
        self.address = code[index].address
        self.index = index
        self.instructions = self.find(code)
        self.flow = None
        self.detect_flow()

    def find(self, code):
        """Assumes nothing will jump to the function from outside"""
        branches_outside = [] # list of target addresses
        for i in range(self.index, len(code)):
            instruction = code[i]
            current_address = instruction.address
            if instruction.mnemonic in flow_changing_mnemonics:
                if instruction.target < self.address:
                    raise CodeError("branch to before function start " + str(instruction))
                if instruction.target > current_address:
                    branches_outside.append(instruction.target)
            elif instruction.mnemonic in finishing_mnemonics:
                # prune branches outside
                new_outside_branches = []
                for branch_target in branches_outside:
                    if branch_target > current_address:
                        new_outside_branches.append(branch_target)
                branches_outside = new_outside_branches
                
                # check if found last return
                if not branches_outside:
                    return code[self.index:i + 1]
                '''
                else:
                    print instruction.addr, [hex(branch) for branch in branches_outside]
                '''
        
        raise FunctionBoundsException("function at {0} doesn't finish within the given code".format(hex(self.address)))

    def get_index(self, address):
        for i, instruction in enumerate(self.instructions):
            if instruction.address == address:
                return i
        raise ValueError("Address {0} out of function range".format(address))

    def find_jumps(self):
        jumps = []
        for i, instruction in enumerate(self.instructions):
            if instruction.mnemonic in flow_changing_mnemonics:
                source = self.get_index(instruction.address)
                destination = self.get_index(instruction.target)
                conditional = (instruction.condition != '')
                jumps.append((source, destination, conditional))
        return jumps

    def detect_flow(self):
        jumps = self.find_jumps()
        joinsplits = jumps_to_joinsplits(jumps)
        self.find_flow_patterns(joinsplits)

    def __str__(self):
        flow_elm_texts = []
        for flow_element in self.flow:
            flow_elm_texts.append(indent(str(flow_element)))

        flow_text = '\n'.join(flow_elm_texts)

        return '\n// {0}\nf_{0}(...) {{\n{1}\n}}\n'.format(hex(self.address), flow_text)
                            

class Split:
    def __init__(self, index, destination, conditional):
        self.index = index
        self.destination = destination
        self.conditional = conditional

    def get_referenced_index(self):
        return self.destination

    def matches(self, join):
        if not isinstance(join, Join):
            raise TypeError
        return join.source == self.index

    def __repr__(self):
        return 's {0} {1}'.format(self.index, self.get_referenced_index())


class Join:
    def __init__(self, index, source):
        self.source = source
        self.index = index

    def get_referenced_index(self):
        return self.source

    def matches(self, split):
        if not isinstance(split, Split):
            raise TypeError
        return split.index == self.source

    def __repr__(self):
        return 'j {0} {1}'.format(self.index, self.get_referenced_index())

def jumps_to_joinsplits(jumps):
    """Unifies joins and splits for easier processing
    """

    # Phase 1: collect all flow changes in an unified form
    # Warning Achtung Внимание: control flow jumps occur IMMEDIATELY AFTER the branch instruction
    joinsplits = []
    for source, destination, conditional in jumps:
        joinsplits.append(Split(source + 1, destination, conditional))
        joinsplits.append(Join(destination, source + 1))

    # Phase 2: linearize according to the code layout and put splits before joins
    def keyfunction(splitjoin):
        return splitjoin.index, isinstance(splitjoin, Join) # True will put it later
            
    return sorted(joinsplits, key=keyfunction)