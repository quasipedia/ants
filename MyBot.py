#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file is needed by the online game engine, and it exposes the main bot
to the game API.
'''

from random import shuffle, choice

import bootstrap
from world import LAND, ENTITY_ID

from checklocal import RUNS_LOCALLY
if RUNS_LOCALLY:
    import logging
    log = logging.getLogger('main')


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Bot(object):

    '''
    The bot's AI.
    '''

    def __init__(self, world):
        self.world = world

    def do_setup(self):
        '''
        This funcion is called only once, after the intial settings are
        received and parsed from the game engine, but before the match
        starts. '''
        world = self.world

    def _do_turn(self):
        '''
        This is the raw function invoked by the game engine at each turn.

        The game engine will actually invoke ``do_turn()`` rather than
        ``_do_turn()``, but the ``main()`` might wrap the turn into a profiler
        when played locally, hence this intermediate step.
        '''
        world = self.world
        destinations = []
        for ant in world.own_ants:
            will_move = False
            scents_by_strength = world.get_scent_strengths(ant)
            for scent, dest, direction in scents_by_strength:
                dest = tuple(dest)
                if not dest in destinations \
                   and world.map[dest][ENTITY_ID] == LAND:
                    world.issue_order((ant, direction))
                    destinations.append(dest)
                    will_move = True
                    break
            if not will_move:
                destinations.append(tuple(ant))
        log.info('AI : done.')

        #import sys
        #sys.stdout.write('v circle(5.0,5.0,20.0,true);\n')
        #sys.stdout.write('v circle 5 5 20 true\n')


if __name__ == '__main__':

    bootstrap.run()
