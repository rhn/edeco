flow_changing_mnemonics = ['bra'] # ret looks more like an instruction, call doesn't change the flow
finishing_mnemonics = ['ret']

class Function:
    def __init__(self, code, index):
        self.address = code[index].address
        self.index = index
        self.instructions = self.find(code)

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
        
        raise ValueError("function doesn't finish within the given code")

    def mark_complete(self):
        self.instructions[0].set_function_entry();
        self.instructions[-1].function_finish = True