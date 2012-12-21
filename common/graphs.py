import pydot

def path_to_edges(path):
    return [edge for edge in zip(path, path[1:])]


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


def iternodes(graph_head, follow_func=None):
    if follow_func is None:
        follow_func = lambda stack: stack[-1].following
    
    visited = set()
    def follow(stack):
        for node in follow_func(stack):
            if node not in visited:
                yield node
    
    for stack in iterpaths(graph_head, follow_func=follow, partial=True):
        yield stack[-1]


def as_dot(filename, graph_head, marked_nodes=None, marked_edges=None):
    if marked_edges is None:
        marked_edges = []
    if marked_nodes is None:
        marked_nodes = []
        
    colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'magenta']
    
    def get_colordict(groups):
        colordict = {}
        for color, group in zip(colors, groups):
            for element in group:
                colordict[element] = color
        return colordict
    
    node_colors = get_colordict(marked_nodes)
    edge_colors = get_colordict(marked_edges)
        
    graph = pydot.Dot('name')
    nodes_to_dot = {}
    for i, node in enumerate(iternodes(graph_head)):
        dotnode = pydot.Node('{0}'.format(i))
        label = '{0}'.format(node)
        dotnode.set_label(label)
        if node in node_colors:
            dotnode.set_color(node_colors[node])
        nodes_to_dot[node] = dotnode
        graph.add_node(dotnode)
    
    for edge in edge_iterator(graph_head):
        src, dst = edge
        dot_edge = pydot.Edge(nodes_to_dot[src], nodes_to_dot[dst])
        if edge in edge_colors:
            dotnode.set_color(edge_colors[node])
        graph.add_edge(dot_edge)
    
    graph.write(filename)
