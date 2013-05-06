import graphs

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

    def replace_following(self, replaced, replacing):
        self.following.remove(replaced)
        replaced.preceding.remove(self)
        self.following.append(replacing)
        replacing.preceding.append(self)

    def replace_preceding(self, replaced, replacing):
        self.preceding.remove(replaced)
        replaced.following.remove(self)
        self.preceding.append(replacing)
        replacing.following.append(self)


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

        self.beginnings = beginnings
        self.endings = endings
        self.rewire_create()

    def rewire_create(self):
        beginnings = self.beginnings
        endings = self.endings
        # place beginnings
        # create a virtual begin node if necessary
        if len(beginnings) == 1:
            self.begin = list(beginnings)[0]
        else:
            self.begin = Closure(self)
            self.begin.following = list(beginnings)
            for beginning in beginnings:
                for preceding in beginning.preceding[:]:
                    if preceding not in self.closures:
                        beginning.preceding.remove(preceding)
                        beginning.preceding.append(self.end)       
        # place endings
        # repeat for end nodes
        if len(endings) == 1:
            self.end = list(endings)[0]
        else:
            self.end = Closure(self)
            self.end.preceding = list(endings)
            for ending in endings:
                for following in ending.following[:]:
                    if following not in self.closures:
                        ending.following.remove(following)
                        ending.following.append(self.end)
    
    def reduce_straightlinks(self):
        """Finds all chains ...A->B... and wraps them into finished bananas."""
        for node in graphs.iternodes(self.begin):
            if len(node.following) == 1 and not node is self.end:
                next = node.following[0]
                if len(next.preceding) == 1 and not node is self.begin:
                    # node is a simple link
                    if isinstance(node, Banana):
                        raise Warning('Packing a banana inside a banana. child: {0}. Check for incorrect finding largest bananas.'.format(node))
                    if isinstance(next, Banana):
                        raise Warning('Packing a banana inside a banana. child: {0}. Check for incorrect finding largest bananas.'.format(next))
                    
                    banana = Banana([node, next])
                    if node is self.begin:
                        self.begin = banana
                    else:
                        banana.preceding = node.preceding[:]
                        for preceding in banana.preceding:
                            preceding.following.remove(node)
                            preceding.following.append(banana)
                    if next is self.end:
                        self.end = banana
                    else:
                        banana.following = next.following[:]
                        for following in banana.following:
                            following.preceding.remove(next)
                            following.preceding.append(banana)
                    
                    self.closures.remove(node)
                    self.closures.remove(next)
                    self.closures.add(banana)
    
    def get_following(self, node): # XXX: include END?
        """Returns high-level followers suitable for display. Replaces virtual end closure wih None."""
        if self.end in self.closures:
            return node.following
        ret = node.following[:]
        if self.end in ret:
            ret.remove(self.end)
        return ret
    
    get_followers = get_following
    
    def get_preceding(self, node):
        return node.preceding
    
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
