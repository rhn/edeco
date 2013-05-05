from common.closures import *
from common.graphs import *

import functools

"""Converts flat control flow graphs into structured (nested) graphs (control flow trees). It doesn't work on graphs with infinite loops/stops.

Definitions:
    Ordering:
        Imagine taking the graph by start node and collective end node. Pull them in opposite directions until a string forms.
        Ordering corresponds to distance from start node (not related to edge direction.
    
    Reverse edge:
        Edge that appears to go from end to start node in "stretched" graph.
    
    post-dominator of e:
        node p that is on all ordered paths containing e, and also p is later than e
    
    TODO: formalize
        
Algorithm:
    Mark reverse edges
    n := head
    While n:
        Find the earliest post-dominator p
        Find all nodes M between n and p. (n and p include exceptions)
        Replace M with a single node N.
        Descend into M.
        n := N->following
Result: chain of M-nodes

Mark reverse edges:
    R = {}
    For each stack S in depth-first order:
        (on just visited)
        n := top(S)
        For each edge E = (n, d):
            If d in S:
                R = R + {E}
                Mark E as visited
        (after all edges (n, d) visited)
        if exists edge (n, d) for any d:
            if all edges (n, d) are marked as visited:
                p := below_top(S)
                R = R + {(p, n)}
                mark (p, n) as visited
    R is the set of reverse edges.

"""

def ordered_next_link(node, reverse_edges):
    for following in node.following:
        if (node, following) not in reverse_edges:
            yield (node, following), following
    for preceding in node.preceding:
        if (preceding, node) in reverse_edges:
            yield (preceding, node), preceding

ordered_next_edge = ordered_next_link


def ordered_next_node(node, reverse_edges):
    return (n for e, n in ordered_next_link(node, reverse_edges))

ordered_next = ordered_next_node


def ordered_prev_link(node, reverse_edges):
    for following in node.following:
        if (node, following) in reverse_edges:
            yield (node, following), following
    for preceding in node.preceding:
        if (preceding, node) not in reverse_edges:
            yield (preceding, node), preceding    


def ordered_prev_node(node, reverse_edges):
    return (n for e, n in ordered_prev_link(node, reverse_edges))

ordered_prev = ordered_prev_node


def structurize_mess(mess, reverse_paths):
    wrapper = MessStructurizer(mess, reverse_paths)
    wrapper.print_dot('raw_mess.dot', marked_edges=[reverse_paths])
    wrapper.wrap_largest_bananas()
    for banana in wrapper.bananas:
        BS(banana).structurize()
    wrapper.merge_straightlinks()
    wrapper.print_dot('straightlinked.dot')


class MessStructurizer:
    def __init__(self, mess_closure, reverse_edges):
        self.mess_closure = mess_closure
        self.reverse_edges = reverse_edges
        self.bananas = None
    
    def wrap_largest_bananas(self):
        """Wraps all bananas that can be potentially found, but starts with largest. They won't be structured at first.
        
        Follow links in "ordered" fashion - in this way find pairs of most distant edges that dominate each other and wrap them in bananas.
        This will wrap forward flows as well as reverse flows.
            Strategy for cutting off: include start node, if node does not split; include end node if node is not joined from elsewhere.
        
        FIXME: strategy for:
            ->M->N
            ->M<-N->
            M should be ghosted somehow...
        
        FIXME: strategy for reducing shortlinks
        """
        def follow_func(stack):
            return ordered_next(stack[-1], self.reverse_edges)
        
        def follow_edge_func(last):
            return ordered_next_edge(last, self.reverse_edges)

        def follow_rev(stack):
            return ordered_prev(stack[-1], self.reverse_edges)

        # XXX: exclude self from pre-dominators
        # XXX: self-loops?
        bananas = []

        # find all pre-dominators and post-dominators
        # XXX: they should be found according to normal flow direction... or something, to reduce simple >A->B< links
        
        def follow_link_iter(stack):
            edge, node = stack[-1]
            return ordered_next_link(node, self.reverse_edges)
            
        def follow_rev_link_iter(stack):
            edge, node = stack[-1]
            return ordered_prev_link(node, self.reverse_edges)
                
        edges_to_predoms = {}
        edges_to_postdoms = {}
        for edge in iteredges(self.mess_closure.begin):
            if edge in self.reverse_edges:
                last, first = edge
            else:
                first, last = edge
                
            edges_to_postdoms[edge] = find_ordered_dominator_edges(last, follow_link_iter)
            edges_to_predoms[edge] = find_ordered_dominator_edges(first, follow_rev_link_iter)
            
        def get_both_dominator(edge):
            """Returns the farthest edge which dominates edge if it is dominated by edge.
            """
            edge_dominators = edges_to_postdoms[edge]
            # if edge has no post-dominators then it is its own dominator and only node dominated by itself
            if not edge_dominators:
                return edge
            
            # start searching from the fathest one
            for postdom in reversed(edge_dominators):
                # if is dominated by edge, then we found it
                if edge in edges_to_predoms[postdom]:
                    return postdom
            
            # if no dominator of edge is also dominated by edge, then edge is the only such dominator
            return edge
            
        def wrap(start, end):
            """Wraps nodes (and whatever is between them) together in a future banana. Rewires accordingly,
            """
     #       FCUK: update reverse edges after each rewiring
            print('Farthest node that is predomed by {0} is {1}, need to wrap'.format(start, end))
        print("reverse", self.reverse_edges)
        print("begin", self.mess_closure.begin)
        print("predoms", edges_to_predoms)
        print("postdoms", edges_to_postdoms)

        for edge in iteredges(self.mess_closure.begin,
                              follow_func=follow_edge_func):
            print("E", edge)
            # find lowest edge for which top is dominator
            both_dominator = get_both_dominator(edge)
#            nodes_between = find_nodes(edge, both_dominator)
            # find all nodes in between
            # remove the top node if it splits
            # XXX: handle the top node if it joins from lower
            # similar rules for bottom
            if edge not in self.reverse_edges:
                print("fw")
                source, target = edge
                end_source, end_target = both_dominator
            else:
                print("rev")
                # do the same thing, but pay attention to order
                source, target = both_dominator
                end_source, end_target = edge
                
            if len(source.following) != 1:
                start = target
            else:
                start = source
            
            if len(end_target.preceding) != 1:
                end = end_source
            else:
                end = end_target
            if start != end and not (end, start) == edge:
                wrap(start, end)            
            
        self.bananas = bananas
        
    def merge_straightlinks(self):
        return self.mess_closure.reduce_straightlinks()
            
    def print_dot(self, filename, marked_edges=None, marked_nodes=None):
        return as_dot(filename, self.mess_closure.begin, marked_nodes=marked_nodes, marked_edges=marked_edges)


class GraphWrapper: # necessarily a bananawrapper
    def __init__(self, graph_head):
        self.cfg_head = graph_head
        self.graph_head = self.wrap_graph(self.cfg_head)
        self.expand_intersections()
        self.reverse_edges = None

    def structurize(self):
        self.mark_reverse_edges()
        self.split()
        self.pack_banana()
        for sub in self.subs:
            structurize_mess(sub, self.reverse_edges)
    
    def pack_banana(self):
        current = self.graph_head
        closures = []
        while True:
            closures.append(current)
            following_count = len(current.following)
            if following_count == 1:
                current = current.following[0]
            elif following_count > 1:
                raise ValueError("more than 1 follower in a trivial flow node")
                
            if following_count == 0: # end node
                break
        
        self.banana = Banana(closures)

    def expand_intersections(self):
        """Creates ghost nodes before any node with more than 1 preceding and following, in order to allow dominator algorithms to see the links between a node start (joins) and end.
        """
        # XXX: should be a filtering stateless call, not a method
        class GhostClosure(NodeClosure):
            def __init__(self, original):
                Closure.__init__(self, None)
                self.preceding = original.preceding[:]
                self.following = original.following[:]
                # XXX: this is so ugly I want to cry
                import flow.emulator
                self.node = flow.emulator.Subflow(flow.emulator.Instructions([], original.node.instructions.start_index, original.node.instructions.end_index))
                self.original = original
            
            def insert(self):
                """Inserts ghost before its original"""
                original = self.original
                self.following = [original]
                original.preceding = [self]
                for preceding in self.preceding:
                    preceding.following.remove(original)
                    preceding.following.append(self)
            
            def remove(self):
                """Removes self from before original"""
                original = self.original
                original.preceding = self.preceding
                for preceding in self.preceding:
                    preceding.following.remove(self)
                    preceding.following.append(original)
                # seppuku now
            
            def __str__(self):
                return 'G({0})'.format(self.original)
             
            __repr__ = __str__
        
        multijoiners = set()
        for node in iternodes(self.graph_head):
            if len(node.preceding) > 1 and len(node.following) > 1:
                multijoiners.add(node)
        
        ghosts = set()
        for multijoiner in multijoiners:
            ghost = GhostClosure(multijoiner)
            ghost.insert()
            ghosts.add(ghost)
        self.ghosts = ghosts

    def collapse_ghosts(self):
        """Removes ghost nodes from the flatness of the graph."""
        for ghost in self.ghosts:
            ghost.remove()
        self.ghosts = None

    def mark_reverse_edges(self):
        self.reverse_edges = find_reverse_edges(self.graph_head)

    def split(self):
        # XXX: this flow is stupid and sleepy. make it stateless and convert to passing data around
        if self.reverse_edges is None:
            raise RuntimeError("No reverse edges data")
        self.subs = []
        current = self.graph_head
        while True:
            # first follow forward trivial chains
            while True:
                nexts = list(self.ordered_next(current))
                nexts_count = len(nexts)
                if nexts_count == 1:
                    current = nexts[0]
                else:
                    break
            if nexts_count == 0: # end node
                break
            
            # not end node, and not a trivial chain may proceed
            dom = find_earliest_post_dominator(current, self.reverse_edges)
            
            if dom is None:
                raise ValueError("Post-dominator not found for {0}".format(current))
            subgraph = self.wrap_sub(current, dom)
            # rewire

            # Assumption: going only forward in respect to flow (only works inside bananas)
            # take into account situation where neither current nor dom are inside, but they need a link (if-then) (XXX: this is from vague memory)
            # FIXME: remember about reverse edges! they need to be connected on the correct side of the mess
            if current is subgraph.begin:
                for preceding in current.preceding[:]:
                    if (preceding, current) not in self.reverse_edges:
                        preceding.following.remove(current)
                        preceding.following.append(subgraph)
                        subgraph.preceding.append(preceding)
                        current.preceding.remove(preceding)
                for following in current.following:
                    if (current, following) in self.reverse_edges:
                        raise Exception("A node initiating a subflow should have all its followers going inside the subflow.")
                        
            else:
                # XXX
                current.following = [subgraph]
                subgraph.preceding = [current]
            
            if dom is subgraph.end:
                for following in dom.following[:]:
                    if (dom, following) not in self.reverse_edges:
                        following.preceding.remove(dom)
                        following.preceding.append(subgraph)
                        subgraph.following.append(following)
                        dom.following.remove(following)
                for preceding in dom.preceding:
                    if (preceding, dom) in self.reverse_edges:
                        raise Exception("A node initiating a subflow should only be reachable from inside the subflow.")
            else:
                # XXX
                dom.preceding = [subgraph]
                subgraph.following = [dom]
            print('sub', subgraph)
            print('begin', subgraph.begin, subgraph.begin.preceding, subgraph.begin.following)
            print('end', subgraph.end, subgraph.end.preceding, subgraph.end.following)
            
            self.subs.append(subgraph)
            self.print_dot('dropped_{0}.dot'.format(len(self.subs)))
            current = dom
    
    def ordered_next(self, node):
        """Returns next nodes in the direction of stretched order.
        """
        return ordered_next(node, self.reverse_edges)
    
    def wrap_sub(self, start, end):
        return find_mess(start, end, self.reverse_edges)
    
    def wrap_graph(self, graph_head):
        node_to_closure = {}
        for node in cfg_iterator(graph_head):
            closure = NodeClosure(node)
            node_to_closure[node] = closure
            
        for node in cfg_iterator(graph_head):
            closure = node_to_closure[node]
            for preceding in node.preceding:
                closure.preceding.append(node_to_closure[preceding])
            for following in node.following:
                closure.following.append(node_to_closure[following])

        return node_to_closure[graph_head]
    
    def print_dot(self, filename):
        if self.reverse_edges is None:
            marked_edges = []
        else:
            marked_edges = [self.reverse_edges]
        as_dot(filename, self.graph_head, marked_edges=marked_edges)
        
        
def find_reverse_edges(graph_head):
    reverse_edges = set()
    
    def follow_func(stack):
        top = stack[-1]
        for next in top.following:
            if not (top, next) in reverse_edges:
                yield next
    
    for path, forward in iterpaths(graph_head,
                                   follow_func=follow_func,
                                   partial=True,
                                   on_backwards=True):
                          
        top = path[-1]
        if forward:
            # when moving into depth, check paths along the way to stop before traversing them
            for next in top.following:
                if next in path:
                    reverse_edges.add((top, next))
        else:
            # when coming back after traversing all child nodes, check the kind of an edge
            # if all following edges are reverse direction, then this one is also.
            if top.following and \
               all(((top, next) in reverse_edges) for next in top.following):
                # top node MUST have a parent, since there must be a split to reverse mode before it
                # XXX: I really hope that's true
                top_parent = path[-2]
                reverse_edges.add((top_parent, top))
    return reverse_edges


def find_earliest_post_dominator(node, reverse_edges):
    def follow_func(stack):
        return ordered_next(stack[-1], reverse_edges)
        
    doms = find_post_dominators(node, follow_func)

    if doms:
        return doms[0]
    else:
        return None


def find_latest_post_dominator(node, follow_func):
    doms = find_post_dominators(node, follow_func)

    if doms:
        return doms[-1]
    else:
        return None


def find_unordered_dominators(node, follow_func):
    doms = None
    for path in iterpaths(node, follow_func=follow_func):
        if doms is None:
            doms = set(path[1:]) # remove self
        else:
            doms.intersection_update(path)
    return doms


def find_unordered_dominator_edges(node, follow_iter):
    doms = None
    for path in iteredgepaths(node, follow_iter=follow_iter):
        edges = path.get_edges()
        if doms is None:
            doms = set(edges)
        else:
            doms.intersection_update(edges)
    return doms


def find_ordered_dominator_edges(node, follow_iter):
    doms = find_unordered_dominator_edges(node, follow_iter)
    print follow_iter, node, doms
    path = iteredgepaths(node, follow_iter=follow_iter).next()

    return list(filter(doms.__contains__, path.get_edges()))


def find_post_dominators(node, follow_func):
    doms = find_unordered_dominators(node, follow_func)
    path = iterpaths(node, follow_func=follow_func).next()

    dom_list = []
    for child in path:
        if child in doms:
            dom_list.append(child)
    return dom_list
    

def find_mess(start, end, reverse_edges):
    #TODO: cut start/end connections
    # determine if starts with split or looplike join
    # XXX: make sure outer loop layers are peeled if joins from nested loops
    start_index = None
    if not any((preceding, start) in reverse_edges for preceding in start.preceding): # if not loop-join
        start_index = 1
    
    # determine if end is a join or a looplike split
    end_index = None
    if not any((end, following) in reverse_edges for following in end.following): # not loop-split
        end_index = -1    
        
    # find all nodes in between
    
    def follow_func(stack):
        if stack[-1] is end:
            return ()
        else:
            return ordered_next(stack[-1], reverse_edges)
    
    contents = set()
    start_nodes = set()
    end_nodes = set()
    for path in iterpaths(start, follow_func=follow_func):
        if len(path) < 2:
            raise Exception("Not sure why. The shortest flow should have separate start and end nodes.")
            
        path = path[start_index:end_index]
        if len(path):
            snode = path[0]
            enode = path[-1]
        else:
            snode = None
            enode = None
            
        start_nodes.add(snode)
        end_nodes.add(enode)
        contents.update(set(path))
    print('mess contents', contents)
    return LooseMess(contents, start_nodes, end_nodes)

    
def structurize(graph_head):
    as_dot('unstructured.dot', graph_head)
    graphmaker = GraphWrapper(graph_head)
    graphmaker.print_dot('unstructured_wrapped.dot')
    graphmaker.mark_reverse_edges()
    graphmaker.print_dot('reverse.dot')
    graphmaker.structurize()
    graphmaker.split()
    graphmaker.print_dot('split.dot')
    graphmaker.pack_banana()
    return graphmaker.banana
