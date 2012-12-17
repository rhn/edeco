from ftree import *
from common.closures import *
import pydot

"""Converts flat control flow graphs into structured (nested) graphs (control flow trees). It doesn't work on graphs with infinite loops/stops.

Definitions:
    Ordering:
        Imagine taking the graph by start node and collective end node. Pull them in opposite directions until a string forms.
        Ordering corresponds to distance from start node (not related to edge direction.
    
    Reverse edge:
        Edge that appears to go from end to start node in "stretched" graph.
    
    TODO: formalize
        
Algorithm:
    Mark reverse edges (define ordering).
    n := head
    While n:
        Find the earliest post-dominator p (define post-dominator).
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


def cfg_iterator(start_node, on_reverse=False):
    """Depth first iterator
    yield value: node, previous
    """
    visited = set()
    if not on_reverse:
        yield start_node
        
    def iterator(node):
        visited.add(node)
        for next in node.following:
            if next not in visited:
                if not on_reverse:
                    yield next
                for n in iterator(next):
                    yield n
                if on_reverse:
                    yield next
                    
    for n in iterator(start_node):
        yield n
        
    if on_reverse:
        yield start_node
    

def edge_iterator(start_node):
    """Depth first iterator"""
    visited = set()
    def iterator(node):
        visited.add(node)
        for next in node.following:
            yield node, next
            if next not in visited:
                for e in iterator(next):
                    yield e
            
    return iterator(start_node)

    
def iterpaths(graph_head, follow_func=None, partial=False, on_backwards=False):
    if follow_func is None:
        follow_func = lambda stack: stack[-1].following

    def make_yield(path, forward):
        if on_backwards:
            return path, forward
        return path

    def iterator(previous, node):
        current_path = previous + [node]
        
        if partial:
            yield make_yield(current_path, True)
        
        child_present = False
        for next in follow_func(current_path):
            for n in iterator(current_path, next):
                child_present = True
                yield n
                
        if not child_present and not partial:
            yield make_yield(current_path, True)
            if on_backwards:
                yield make_yield(current_path, False)
            return

        if on_backwards and partial:
            yield make_yield(current_path, False)

    for n in iterator([], graph_head):
        yield n


def ordered_next(node, reverse_edges):
    for following in node.following:
        if (node, following) not in reverse_edges:
            yield following
    for preceding in node.preceding:
        if (preceding, node) in reverse_edges:
            yield preceding

    
class GraphWrapper:
    class NodeMeta:
        def __init__(self, node, order=None):
            self.node = node
            self.order = order
            self.dominator = None
            self.postdominator = None
            
        def to_str(self, node_to_meta):
            out = ['o{0}'.format(self.order)]
            if self.dominator:
                out.append('d{1}'.format(node_to_meta[self.dominator].order))
            if self.postdominator:
                out.append('pd{1}'.format(node_to_meta[self.postdominator].order))
            return ' '.join(out)
            
            
    def __init__(self, graph_head):
        self.cfg_head = graph_head
        self.graph_head = self.wrap_graph(self.cfg_head)
        self.reverse_edges = None
        self.dominance = None

    def mark_reverse_edges(self):
        self.reverse_edges = find_reverse_edges(self.graph_head)

    def split(self):
        # XXX: this flow is stupid and sleepy. make it stateless and convert to passing data around
        if self.reverse_edges is None:
            raise RuntimeError("No reverse edges data")
        self.subs = []
        current = self.graph_head
        while True:
            dom = find_post_dominator(current, self.reverse_edges)
            subgraph = self.wrap_sub(current, dom)
            
            def rewire(node, sub):
                for following in node.following[:]:
                    if following in sub.closures:
                        node.following.remove(following)
                        node.following.append(sub)
                for preceding in node.preceding[:]:
                    if preceding in sub.closures:
                        node.preceding.remove(preceding)
                        node.preceding.append(sub)
                        
            # rewire
            if current not in subgraph.closures:
                rewire(current, subgraph)
            else:
                # TODO
                pass
            
            if dom not in subgraph.closures:
                rewire(dom, subgraph)
                    
            self.subs.append(subgraph)
            
            if not list(self.ordered_next(dom)):
                break
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
        graph = pydot.Dot('sorting')
        nodes_to_dot = {}
        for i, node in enumerate(cfg_iterator(self.graph_head)):
            dotnode = pydot.Node('{0}'.format(i))
            label = '{0}'.format(node)
            if self.dominance is not None:
                label = label + ' {0}'.format(self.dominance[node])
            dotnode.set_label(label)
            nodes_to_dot[node] = dotnode
            graph.add_node(dotnode)
        
        for src, dst in edge_iterator(self.graph_head):
            edge = pydot.Edge(nodes_to_dot[src], nodes_to_dot[dst])
            if self.reverse_edges and (src, dst) in self.reverse_edges:
                edge.set_color('red')
            graph.add_edge(edge)
        
        graph.write(filename)
        
        
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


def find_post_dominator(node, reverse_edges):
    def follow_func(stack):
        return ordered_next(stack[-1], reverse_edges)
        
    dom_candidates = None
    for path in iterpaths(node, follow_func=follow_func):
        if dom_candidates is None:
            dom_candidates = set(path[1:]) # remove self
        else:
            dom_candidates.intersection_update(frozenset(path))
    
    # got dom_candidates. Figure out the earliest one
    post_dominator = None
    path = iterpaths(node, follow_func=follow_func).next()
    for child in path:
        if child in dom_candidates:
            post_dominator = child
            break
    if post_dominator is None:
        raise ValueError("Post-dominator not found")
    return post_dominator


def make_mess(start, end, reverse_edges):
    #TODO: cut start/end connections
    exclude = set()
    # determine if starts with split or looplike join
    # XXX: make sure outer loop layers are peeled if joins from nested loops
    if not any((preceding, start) in reverse_edges for preceding in start.preceding): # if loop-join
        exclude.add(start)
    
    # determine if end is a join or a looplike split
    if not any((end, following) in reverse_edges for following in end.following):
        exclude.add(end)
    
    # find all nodes in between
    
    def follow_func(stack):
        for node in ordered_next(stack[-1], reverse_edges):
            if node is not end:
                yield node
    
    contents = set()
    for path in iterpaths(start, follow_func=follow_func):
        print('p', path)
        contents.update(set(path))
    
    print('cont', contents)
    print('ex', exclude)
    contents.difference_update(exclude)
    return LooseMess(contents)
    
def structurize(graph_head):
    graphmaker = GraphWrapper(graph_head)
#    graphmaker.layer_nodes()
    graphmaker.mark_reverse_edges()
    graphmaker.print_dot('reverse.dot')
    graphmaker.split()
    graphmaker.print_dot('split.dot')
    print(graphmaker.subs)
    raise NotImplementedError
