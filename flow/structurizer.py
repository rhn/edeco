from ftree import *
from common.closures import *
import pydot

"""Converts flat control flow graphs into structured (nested) graphs (control flow trees).

Definitions:
    Ordering:
        if node a lies before node b on any path in graph with reverse edges removed, it's "earlier" than b
        if node a is earlier than b and b is earlier than c, c is "between" a and b
        
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
        n := top(S)
        For each edge E = (s, d) from n:
            If d in S:
                R = R + {E}
                Remove E from graph
    R is the set of reverse edges.

"""


def cfg_iterator(start_node):
    """Depth first iterator
    yield value: node, previous
    """
    visited = set()
    yield start_node
    def iterator(node):
        visited.add(node)
        for next in node.following:
            if next not in visited:
                yield next
                for n in iterator(next):
                    yield n
    for n in iterator(start_node):
        yield n
    

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
        """Flat_graph: first node of the graph"""
        self.graph_head = graph_head
        self.nodes = None
        self.reverse_edges = None

    def mark_reverse_edges(self):
        self.reverse_edges = find_reverse_edges(self.graph_head)

    def mark_dominance(self):
        # XXX: this flow is stupid and sleepy. make it stateless and convert to passing data around
        if self.reverse_edges is None:
            raise RuntimeError("No reverse edges data")
        self.dominance = find_post_dominators(self.graph_head, self.reverse_edges)
    
    def print_dot(self, filename):
        graph = pydot.Dot('sorting')
        nodes_to_dot = {}
        for i, node in enumerate(cfg_iterator(self.graph_head)):
            dotnode = pydot.Node('{0}'.format(i))
            if self.nodes:
                label = '{0} {1}'.format(node, self.nodes[node].to_str(self.nodes))
            else:
                label = '{0}'.format(node)
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
    for path, forward in iterpaths(graph_head,
                          follow_cond=lambda stack, next: (stack[-1], next) not in reverse_edges,
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


def find_post_dominators(graph_head, reverse_edges):
    dominators = {}
    for node in cfg_iterator(graph_head):
        dom_candidates = None
        for path in iterpaths(node,
                              follow_ordered=True,
                              reverse=reverse_edges):
            if dom_candidates is None:
                dom_candidates = set(path)
            else:
                dom_candidates.intersection_update(frozenset(path))
        
        # got dom_candidates. Figure out the earliest one
        post_dominator = None
        path = iterpaths(node,
                         follow_ordered=True,
                         reverse=reverse_edges).next()
        for child in path:
            if child in dom_candidates:
                post_dominator = child
        if post_dominator is None:
            raise ValueError("Post-dominator not found")   
        dominators[node] = post_dominator
    
    return dominators
        

def iterpaths(graph_head, follow_cond=None, partial=False, on_backwards=False):
    if follow_cond is None:
        follow_cond = lambda x: True

    def make_yield(path, forward):
        if on_backwards:
            return path, forward
        return path

    def iterator(previous, node):
        current_path = previous + [node]

        if not node.following:
            yield make_yield(current_path, True)
            if on_backwards:
                yield make_yield(current_path, False)
            return
        if partial:
            yield make_yield(current_path, True)
            
        for next in node.following: 
            if follow_cond(current_path, next):
                for n in iterator(current_path, next):
                    yield n

        if on_backwards and partial:
            yield make_yield(current_path, False)

    for n in iterator([], graph_head):
        yield n
    
def structurize(graph_head):
    graphmaker = GraphWrapper(graph_head)
#    graphmaker.layer_nodes()
    graphmaker.mark_reverse_edges()
    graphmaker.print_dot('layered.dot')    
    raise NotImplementedError
