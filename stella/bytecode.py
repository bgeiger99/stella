import dis
import logging
import sys

from .llvm import *
from .exc import *
from abc import ABCMeta, abstractmethod, abstractproperty
from llvm.core import INTR_FLOOR

NoType = ''

class Variable(object):
    name = None
    type = NoType

    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        if not self.name:
            name = '$'
        else:
            name = self.name

        if self.type is NoType:
            type_name = '?'
        else:
            type_name = self.type.__name__

        return "{0}<{1}>".format(name, type_name)

    def unify_type(self, tp2, debuginfo):
        tp1 = self.type
        if   tp1 == tp2:    pass
        elif tp1 == NoType: self.type = tp2
        elif tp2 == NoType: pass
        elif (tp1 == int and tp2 == float) or (tp1 == float and tp2 == int):
            self.type = float
            return True
        else:
            raise TypingError ("Unifying of types " + str(tp1) + " and " + str(tp2) + " not yet implemented", debuginfo)

        return False


class Const(object):
    type = ''
    value = None

    def __init__(self, value):
        self.value = value
        self.type = type(value)
        self.llvm = llvm_constant(value)
        self.name = str(value)

    def __str__(self):
        return str(self.value)

class Target(object):
    type = ''
    bc = None
    label = None

    def __init__(self, label, type='jabs'):
        self.label = label
        self.type = type

    def __str__(self):
        if self.type == 'jabs':
            c = 'a'
        elif self.type == 'jrel':
            c = 'r'
        else:
            c = '?'
        return 'J{0}[{1}]'.format(c, self.label)

class Cast(object):
    def __init__(self, obj, tp):
        assert obj.type != tp
        self.obj = obj
        self.type = tp
        self.emitted = False

        logging.debug("Casting {0} to {1}".format(self.obj.name, self.type))
        self.name = "({0}){1}".format(self.type, self.obj.name)

    def translate(self, builder):
        if self.emitted:
            assert hasattr(self, 'llvm')
            return
        self.emitted = True

        #import pdb; pdb.set_trace()

        # TODO: HACK: instead of failing, let's make it a noop
        #assert self.obj.type == int and self.type == float
        if self.obj.type ==  self.type:
            self.llvm = self.obj.llvm
            return

        # if value attribute is present, then it is a Const
        if hasattr(self.obj, 'value'):
            self.value = float(self.obj.value)
            self.llvm = llvm_constant(self.value)
        else:
            self.llvm = builder.sitofp(self.obj.llvm, py_type_to_llvm(float), self.name)

    def __str__(self):
        return self.name


class Local(Variable):
    @staticmethod
    def tmp():
        l = Local('')
#        if isinstance(template, Variable):
#            l.type = template.type
#        else:
#            l.type = template
        return l

def use_stack(n):
    """
    Decorator, it takes n items off the stack
    and adds them as bytecode arguments.
    """
    def extract_n(f):
        def extract_from_stack(self, *f_args):
            args = []
            for i in range(n):
                args.append(self.stack.pop())
            args.reverse()
            if self.args == None:
                self.args = args
            else:
                self.args.extend(args)
            return f(self, *f_args)
        return extract_from_stack
    return extract_n

class LinkedListIter(object):
    def __init__(self, start):
        self.next = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.next == None:
            raise StopIteration()
        current = self.next
        self.next = self.next.next
        return current

class IR(metaclass=ABCMeta):
    args = None
    result = None
    debuginfo = None
    llvm = None
    block = None
    next = None
    prev = None
    loc = None
    discard = False

    def __init__(self, debuginfo, stack):
        self.debuginfo = debuginfo
        self.stack = stack
        self.args = []

    def addConst(self, arg):
        self.addArg(Const(arg))

    def addArg(self, arg):
        self.args.append(arg)

    def cast(self, builder):
        #import pdb; pdb.set_trace()
        for arg in self.args:
            if isinstance(arg, Cast):
                arg.translate(builder)

    @abstractmethod
    def stack_eval(self, func):
        pass

    @abstractmethod
    def translate(self, module, builder):
        pass

    @abstractmethod
    def type_eval(self, func):
        pass

    def __iter__(self):
        return LinkedListIter(self)

    def __str__(self):
        return "{0} {1} {2}".format(
                    self.__class__.__name__,
                    self.result,
                    ", ".join([str(v) for v in self.args]))

class PhiNode(IR):
    @use_stack(1)
    def stack_eval(self, func):
        self.result = Local.tmp()
        self.stack.push(self.result)

    def type_eval(self, func):
        for arg in self.args:
            self.result.unify_type(arg.type, self.debuginfo)

    def translate(self, module, builder):
        phi = builder.phi(py_type_to_llvm(self.result.type), self.result.name)
        for arg in self.args:
            phi.add_incoming(arg.llvm, arg.block)

        self.result.llvm = phi
        #import pdb; pdb.set_trace()

class Bytecode(IR):
    pass

class LOAD_FAST(Bytecode):
    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    def stack_eval(self, func):
        # don't use func.getLocal() here because the semantics of
        # LOAD_FAST require the variable to exist
        self.result = func.locals[self.args[0].name]
        self.stack.push(self.result)

    def type_eval(self, func):
        pass
    def translate(self, module, builder):
        pass

    def __str__(self):
        return "(LOAD_FAST {0})".format(self.args[0])

class STORE_FAST(Bytecode):
    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    @use_stack(1)
    def stack_eval(self, func):
        #self.result = func.getLocal(self.args[0].name)
        self.result = self.args[0]

    def type_eval(self, func):
        #func.retype(self.result.unify_type(self.args[1].type, self.debuginfo))
        arg = self.args[1]
        #import pdb; pdb.set_trace()
        tp_changed = self.result.unify_type(arg.type, self.debuginfo)
        if tp_changed:
            # TODO: can I avoid a retype in some cases?
            func.retype()
            if self.result.type != arg.type:
                self.args[1] = Cast(arg, self.result.type)

    def translate(self, module, builder):
        self.cast(builder)
        self.result.llvm = self.args[1].llvm

class LOAD_CONST(Bytecode):
    discard = True
    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    def stack_eval(self, func):
        self.result = self.args[0]
        self.stack.push(self.result)

    def type_eval(self, func):
        pass
    def translate(self, module, builder):
        pass

class BinaryOp(Bytecode):
    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    @use_stack(2)
    def stack_eval(self, func):
        self.result = Local.tmp()
        self.stack.push(self.result)

    def type_eval(self, func):
        for i in range(len(self.args)):
            arg = self.args[i]
            tp_changed = self.result.unify_type(arg.type, self.debuginfo)
            if tp_changed:
                if self.result.type != arg.type:
                    self.args[i] = Cast(arg, self.result.type)
                # TODO: can I avoid a retype in some cases?
                func.retype()

    def builderFuncName(self):
        try:
            return self.b_func[self.result.type]
        except KeyError:
            raise TypingError("{0} does not yet implement type {1}".format(self.__class__.__name__, self.result.type))

    def translate(self, module, builder):
        self.cast(builder)
        f = getattr(builder, self.builderFuncName())
        self.result.llvm = f(self.args[0].llvm, self.args[1].llvm, self.result.name)

    @abstractproperty
    def b_func(self):
        return {}

class BINARY_ADD(BinaryOp):
    b_func = {float: 'fadd', int: 'add'}

class BINARY_SUBTRACT(BinaryOp):
    b_func = {float: 'fsub', int: 'sub'}

class BINARY_MULTIPLY(BinaryOp):
    b_func = {float: 'fmul', int: 'mul'}

class BINARY_MODULO(BinaryOp):
    b_func = {float: 'frem', int: 'srem'}

class BINARY_POWER(BinaryOp):
    b_func = {float: INTR_POW, int: INTR_POWI}

    @use_stack(2)
    def stack_eval(self, func):
        self.result = Local.tmp()
        self.stack.push(self.result)

    def type_eval(self, func):
        # TODO if args[1] is int but negative, then the result will be float, too!
#        if self.args[0].type == int and self.args[1].type == int:
#            tp = int
#        else:
#            tp = float
#        tp_changed = self.result.unify_type(tp, self.debuginfo)
        super().type_eval(func)

    def translate(self, module, builder):
        # llvm.pow[i]'s first argument always has to be float
        if self.args[0].type == int:
            self.args[0] = Cast(self.args[0], float)

        self.cast(builder)

        if self.args[1].type == int:
            # powi takes a i32 argument
            power = builder.trunc(self.args[1].llvm, tp_int32, '(i32)'+self.args[1].name)
        else:
            power = self.args[1].llvm

        llvm_pow = Function.intrinsic(module, self.b_func[self.args[1].type], [py_type_to_llvm(self.args[0].type)])
        pow_result = builder.call(llvm_pow, [self.args[0].llvm, power])

        if isinstance(self.args[0], Cast) and self.args[0].obj.type == int and self.args[1].type == int:
            # cast back to an integer
            self.result.llvm = builder.fptosi(pow_result, py_type_to_llvm(int))
        else:
            self.result.llvm = pow_result

class BINARY_FLOOR_DIVIDE(BinaryOp):
    """Python compliant `//' operator: Slow since it has to perform type conversions and floating point division for integers"""
    b_func = {float: 'fdiv', int: 'fdiv'} # NOT USED, but required to make it a concrete class

    def type_eval(self, func):
        for arg in self.args:
            # TODO: this is a HACK
            if isinstance(arg, Cast):
                tp = arg.obj.type
            else:
                tp = arg.type
            self.result.unify_type(tp, self.debuginfo)

        # convert all arguments to float, since fp division is required to apply floor
        for i in range(len(self.args)):
            arg = self.args[i]
            do_cast = arg.type != float
            if do_cast:
                self.args[i] = Cast(arg, float)
                func.retype()

    def translate(self, module, builder):
        self.cast(builder)

        tmp = builder.fdiv(self.args[0].llvm, self.args[1].llvm, self.result.name)
        llvm_floor = Function.intrinsic(module, INTR_FLOOR, [py_type_to_llvm(float)])
        self.result.llvm = builder.call(llvm_floor, [tmp])

        #import pdb; pdb.set_trace()
        if all([isinstance(a,Cast) and a.obj.type == int for a in self.args]):
            # TODO this may be superflous if both args got converted to float in the translation stage -> move toFloat partially to the analysis stage.
            self.result.llvm = builder.fptosi(self.result.llvm, py_type_to_llvm(int), "(int)"+self.result.name)

class BINARY_TRUE_DIVIDE(BinaryOp):
    b_func = {float: 'fdiv'}

    @use_stack(2)
    def stack_eval(self, func):
        # The result of `/', true division, is always a float
        self.result = Local.tmp()
        self.stack.push(self.result)

    def type_eval(self, func):
        # this op always returns a float
        self.result.type = float
        super().type_eval(func)

#class InplaceOp(BinaryOp):
#    @use_stack(2)
#    def stack_eval(self, func):
#        tp = unify_type(self.args[0].type, self.args[1].type, self.debuginfo)
#        if tp != self.args[0].type:
#            self.result = Local.tmp(self.args[0])
#            self.result.type = tp
#        else:
#            self.result = self.args[0]
#        self.stack.push(self.result)
#
#    def translate(self, module, builder):
#        self.floatArg(builder)
#        f = getattr(builder, self.builderFuncName())
#        self.result.llvm = f(self.args[0].llvm, self.args[1].llvm, self.result.name)

# Inplace operators don't have a semantic difference when used on primitive types
class INPLACE_ADD(BINARY_ADD): pass
class INPLACE_SUBTRACT(BINARY_SUBTRACT): pass
class INPLACE_MULTIPLY(BINARY_MULTIPLY): pass
class INPLACE_TRUE_DIVIDE(BINARY_TRUE_DIVIDE): pass
class INPLACE_FLOOR_DIVIDE(BINARY_FLOOR_DIVIDE): pass
class INPLACE_MODULO(BINARY_MODULO): pass

class COMPARE_OP(Bytecode):
    b_func = {float: 'fcmp', int: 'icmp', bool: 'icmp'}
    op = None

    icmp = {'==': ICMP_EQ,
            '!=': ICMP_NE,
            '>':  ICMP_SGT,
            '>=': ICMP_SGE,
            '<':  ICMP_SLT,
            '<=': ICMP_SLE,
            }

    fcmp = {'==': FCMP_OEQ,
            '!=': FCMP_ONE,
            '>':  FCMP_OGT,
            '>=': FCMP_OGE,
            '<':  FCMP_OLT,
            '<=': FCMP_OLE,
            }

    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    def addCmp(self, op):
        self.op = op

    @use_stack(2)
    def stack_eval(self, func):
        self.result = Local.tmp()
        self.stack.push(self.result)

    def type_eval(self, func):
        #func.retype(self.result.unify_type(bool, self.debuginfo))
        self.result.type = bool
        if self.args[0].type != self.args[1].type:
            raise TypingError("Comparing different types ({0} with {1})".format(self.args[0].type, self.args[1].type))

    def translate(self, module, builder):
        # assume both types are the same, see @stack_eval
        tp = self.args[0].type
        if not self.args[0].type in self.b_func:
            raise UnimplementedError(tp)

        f = getattr(builder, self.b_func[tp])
        m = getattr(self,    self.b_func[tp])

        self.result.llvm = f(m[self.op], self.args[0].llvm, self.args[1].llvm, self.result.name)

class RETURN_VALUE(Bytecode):
    def __init__(self, debuginfo, stack):
        super().__init__(debuginfo, stack)

    @use_stack(1)
    def stack_eval(self, func):
        self.result = self.args[0]

    def type_eval(self, func):
        pass

    def translate(self, module, builder):
        builder.ret(self.args[0].llvm)

    def __str__(self):
        return 'RETURN ' + str(self.args[0])

class Jump(IR):
    target = None
    def addTargetBytecode(self, bc):
        """
        assert isinstance(self, IR)
        assert isinstance(self.args[0], Target)
        """
        self.target.bc = bc

    @use_stack(1)
    def stack_eval(self,func):
        pass

    def type_eval(self,func):
        pass

    def translate(self, module, builder):
        builder.branch(self.target.bc.block)

    def addTarget(self, arg, jmp_tp):
        self.target = Target(arg, jmp_tp)

class JUMP_IF_FALSE_OR_POP(Jump, Bytecode):
    def translate(self, module, builder):
        builder.cbranch(self.args[1].llvm, self.next.block, self.args[0].bc.block)

opconst = {}
# Get all contrete subclasses of Bytecode and register them
for name in dir(sys.modules[__name__]):
    obj = sys.modules[__name__].__dict__[name]
    try:
        if issubclass(obj, Bytecode) and len(obj.__abstractmethods__) == 0:
            opconst[dis.opmap[name]] = obj
    except TypeError:
        pass
