import operations


class GenericInstruction:
    def __init__(self, architecture, address, mnemonic, operands):
        self.arch = architecture
        self.addr = address
        self.address = self.addrtoint()
        self.mnemonic = mnemonic
        self.operands = operands

        # a little bridge to make an Instruction closer to a small Operation
        self.operation_result = None

        # get rid of these eventually. replacement will be handled in a structured manner
        self.used_in = [] # list of addresses of final instructions this one contributed to
        self.replaced_by = None # an Operation that completely replaces this instruction

    def addrtoint(self):
        return int(self.addr, 16)

    def mark_chain(self, address):
        self.used_in.append(address)

    def __str__(self):
        ins = ' '.join([self.addr + ':   ', self.mnemonic] + self.operands)
        if self.used_in:
            ins = ins + ' // ' + ' '.join(self.used_in)
        if self.replaced_by is not None:
            ins = '// ' + ins + '\n' + str(self.replaced_by) + '\n'
        return ins

    def evaluate(self, machine_state):
        """Changes the machine state to the best of out knowledge. no return value.
        """
        raise NotImplementedError

    def get_read_regs(self):
        state = self.arch.DummyMachineState()
        self.evaluate(state)
        return state.get_read_places()

    def get_modified_regs(self):
        state = self.arch.DummyMachineState()
        self.evaluate(state)
        return state.get_written_places()

    def get_result_value(self, context, reg_spec):
        instructions, index, memory = context
        state = self.arch.MachineState(memory)
        print 'findin', reg_spec, 'after', self
        for reg in self.get_read_regs():
            print reg
            value = operations.traceback_register(context, reg)
            try:
                state.regs.set(reg, value)
            except:
                raise NotImplementedError
        self.evaluate(state)
        return state.regs.get(reg_spec)

    # FLOW DETECTION METHODS. PAY SPECIAL ATTENTION TO CAPTURE ALL INSTRUCTIONS
    def jumps(self):
        """Returns True if this instruction orders a jump - with a branch delay slot or without one. Must have "target" attribute with jump address.
        """
        return False

    def calls_function(self):
        """Returns True if calls a function. Must have "function" attribute with function address.
        """
        return False

    def breaks_function(self):
        """Returns True if causes a return from a function."""
        return False

    def is_conditional(self):
        """Returns true is jump is conditional"""
        raise NotImplementedError

    def stores_memory(self):
        return False


def Instruction(architecture, address, mnemonic, operands, instruction_map):
    """Creates instructions based on instruction_map"""
    try:
        cls = instruction_map[mnemonic]
    except KeyError:
        cls = GenericInstruction
    try:
        return cls(architecture, address, mnemonic, operands)
    except:
        print GenericInstruction(architecture, address, mnemonic, operands)
        raise