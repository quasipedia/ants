#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file is needed by the online game engine, and it exposes the main bot
to the game API.
'''

from random import shuffle, choice

from numpy import any as np_any
from numpy import array

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

    def do_setup(self):
        '''
        This funcion is called only once, after the intial settings are
        received and parsed from the game engine, but before the match
        starts. '''
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

    def attack(self):
        '''
        Manage attacking ants.
        '''
        world = self.world
        # Isolate enemies and own ants which are at attackradius + 2.
        enemy_engageable = {}
        own_engageable = {}
        f = self.world.get_engageable
        for enemy in world.enemy_ants:
            tmp = f(enemy)
            if np_any(tmp):
                tmp = set([tuple(loc) for loc in tmp])
                enemy_engageable[enemy] = tmp
                for own in tmp:
                    try:
                        own_engageable[own].add(enemy)
                    except KeyError:
                        own_engageable[own] = set(enemy)
        if RUNS_LOCALLY:
            log.debug('# OWN ENGAGEABLE : %s' % own_engageable)
            log.debug('# ENEMY ENGAGEABLE : %s' % enemy_engageable)

        # BASIC, INTIAL STRATEGY (PROBABLY ONLY GOOD FOR ISOLATED ENEMIES)
        # Notably, it does not consider clusters of enemy ants, pretending
        # enemy ants are always isolated.

        attack_mask = world.attack_mask
        get_legal_moves = world.get_legal_moves
        for enemy, engageable in enemy_engageable.items():
            own_moves = {}
            enemy_moves = get_legal_moves(enemy)
            for own in engageable:
                own_moves[own] = {}
                # Here's the key-passage: find out how each move would score
                # relative to the opponent's one.
                for odest, odir in get_legal_moves(own):
                    for edest, edir in enemy_moves:
                        if odest in world.get_in_attackradius(edest):
                            try:
                                own_moves[own][odest, odir].append((edest,
                                                                    edir))
                            except KeyError:
                                own_moves[own][odest, odir] = [(edest, edir)]
            if RUNS_LOCALLY:
                log.debug('# OWN MOVES FOR ENEMY %s : %s' % (enemy, own_moves))
                overlay.show_dangers(own_moves)
        #if RUNS_LOCALLY:
            #overlay.show_battlegroups(own_engageable, enemy_engageable)


        # - Wait for 2 own engageable by 1 enemy, else goback.
        # - Try to find which moves of each own ants would result in the same
        #   (enemy, movement) tuples.

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

    def _get_fighters(self):
        '''
        Find all those ants that are close enought to an enemy to engage during
        the following turn.
        '''
        # Identify attackrange + 1 (A1) or attackrange + 2 (A2) tiles
        # Deteach from the main scent mechanism all those ants that are on
        # either A1 or A2 tiles
