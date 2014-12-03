import test.si1l1s_struct
import test.basicmath
import test.langconstr
import test.objects
import test.external_func
import test.si1l1s_struct
import test.si1l1s_obj
import test.virtnet_purepython
import stella
from stella import exc  # noqa
import numpy as np
import mtpy  # noqa
import ctypes  # noqa


a = np.zeros(5, dtype=int)
b = test.objects.B()
b2 = test.objects.B(0.0, 1.0)
c = test.objects.C(np.array([1, 2, 3, 42]))
e = test.objects.E()
e2 = test.objects.E()
settings = test.virtnet_purepython.Settings(['seed=42'])
sim = test.virtnet_purepython.Simulation(settings)


def current_work(run=False):
    if type(run) == bool:
        ir = not run
    else:
        ir = run
    print(stella.wrap(sim.run, ir=ir)())
