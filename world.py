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
OWN_HILL = -10  # Other players' ants are -11, -12... [OWN_HILL - owner]
WATER = -1
LAND = 0
FOOD = 1
OWN_ANT = 10    # Other players' ants are 11, 12... [OWN_ANT + owner]
OWN_DEAD = 100  # Other players' ants are 101, 102... [OWN_DEAD + owner]

# VIEW_MASK
VISIBLE = True
FOGGED = False

AIM = {'n': array((0, -1), int8),
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
        # Store received data
        data = [line.split() for line in data]
        for k, v in data:
            setattr(self, k, int(v))
        self.map_size = array((self.cols, self.rows))
        # Generate map and hud
        self.map = zeros((self.cols, self.rows, 3), dtype=float)
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
        Parse engine input, updating the map.
        '''
        # start timer
        self.turn_start_time = time.time()

        # eliminate all temporay objects, keep water + hills.

        # reset turn variables
        self.food = []
        self.own_ants = []
        self.own_hills = []
        self.own_deads = []
        self.enemy_ants = []
        self.enemy_hills = []
        self.enemy_deads = []

        # parse input lines
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
                            self.own_world.append(array((col, row)))
                            #TODO: viewmask here
                        else:
                            self.enemy_world.append(array((col, row)))
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


        # eliminate hills whose destruction has been positively confirmed

        # use view_mask to reset the last_seen counter of visible land

    def diffuse(self, steps=None):
        '''
        Diffuse scents over the map. Iterate ``step`` times. Default to the
        square of the view radius.
        '''
        if steps == None:
            steps = world.viewradius2

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
        return self.turntime - elapsed

    def manhattan(self, loc1, loc2):
        '''
        Return the distance between two location in taxicab geometry.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        absolute = np_abs(loc1 - loc2)  # slightly faster than abs()
        modular = self.map_size - absolute
        return sum(minimum(absolute, modular))  # slightly faster than a.sum()

    def destination(self, loc, direction):
        '''
        Return target location given the direction.
        Uses the numpy arrays and wrap/warp correctly.
        '''
        return (loc + AIM[direction]) % self.map_size


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
                world.setup(map_data)
                bot.do_setup(ants)
                world.finish_turn()
                map_data = []
            elif current_line == 'go':
                world.update(map_data)
                world.diffuse()
                bot.do_turn(ants)
                world.finish_turn()
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

