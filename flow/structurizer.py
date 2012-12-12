from ftree import *
from common.closures import *
import pydot

"""Converts flat control flow graphs into structured (nested) graphs (control flow trees).

Step 1: Sort graph vertexes to maintain the following relationships:
            * if an edge leads to a previously unvisited node, source ordinal is smaller than destination's
            * if an edge leads to an already visited node, source ordinal must be larger than destination's ("loops")
            * beginning node always has the smallest ordinal
            * end node always has the greatest ordinal
            
Step 2: For each node, find the greatest node smaller than self that has all paths in common
Step 3: Find smallest node lesser than self sharing all paths
"""


def cfg_iterator(start_node, join_wait=False):
    """Depth first iterator
    join_wait: if True, nodes that are joined from other unvisited sources will not be visited. Use for sorting.
    yield value: node, previous
    """
    visited = set()
    yield start_node
    def iterator(node):
        print 'iter', node, node.following
        visited.add(node)
        print 'visited now', sorted(visited)
        for next in node.following:
            if next not in visited:
                if join_wait:
                    print next.preceding
                    if all(joiner in visited or joiner is node for joiner in next.preceding): # all nodes joining to next have been visited
                        yield next
                        for n in iterator(next):
                            yield n
                else:
                    yield next
                    for n in iterator(next):
                        yield n
    print 'NEW'
    for n in iterator(start_node):
        print 'new', n
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
            
            
    def __init__(self, flat_graph):
        """Flat_graph: first node of the graph"""
        self.flat_graph = flat_graph
        self.nodes = {}

    def sort_nodes(self):
        for i, node in enumerate(cfg_iterator(self.flat_graph, join_wait=True)):
            print i, node
            self.nodes[node] = self.NodeMeta(node, i)
            
    def print_dot(self, filename):
        graph = pydot.Dot('sorting')
        nodes_to_dot = {}
        for i, node in enumerate(cfg_iterator(self.flat_graph)):
            dotnode = pydot.Node('{0}'.format(i))
            dotnode.set_label('{0} {1}'.format(node, self.nodes[node].to_str(self.nodes)))
            nodes_to_dot[node] = dotnode
            graph.add_node(dotnode)
        
        for src, dst in edge_iterator(self.flat_graph):
            graph.add_edge(pydot.Edge(nodes_to_dot[src], nodes_to_dot[dst]))
        
        graph.write(filename)
        

def structurize(flat_graph):
    graphmaker = GraphWrapper(flat_graph)
    graphmaker.sort_nodes()
    graphmaker.print_dot('sorted.dot')
    raise NotImplementedError
    return ClosureFinder(flat_graph).closure
