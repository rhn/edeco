class CodeMemory:
    def __init__(self, functions, function_mappings):
        self.function_mappings = function_mappings
        self.functions = functions

    def __str__(self):
        functions = self.functions
        function_strings = []
        for function in functions:
            try:
                name = self.function_mappings[function.address]
            except KeyError:
                name = 'f_' + hex(function.address)

            function_strings.append(function.into_code(name))
            
        return '\n\n'.join(function_strings)

