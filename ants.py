#!/usr/bin/env python

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file parses the game engine output and contains a game state class.
It is based off the starter package available online.
'''

import sys
import traceback
import random
import time
from numpy import array, zeros, int8, minimum


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

# MAP DESCRIPTORS
WATER = -1
UNEXPLORED = 0
LAND = 1
OWN_HILL = 50  # Enemy hills are "OWN_HILL + owner"

# VIEW DESCRIPTORS
VISIBLE = True
FOGGED = False

# HUD DESCRIPTORS
# The basic idea is to have the values sorted in a way that facilitate testing
# through the minor and major (<, >) operators. As a rule of thumb, the lower
# the number, the most attractive the target.
FOOD = 100
OWN_ANT = 10    # Other players' ants are 11, 12... [OWN_ANTS + owner]
OWN_DEAD = -10  # Other players' ants are -11, -12... [OWN_ANTS - owner]
# HILLS: constants defined for map are used

# This is just to prevent myself from screwing up!
assert WATER != UNEXPLORED != LAND != OWN_HILL != VISIBLE != FOGGED != \
       FOOD != OWN_ANT != OWN_DEAD
assert WATER < UNEXPLORED < min(LAND, OWN_HILL)

AIM = {'n': array((0, -1), int8),
       'e': array((1, 0), int8),
       's': array((0, 1), int8),
       'w': array((-1, 0), int8)}

class Ants():

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
        # Store received data
        data = [line.split() for line in data]
        for k, v in data:
            setattr(self, k, int(v))
        self.map_size = array((self.cols, self.rows))
        # Generate map and hud
        self.map = zeros(self.map_size, dtype=int8)
        self.view = zeros(self.map_size, dtype=bool)
        self.hud = zeros(self.map_size, dtype=int8)
        # Generate the field-of-view mask
        mx = int(self.viewradius2**0.5)
        side = mx * 2 + 1
        self.view_mask = zeros((side, side), dtype=bool)
        for d_row in range(-mx, mx+1):
            for d_col in range(-mx, mx+1):
                d = d_row**2 + d_col**2
                if d <= self.viewradius2:
                    self.view_mask[mx+d_col][mx+d_row] = VISIBLE
        self.viewradiusint = mx

    def update(self, data):
        '''
        Parse engine input and update the game state.
        '''
        # start timer
        self.turn_start_time = time.clock()

        # reset turn variables
        self.hud *= FOGGED
        self.food = []
        self.own_ants = []
        self.own_hills = []
        self.own_deads = []
        self.enemy_ants = []
        self.enemy_hills = []
        self.enemy_deads = []

        # update map and create new ant and food lists
        for line in data:
            tokens = line.split()
            if len(tokens) >= 3:
                row = int(tokens[1])
                col = int(tokens[2])
                if tokens[0] == 'w':
                    self.map[col][row] = WATER
                elif tokens[0] == 'f':
                    self.hud[col][row] = FOOD
                    self.food.append((col, row))
                else:
                    owner = int(tokens[3])
                    if tokens[0] == 'a':
                        self.hud[col][row] = OWN_ANT + owner
                        if not owner:  # owner == 0 --> player's ant
                            self.own_ants.append(array((col, row)))
                            #TODO: viewmask here
                        else:
                            self.enemy_ants.append(array((col, row)))
                    elif tokens[0] == 'd':
                        # food could spawn on a spot where an ant just died
                        # don't overwrite the space on the hud.
                        self.hud[col][row] = self.hud[col][row] or DEAD
                        # but always add to the dead list
                        if not owner:  # owner == 0 --> player's ant
                            self.own_deads.append(array((col, row)))
                        else:
                            self.enemy_deads.append((array(col, row)))
                    elif tokens[0] == 'h':
                        if not owner:  # owner == 0 --> player's hill
                            self.own_hills.append(array((col, row)))
                        else:
                            self.enemy_hills.append(array((col, row)))

    def issue_order(self, order):
        '''
        Issue an order by writing the proper ant location and direction.
        '''
        (row, col), direction = order
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
        elapsed = int(1000 * (time.clock() - self.turn_start_time))
        return self.turntime - elapsed

    def manhattan(self, loc1, loc2):
        '''
        Return the distance between two location in taxicab geometry.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        absolute = abs(loc1 - loc2)
        modular = self.map_size - absolute
        return sum(minimum(absolute, modular))

    def destination(self, loc, direction):
        '''
        Return target location given the direction.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        return (loc + AIM[direction]) % self.map_size

    def direction(self, loc1, loc2):
        '''
        Return a list (0, 1 or 2 elements) containing the direction to reach
        loc2 from loc1 in the shortest manhattan distance.
        '''
        row1, col1 = loc1
        row2, col2 = loc2
        height2 = self.rows//2
        width2 = self.cols//2
        d = []
        if row1 < row2:
            if row2 - row1 >= height2:
                d.append('n')
            elif row2 - row1 <= height2:
                d.append('s')
        if row2 < row1:
            if row1 - row2 >= height2:
                d.append('s')
            elif row1 - row2 <= height2:
                d.append('n')
        if col1 < col2:
            if col2 - col1 >= width2:
                d.append('w')
            elif col2 - col1 <= width2:
                d.append('e')
        if col2 < col1:
            if col1 - col2 >= width2:
                d.append('e')
            elif col1 - col2 <= width2:
                d.append('w')
        return d


def run(bot):
    '''
    Parse input, update game state and call the bot classes do_turn method.
    '''
    ants = Ants()
    map_data = []
    while(True):
        try:
            # This is where input validation should happen (modify case,
            # strip whitespaces, skip empty lines...)
            current_line = sys.stdin.readline().strip().lower()
            if not current_line:
                continue  #skip empty lines
            if current_line == 'ready':
                ants.setup(map_data)
                bot.do_setup(ants)
                ants.finish_turn()
                map_data = []
            elif current_line == 'go':
                ants.update(map_data)
                bot.do_turn(ants)
                ants.finish_turn()
                map_data = []
            else:
                map_data.append(current_line)
        except EOFError:
            break
        except KeyboardInterrupt:
            raise
        except:
            # don't raise error or return so that bot attempts to stay alive
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

