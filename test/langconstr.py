import numpy as np

from test import *  # noqa
from stella.intrinsics.python import zeros
import stella
from .basicmath import addition, subtraction
from . import basicmath


def direct_assignment(x, y):
    a = x
    return a + y


def simple_assignment(x, y):
    a = x + y
    return a


def return_const():
    return 41


def assign_const():
    r = 42
    return r


def double_assignment(x, y):
    a = x
    b = 5 + y
    a += b
    return a


def double_cast(x, y):
    a = x / y
    b = y // x
    return a + b


def simple_if(x):
    if x:
        return 0
    else:
        return 42


def simple_ifeq(x, y):
    if x == y:
        return 0
    else:
        return 42


def simple_ifeq_const(x):
    if x == False:  # noqa TODO: support `is' here!
        return 0
    else:
        return 42


def for1(x):
    r = 0
    for i in range(x):
        r += i
    return r


def for2(x):
    r = 0
    s = 1
    for i in range(x):
        r += i
        s *= 2
    return r + s


def for_loop_var(x):
    for i in range(x):
        x = i
    return x


def while1(x):
    r = 0
    while x > 0:
        r += x
        x -= 1
    return r


def recursive(x):
    if x <= 0:
        return 1
    else:
        return x + recursive(x - 1)


def fib(x):
    if x <= 2:
        return 1
    return fib(x - 1) + fib(x - 2)


def fib_nonrecursive(n):
    if n == 0:
        return 1
    if n == 1:
        return 3
    grandparent = 1
    parent = 3
    me = 0  # required for stella only
    for i in range(2, n):
        me = 3 * parent - grandparent
        grandparent = parent
        parent = me
    return me


def hof_f(n):
    if n == 0:
        return 1
    else:
        return n - hof_m(hof_f(n - 1))


def hof_m(n):
    if n == 0:
        return 0
    else:
        return n - hof_f(hof_m(n - 1))


def and_(a, b):
    return a and b


def or_(a, b):
    return a or b

some_global = 0


def use_global():
    global some_global
    some_global = 0
    x = 5
    while some_global == 0:
        x = global_test_worker(x)
    return x


def global_test_worker(x):
    global some_global
    if x < 0:
        some_global = 1
    return x - 1


def new_global_const():
    global prev_undefined
    prev_undefined = 1


def new_global_var(x):
    global prev_undefined
    prev_undefined = x
    return prev_undefined  # TODO: / 2 fails!


def kwargs(a=0, b=1):
    return a + b


def kwargs_call1(x):
    return kwargs(a=x)


def kwargs_call2(x):
    return kwargs(b=x)


def kwargs_call3(x):
    return kwargs(a=1, b=x)


def kwargs_call4(x):
    return kwargs(a=x, b=x)


def return_without_init(x, y):
    if y > 0:
        return addition(x, y)
    else:
        return subtraction(x, y)


def ext_call(x):
    return basicmath.subtraction(0, x)


def array_allocation():
    a = zeros(5, dtype=int)  # noqa
    return 0


def array_allocation_reg():
    """
    Since memory allocation is not a focus right now,
    this test will be skipped indefinitely.
    """
    l = 2
    a = zeros(l, dtype=int)  # noqa
    return 0


def array_alloc_assignment():
    a = zeros(5, dtype=int)
    i = 0
    a[0] = i


def array_alloc_assignment2():
    a = zeros(5, dtype=int)
    for i in range(5):
        a[i] = 42


def array_alloc_assignment3():
    a = zeros(5, dtype=int)
    for i in range(5):
        a[i] = i + 1


def void():
    pass


def call_void():
    void()
    return 1


def array_alloc_use():
    a = zeros(5, dtype=int)
    a[0] = 1
    return a[0]


def array_alloc_use2():
    a = zeros(5, dtype=int)
    for i in range(5):
        a[i] = i ** 2
    r = 0
    for i in range(5):
        r += a[i]
    return r


def array_len():
    a = zeros(5, dtype=int)
    return len(a)


def numpy_array(a):
    a[1] = 4
    a[2] = 2
    a[3] = -1


def numpy_len_indirect(a):
    l = len(a)
    for i in range(l):
        a[i] = i + 1


def numpy_len_direct(a):
    for i in range(len(a)):
        a[i] = i + 1


def numpy_passing(a):
    a[0] = 3
    a[2] = 1
    numpy_receiving(a)


def numpy_receiving(a):
    l = len(a)
    for i in range(l):
        if a[i] > 0:
            a[i] += 1


def numpy_global():
    global numpy_global_var
    numpy_global_var[3] = 4
    numpy_global_var[4] = 2


def return_2():
    return 2


def if_func_call():
    return return_2() > 1


def numpy_func_limit(a):
    for i in range(return_2()):
        a[i] = i + 1


@mark.parametrize('args', [(40, 2), (43, -1), (41, 1)])
@mark.parametrize('f', [direct_assignment, simple_assignment, double_assignment, double_cast,
                        return_without_init])
def test1(f, args):
    make_eq_test(f, args)


@mark.parametrize('args', [(True, True), (True, False), (False, True), (False, False)])
@mark.parametrize('f', [and_, or_])
def test2(f, args):
    make_eq_test(f, args)


@mark.parametrize('arg', single_args([True, False]))
@mark.parametrize('f', [simple_if, simple_ifeq_const])
def test3(f, arg):
    make_eq_test(f, arg)


@mark.parametrize('args', [(True, False), (True, True), (4, 2), (4.0, 4.0)])
@mark.parametrize('f', [simple_ifeq])
def test4(f, args):
    make_eq_test(f, args)


@mark.parametrize('f', [return_const, assign_const, use_global, array_allocation,
                        array_alloc_assignment, array_alloc_assignment2, array_alloc_assignment3,
                        void, call_void, array_alloc_use, array_alloc_use2, array_len,
                        if_func_call])
def test5(f):
    make_eq_test(f, ())


@mark.parametrize('f', [array_allocation_reg])
@unimplemented
def test5b(f):
    make_eq_test(f, ())


@mark.parametrize('arg', single_args([0, 1, 2, 42, -1, -42]))
@mark.parametrize('f', [for1, for2, for_loop_var, while1, recursive, ext_call, kwargs_call1,
                        kwargs_call2, kwargs_call3, kwargs_call4])
def test6(f, arg):
    make_eq_test(f, arg)


@mark.parametrize('arg', single_args([0, 1, 2, 5, 8, -1, -3]))
@mark.parametrize('f', [fib, fib_nonrecursive])
def test7(f, arg):
    make_eq_test(f, arg)


@mark.parametrize('f', [kwargs])
def test8(f):
    make_eq_test(f, (1, 30))


@mark.parametrize('arg', single_args([0, 1, 2, 5, 8, 12]))
@mark.parametrize('f', [hof_f])
def test9(f, arg):
    make_eq_test(f, arg)


@mark.parametrize('args', [{'a': 1}, {'b': 2}, {'a': 1, 'b': 0}, {'b': 1, 'a': 0}, {'a': 1.2},
                           {'b': -3}, {}])
def test10(args):
    make_eq_kw_test(kwargs, args)


@mark.parametrize('args', [{'c': 5}, {'b': -1, 'c': 5}])
@mark.xfail()
def test11(args):
    make_eq_kw_test(kwargs, args)


@mark.parametrize('arg', single_args([np.zeros(5, dtype=int)]))
@mark.parametrize('f', [numpy_array, numpy_len_indirect, numpy_receiving, numpy_passing,
                        numpy_len_direct])
def test12(f, arg):
    make_eq_test(f, arg)


@mark.parametrize('arg', single_args([np.zeros(5, dtype=int)]))
@mark.parametrize('f', [])
@unimplemented
def test12b(f, arg):
    make_eq_test(f, arg)


def test13():
    global numpy_global_var

    orig = np.zeros(5, dtype=int)

    numpy_global_var = np.array(orig)
    py = numpy_global()
    py_res = numpy_global_var

    numpy_global_var = orig
    st = stella.wrap(numpy_global)()
    st_res = numpy_global_var

    assert py == st
    assert all(py_res == st_res)


def test13b():
    """Global scalars are currently not updated in Python when their value changes in Stella"""
    global some_global

    some_global = 0
    py = use_global()
    assert some_global == 1

    some_global = 0
    st = stella.wrap(use_global)()
    assert some_global == 0

    assert py == st


def test13c():
    """Defining a new (i.e. not in Python initialized) global variable

    and initialize it with a constant
    """
    global prev_undefined

    assert 'prev_undefined' not in globals()
    py = new_global_const()
    assert 'prev_undefined' in globals()

    del prev_undefined
    assert 'prev_undefined' not in globals()
    st = stella.wrap(new_global_const)()
    # Note: currently no variable updates are transfered back to Python
    assert 'prev_undefined' not in globals()

    assert py == st


def test13d():
    """Defining a new (i.e. not in Python initialized) global variable

    and initialize it with another variable
    """
    global prev_undefined

    assert 'prev_undefined' not in globals()
    py = new_global_var(42)
    assert 'prev_undefined' in globals()

    del prev_undefined
    assert 'prev_undefined' not in globals()
    st = stella.wrap(new_global_var)(42)
    # Note: currently no variable updates are transfered back to Python
    assert 'prev_undefined' not in globals()

    assert py == st
