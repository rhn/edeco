import common.closures
from flow.emulator import StartNode, EndNode # TODO: get rid of those before passing data to display

def indent(text, prefix='    '):
    return '\n'.join(prefix + se 
                   for se in
                   text.split('\n'))


class NodeDisplay:
    def __init__(self, closure, function_mappings):
        self.closure = closure
        self.function_mappings = function_mappings
        self.statements = []
        self.analyze()
        
    def analyze(self):
        if isinstance(self.closure.node, StartNode):
            self.statements.append('// Start marker')
        elif isinstance(self.closure.node, EndNode):
            self.statements.append('// End marker')
        else:            
            for instruction in self.closure.node.instructions.instructions:
                self.statements.append(str(instruction))
    
    def __str__(self):
        return '\n'.join(self.statements)


class LooseMessDisplay:
    def __init__(self, closure, function_mappings):
        self.closure = closure
        self.function_mappings = function_mappings
        self.insides = []
        self.analyze()
    
    def analyze(self):
        for closure in self.closure.closures:
            self.insides.append(make_closuredisplay(closure, self.function_mappings))
    
    def __str__(self):
        return 'UnconnectedUnknownFlow {{\n' + indent('\n'.join(map(str, self.insides))) + '\n}}'


class ConnectedMessDisplay(LooseMessDisplay):
    def get_display(self, closure):
        for closuredisplay in self.insides:
            if closure == closuredisplay.closure:
                return closuredisplay
                
    def get_short_name(self, display):
        return str(self.insides.index(display))
                
    def __str__(self):
        inside = []

        for closuredisplay in self.insides:
            closure = closuredisplay.closure

            preceding = []
            for previous, next in self.closure.connections:
                if next == closure:
                    preceding.append(previous)

            preceding_string = indent('\n'.join(map(str, preceding)), '// From: ') + '\n'

            following = []
            for previous, next in self.closure.connections:
                if previous == closure:
                    following.append(next)
            if following:
                following_string = '\n' + indent('\n'.join(map(str, following)), '// To: ')
            else:
                following_string = '\n// END'
            
            id_string = 'Item #' + self.get_short_name(closuredisplay) + ': '
            inside.append(preceding_string + id_string + str(closuredisplay) + following_string)
        
        starts = []
        for source, target in self.closure.connections:
            if source is None:
                starts.append(self.get_short_name(self.get_display(target)))
        starts_str = ' '.join(map(lambda x: '#' + str(x), starts))
        
        return 'UnknownFlow {{\n' + indent('// Start points: ' + starts_str + '\n\n' + '\n\n'.join(inside)) + '\n}}'
        
class BananaDisplay:
    def __init__(self, closure, function_mappings):
        self.closure = closure
        self.function_mappings = function_mappings
        self.subdisplays = []
        self.create_display_tree()
            
    def create_display_tree(self):
        for closure in self.closure.closures:
            self.subdisplays.append(make_closuredisplay(closure, self.function_mappings))
            
    def __str__(self):
        inside = '\n\n'.join(map(str, self.subdisplays))
        return '{{\n{0}\n}}'.format(indent(inside))


def make_closuredisplay(closure, function_mappings):
    if isinstance(closure, common.closures.NodeClosure):
        return NodeDisplay(closure, function_mappings)
    elif isinstance(closure, common.closures.LooseMess):
        return LooseMessDisplay(closure, function_mappings)
    elif isinstance(closure, common.closures.Banana):
        return BananaDisplay(closure, function_mappings)
    elif isinstance(closure, common.closures.ConnectedMess):
        return ConnectedMessDisplay(closure, function_mappings)
    raise TypeError('Unknown closure type ' + str(closure.__class__))


class FunctionDisplay(BananaDisplay):
    """Class simplifying and displaying a function in pseudo-C."""
    def __str__(self):
        inside = '\n\n'.join(map(str, self.subdisplays))
        return '// 0x{0:x}\n... f_0x{0:x}(...) {{\n{1}\n}}'.format(self.closure.address, indent(inside))


def function_into_code(function, function_mappings):
    """Returns a string representation of the function. Takes all mappings necessary to decode hex values (e.g. function addresses, variable addresses)."""
    return str(FunctionDisplay(function, function_mappings))
        
