#!/usr/bin/env python3
# Copyright 2013-2015 David Mohr
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mtpy # cython wrapper around mtwist
from math import log
import sys
from copy import deepcopy
from numpy import zeros, copy
try:
    from .virtnet_utils import Settings
except SystemError:
    from virtnet_utils import Settings


#### HELPERS ####

class Rnd(object):
    @staticmethod
    def seed(s):
        #random.seed(s)
        mtpy.mt_seed32new(s)

    @staticmethod
    def uniform():
        #return random.random()
        return mtpy.mt_drand()

    @staticmethod
    def exp(p):
        u = 1.0 - mtpy.mt_drand()
        return -log(u)/p


class SimObj(object):
    @classmethod
    def make(klass, n, initializer):
        r = []
        for i in range(n):
            r.append(klass(next(initializer)))
        return r

    @classmethod
    def pick(klass, l):
        prob = Rnd.uniform()
        return l[int(prob*len(l))]


class Point(object):
    def __init__(self, pos = None):
        if pos == None:
            self.pos = zeros(shape=Point.dim, dtype=int)
        elif type(pos) == Point:
            self.pos = copy(pos.pos)
        else:
            self.pos = pos

    def reset(self):
        for i in range(Point.dim):
            self.pos[i] = 0

    def setTo(self, p):
        for i in range(Point.dim):
            self.pos[i] = p.pos[i]

    def getPos(self):
        return self.pos

    def reldist(self, pos2):
        p1 = self.pos
        p2 = pos2.getPos()
        d = len(p1)
        s = 0
        for i in range(d):
            rel = p1[i] - p2[i]
            s += rel**d
        return pow(s, 1.0/Point.dim)

    def add(self, p2):
        self.pos += p2
    def addPos(self, p2):
        pos2 = p2.getPos()
        for i in range(len(self.pos)):
            self.pos[i] += pos2[i]
    def addToDim(self, dim, val):
        self.pos[dim] += val

    #def sub(self, p2):
    #    self.pos -= p2

    def div(self, p2):
        for i in range(Point.dim):
            self.pos[i] /= p2

    #def mul(self, p2):
    #    self.pos *= p2
    def __repr__(self):
        return self.pos.__repr__()


#### MAIN OBJECTS ####

class Leg(SimObj):
    def __init__(self, params):
        self.dim = params['dim']
        self.pos = params['pos']
        self.r = params['r']
        self.no = params['no']
        # pre-allocate space for moves
        self.moves = []
        for i in range(2*self.dim):
            self.moves.append(Point())

        params['surface'].putDown(self.pos)

    def __repr__(self):
        return "Leg {0}".format(self.no)

    def move(self, spider, surface):
        # TODO gait check, extend possible moves?
        i = 0
        for d1 in range(surface.dim):
            pos = self.moves[i]
            pos.setTo(self.pos)
            pos.addToDim(d1, -1)
            if not surface.isOccupied(pos) and spider.gaitOk(pos, self):
                i += 1

            pos = self.moves[i]
            pos.setTo(self.pos)
            pos.addToDim(d1, 1)
            if not surface.isOccupied(pos) and spider.gaitOk(pos, self):
                i += 1
        if i == 0:
            raise Exception ("No moves -- this shouldn't happen")
        move = self.moves[int(Rnd.uniform() * i)]

        surface.pickUp(self.pos)
        self.r = surface.putDown(move)
        #print ("# Moving to {0}".format(move))

        self.pos.setTo(move)

    def getRate(self):
        return self.r
    def getPosition(self):
        return self.pos
    def getDistance(self, pos):
        return self.pos.reldist(pos)

    @classmethod
    def pick(klass, legs):
        prob = Rnd.uniform()
        R = 0.0
        for leg in legs:
            R += leg.getRate()
        Ridx = R * prob
        for leg in legs:
            r = leg.getRate()
            if Ridx < r:
                #print ("# Using {0}".format(leg))
                return leg
            else:
                Ridx -= r
        raise Exception ("No leg was picked")


class Spider(SimObj):
    def __init__(self, params):
        def legInit():
            pos = Point(Point.center)
            i = 0
            while True:
                yield {'r': params['r'], 'pos': Point(pos), 'dim': params['dim'], 'surface': params['surface'], 'no': i}
                pos.addToDim(0,1)
                i += 1

        self.legs = Leg.make(params['nlegs'], legInit())
        self.nlegs = params['nlegs']
        self.gait = params['gait']
        self._refPoint = Point()

    def refPoint(self):
        """This is `single threaded', can only be used by one consumer at a time!"""
        self._refPoint.reset()
        return self._refPoint

    def getLegs(self):
        return self.legs

    def getRate(self):
        r = 0.0
        for leg in self.legs:
            r += leg.getRate()
        return r

    def getDistance(self):
        pos = self.refPoint()
        for leg in self.legs:
            pos.addPos(leg.getPosition())
        pos.div(self.nlegs)
        return pos.reldist(Point.center)

    def gaitOk(self, pos, leg):
        for oleg in self.legs:
            if oleg == leg:
                continue
            if oleg.getDistance(pos) > self.gait:
                return False
        return True

    @classmethod
    def pick(klass, spiders):
        # FIXME: compatability with the optimized C version
        #assert len(spiders) == 1
        return spiders[0]


class Surface(object):
    (substrate, product, occupied) = range(3)
    def __init__(self, params):
        self.dim = params['dim']
        self.r = params['r']
        self.koff = params['koff']
        self.s = zeros(shape=[params['center']*2 for d in range(self.dim)], dtype=int)

    def __getitem__ (self, idx):
        a = self.s
        for i in range(len(idx)):
            try:
                a = a[idx[i]]
            except IndexError:
                raise Exception ("Index {0:s}[{1:d}] out of range".format(idx, i ))
        return a

    def __setitem__ (self, idx, value):
        a = self.s
        for i in range(len(idx)-1):
            a = a[idx[i]]
        a[idx[len(idx)-1]] = value

    def isOccupied(self, idx):
        idx = tuple(idx.getPos())
        return self.s[idx] & self.occupied

    def pickUp(self,idx):
        idx = tuple(idx.getPos())
        if not (self.s[idx] & self.product):
            self.s[idx] += self.product
        self.s[idx] -= self.occupied

    def putDown(self,idx):
        idx = tuple(idx.getPos())
        #try:
        self.s[idx] += self.occupied
        #except IndexError:
        #    # this shouldn't happen
        #    print ("Error: {0} is out of range".format(idx))
        #    raise
        if self.s[idx] & self.product:
            return self.koff
        else:
            return self.r



class Simulation(object):
    def __init__(self, params):
        Rnd.seed(params['seed'])

        params['center'] = params['radius'] + 2

        Point.dim = params['dim']
        Point.center = Point([params['center'] for x in range(params['dim'])])

        self.surface = Surface(params)
        def spiderInit():
            init_params = deepcopy(params)
            init_params['surface'] = self.surface
            while True:
                yield init_params
        self.spiders = Spider.make(params['nspiders'], spiderInit())
        max_observations = 15  # pre-allocate space for observations, this is arbitrary and only limited by memory
        self.observations = zeros(max_observations, dtype=float)
        self.obs_i = 0
        self.radius = params['radius']
        self.t = 0.0  # added for Stella
        self.nextObsDist = 1

    def end(self):
        return self.nextObsDist > self.radius or self.obs_i >= len(self.observations)

    def isNewObservation(self, spider):
        return spider.getDistance() >= self.nextObsDist

    def getHeader(self):
        return "# sim_time"

    def observe(self, spider):
        #dist = spider.getDistance()
        #print ("{t:.4f} {dist:.1f} {secs:.2f}".format(t=self.t, dist=dist, secs=self.params['elapsedTime']()))
        self.observations[self.obs_i] = self.t
        self.obs_i += 1

    def __eq__(self, o):
        return (self.observations == o.observations).all()

    def run(self):
        # self.t = 0  # removed for Stella, widening of self.t not yet supported
        self.nextObsDist = 1
        while not self.end():
            spider = Spider.pick(self.spiders)
            #print ("Moving spider {0}".format(spider))

            self.t += Rnd.exp(spider.getRate())

            leg = Leg.pick(spider.getLegs())
            #print ("Moving leg {0}".format(leg))

            leg.move(spider, self.surface)

            if self.isNewObservation(spider):
                self.observe(spider)
                self.nextObsDist += 1



def verify_results():
    """
    This test assures that the simulation computes exactly the same result as the C version.
    """
    seed = 1368048967
    exp_results = [(9.041135791947408, 1.118033988749895), (19.667526963260286, 2.0615528128088303), (43.08767021796176, 3.0413812651491097), (119.12422328354563, 4.301162633521313), (235.72355926459574, 5.315072906367325), (244.49982281025584, 6.020797289396148), (252.74106914186763, 7.0710678118654755), (298.1731077872496, 8.06225774829855), (383.2934150062547, 9.013878188659973), (412.1063434596637, 10.012492197250394)]
    exp_times = list(map(lambda x: x[0], exp_results))

    settings = Settings()
    settings['seed'] = seed

    sim = Simulation(settings)
    sim.run()

    actual_results = sim.observations
    for e_t, a_t in zip(exp_times, actual_results):
        assert (e_t == a_t).all()


def main(argv):
    settings = Settings(argv)
    print("## {0}".format(settings))

    sim = Simulation(settings)
    sim.run()

    print (sim.getHeader())
    for t in sim.observations:
        print ("{t:.4f}".format(t=t))

    #print ([(x[0], x[1]) for x in results])


if __name__ == '__main__':
    main(sys.argv[1:])
