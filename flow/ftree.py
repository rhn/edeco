def get_joins(tree):
    if isinstance(tree, Stub):
        return
    for joiner in tree.joiners:
        yield (joiner, tree.startnode)

    if isinstance(tree, Continuation):
        for join in get_joins(tree.continuation):
            yield join

    if isinstance(tree, Bulge):
        for join in tree.get_joins():
            yield join


def get_collisions(tree):
    if isinstance(tree, Collision):
        yield tree.get_collision()
        
    if isinstance(tree, Continuation):
        for collision in get_collisions(tree.continuation):
            yield collision
    
    if isinstance(tree, Stub):
        yield tree.get_collision()
            
    if isinstance(tree, Bulge):
        for collision in tree.get_collisions():
            yield collision


def collides_with(collision, tree):
    for join in get_joins(tree):
        if collision == join:
            return True
    return False


class CollisionMixin:
    def get_collision(self):
        return self.colliding_node, self.collision
    

class Stub(CollisionMixin):
    def __init__(self, source, destination):
        self.colliding_node = source
        self.collision = destination
        
    def get_joins(self):
        return
    
    def __str__(self):
        return 'Stub(' + str(self.colliding_node) + '->' + str(self.collision) + ')'
        
    __repr__ = __str__
        

class Node:
    name = 'GenNode'
    def __init__(self, wrapper, startnode, joiners):
        self.wrapper = wrapper
        self.startnode = startnode
        self.joiners = joiners
    
    def get_joins(self):
        for joiner in self.joiners:
            yield joiner, self.startnode
    
    def contains_join(self, join):
        return join in self.get_joins()
    
    def drop_join(self, join):
        if join in self.get_joins():
            src, dst = join
            self.joiners.remove(src)
        else:
            raise Exception("Attempted to remove join that's not present")
    
    def descr(self):
        return str(self.__class__) + '<' + hex(id(self)) + '> ' + str(self.wrapper) + ' ' + str(self.joiners)
      
    def __str__(self):
        return '(' + self.descr() + ')'
        

class Continuation(Node):
    name = 'Continuation'
    def __init__(self, wrapper, startnode, joiners, continuation):
        Node.__init__(self, wrapper, startnode, joiners)
        self.continuation = continuation
    
    def descr(self):
        return Node.descr(self) + ' ' + str(self.continuation)
        
class Collision(Node, CollisionMixin):
    name = 'Collision'
    def __init__(self, wrapper, startnode, joiners, colliding_node, target):
        Node.__init__(self, wrapper, startnode, joiners)
        self.collision = target
        self.colliding_node = colliding_node

    def descr(self):
        return Node.descr(self) + ' ' + str(self.collision)
                

class UltimateEnd(Node):
    pass
    

def compress_join(tree, limit):
    """Follows the tree to (but not including) join point (limit) and transforms it into a bulge with all closures along the path inside the bulge. Keeps the join point attached to resulting bulge.
    Returns (bulge, branch) where branch is the one off of bulge that contains the join.
    """
    """P.S. This is a mess."""
#    print 'COMPRESSING JOIN', limit, tree
    if isinstance(tree, Bulge):
        for join in tree.outside_joins:
            if join == limit:
                join_destination = tree.connections.get_join_destination(join)
                # TODO: special case for when join destination equals start
                tree.drop_join(limit)
                return tree, (tree, join_destination)
                
        for branch in tree.outside_branches:
            if limit in get_joins(branch):
                source_closures = tree.connections.get_branch_sources(branch)
                bulge, join_target = compress_join(branch, limit)
                tree.outside_branches.remove(branch)
                tree.assimilate_bulge(source_closures, bulge)
                # tree.replace_outside_branch(branch, bulge.startnodes)
                return tree, join_target
        raise Exception("join limit not found in bulge")
    
    if tree.contains_join(limit):
        bulge = Bulge()
        bulge._insert_branch(None, tree) # _insert can be used instead of add if the tree is expected to be presimplified, which seems to be the case
        tree.drop_join(limit)
        return bulge, (tree, None)
    
    outside_joins = []
    for join in tree.get_joins():
        outside_joins.append(join)

    if isinstance(tree, Continuation):
        bulge, join_target = compress_join(tree.continuation, limit)
        bulge._insert_start(tree.wrapper, outside_joins)
#        print 'COMPRESSED', limit, bulge
        return bulge, join_target

    raise Exception(str(tree.__class__) + " unsupported")


def compress_collision(tree, collision):
    """Follows the tree to collision point and transforms it into a bulge with all closures along the path inside the bulge.
    Returns (bulge, closure) where closure is the closure corresponding to the colliding node.
    """
    if isinstance(tree, Stub):
        if tree.get_collision() == collision:
            bulge = Bulge()
            return bulge, None
        else:
            raise Exception("stub reached but it's not the one. BUG")

    if isinstance(tree, Bulge):
        for branch in tree.outside_branches:
            if collision in get_collisions(branch):
                source_closures = tree.connections.get_branch_sources(branch)
                tree._remove_branch(branch)
                bulge, closure = compress_collision(branch, collision)
                
                if closure is None:
                    if len(source_closures) != 1:
                        raise Exception("BUG")
                    closure = source_closures[0]
                tree.assimilate_bulge(source_closures, bulge)
                return tree, closure
        raise Exception("collision limit not found in bulge")
    
    outside_joins = []
    for join in tree.get_joins():
        outside_joins.append(join)

    if isinstance(tree, Continuation):
        bulge, closure = compress_collision(tree.continuation, collision)
        bulge._insert_start(tree.wrapper, outside_joins)
        if closure is None:
            closure = tree.wrapper
        return bulge, closure
    
    if isinstance(tree, Collision):
        if tree.get_collision() == collision:
            bulge = Bulge()
            bulge._insert_start(tree.wrapper, outside_joins)
            return bulge, tree.wrapper
        raise Exception("Probably bug?")

    print tree
    raise Exception(str(tree.__class__) + " unsupported")


class BulgeConnections:
    """Class defining connections around Bulge"""
    def __init__(self):
        self.trees = [] # pairs (from_closure, to_branch)
        self.closures = [] # pairs (from_closure, to_closure); if from is None then this is the attach point
        self.joins = [] # pairs (bulge_outside_join, to_closure)

    def remove_branch(self, branch):
        for connection, tree in self.trees[:]:
            if tree == branch:
                self.trees.remove((connection, tree))
    
    def get_branch_sources(self, branch):
        """Returns a list of sources leading to the branch"""
        # TODO: is it possible for a tree to be connected from multiple points?
        sources = []
        for connection, tree in self.trees:
            if tree == branch:
                sources.append(connection)
        return sources
    
    def get_join_destination(self, join):
        for connection, closure in self.joins:
            if connection == join:
                return closure
        raise ValueError("No such join: " + str(join)) 
    
    def drop_join(self, target_join):
        return # XXX: test whether the new code breaks anything
        new_joins = []
        for joinpair in self.joins:
            join, destination = joinpair
            if join != target_join:
                new_joins.append(joinpair)
        if len(new_joins) == len(self.joins):
            raise ValueError("Target join not found")
        self.joins = new_joins
    
    def _replace_start(self, new_start_closures):
        new_closures = []
        for source, destination in self.closures:
            if source is None:
                for new_start in new_start_closures:
                    source = new_start
                    new_closures.append((source, destination))
            else:
                new_closures.append((source, destination))
        self.closures = new_closures
        
        # branches can also be linked directly to start, e.g. in trivial cases
        new_branches = []
        for source, destination in self.trees:
            if source is None:
                for new_start in new_start_closures:
                    source = new_start
                    new_branches.append((source, destination))
            else:
                new_branches.append((source, destination))
        self.trees = new_branches
        
    def insert_start(self, new_start, joins):
        self._replace_start([new_start])
            
        self.closures.append((None, new_start))
        
        for join in joins:
            self.joins.append((join, new_start))

    def assimilate_connections(self, join_closures, other):
        other._replace_start(join_closures)
        self.trees.extend(other.trees)
        self.closures.extend(other.closures)
        self.joins.extend(other.joins)
    
    def __str__(self):
        return 'Conn(int{0}, ext{1}, join{2})'.format(*map(str, (self.closures, self.trees, self.joins)))
    

class Bulge(Node):
    def __init__(self):
        self.connections = BulgeConnections()
        self.joiners = []
        self.closures = []
        self.outside_joins = []
        self.outside_branches = []

    def __str__(self):
        return '{4}{{{0} into{1} bra{2} {3}}}'.format(self.closures, self.outside_joins, map(str, self.outside_branches), self.connections, repr(self))

    def __repr__(self):
        return 'B<{0}>'.format(hex(id(self)))

    def _insert_start(self, closure, joins):
        self.closures.append(closure)
        self.outside_joins.extend(joins)
        self.connections.insert_start(closure, joins)

    def _insert_branch(self, source, branch):
        self.connections.trees.append((source, branch))
        self.outside_branches.append(branch)

    def _remove_branch(self, branch):
        self.connections.remove_branch(branch)
        self.outside_branches.remove(branch)

    def add_branch(self, tree):
        """Adds branch and simplifies the whole bulge structure, swallowing trees if necessary."""
#        print 'ADDING BRANCH', tree
        self._insert_branch(None, tree)
        self._cleanup_branches()
    
    def drop_join(self, join):
        self.outside_joins.remove(join)
        self.connections.drop_join(join)
    
    def _cleanup_branches(self):
        """Merges all joins that have corresponding splits within the tree, including in the same branch."""
        collisions = []
        for colliding in self.outside_branches:
            possible_collisions = [collision for collision in get_collisions(colliding)]
            for collided in self.outside_branches:
                for collision in possible_collisions:
                    if collides_with(collision, collided):
                        collisions.append(collision)
            for collision in possible_collisions:
                for join in self.outside_joins:
                    if collision == join:
                        collisions.append(collision)

        # clean up the collisions. can't save the trees where they originate: those trees might get swallowed
        
        for collision in collisions:
#            print 'FOUND', collision
            self.swallow(collision)

    def get_collisions(self):
        for branch in self.outside_branches:
            for collision in get_collisions(branch):
                yield collision
    
    def swallow_collision(self, collision):
        for src_branch in self.outside_branches[:]:
            for src_collision in get_collisions(src_branch):
                if src_collision == collision:
                    branch_sources = self.connections.get_branch_sources(src_branch)
                    self._remove_branch(src_branch)
                    bulge, colliding_closure = compress_collision(src_branch, collision)
                    self.assimilate_bulge(branch_sources, bulge)
                    return colliding_closure
                    
        raise Exception("Collision source not in here. " + str(collision))
    
    def swallow_join(self, collision, colliding_closure):
        """Swallows subtree leading to collision point, including that point"""
        for join in self.outside_joins[:]:
            if collision == join:
                joining_closure = self.connections.get_join_destination(join)
                self.drop_join(join)
                self.connections.closures.append((colliding_closure, joining_closure))
                return
        
        for dst_branch in self.outside_branches[:]:
            for join in get_joins(dst_branch):
                if collision == join:
                    branch_sources = self.connections.get_branch_sources(dst_branch)
                    self._remove_branch(dst_branch)
                    bulge, (joined_branch, internal) = compress_join(dst_branch, collision)
                    self.assimilate_bulge(branch_sources, bulge)
                    if internal is None:
                        self.connections.trees.append((colliding_closure, joined_branch))
                    else:
                        if joined_branch != bulge:
                            if internal not in bulge.closures:
                                print internal
                                print joined_branch
                                print bulge
                                raise Exception
                        self.connections.closures.append((colliding_closure, internal))
                    return
                    
        raise Exception("Collision destination not in here. " + str(collision))
    
    def swallow(self, collision):
        """Reaches out to collision point and swallows both subtrees leading to it"""
        colliding_closure = self.swallow_collision(collision)
        self.swallow_join(collision, colliding_closure)
#        print 'RESULT', self
    
    def assimilate_bulge(self, join_closures, other):
        """Swallows bulge other, internally connecting it to join_closures"""
        self.closures.extend(other.closures)
        self.outside_branches.extend(other.outside_branches)
        self.outside_joins.extend(other.outside_joins)
        self.connections.assimilate_connections(join_closures, other.connections)
    
    def get_joins(self):
        for join in self.outside_joins:
            yield join
        for branch in self.outside_branches:
            for join in get_joins(branch):
                yield join
                
    def get_collisions(self):
        for branch in self.outside_branches:
            for collision in get_collisions(branch):
                yield collision

    def contains_join(self, join):
        return join in self.outside_joins
