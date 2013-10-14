#!/usr/bin/env python

from stella import stella
from random import randint
import sys
from test import make_eq_test, make_delta_test

def addition(a,b):       return a+b
def subtraction(a,b):    return a-b
def multiplication(a,b): return a*b
def division(a,b):       return a/b
def floor_division(a,b): return a//b
def chained(a,b): return (a-b)/b*a;

arglist1 = [(-1,0), (84, -42), (1.0, 1), (0,1), (randint(0, 1000000), randint(0, 1000000)), (-1*randint(0, 1000000), randint(0, 1000000))]
for f in [addition, subtraction, multiplication]:
    make_eq_test(__name__, f, arglist1)


arglist2 = [(0,1), (5,2), (5.0,2), (4.0,4), (-5,2), (5.0,-2), (randint(0, 1000000), randint(1, 1000000)), (341433, 673069)]
for f in [division, floor_division, chained]:
    make_delta_test(__name__, f, arglist2)

if __name__ == '__main__':
    print(stella(addition)(41, 1))
    print(stella(addition)(43, -1))
    print(stella(subtraction)(44,2))
    print(stella(multiplication)(21,2))
    print(stella(division)(42,10))
    print(stella(floor_division)(85,2.0))
    print(stella(floor_division)(85,-2.0))
    x = chained(5,2)
    y = stella(chained)(5,2)
    print("chained difference: {0:.10f}".format(x-y))