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
        return str(self.__class__) + ' ' + str(self.wrapper) + ' ' + str(self.joiners)
      
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
    

def compress(tree, limit, compress_method):
    """Turns tree into a flat graph of Closures(Bananas?), in the future leave outside branches outside.
    Actually, this should just pull the spine of the tree into the bag. Real trouble begins when different bags need to be merged.
    Limit is join/collision spec tuple(src, dst)
    """

    if isinstance(tree, Bulge):
        if compress_method == compress_join:
            for join in tree.outside_joins:
                if join == limit:
                    tree.drop_join(limit)
                    # tree.add_entry(join)
                    return tree
                    
            for branch in tree.outside_branches:
                if limit in get_joins(branch):
                    bulge = compress_method(branch, limit)
                    tree.outside_branches.remove(branch)
                    tree.assimilate_bulge(bulge)
                    # tree.replace_outside_branch(branch, bulge.startnodes)
                    return tree
            raise Exception("join limit not found in bulge")
        else:
            raise Exception("BUG")
    
    if compress_method == compress_join:
        if tree.contains_join(limit):
            bulge = Bulge()
            bulge.outside_branches.append(tree)
            tree.drop_join(limit)
            # bulge.add_branch(tree)
            return bulge
    
    outside_joins = []
    for join in tree.get_joins():
        outside_joins.append(join)

    if isinstance(tree, Continuation):
        bulge = compress_method(tree.continuation, limit)
        bulge._insert_start(tree.wrapper, outside_joins)
        return bulge
        
    if compress_method == compress_collision:
        if isinstance(tree, Collision):
            if tree.get_collision() == limit:
                bulge = Bulge()
                bulge._insert_start(tree.wrapper, outside_joins)
                return bulge
            raise Exception("Todo. Or bug?")
    if isinstance(tree, UltimateEnd):
        raise Exception("Should never be reached. BUG")
    print tree
    raise Exception(str(tree.__class__) + " unsupported")


def compress_join(tree, join):
    return compress(tree, join, compress_join)

def compress_collision(tree, collision):
    if isinstance(tree, Stub):
        if tree.get_collision() == collision:
            return Bulge()
        else:
            raise Exception("stub reached but it's not the one. BUG")

    if isinstance(tree, Bulge):
        for branch in tree.outside_branches:
            if collision in get_collisions(branch):
                source_closures = tree.connections.get_branch_sources(branch)
                tree._remove_branch(branch)
                bulge = compress_collision(branch, collision)
                tree.assimilate_bulge(source_closures, bulge)
                return tree
        raise Exception("collision limit not found in bulge")
    return compress(tree, collision, compress_collision)


class BulgeConnections:
    def __init__(self):
        self.trees = []
        self.closures = []
        self.joins = []

    def remove_branch(self, branch):
        for connection, tree in self.trees[:]:
            if tree == branch:
                self.trees.remove((connection, tree))
    
    def get_branch_sources(self, branch):
        sources = []
        for connection, tree in self.trees:
            if tree == branch:
                sources.append(connection)
        return sources
    
    def _replace_start(self, new_start):
        new_closures = []
        for source, destination in self.closures:
            if source is None:
                source = new_start
            new_closures.append((source, destination))
        self.closures = new_closures
        
    def insert_start(self, new_start, joins):
        self._replace_start(new_start)
            
        self.closures.append((None, new_start))
        
        for join in joins:
            self.joins.append((join, new_start))

    def assimilate_connections(self, join_closure, other):
        other._replace_start(join_closure)
        self.trees.extend(other.trees)
        self.closures.extend(other.closures)
        self.joins.extend(other.joins)
        

class Bulge(Node):
    def __init__(self):
        self.connections = BulgeConnections()
        self.joiners = []
        self.closures = []
        self.outside_joins = []
        self.outside_branches = []

    def __str__(self):
        return 'B{{in{0} into{1} bra{2}}}'.format(self.closures, self.outside_joins, map(str, self.outside_branches))

    def __repr__(self):
        return 'B' + str(self.closures)

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
        print 'ADDING BRANCH', tree
        self._insert_branch(None, tree)
        self._cleanup_branches()
    
    def drop_join(self, join):
        self.outside_joins.remove(join)
    
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
            print 'FOUND', collision
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
                    self.assimilate_bulge(branch_sources, compress_collision(src_branch, collision))
                    return
                    
        raise Exception("Collision source not in here. " + str(collision))
    
    def swallow_join(self, collision):
        """Swallows subtree leading to collision point, including that point"""
        for join in self.outside_joins[:]:
            if collision == join:
                self.outside_joins.remove(join)
                return
        
        for dst_branch in self.outside_branches[:]:
            for join in get_joins(dst_branch):
                if collision == join:
                    self.outside_branches.remove(dst_branch)
                    self.assimilate_bulge(compress_join(dst_branch, collision))
                    return
                    
        raise Exception("Collision destination not in here. " + str(collision))
    
    def swallow(self, collision):
        """Reaches out to collision point and swallows both subtrees leading to it"""
        print 'before swallowing collision', self
        self.swallow_collision(collision)
        print 'after swallowing collision', self
        self.swallow_join(collision)
    
    def assimilate_bulge(self, join_closures, other):
        """Swallows bulge other, internally connecting it using join_closures"""
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

