#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file parses the game engine output and contains a game state class.
'''

import sys
from time import time

from numpy import array, zeros, ones, int8, minimum, where, roll, logical_and
from numpy import abs as np_abs

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
# Scents are power of four (or zero). Since scent intensity decreases in a
# straight line of ¼ of its intensity, using it is possible to say that the
# scent of an object whose smell is 4**4 is at 4 tiles distance the same of an
# object 4**1 at 1 tile distance.
SCENTS = {ENEMY_HILL : 4 ** 6,
          FOOD : 4 ** 3,
          ENEMY_ANT: 4 ** 2,
          WATER : 0,
          OWN_HILL: 0,
          OWN_ANT: 0}

# SCENT OF UNSEEN TERRITORY
LAST_SEEN_COUNTER_STEP = 1
INITIAL_LAST_SEEN_COUNTER = 1
UNSEEN_LAND_SMELL = 4 ** 1

# SCENT OF OWN DEAD
OWN_DEAD_FADING_COUNTER = 10
OWN_DEAD_SCENT = 4**5

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
        self.turn_start_time = time()

        # Store received data
        data = [line.split() for line in data]
        for k, v in data:
            setattr(self, k, int(v))
        self.world_size = array((self.cols, self.rows))
        self.turns_left = self.turns
        # Generate the empty map - the final array contains:
        # entity_ID, last_seen counter, scent amount
        self.map = zeros((self.cols, self.rows, 3), dtype=float)
        self.map[..., LAST_SEEN_COUNTER] = INITIAL_LAST_SEEN_COUNTER
        # Compute radii
        self.attackradiusint = int(self.attackradius2**0.5)
        self.spawnradiusint = int(self.spawnradius2**0.5)
        self.viewradiusint = int(self.viewradius2**0.5)
        # Generate the field-of-view mask
        mx = self.viewradiusint  # for speed in following loop
        self.view_mask = self._get_circular_mask(mx)
        # Generate the diffusion range for enemy hills.
        self.enemy_hill_diffusion_mask = self._get_circular_mask(2 * mx)
        # Initialise hills and own_dead list/sets. This happens here as they
        # are not reset at each update.
        self.own_hills = set([])
        self.enemy_hills = set([])
        self.own_dead = []
        if RUNS_LOCALLY:
            log.info('####### NEW GAME! ########')
            log.info('STARTUP DATA : %s' % data)


    def _update(self, data):
        '''
        Parse engine input, updating the map.
        '''
        # START TIMER
        self.turn_start_time = time()

        if RUNS_LOCALLY:
            log.info('** TURN %03d **' % self.turn)

        # ELIMINATE ALL TEMPORAY OBJECTS, keep water + hills. [cfr. entity ID]
        self.map[:, :, ENTITY_ID][self.map[:, :, ENTITY_ID] > LAND] = LAND

        # RESET TURN VARIABLES - turn variables are really just redoundant,
        # given that one could poll the map instead, but they are convenient
        # and CPU-wise cheap.
        self.food = []
        self.own_ants = []
        self.enemy_ants = []
        self.enemy_dead = []
        turn_own_dead = []
        turn_own_hills = []
        turn_enemy_hills = []

        # PARSE INPUT LINES
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
                            turn_own_dead.append(array((col, row)))
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
                self.turns_left = self.turns - self.turn

        # INCREMENT THE LAST VIEW COUNTER for all the map, then use view_mask
        # to reset it where land is visible
        self.map += 0, LAST_SEEN_COUNTER_STEP, 0
        for loc in self.own_ants:
            self.map[:, :, LAST_SEEN_COUNTER][[(axis + loc[i]) % \
                    self.world_size[i] for i, axis in \
                    enumerate(self.view_mask)]] = 0

        # HILLS MANAGEMENT - hills need to be managed in a special way given
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

        # OWN_DEAD MANAGEMENT - own_dead need to be managed in a special way as
        # they are shown as input only during the turn after they have been
        # killed. We want contrarily to have their scent gradually fading post-
        # mortem, in order to attract more ants on the crime scene.
        for idx, pair_ in enumerate(self.own_dead):
            pair_[1] -= 1
        self.own_dead = filter(lambda p : p[1] > 0, self.own_dead)
        for ant in turn_own_dead:
            self.own_dead.append([ant, OWN_DEAD_FADING_COUNTER])

        # PERFORM DIFFUSION
        self.diffuse()


    def diffuse(self, abs_left=None, perc_left=None):
        '''
        Diffuse scents over the map. Diffusion progresses until the time left
        to the end of the turn equals ``abs_left``. Specify the time that must
        be left at the end of the diffusion process by either its absolute
        value in ms or as percentage of the turn length.
        - abs_limit  : milliseconds to leave after diffusion
        - perc_limit : percentage of turn time to leave after diffusion
        '''
        # EVALUATE WHEN TO STOP
        if abs_left == perc_left == None:
            perc_left = 0.5 if RUNS_LOCALLY else 0.15  #gives time for profil
        if abs_left is None:
            abs_left = self.turntime * perc_left
        hard_time_limit = self.turn_start_time + \
            (self.turntime - abs_left) / 1000.0
        # No ant would manage to reach a destination beyond max_diffusion_steps
        # Better scenario: straight path to an enemy ant, `5` is for prudence
        # only. I'm quite positive 1 or 2 should be enough...
        max_diffusion_steps = self.turns_left + \
            self.attackradiusint + 5

        # RESET THE SCENTS
        self.map[:, :, SCENT] *= 0

        # CREATE THE STARTING MASK (emitters' own smell)
        # 0. empty mask
        scent_mask = ones(self.world_size) * EMPTY
        # 1. smelly entities
        for entity in SCENTS:
            scent_mask[self.map[:, : , ENTITY_ID] == entity] = SCENTS[entity]
        # 2. out-of-sight territory (note that the value is sum as the
        #    territory might be a hill of the corpse of an ant too)
        unseen_idx = (self.map[:, :, LAST_SEEN_COUNTER] > 0)
        to_sum_idx = logical_and(unseen_idx, scent_mask > EMPTY)
        scent_mask[to_sum_idx] += \
                self.map[to_sum_idx, LAST_SEEN_COUNTER] * UNSEEN_LAND_SMELL
        # 3. own dead. Values are also added
        for ant, counter in self.own_dead:
            tant = tuple(ant)
            existing_scent = scent_mask[tant]
            if existing_scent == EMPTY:
                scent_mask[tant] = 0
            scent_mask[tuple(ant)] = OWN_DEAD_SCENT * \
                                     float(counter) / OWN_DEAD_FADING_COUNTER
        # 4. define the indexes of the emitters
        idx = scent_mask != EMPTY

        # CREATE THE BLITTING LAYERS
        single_layer = zeros(self.world_size)
        single_layer[idx] = scent_mask[idx]  # seed layer with emitters
        layers = [single_layer, single_layer.copy()]
        toggler = False

        # DIFFUSE!
        counter = 0
        while time() < hard_time_limit and counter < max_diffusion_steps:
            counter += 1
            toggler = not toggler
            source = layers[toggler]
            dest = layers[not toggler]
            dest *= 0
            # calculate the scent for each tile
            for amount, axis in ((1, 0), (1, 1), (-1, 0), (-1, 1)):
                dest += roll(source, amount, axis=axis)
            dest *= 0.25
            # blit the emitters map
            dest[idx] = scent_mask[idx]
        # transfer back to world map
        self.map[:, :, SCENT] = dest
        if RUNS_LOCALLY:
            log.info('DIFFUSE : %d passes - %d more needed' %
                (counter, max_diffusion_steps - counter))

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
        if RUNS_LOCALLY:
            duration = int((time() - self.turn_start_time) * 1000)
            log.info('TURN DURATION : %d ms' % duration)
            if self.turn > 0:
                overlay.show_all()
        sys.stdout.write('go\n')
        sys.stdout.flush()

    def time_remaining(self):
        '''
        Milliseconds before turn end.
        '''
        elapsed = int(1000 * (time() - self.turn_start_time))
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

    def _get_circular_mask(self, radius):
        '''
        Return a tuple of two arrays, corresponding to the offsets of the tiles
        within radius relative to a given centre point (0, 0).
            These kind of masks are used to quickly find out which coordindates
        are within view or attack radii from an ant, or similar.
        '''
        side = radius * 2 + 1
        tmp = zeros((side, side), dtype=bool)
        for d_row in range(-radius, radius+1):
            for d_col in range(-radius, radius+1):
                if d_row**2 + d_col**2 <= self.viewradius2:
                    tmp[radius+d_col][radius+d_row] = True
        # At this point `tmp` contains a representation of the field of view,
        # what we want is coordinate offsets from the ant position
        tmp = where(tmp)
        self.view_mask = tuple([value - radius for value in tmp])
