import test.si1l1s
import test.basicmath
import test.langconstr
import test.struct
import stella
#args_mod = list(filter(lambda e: e[0] >= 0, arglist2))
import numpy as np
import mtpy

a = np.zeros(5, dtype=int)
b = test.struct.B()

def current_work(run=False):
    print(stella.wrap(test.struct.justPassing, ir=not run)(b))
