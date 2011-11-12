#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file is needed by the online game engine, and it exposes the main bot
to the game API.
'''

from random import shuffle, choice

from numpy import any as np_any

from world import WATER, OWN_HILLS, H_EXPLORE, H_HARVEST, H_FIGHT, EXPLORER, \
                  HARVESTER, ATTACKER, OWN_ANTS

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
        self.need_for_food = True

    def _do_turn(self):
        '''
        This is the raw function invoked by the game engine at each turn.

        The game engine will actually invoke ``do_turn()`` rather than
        ``_do_turn()``, but the ``main()`` might wrap the turn into a profiler
        when played locally, hence this intermediate step.
        '''
        # Init turn variables
        self.ants_to_process = set(self.world.own_ants.keys())
        self.destinations = set(())  # tiles that are targeted by a movement

        # Turn phases
        self.attack()
        self.world.diffuse()
        if self.need_for_food == True:
            self.harvest()
        self.explore()
        self._save_data()

    def attack(self):
        '''
        Manage attacking ants.
        '''
        # Define weighted map of attack areas

        # Identify attackrange + 1 (A1) or attackrange + 2 (A2) tiles

        # Deteach from the main scent mechanism all those ants that are on
        # either A1 or A2 tiles

        # Do best offensive move for A1 (forward|stay) or suspend judgment

        # Do best offensive move for A2 (forward|stay)

        # If A1 was suspended and A2 moved forward, re-evaluate after A2 move.

        # Else: retreat.

        attackers = []
        self.data_to_keep['attackers'] = attackers

    def harvest(self):
        '''
        Instruct the ant closer to each food resource to collect it.
        '''
        world = self.world
        destinations = self.destinations
        own_ants = self.ants_to_process
        for loc in world.food:
            ranking = []  # will contain tuples: scent, dest, direction, ant
            ants = world.get_stuff_in_sight(loc, OWN_ANTS)
            for ant in ants:
                ant = tuple(ant)
                if ant not in own_ants:  #already busy with something
                    continue
                options = world.get_scent_strengths(ant, H_HARVEST)
                for option in options:
                    option.append(ant)
                    ranking.append(option)
            ranking.sort(reverse=True)
            for scent, dest, direction, ant in ranking:
                dest = tuple(dest)
                if not dest in destinations \
                            and world.is_tile_passable(dest):
                    world.issue_order((ant, direction))
                    destinations.add(dest)
                    own_ants.remove(ant)
                    break

    def explore(self):
        '''
        Move all the ants that haven't been assigned to any specific and
        alternative task towards the strongest scent.
        '''
        world = self.world
        destinations = self.destinations
        own_ants = self.ants_to_process
        for ant in own_ants:
            scents_by_strength = world.get_scent_strengths(ant, H_EXPLORE)
            for scent, dest, direction in scents_by_strength:
                dest = tuple(dest)
                if not dest in destinations and world.is_tile_passable(dest):
                    world.issue_order((ant, direction))
                    destinations.add(dest)
                    break
            else:  #executes only if a break is never called
                destinations.add(ant)

    def _save_data(self):
        '''
        Save across-turns data.
        '''
        self.last_turn_data = self.data_to_keep
