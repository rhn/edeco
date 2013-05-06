import common.closures
from common import graphs
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
    """Controls all kind of display."""
    # TODO: there should probably be a mapping closure->displaying owner, in case the owner decides to mangle/simplify structure
    def get_display(self, closure):
        if closure is None:
            return None
        for closuredisplay in self.insides:
            if closure == closuredisplay.closure:
                return closuredisplay
        raise ValueError("Closure " + str(closure) + ' not found in subdisplays of ' + str(self.closure))
                
    def get_short_name(self, display, end=False):
        if display is None:
            return 'End' if end else 'Start'
        return '#' + str(self.insides.index(display))
    
    def get_starting_subdisplays(self):
        ret = []
        for source, target in self.closure.connections:
            if source is None:
                ret.append(self.get_display(target))
        return ret
    
    def _get_display_followers(self, display):
        return [self.get_display(closure) for closure in self.closure.get_followers(display.closure)]
    
    def sort_depth_first(self):
        """Sorts the nodes within this subgraph. Depth first within this graph, sorting internals of subgraphs is their responsibility."""
        new_order = []
        
        def follow_deeper(display):
            if display is None:
                return
            if display in new_order:
                return
            new_order.append(display)
            followers = self._get_display_followers(display)
            for follower in followers:
                follow_deeper(follower)
        
        for start in self.get_starting_subdisplays(): # there can be a few starts, so need to do some breadth-first first
            follow_deeper(start)
        self.insides = new_order
    
    def __str__(self):
        def get_short_name(closure, end=False):
            if closure is None:
                display = None
            else:
                display = self.get_display(closure)
            return self.get_short_name(display, end)

        def get_short_dest_name(closure):
           return get_short_name(closure, True)
           
        self.sort_depth_first()
        inside = []

        for closuredisplay in self.insides:
            closure = closuredisplay.closure

            preceding = self.closure.get_preceding(closure)

            preceding_string = indent('\n'.join(map(get_short_name,
                                                    preceding)),
                                      '// From: ') + '\n'

            following = self.closure.get_following(closure)
            if following:
                following_strings = list(map(get_short_dest_name, following))
            else:
                following_strings = []
            if closure is self.closure.end:
                following_strings.append("End")
            
            following_string = '\n' + indent('\n'.join(following_strings),
                                             '// To: ')
            
            id_string = 'Item ' + self.get_short_name(closuredisplay) + ': '
            inside.append(preceding_string + id_string + str(closuredisplay) + following_string)
        
        starts = self.get_starting_subdisplays()
        starts_str = ' '.join(map(self.get_short_name, starts))
        
        return 'UnknownFlow {{\n' + indent('// Start points: ' + starts_str + '\n\n' + '\n\n'.join(inside)) + '\n}}'


class NodeBasedMessDisplay(ConnectedMessDisplay):
    def get_starting_subdisplays(self):
        return [self.get_display(closure) for closure in self.closure.beginnings]
            
LooseMessDisplay = NodeBasedMessDisplay


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
        
