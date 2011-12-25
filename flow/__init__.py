# --- *coding=UTF-8* ---
import emulator
import structurizer
from common import closures
from exceptions import *


class Function:
    def __init__(self, address, closures):
        self.address = address
        self.closures = closures
    
    def into_code(self, name):
        str_clos = []
        for closure in self.closures:
            str_clos.append(closure.into_code())
        return '{0}(...) {{\n{1}\n}}'.format(name, closures.indent('\n'.join(str_clos)))


def into_function(address, closure):
    return Function(address, closure.closures)


def detect_function(arch, instructions, start_address):
    flat_graph = emulator.emulate_flow(arch, instructions, start_address)
    closure = structurizer.structurize(flat_graph)
    return into_function(start_address, closure)
