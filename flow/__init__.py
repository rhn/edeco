# --- *coding=UTF-8* ---
import emulator
import structurizer
from common import closures
from exceptions import *


class Function:
    """Basic structure of the code: nested graphs of code blocks - enough to describe control flow. No postprocessing is done here.
    Use this class to store graphs maximally simplified in respect to nesting, but not in respect to display language.
    """
    def __init__(self, address, closures):
        """Closures are an ordered set of closures (which should be nested graphs). Order of closures must represent flow of control.
        """
        self.address = address
        self.closures = closures
    
    def into_code(self, name):
        """Debug only! To decode a function, use display module. This is just a dumb dump of unprocessed data."""
        str_clos = []
        for closure in self.closures:
            str_clos.append(closure.into_code())
        return '{0}(...) {{\n{1}\n}}'.format(name, closures.indent('\n'.join(str_clos)))


def into_function(address, nested_graph):
    return Function(address, nested_graph.closures)


def detect_function(arch, instructions, start_address):
    flat_graph = emulator.emulate_flow(arch, instructions, start_address)
    nested_graph = structurizer.structurize(flat_graph)
    return into_function(start_address, nested_graph)
