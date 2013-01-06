from common.closures import *
from common.graphs import *

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

def ordered_next(node, reverse_edges):
    for following in node.following:
        if (node, following) not in reverse_edges:
            yield following
    for preceding in node.preceding:
        if (preceding, node) in reverse_edges:
            yield preceding


def ordered_prev(node, reverse_edges):
    for following in node.following:
        if (node, following) in reverse_edges:
            yield following
    for preceding in node.preceding:
        if (preceding, node) not in reverse_edges:
            yield preceding


def structurize_mess(mess, reverse_paths):
    wrapper = MessStructurizer(mess, reverse_paths)
    wrapper.wrap_largest_bananas()
    for banana in wrapper.bananas:
        BS(banana).structurize()


class MessStructurizer:
    def __init__(self, mess_closure, reverse_edges):
        self.mess_closure = mess_closure
        self.reverse_edges = reverse_edges
    
    def wrap_largest_bananas(self):
        def follow_func(stack):
            return ordered_next(stack[-1], self.reverse_edges)

        def follow_rev(stack):
            return ordered_prev(stack[-1], self.reverse_edges)

        # XXX: exclude self from pre-dominators
        # XXX: self-loops?

        # find all pre-dominators
        nodes_to_predoms = {}
        for node in iternodes(self.mess_closure.begin,
                              follow_func=follow_func):
            nodes_to_predoms[node] = find_unordered_dominators(node, follow_func=follow_rev)

        for startnode in iternodes(self.mess_closure.begin,
                               follow_func=follow_func):
            if startnode is self.mess_closure.begin:
                continue
            
            path = iterpaths(startnode, follow_func=follow_func).next()
            
            end = None
            for endnode in reversed(path):
                if startnode in nodes_to_predoms[endnode]:
                    end = endnode
            
            if end is None:
                self.print_dot('noend.dot', marked_edges=[path_to_edges(path)], marked_nodes=[[startnode]])
                raise Exception("not sure.")
            # find lowest node for which top is dominator
   #         wrap them together in a bananacandidate
    #        rewire
     #       FCUK: update reverse edges after each rewiring
            
    def print_dot(self, filename, marked_edges=None, marked_nodes=None):
        return as_dot(filename, self.mess_closure.begin, marked_nodes=marked_nodes, marked_edges=marked_edges)


class GraphWrapper: # necessarily a bananawrapper
    def __init__(self, graph_head):
        self.cfg_head = graph_head
        self.graph_head = self.wrap_graph(self.cfg_head)
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
            print('our glorious ominator from {0}: {1}'.format(current, dom))
            
            if dom is None:
                raise ValueError("Post-dominator not found for {0}".format(current))
            subgraph = self.wrap_sub(current, dom)
            
            print(subgraph)
            # rewire

            # Assumption: going only forward in respect to flow (only works inside bananas)
            # take into account situation where neither current nor dom are inside, but they need a link (if-then) (XXX: this is from vague memory)
            if current is subgraph.begin:
                for preceding in current.preceding:
                    preceding.following.remove(current)
                    preceding.following.append(subgraph)
                    subgraph.preceding.append(preceding)
            else:
                current.following = [subgraph]
                subgraph.preceding = [current]
            
            if dom is subgraph.end:
                for following in dom.following:
                    following.preceding.remove(dom)
                    following.preceding.append(dubgraph)
                    subgraph.following.append(following)
            else:
                dom.preceding = [subgraph]
                subgraph.following = [dom]
            dontprint
            self.subs.append(subgraph)
            self.print_dot('dropped_{0}.dot'.format(len(self.subs)))
            current = dom
    
    def ordered_next(self, node):
        """Returns next nodes in the direction of stretched order.
        """
        return ordered_next(node, self.reverse_edges)
    
    def wrap_sub(self, start, end):
        return make_mess(start, end, self.reverse_edges)
    
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
            doms.intersection_update(frozenset(path))
    return doms


def find_post_dominators(node, follow_func):
    doms = find_unordered_dominators(node, follow_func)
    path = iterpaths(node, follow_func=follow_func).next()

    dom_list = []
    for child in path:
        if child in doms:
            dom_list.append(child)
    return dom_list
    

def make_mess(start, end, reverse_edges):
    #TODO: cut start/end connections
    # determine if starts with split or looplike join
    # XXX: make sure outer loop layers are peeled if joins from nested loops
    
    start_index = None
    if not any((preceding, start) in reverse_edges for preceding in start.preceding): # if loop-join
        start_index = 1
    
    # determine if end is a join or a looplike split
    end_index = None
    if not any((end, following) in reverse_edges for following in end.following):
        end_index = -1
    
    # find all nodes in between
    
    def follow_func(stack):
        for node in ordered_next(stack[-1], reverse_edges):
            if node is not end:
                yield node
    
    contents = set()
    start_nodes = set()
    end_nodes = set()
    for path in iterpaths(start, follow_func=follow_func):
        path = path[start_index:end_index]
        start_nodes.add(path[0])
        end_nodes.add(path[-1])
        contents.update(set(path))
        
    print('mess contents', contents)
    return LooseMess(contents, start_nodes, end_nodes)

    
def structurize(graph_head):
    as_dot('unstructured.dot', graph_head)
    graphmaker = GraphWrapper(graph_head)
    graphmaker.print_dot('unstructured_wrapped.dot')
    graphmaker.structurize()
    graphmaker.mark_reverse_edges()
    graphmaker.print_dot('reverse.dot')
    graphmaker.split()
    graphmaker.print_dot('split.dot')
    print(graphmaker.subs)
    graphmaker.pack_banana()
    return graphmaker.banana
