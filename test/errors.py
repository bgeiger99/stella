#!/usr/bin/env python

from stella.exc import *
from test import *

def undefined1():
    if False:
        r = 1
    return r

def undefined2():
    if False:
        x = 1
    y = 0 + x
    return True

def zeros_no_type():
    a = zeros(5)

@mark.parametrize('f', [undefined1, undefined2, zeros_no_type])
def test_undefined(f):
    make_exc_test(f, (), UnboundLocalError, UndefinedError)

