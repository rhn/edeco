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
    """Linear flow, composed of 0 or more ordered Closures."""
    def __init__(self, closures):
        Closure.__init__(self, None)
        self.closures = closures
        
    def prepend(self, closures):
        self.closures[:0] = closures
        
    def finish(self, closures):
        self.closures = closures[:]

    def __str__(self):
        return 'Banana' + str(self.closures)
    __repr__ = __str__
    

class NodeClosure(Closure):
    """Single node encapsulated into new graph structure"""
    def __init__(self, node, parent=None):
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
    def __init__(self, closures, beginnings, endings):
        """With multiple beginnings, they MUST be flown INTO
        """
        Closure.__init__(self, None)
        self.closures = closures
        # TODO: figure out how to describe connection to parent. virtual node of special type would be able to stop propagation
        
        # cut the connections from inside to outside and replace them with connections from closure to outside
        # this will leave the closure itself in a workable state. Connections from outside to closure STILL need to be taken care of. XXX: is this a good separation?

        # create a virtual begin node if necessary
        if len(beginnings) == 1:
            self.begin = list(beginnings)[0]
        else:
            self.begin = Closure(self)
            self.begin.following = beginnings
            for beginning in beginnings:
                beginning.preceding = [self.begin]
        
        # repeat for end nodes
        mess_following
        
    def __str__(self):
        return '{' + ', '.join(map(str, self.closures)) + '}'
    __repr__=__str__    
    
    def into_code(self):
        str_clos = []
        for closure in self.closures:
            str_clos.append(closure.into_code())
        return 'LooseMess {{{{\n{0}\n}}}}'.format(indent('\n'.join(str_clos)))


class ConnectedMess(Closure):
    """A closure with many small closures in it, contains connection information."""
    def __init__(self, bulge):
        Closure.__init__(self, None)
        if len(bulge.outside_branches) > 1:
            raise Exception("BUG: Trying to create Mess with more than 1 exit")
        if len(bulge.outside_branches) == 0:
            raise Exception("Unsupported: Trying to create a dead end.")
        self.closures = bulge.closures[:]
        self.connections = bulge.connections.closures[:]
        for source, branch in bulge.connections.trees:
            self.connections.append((source, None))
        
    
    def get_followers(self, closure):
        followers = []
        for source, destination in self.connections:
            if source == closure:
                followers.append(destination)
        return followers
    
    def __str__(self):
        return '{' + str(len(self.connections)) + 'x | ' + ', '.join(map(str, self.closures)) + '}'
