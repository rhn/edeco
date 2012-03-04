import display

class CodeMemory:
    """This should probably be put inside display, as it has nothing to do with actual memory layout."""
    def __init__(self, functions, function_mappings):
        self.function_mappings = function_mappings
        self.functions = functions

    def __str__(self):
        functions = self.functions
        function_strings = []
        for function in functions:
            if not function.address in self.function_mappings:
                self.function_mappings[function.address] = 'f_' + hex(function.address)

        for function in functions:
            function_strings.append(display.function_into_code(function, self.function_mappings))
            
        return '\n\n'.join(function_strings)

