#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file is needed by the online game engine, and it exposes the main bot
to the game API.
'''

from random import shuffle, choice

from numpy import any as np_any

import bootstrap
from world import LAND, ENTITY_ID, OWN_HILL

from checklocal import RUNS_LOCALLY
if RUNS_LOCALLY:
    from overlay import overlay
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
        self.data_to_keep = {}

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
        self.attack()
        self.move()
        self._save_data()

    def attack(self):
        '''
        Manage attacking ants.
        '''
        frfoe = self.world.get_friendfoes
        attackers = []
        for enemy in self.world.enemy_ants:
            friends, foes = frfoe(enemy)
            if np_any(foes):
                attackers.append(foes[0])  #the list is contained in 2D array
        len1 = len(attackers)
        attackers = [ant for ant in attackers if np_any(ant)]
        len2 = len(attackers)
        if RUNS_LOCALLY and len1 != len2:
            log.debug('In turn %d found %s ghost ants' % (self.world.turn,
                                                          len2 - len1))
        self.data_to_keep['attackers'] = attackers
        log.debug(attackers)

    def move(self):
        '''
        Move all the ants that haven't been assigned to any specific and
        alternative task.
        '''
        world = self.world
        destinations = []
        for ant in world.own_ants:
            will_move = False
            scents_by_strength = world.get_scent_strengths(ant)
            for scent, dest, direction in scents_by_strength:
                dest = tuple(dest)
                if not dest in destinations \
                   and (world.map[dest][ENTITY_ID] == LAND or
                        world.map[dest][ENTITY_ID] < OWN_HILL):
                    world.issue_order((ant, direction))
                    destinations.append(dest)
                    will_move = True
                    break
            if not will_move:
                destinations.append(tuple(ant))
        if RUNS_LOCALLY:
            log.info('AI : done.')

    def _save_data(self):
        '''
        Save across-turns data.
        '''
        self.last_turn_data = self.data_to_keep



if __name__ == '__main__':

    bootstrap.run()
