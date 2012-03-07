def indent(text, prefix='    '):
    return '\n'.join(prefix + se 
                   for se in
                   text.split('\n'))


class Closure:
    """Represents a mess of flow. Ideally, it should not contain any subgraphs possible to collapse into subelements. Flow is defined by entry and exit, which are the graph nodes.
    """
    def __init__(self, parent):
        self.preceding = []
        self.following = []
        self.parent = parent


class Banana(Closure):
    def __init__(self):
        Closure.__init__(self, None)
        
    def prepend(self, closures):
        self.closures[:0] = closures
        
    def finish(self, closures):
        self.closures = closures[:]

    def __str__(self):
        return 'Banana' + str(self.closures)
    __repr__ = __str__
    

class NodeClosure(Closure):
    """Single node encapsulated into new graph structure"""
    def __init__(self, node, parent):
        Closure.__init__(self, parent)
        self.node = node

    def __str__(self):
        return str(self.node)

    def __repr__(self):
        return str(self)
        
    def get_entry_address(self):
        return self.node.instructions.instructions.address


class LooseMess(Closure):
    """A closure with many small closures in it, in no particular order, not internally connected. Debug only"""
    def __init__(self, closures):
        Closure.__init__(self, None)
        self.closures = closures
        
    def __str__(self):
        return '{' + ', '.join(map(str, self.closures)) + '}'
    __repr__=__str__    
    
    def into_code(self):
        str_clos = []
        for closure in self.closures:
            str_clos.append(closure.into_code())
        return 'LooseMess {{{{\n{0}\n}}}}'.format(indent('\n'.join(str_clos)))


class ConnectedMess(Closure):
    """A closure with many small closures in it, contanis connection information."""
    def __init__(self, bulge):
        Closure.__init__(self, None)
        self.closures = bulge.closures[:]
        self.connections = bulge.connections.closures[:]
        print 'FINALLY:', self.connections
    
    def get_followers(self, closure):
        followers = []
        for source, destination in self.connections:
            if source == closure:
                followers.append(destination)
        return followers
    
    def __str__(self):
        return '{' + len(self.connections) + 'x | ' + ', '.join(map(str, self.closures)) + '}'
