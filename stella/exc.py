import dis

class StellaException(Exception):
    def addDebug(self, debuginfo):
        self.debuginfo = debuginfo

    def __str__(self):
        if hasattr(self, 'debuginfo'):
            return '{0} at {1}'.format(super().__str__(), self.debuginfo)
        else:
            return super().__str__()

class UnsupportedOpcode(StellaException):
    def __init__(self, op, debuginfo):
        super().__init__(dis.opname[op])
        self.addDebug(debuginfo)

class TypingError(StellaException):
    pass
class UnimplementedError(StellaException):
    pass