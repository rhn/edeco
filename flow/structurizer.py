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

    def sort_nodes(self):
        for i, node in enumerate(cfg_iterator(self.flat_graph, join_wait=True)):
            print i, node
            self.nodes[node] = self.NodeMeta(node, i)
            
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
    for path in iterpaths(graph_head,
                          follow_cond=lambda stack, next: (stack[-1], next) not in reverse_edges,
                          partial=True):
        top = path[-1]
        for next in top.following:
            if next in path:
                reverse_edges.add((top, next))
    return reverse_edges
    
def iterpaths(graph_head, follow_cond=None, partial=False):
    if follow_cond is None:
        follow_cond = lambda x: True

    def iterator(previous, node):
        current_path = previous + [node]

        if not node.following:
            yield current_path
            return
        if partial:
            yield current_path  
            
        for next in node.following: 
            if follow_cond(current_path, next):
                for n in iterator(current_path, next):
                    yield n

    for n in iterator([], graph_head):
        yield n
    
def structurize(graph_head):
    graphmaker = GraphWrapper(graph_head)
#    graphmaker.layer_nodes()
    graphmaker.mark_reverse_edges()
    graphmaker.print_dot('layered.dot')    
    raise NotImplementedError
