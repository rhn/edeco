class FlowDetectionError(Exception):
    pass

class InvalidCodeError(ValueError, FlowDetectionError):
    pass

class FunctionBoundsException(InvalidCodeError):
    pass

class EmulationUnsupported(FlowDetectionError):
    pass
    
class EmulatorOutOfBounds(FlowDetectionError):
    pass
