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
        
    def into_code(self):
        return self.wrapper.into_code() + '"\"' + self.continuation.into_code()

class Collision(Node, CollisionMixin):
    name = 'Collision'
    def __init__(self, wrapper, startnode, joiners, colliding_node, target):
        Node.__init__(self, wrapper, startnode, joiners)
        self.collision = target
        self.colliding_node = colliding_node

    def descr(self):
        return Node.descr(self) + ' ' + str(self.collision)
        
    def into_code(self):
        raise Exception
        

class UltimateEnd(Node):
    def into_code(self):
        return self.wrapper.into_code()


def compress(tree, limit, typ):
    """Turns tree into a flat graph of Closures(Bananas?), in the future leave outside branches outside.
    Actually, this should just pull the spine of the tree into the bag. Real trouble begins when different bags need to be merged.
    Limit is join/collision spec tuple(src, dst)
    """

    if isinstance(tree, Bulge):
        if typ == 'join':
            for join in tree.outside_joins:
                if join == limit:
                    tree.drop_join(limit)
                    # tree.add_entry(join)
                    return tree
                    
            for branch in tree.outside_branches:
                if limit in get_joins(branch):
                    bulge = compress_join(branch, limit)
                    tree.outside_branches.remove(branch)
                    tree.merge_bulge(bulge)
                    # tree.replace_outside_branch(branch, bulge.startnodes)
                    return tree
        elif typ == 'collision':
            for branch in tree.outside_branches:
                if limit in get_collisions(branch):
                    bulge = compress_collision(branch, limit)
                    tree.outside_branches.remove(branch)
                    tree.merge_bulge(bulge)
                    # tree.replace_outside_branch(branch, bulge.startnodes)
                    return tree
        raise Exception("limit not found in bulge")
    
    if typ == 'join':
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
        bulge = compress(tree.continuation, limit, typ)
        bulge.closures.append(tree.wrapper)
        # bulge.replace_start(tree.wrapper)
        bulge.outside_joins.extend(outside_joins)
        # bulge.map_joins(outside_joins, tree.wrapper)
        return bulge
        
    if typ == 'collision':
        if isinstance(tree, Collision):
            if tree.get_collision() == limit:
                bulge = Bulge()
                bulge.closures.append(tree.wrapper)
                # bulge.replace_start(tree.wrapper)
                bulge.outside_joins.extend(outside_joins)
                # bulge.map_joins(outside_joins, tree.wrapper)
                return bulge
            raise Exception("Todo. Or bug?")
    if isinstance(tree, UltimateEnd):
        raise Exception("Should never be reached. BUG")
    print tree
    raise Exception(str(tree.__class__) + " unsupported")


def compress_join(tree, join):
    return compress(tree, join, "join")

def compress_collision(tree, collision):
    if isinstance(tree, Stub):
        if tree.get_collision() == collision:
            return Bulge()
        else:
            raise Exception("stub reached but it's not the one. BUG")
    return compress(tree, collision, "collision")


class Bulge(Node):
    def __init__(self):
        self.joiners = []
        self.closures = []
        self.outside_joins = []
        self.outside_branches = []

    def __str__(self):
        return ' | '.join(map(str, (self.closures, self.outside_joins, map(str, self.outside_branches))))

    def __repr__(self):
        return 'B' + str(self.closures)
        
    def into_code(self):
        raise Exception("Bulge")

    def add_branch(self, tree):
        print 'ADDING BRANCH', tree
        self.outside_branches.append(tree)
        self._cleanup_branches()
    
    def drop_join(self, join):
        self.outside_joins.remove(join)
    
    def _cleanup_branches(self):
        collisions = []
        for colliding in self.outside_branches:
            possible_collisions = [collision for collision in get_collisions(colliding)]
            for collided in self.outside_branches:
#                if colliding == collided:
 #                   continue
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
                    self.outside_branches.remove(src_branch)
                    self.merge_bulge(compress_collision(src_branch, collision))
                    return
                    
        raise Exception("Collision source not in here. " + str(collision))
    
    def swallow_join(self, collision):
        for join in self.outside_joins[:]:
            if collision == join:
                self.outside_joins.remove(join)
                return
        
        for dst_branch in self.outside_branches[:]:
            for join in get_joins(dst_branch):
                if collision == join:
                    self.outside_branches.remove(dst_branch)
                    self.merge_bulge(compress_join(dst_branch, collision))
                    return
                    
        raise Exception("Collision destination not in here. " + str(collision))
    
    def swallow(self, collision):
        self.swallow_collision(collision)
        self.swallow_join(collision)
    
    def merge_bulge(self, other):
        self.closures.extend(other.closures)
        self.outside_branches.extend(other.outside_branches)
        self.outside_joins.extend(other.outside_joins)
    
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
