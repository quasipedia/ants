#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file parses the game engine output and contains a game state class.
'''

import sys
import time

from numpy import array, zeros, ones, int8, minimum, where, roll
from numpy import abs as np_abs


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# MAP ENTITY DESCRIPTORS
# The arragement of values is such that all but the "enemy dead ant" case can
# be checked with equality (entity == x) or major/minor. Enemy ants requires a
# double check (minor of ... and major of...).
OWN_HILL = -10  # Other players' ants are -11, -12... [OWN_HILL - owner]
WATER = -1
LAND = 0
FOOD = 1
OWN_DEAD = 10   # Other players' ants are 11, 12... [OWN_DEAD + owner]
OWN_ANT = 100   # Other players' ants are 101, 102... [OWN_ANT + owner]

# ADDITIONAL SCENT ENTITY DESCRIPTORS
# These desciptors are not to be used on the map, but only for calculating
# the scent values or other kind of tests
EMPTY = -666
ENEMY_HILL = -11
ENEMY_DEAD = 11
ENEMY_ANT = 101

# ENTITY SCENTS
SCENTS = {ENEMY_HILL : 300,
          OWN_DEAD : 300,
          FOOD : 200,
          WATER : 0,
          ENEMY_ANT: 100,
          OWN_HILL : 0,
          OWN_ANT: 0}

# SCENT OF UNSEEN TERRITORY
LAST_SEEN_COUNTER_STEP = 1
INITIAL_LAST_SEEN_COUNTER = 30

# MAP INDEXES
ENTITY_ID = 0
LAST_SEEN_COUNTER = 1
SCENT = 2

DIRECTIONS = {'n': array((0, -1), int8),
              'e': array((1, 0), int8),
              's': array((0, 1), int8),
              'w': array((-1, 0), int8)}


class World():

    '''
    This class act as a middle layer between the bot AI and the game engine.

    It contains the state of the game (including a representation of the world)
    and some helper functions to be used by the bot directly.

      - map  : a representation of the terrain features
      - view : a representation of the viewable area of the map
      - hud  : [head-up display] a representation of tactical targets
    '''

    def setup(self, data):
        '''
        Parse the initial input, containing data about the map size, the
        visibility range, and so on... Known keys passed in the intial input:
          - loadtime       # in milliseconds, time given for bot to start up
          - turntime       # in milliseconds, time given to the bot each turn
          - rows           # number of rows in the map
          - cols           # number of columns in the map
          - turns          # maximum number of turns in the game
          - viewradius2    # view radius squared
          - attackradius2  # battle radius squared
          - spawnradius2   # food gathering radius squared (unfortunate name)
          - player_seed    # seed for random number generator
        '''
        # start timer
        self.turn_start_time = time.time()

        # Store received data
        data = [line.split() for line in data]
        for k, v in data:
            setattr(self, k, int(v))
        self.world_size = array((self.cols, self.rows))
        # Generate the empty map - the final array contains:
        # entity_ID, last_seen counter, scent amount
        self.map = zeros((self.cols, self.rows, 3), dtype=float)
        self.map[..., LAST_SEEN_COUNTER] = INITIAL_LAST_SEEN_COUNTER
        # Generate the field-of-view mask
        self.viewradiusint = int(self.viewradius2**0.5)
        mx = self.viewradiusint  # for speed in following loop
        side = mx * 2 + 1
        tmp = zeros((side, side), dtype=bool)
        for d_row in range(-mx, mx+1):
            for d_col in range(-mx, mx+1):
                if d_row**2 + d_col**2 <= self.viewradius2:
                    tmp[mx+d_col][mx+d_row] = True
        # At this point `tmp` contains a representation of the field of view,
        # what we want is coordinate offsets from the ant position
        tmp = where(tmp)
        self.view_mask = tuple([value - mx for value in tmp])
        # Initialise hills set. This happens here as they are not reset at each
        # update.
        self.own_hills = set([])
        self.enemy_hills = set([])

    def _update(self, data):
        '''
        Parse engine input, updating the map.
        '''
        # start timer
        self.turn_start_time = time.time()

        # eliminate all temporay objects, keep water + hills. [cfr. entity ID]
        self.map[:, :, ENTITY_ID][self.map[:, :, ENTITY_ID] > LAND] = LAND

        # reset turn variables - turn variables are really just redoundant,
        # given that one could poll the map instead, but they are convenient
        # and CPU-wise cheap.
        self.food = []
        self.own_ants = []
        self.enemy_ants = []
        self.own_dead = []
        self.enemy_dead = []
        turn_own_hills = []
        turn_enemy_hills = []

        # parse input lines
        for line in data:
            tokens = line.split()
            if len(tokens) >= 3:
                row = int(tokens[1])
                col = int(tokens[2])
                if tokens[0] == 'w':
                    self.map[col][row][ENTITY_ID] = WATER
                elif tokens[0] == 'f':
                    self.map[col][row][ENTITY_ID] = FOOD
                    self.food.append((col, row))
                else:
                    owner = int(tokens[3])
                    if tokens[0] == 'a':
                        self.map[col][row][ENTITY_ID] = OWN_ANT + owner
                        if not owner:  # owner == 0 --> player's ant
                            self.own_ants.append(array((col, row)))
                        else:
                            self.enemy_ants.append(array((col, row)))
                    elif tokens[0] == 'd':
                        # food could spawn on a spot where an ant just died
                        # don't overwrite the space on the hud.
                        self.map[col][row][ENTITY_ID] = \
                            self.map[col][row][ENTITY_ID] or OWN_DEAD + owner
                        # but always add to the dead list
                        if not owner:  # owner == 0 --> player's ant
                            self.own_dead.append(array((col, row)))
                        else:
                            self.enemy_dead.append(array((col, row)))
                    elif tokens[0] == 'h':
                        # Hills are not added to the map as they might have an
                        # ant on top, and the ant gets priority.
                        if not owner:  # owner == 0 --> player's hill
                            turn_own_hills.append((col, row))
                        else:
                            turn_enemy_hills.append((col, row))
            elif tokens[0] == 'turn':
                self.turn = int(tokens[1])

        # increment the last view counter for all the map, then use view_mask
        # to reset it where land is visible
        self.map += 0, LAST_SEEN_COUNTER_STEP, 0
        for loc in self.own_ants:
            self.map[:, :, LAST_SEEN_COUNTER][[(axis + loc[i]) % \
                    self.world_size[i] for i, axis in \
                    enumerate(self.view_mask)]] = 0

        # hills management - hills need to be managed in a special way given
        # that they might have an ant on top.
        for set_, list_, entity in ((self.own_hills, turn_own_hills, OWN_HILL),
                        (self.enemy_hills, turn_enemy_hills, ENEMY_HILL)):
            # eliminate hills whose destruction has been positively confirmed
            # use a copy of the set to prevent modifying it's size during
            # iteration.
            for loc in set_.copy():
                if self.is_visible(loc) and loc not in list_:
                    set_.remove(loc)
            # add the new ones
            for loc in list_:
                set_.add(loc)
            # add hills on the map where the spot isn't overlapping anything
            for loc in set_:
                col, row = loc
                if self.map[col, row, ENTITY_ID] == LAND:
                    self.map[col, row, ENTITY_ID] = entity

        # perform diffusion
        self.diffuse()

    def diffuse(self, steps=None):
        '''
        Diffuse scents over the map. Iterate ``step`` times. Default to the
        square of the view radius.
        '''
        if steps == None:
            steps = 100
        # RESET THE SCENTS
        self.map[:, :, SCENT] *= 0

        # CREATE THE STARTING MASK (emitters' own smell)
        # 0. empty mask
        scent_mask = ones(self.world_size) * EMPTY
        # 1. smelly entities
        for entity in SCENTS:
            scent_mask[self.map[:, : , ENTITY_ID] == entity] = SCENTS[entity]
        # 2. out-of-sight land
        unseen_idx = (self.map[:, :, ENTITY_ID] == LAND) & \
                     (self.map[:, :, LAST_SEEN_COUNTER] > 0)
        scent_mask[unseen_idx] = self.map[unseen_idx, LAST_SEEN_COUNTER]
        idx = scent_mask != EMPTY

        # CREATE THE BLITTING LAYERS
        single_layer = zeros(self.world_size)
        single_layer[idx] = scent_mask[idx]  # seed layer with emitters
        layers = [single_layer, single_layer.copy()]
        toggler = False

        # DIFFUSE!
        for step in range(steps):
            toggler = not toggler
            source = layers[toggler]
            dest = layers[not toggler]
            dest *= 0
            # calculate the scent for each tile
            for amount, axis in ((1, 0), (1, 1), (-1, 0), (-1, 1)):
                dest += roll(source, amount, axis=axis)  #may be cached for sp!
            dest /= 4
            # blit the emitters map
            dest[idx] = scent_mask[idx]
        # transfer back to world map
        self.map[:, :, SCENT] = dest

    def is_visible(self, loc):
        '''
        Return True if the location is currently visible.
        '''
        return 0 == self.map[loc[0], loc[1], LAST_SEEN_COUNTER]

    def issue_order(self, order):
        '''
        Issue an order by writing the proper ant location and direction.
        '''
        (col, row), direction = order
        # note that game API wants row before col!
        sys.stdout.write('o %s %s %s\n' % (row, col, direction))

    def finish_turn(self):
        '''
        Finish the turn by writing the go line.
        '''
        sys.stdout.write('go\n')
        sys.stdout.flush()

    def time_remaining(self):
        '''
        Milliseconds before turn end.
        '''
        elapsed = int(1000 * (time.time() - self.turn_start_time))
        reference = self.turntime if self.turn > 0 else self.loadtime
        return reference - elapsed

    def manhattan(self, loc1, loc2):
        '''
        Return the distance between two location in taxicab geometry.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        absolute = np_abs(loc1 - loc2)  # slightly faster than abs()
        modular = self.world_size - absolute
        return sum(minimum(absolute, modular))  # slightly faster than a.sum()

    def destination(self, loc, direction):
        '''
        Return target location given the direction.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        return (loc + DIRECTIONS[direction]) % self.world_size

    def get_scent_strengths(self, loc):
        '''
        Return a list of tuples (scent, destination, direction) sorted
        according to scent intensity.
        '''
        result = []
        for direction, offset in DIRECTIONS.items():
            destination = tuple((loc + offset) % self.world_size)
            scent = self.map[..., SCENT][destination]
            result.append((scent, destination, direction))
        return sorted(result, reverse=True)
