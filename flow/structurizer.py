from ftree import *
from common.closures import *


"""Converts flat flow graphs into structured (nested) graphs.

The process technically consists of 2 steps, but this code performs them at the same time.

First "step" is the creation of a spanning tree which remembers the following information: what other nodes (except of direct parent) join this one and which node this one joins into (except direct child). These two will be referred to as "join" and "collision". Each join must have a correspoinding collision.

The tree is built from objects in ftree.py. Note that there is no "split" object. Instead, Bulge (belonging more to the next step) is used.

After the tree is finished, it's compressed into a nested graph of graphs of Closures. Tree is traversed depth-first, recursively. While going forward, Banana objects are started in order to contain linear flow fragments as big as possible. Linear flow in this understanding is a chain A0->A1->... where Ax is a code block or a subgraph and for x > 0 only A(x-1) flows into Ax.

While going back, relationships between ftree objects are evaluated. If there are any unresolved joins/collisions, a Bulge is created and passed back. If all joins/collisions are resolved, the ftree object is simplified and turned into Closures.
TODO: Describe in detail.

DISCLAIMER: this code is unnecessarily complex, undocumented, expensive, excessively layered and generally unmaintainable. But it works and it's the most effort per LOC I ever made, so there will be no improvements unless required :)
"""


def simplified_continuation(to_be_wrapped, start_node, joiners, branch):
    if isinstance(branch, Stub):
        wrapper = Banana()
        wrapper.finish(to_be_wrapped)
        return Collision(wrapper, start_node, joiners, branch.colliding_node, branch.collision)
    elif not isinstance(branch, Bulge) and len(branch.joiners) == 0:
        branch.wrapper.prepend(to_be_wrapped)
        branch.startnode = start_node
        branch.joiners = joiners
        return branch
    else:
        wrapper = Banana()
        wrapper.finish(to_be_wrapped)
        return Continuation(wrapper, start_node, joiners, branch)


def simplified_bulge(to_be_wrapped, start_node, joiners, bulge):
    if len(bulge.outside_branches) == 1 and len(bulge.outside_joins) == 0:
        if len(bulge.closures) > 0:
            to_be_wrapped.append(ConnectedMess(bulge))
        return simplified_continuation(to_be_wrapped, start_node, joiners, bulge.outside_branches[0])
    else:
        wrapper = Banana()
        wrapper.finish(to_be_wrapped)
        return Continuation(wrapper, start_node, joiners, bulge)
    

class ClosureFinder:
    """Finds closures. Closes them up in functions.
    """

    def __init__(self, flow):
        self.start = NodeClosure(flow, None)
        self.closure = self.discover(self.start, flow)

    def discover(self, closure, node):
        # dfs algorithm

        visited_nodes = set()

        def wrap_node(node):
            """Node closure only contains a single node. Will not be removed until graph is finished."""
            closure = NodeClosure(node, None)
            visited_nodes.add(node)
            return closure


        def split_action(to_be_wrapped, start_node, joiners, current_node):
            to_be_wrapped.append(wrap_node(current_node)) # last node of the wrap
            
#            print 'split from', current_node, 'to', current_node.following, 'with', to_be_wrapped
            
            if len(current_node.following) < 2:
                raise Exception("less-than-2-split. Should have been bananized or dead-ended, BUG")
            elif len(current_node.following) > 2:
                raise Exception("Only 2-split supported. More should be easy to add (or try commenting out this line).")
                
            # TODO: dead ends
            branches = [] # join stuff
            
            for next in current_node.following:
                if next not in visited_nodes:
                    branch = dft_action(next, current_node) # bananize
                else:
                    branch = Stub(current_node, next)
                branches.append(branch)
                
#            print '  Returned from split after', current_node
            bulge = Bulge()
            for branch in branches:
                bulge.add_branch(branch)
            
#            print 'result\n', bulge
            
            return simplified_bulge(to_be_wrapped, start_node, joiners, bulge)

        def join_action(to_be_wrapped, start_node, joiners, previous_node, join_target):
            # regular join: start a single banana. Even if it splits immediately, the subbanana detects it
#            print 'proceeding past join to', join_target, 'with', to_be_wrapped, 'joining', joiners
            branch = dft_action(join_target, previous_node, just_joined=True) # start new banana as child
            # result contains join_target
#            print 'returned from join before', join_target
            # two options: goes to finish or joins with something before it
            
            # if it goes straight to end without joining past stuff then nothing can be done. They will end up being wrapped in each other (continuations and bulges)
            # the path will end at a split that consolidates all the subsequent joins.
            
            # try to simplify further splits using current joins. XXX: is it guaranteed that no other join will reach here -> is it safe to take all joins? 
            join_sources = set(join_target.preceding).difference(set([previous_node]))
            joins = []
            for joiner in join_sources:
                joins.append((joiner, join_target))
            
            # find joins matching further splits
            matching = []
            unmatched = []
            for join in joins:
                if join in get_collisions(branch):
                    matching.append(join)
                else:
                    unmatched.append(join)
            if len(matching) > 0: # TODO: this check is probably not needed, bulge would simplify anyway
                # need to create a bulge to join the join
                bulge = Bulge()
                bulge.add_branch(branch)
                
                ret = simplified_bulge(to_be_wrapped, start_node, joiners, bulge)
#                print 'joined result'
#                print ret
                return ret
                
            # didn't curl itself, so touched something other than the join here.
            # Tree must be forwarded up to resolve the join(s)
            
            # ----- back to normal code -----
            wrapper = Banana()
            wrapper.finish(to_be_wrapped) # will never be modified again, can forget about those nodes
            
            ret = Continuation(wrapper, start_node, joiners, branch)
#            print ret
            return ret

        def collision_action(to_be_wrapped, start_node, joiners, end_node, collision_target):
            # what if join with the banana that was just made? Only can join its first node
            # answer: banana inside, FlowPattern around it. Therefore parent action must detect & wrap this (dead end)
#            print 'collision with visited', collision_target, 'from', to_be_wrapped
            wrapper = Banana()
            wrapper.finish(to_be_wrapped)
#            print wrapper
            return Collision(wrapper, start_node, joiners, end_node, collision_target) # need to let parent know what was touched


        """dft_action returns ready closures until some point. Return status says what kind of point is reached.
        E.g. function end, join.
        
        Bananizes as much as it can (make consecutive ClosureNodes a single Closure) and stops when split/join found, spawning dft_action in the direction of the flow.
                
        Depending on return status of the spawned, can continue bananization with spawned *entirely* inside or stop and pass control of bananas (which ones?) to parent.
        
        NOTE super-important: after dft_action returns, its traversed tree has both hanging splits and joins! A hanging split occurs when a mess/loop is in progress.
        """
        
        def dft_action(node, source_node, just_joined=False): # one piece of action: bananize until split/join
            """Creates tree branch at node, from source_node as tree root"""
#            raw_input()
#            print 'start with', node, 'from', source_node

            start_node = node
            joiners = [] # nodes thtat join to beginning of this banana
            to_be_wrapped = [] # bananization list
            
            if just_joined:
                if source_node not in node.preceding and not source_node is None:
                    print node.preceding
                    print source_node
                    print source_node.following
                    raise Exception("Bug. Non-null root node not in preceding nodes")
                preceders = node.preceding[:]
                if source_node is not None:
                    preceders.remove(source_node)
                joiners = preceders
            
#            print 'joiners', joiners, 'just_joined', just_joined, 'preceding', node.preceding
            # bananize until a node with join/split or visited. If visited, then already bananized and stop before.
            # if join, stop before node. If split, put node inside too.

            previous_node = source_node
            while True:
                if node in visited_nodes:
                    return collision_action(to_be_wrapped, start_node, joiners, previous_node, node)
            
                # don't stop if there are joins into first node, it's been taken care of
                if not just_joined and len(node.preceding) > 1:
                    return join_action(to_be_wrapped, start_node, joiners, previous_node, node)
                    
                if len(node.following) > 1:
                    return split_action(to_be_wrapped, start_node, joiners, node)

                to_be_wrapped.append(wrap_node(node))
                
                if len(node.following) == 0:
#                    print 'end reached', node
                    wrapper = Banana()
                    wrapper.finish(to_be_wrapped)
#                    print wrapper
                    return UltimateEnd(wrapper, start_node, joiners)
                previous_node = node
                node = node.following[0]
                just_joined = False
            
            raise Exception("Ha-ha. Impossible to even get here.")
                
        result = dft_action(node, None)
#        print result
        return result.wrapper
        

def structurize(flat_graph):
    return ClosureFinder(flat_graph).closure
