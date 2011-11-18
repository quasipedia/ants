#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file parses the game engine output and contains a game state class.

This module/class exposes to the main bot:
- A map of the world (intended to provide an object to perform spacial analysis
  like "object X is in range of object Y" and so on)
- A series of dictionaries containing the various world entities (these are
  mostly intended to perform lookups and iterations)
- Several utility functions to issue orders, perform proximity checks, diffuse
  the hormons, etc...

The MAP is a 3 dimensional numpy array, in which the first two axis are the
X, Y coordinates of the world, and the third dimension contains a stack of
layers, where 0 means "empty" and any other value means "something is here".
This structure was chosed to allow:
- different entities to be stacked (food can spawn on a dead ant, for example)
- nonzero tests
- easy multiplication of the scent
The layers in the map are:
- water
- onw hills
- enemy hills
- food
- own ants
- enemy ants
- own dead
- enemy dead
- unseen counter
- exploration hormon value
- food hormon value
- fighting hormon value
All layers can contain a value >=0, with 0 == no entity of that type there and
the other values being used as multipliers for the scent.
    Given that contest organisers assert the max size of a map is be 200x200,
and that the numpy array is float64, and has 12 layers, the overall size of the
map can reach a maximum of 64/8/1024 * 12 * 200 * 200 = 3.75 Mbytes.
'''

import sys
from time import time

from numpy import array, zeros, ones, int8, minimum, where, roll, \
                  logical_and, nonzero, isnan
from numpy import abs as np_abs
from numpy import nan as np_nan
from numpy import sum as np_sum

from utils import *
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


# FADINGS
# The smell of certain entities (corpses, unseen food...) diminishes over time
# these values indicate in how many turns the scent will have totally gone.
FADING_OWN_DEAD = 1.0 / 10
FADING_ENEMY_DEAD = 1.0 / 1
FADING_UNSEEN_FOOD = 1.0 / 10
UNSEEN_LAND_STEP = 1

# SCENT MASK INDEXES
MASK_H_EXPLORE = 0
MASK_H_HARVEST = 1
MASK_H_FIGHT = 2

# MAP INDEXES - (layer of the map where info about a given entity is stored)
WATER = 0
OWN_HILLS = 1
ENEMY_HILLS = 2
FOOD = 3
OWN_ANTS = 4
ENEMY_ANTS = 5
OWN_DEAD = 6
ENEMY_DEAD = 7
UNSEEN_COUNTER = 8  # this MUST be just before the hormons!!!
H_EXPLORE = 1 + UNSEEN_COUNTER + MASK_H_EXPLORE
H_HARVEST = 1 + UNSEEN_COUNTER + MASK_H_HARVEST
H_FIGHT = 1 + UNSEEN_COUNTER + MASK_H_FIGHT

# ENTITY SCENTS
# Scents are power of four (or zero). Since scent intensity decreases in a
# straight line of ¼ of its intensity, using it is possible to say that the
# scent of an object whose smell is 4**4 is at 4 tiles distance the same of an
# object 4**1 at 1 tile distance.
#    Note that 0 means that that entity is "transparent" to that particular
# hormone, while OPAQUE means that it will remove any scent from that tile.
# this allows to sum scents from various emitters.
#    Scents are lists, each list element describe a different hormone. The
# order in this list is EXPLORE, FOOD, FIGHT.
OPAQUE = np_nan  # Not a Number!
TRANSPARENT = -1  # Used in _get_scent_mask()
SCENTS = {
    WATER : array((OPAQUE, OPAQUE, OPAQUE), dtype=float),
    UNSEEN_COUNTER : array((4**1, 0, 0), dtype=float),
    OWN_HILLS: array((OPAQUE, OPAQUE, 0), dtype=float),
    ENEMY_HILLS : array((4 ** 6, 0, 4 ** 6), dtype=float),
    FOOD : array((0, 4 ** 3, 0), dtype=float),
    OWN_ANTS: array((OPAQUE, OPAQUE, OPAQUE), dtype=float),
    ENEMY_ANTS: array((4 ** 2, OPAQUE, 4 ** 2), dtype=float),
    OWN_DEAD: array((4 ** 5, OPAQUE, 4 ** 5), dtype=float),
    ENEMY_DEAD: array((0, 0, 0), dtype=float),
}

# ANT ROLES
EXPLORER = 0
HARVESTER = 1
ATTACKER = 2

# HILL STATUS
JUST_SEEN = 0
PREVIOUSLY_SEEN = 1
INFERRED = 2
RAZED = 3

# DIRECTIONS
DIRECTIONS = {'n': array((0, -1), int8),
              'e': array((1, 0), int8),
              's': array((0, 1), int8),
              'w': array((-1, 0), int8)}


class World():

    '''
    The only class provided by the module. It is assumed only one instantiation
    of this class will be performed. See module documentation for details.
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
        # Initialise a few variables
        self.world_size = (self.cols, self.rows)
        self.turns_left = self.turns
        # Generate the empty map
        # ATTENTION TO THE HARDCODED THIRD DIMENSION!!
        self.map = zeros((self.cols, self.rows, 12), dtype=float)
        # Compute radii
        self.attackradiusint = int(self.attackradius2**0.5)
        self.battleradiusint = int(self.attackradius2**0.5 + 2)
        self.spawnradiusint = int(self.spawnradius2**0.5)
        self.viewradiusint = int(self.viewradius2**0.5)
        # Generate the field-of-view and attack-range masks
        self.view_mask = get_circular_mask(self.viewradius2)
        self.attack_mask = get_circular_mask(self.attackradius2)
        self.movement_mask = get_circular_mask(1)
        # Initialise dictionaries for those temporary but non-moveable entities
        # whose visibility may change.
        self.food = {}
        self.own_hills = {}
        self.enemy_hills = {}
        self.own_dead = {}
        self.enemy_dead = {}

        if RUNS_LOCALLY:
            log.info('####### NEW GAME! ########')
            log.info('####### STARTUP DATA : %s' % data)

    def _update(self, data):
        '''
        Parse engine input, updating the map.
        '''
        # START TIMER
        self.turn_start_time = time()

        if RUNS_LOCALLY:
            log.info('## TURN %03d ##' % self.turn)

        # RESET the MAP - only water is an immutable characteristic of the map
        self.map[..., WATER + 1:] = 0

        # RESET TURN VARIABLES - turn variables are really just redoundant,
        # given that one could poll the map instead, but they are convenient
        # and CPU-wise cheap.
        self.own_ants = {}
        self.enemy_ants = {}

        # The rest of the update procedure has been devided in other methods
        # to facilitate code managment and profiling.
        self._parse_input_lines(data)
        self._update_view_counter()
        self._update_hills()
        self._update_faders()

    def diffuse(self, abs_left=None, perc_left=None):
        '''
        Diffuse scents over the map. Diffusion progresses until the time left
        to the end of the turn equals ``abs_left``. Specify the time that must
        be left at the end of the diffusion process by either its absolute
        value in ms or as percentage of the turn length.
        - abs_limit  : milliseconds to leave after diffusion
        - perc_limit : percentage of turn time to leave after diffusion
        '''
        # reset the scents
        self.map[:, :, H_EXPLORE:] *= 0
        # fix the limit of diffusion
        hard_time_limit, max_diffusion_steps = \
            self._get_diffusion_limits(abs_left, perc_left)
        # creating the starting mask (emitters' own smell)
        scent_mask = self._get_scent_mask()
        idx = scent_mask >= 0

        # CREATE THE BLITTING LAYERS
        single_layer = zeros((self.cols, self.rows, 3), dtype=float)
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
        self.map[:, :, H_EXPLORE:] = dest
        if RUNS_LOCALLY:
            log.info('DIFFUSE : %d passes, %d needed' %
                (counter, max_diffusion_steps))

    def is_tile_visible(self, loc):
        '''
        Return True if the location is currently visible.
        '''
        return 0 == self.map[loc[0], loc[1], UNSEEN_COUNTER]

    def is_tile_passable(self, loc):
        '''
        Return True if location is not occupied by an obstacle.
        '''
        return 0 == self.map[loc][WATER] == self.map[loc][OWN_ANTS] \
                 == self.map[loc][FOOD] == self.map[loc][ENEMY_ANTS]

    def get_stuff_in_sight(self, loc, layer):
        '''
        Return the location of all the entities of layer `layer` that are
        visible from location `loc`
        '''
        m = self.map
        visible_idx = [(axis + loc[i]) % self.world_size[i] for i, axis in \
                       enumerate(self.view_mask)]
        # For the following lines see: http://goo.gl/zY6VD
        transposed = array(visible_idx).T
        return transposed[where(m[visible_idx][..., layer])[0]]

    def get_engageable(self, ant):
        '''
        Returns a list of enemy ants that might be engaged the following turn
        (battle radius = attack radius + 2).
        '''

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

    def get_scent_strengths(self, loc, hormone):
        '''
        Return a list of tuples (scent, destination, direction) sorted
        according to scent intensity. The returned value of `scent` refers to
        the intensity of `hormone`.
        '''
        result = []
        for direction, offset in DIRECTIONS.items():
            destination = tuple((loc + offset) % self.world_size)
            scent = self.map[..., hormone][destination]
            result.append([scent, destination, direction])
        return sorted(result, reverse=True)

    def _parse_input_lines(self, data):
        '''
        Parse the data received by the game engine.
        '''
        for line in data:
            tokens = line.split()
            if len(tokens) >= 3:
                row = int(tokens[1])
                col = int(tokens[2])
                if tokens[0] == 'w':
                    self.map[col][row][WATER] = True
                elif tokens[0] == 'f':
                    self.food[(col, row)] = 1
                else:
                    owner = int(tokens[3])
                    if tokens[0] == 'a':
                        if not owner:  # owner == 0 → player's ant
                            self.map[col][row][OWN_ANTS] = 1
                            self.own_ants[(col, row)] = EXPLORER
                        else:
                            self.map[col][row][ENEMY_ANTS] = owner
                            self.enemy_ants[(col, row)] = owner
                    elif tokens[0] == 'd':
                        if not owner:  # owner == 0 → player's dead
                            self.own_dead[(col, row)] = 1
                        else:
                            self.enemy_dead[(col, row)] = [1, owner]
                    elif tokens[0] == 'h':
                        if not owner:  # owner == 0 → player's hill
                            self.own_hills[(col, row)] = JUST_SEEN
                        else:
                            self.enemy_hills[(col, row)] = [JUST_SEEN, owner]
            elif tokens[0] == 'turn':
                self.turn = int(tokens[1])
                self.turns_left = self.turns - self.turn

    def _update_view_counter(self):
        '''
        Increment the `last view counter` for all the map, then use view_mask
        to reset it where land is visible.
        '''
        self.map[..., UNSEEN_COUNTER] += UNSEEN_LAND_STEP
        for loc in self.own_ants:
            self.map[:, :, UNSEEN_COUNTER][[(axis + loc[i]) % \
                    self.world_size[i] for i, axis in \
                    enumerate(self.view_mask)]] = 0

    def _update_hills(self):
        '''
        Hills require a special managment:
        - they need to remain on the map even if not seen.
        - the player needs to infer when they have been razed.
        - the player might infer their presence based on symmetry.
        '''
        # OWN HILLS
        hills = self.own_hills
        for hill, status in hills.items():
            if status == PREVIOUSLY_SEEN and self.is_tile_visible(hill):
                hills[hill] = RAZED
            elif status == JUST_SEEN:
                hills[hill] = PREVIOUSLY_SEEN
            if hills[hill] != RAZED:
                self.map[hill][OWN_HILLS] = 1
        # ENEMY HILLS - they have the owner too!
        hills = self.enemy_hills
        for hill, (status, owner) in hills.items():
            if status == PREVIOUSLY_SEEN and self.is_tile_visible(hill):
                hills[hill] = [RAZED, owner]
            elif status == JUST_SEEN:
                hills[hill] = [PREVIOUSLY_SEEN, owner]
            if hills[hill][0] != RAZED:
                self.map[hill][ENEMY_HILLS] = owner

    def _update_faders(self):
        '''
        Update all those entities that fade with time (unseen food, corpses...)
        '''
        # FOOD MANAGEMENT - food presence is signalled by the game engine every
        # time food is in sight. The smell of food that fell out of sight
        # gradully decays... Initial value is set to 1 by `_parse_input_lines`
        # every time the food is (re)seen.
        to_remove = []
        for loc, value in self.food.items():
            # remove unseen from too long and food that has been eaten
            if value <= 0 or (value < 1 and self.is_tile_visible(loc)):
                to_remove.append(loc)
            else:
                self.map[loc][FOOD] = value
                self.food[loc] -= FADING_UNSEEN_FOOD
        for loc in to_remove:
            del self.food[loc]
        # DEAD MANAGEMENT - dead need to be managed in a special way as
        # they are shown as input only during the turn after they have been
        # killed. We want contrarily to have their scent gradually fading post-
        # mortem, in order to attract more ants on the crime scene, if they
        # emit an hormone.
        to_remove = []
        for loc, value in self.own_dead.items():  # own dead
            if value <= 0:
                to_remove.append(loc)
            else:
                self.map[loc][OWN_DEAD] = value
                self.own_dead[loc] -= FADING_OWN_DEAD
        for loc in to_remove:
            del self.own_dead[loc]
        to_remove = []
        for loc, (value, owner) in self.enemy_dead.items():  # enemy dead
            if value <= 0:
                to_remove.append(loc)
            else:
                self.map[loc][ENEMY_DEAD] = value
                self.enemy_dead[loc][0] -= FADING_ENEMY_DEAD
        for loc in to_remove:
            del self.enemy_dead[loc]

    def _get_diffusion_limits(self, abs_left, perc_left):
        '''
        Return the limits for the diffusion process:
        - hard_time_limit : value of time.time() at which to stop processing
        - max_diffusion_steps : max number of diffusion steps to perform
        '''
        # EVALUATE WHEN TO STOP
        if abs_left == perc_left == None:
            perc_left = 0.25 if RUNS_LOCALLY else 0.15  #gives time to profile
        if abs_left is None:
            abs_left = self.turntime * perc_left
        hard_time_limit = self.turn_start_time + \
            (self.turntime - abs_left) / 1000.0
        # No ant would manage to reach a destination beyond max_diffusion_steps
        # Better scenario: straight path to an enemy ant, `5` is for prudence
        # only. I'm quite positive 1 or 2 should be enough...
        max_diffusion_steps = self.turns_left + \
            self.attackradiusint + 5
        return hard_time_limit, max_diffusion_steps

    def _get_scent_mask(self):
        '''
        Return a COLS x ROWS x HORMONES mask of scent emitters. This is used
        to initiate the diffusion process.
        '''
        map_ = self.map
        # initialise the mask
        scent_mask = zeros((self.cols, self.rows, 3), dtype=float)
        # cycle through all the layers that can contain emitters...
        for layer in (WATER, OWN_HILLS, ENEMY_HILLS, FOOD, OWN_ANTS,
                      ENEMY_ANTS, OWN_DEAD, ENEMY_DEAD, UNSEEN_COUNTER):
            # ...isolate those who have them...
            positions = nonzero(map_[..., layer])
            # ...and blit on the mask, in that position, their value multiplied
            # the standard scent for that entity!
            scent_mask[positions] += \
                map_[positions][..., layer].reshape(len(positions[0]), 1) \
                * SCENTS[layer]
        # here there is some magic: we used numpy's NaN as "OPAQUE" because
        # we wanted to be impossible to sum scents in that location. Now that
        # the mask is ready - though - we want the mask to explicitely say
        # "here goes no scent" where NaN was. Conversely, we want a way to
        # indicate where scent should be flowing indisturbed...
        scent_mask[scent_mask == 0] = -1
        scent_mask[isnan(scent_mask)] = 0
        return scent_mask
