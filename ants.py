#!/usr/bin/env python3

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file parses the game engine output and contains a game state class.
It is based off the starter package available online.
'''

import sys
import traceback
import random
import time
from collections import defaultdict


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


MY_ANT = 0
ANTS = 0
DEAD = -1
LAND = -2
FOOD = -3
WATER = -4

PLAYER_ANT = 'abcdefghij'
HILL_ANT = string = 'ABCDEFGHI'
PLAYER_HILL = string = '0123456789'
MAP_OBJECT = '?%*.!'
MAP_RENDER = PLAYER_ANT + HILL_ANT + PLAYER_HILL + MAP_OBJECT

AIM = {'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}
RIGHT = {'n': 'e',
         'e': 's',
         's': 'w',
         'w': 'n'}
LEFT = {'n': 'w',
        'e': 'n',
        's': 'e',
        'w': 's'}
BEHIND = {'n': 's',
          's': 'n',
          'e': 'w',
          'w': 'e'}

class Ants():

    '''
    This class act as a middle layer between the bot AI and the game engine.

    It contains the state of the game (including a representation of the world)
    and some helper functions to be used by the bot directly.
    '''

    def __init__(self):
        self.cols = None
        self.rows = None
        self.map = None
        self.hill_list = {}
        self.ant_list = {}
        self.dead_list = defaultdict(list)
        self.food_list = []
        self.turntime = 0
        self.loadtime = 0
        self.turn_start_time = None
        self.vision = None
        self.viewradius2 = 0
        self.attackradius2 = 0
        self.spawnradius2 = 0
        self.turns = 0

    def setup(self, data):
        '''
        Parse the initial input, containing data about the map size, the
        visibility range, and so on...
        '''
        for line in data.split('\n'):
            if len(line) > 0:
                tokens = line.split()
                key = tokens[0]
                if key == 'cols':
                    self.cols = int(tokens[1])
                elif key == 'rows':
                    self.rows = int(tokens[1])
                elif key == 'player_seed':
                    random.seed(int(tokens[1]))
                elif key == 'turntime':
                    self.turntime = int(tokens[1])
                elif key == 'loadtime':
                    self.loadtime = int(tokens[1])
                elif key == 'viewradius2':
                    self.viewradius2 = int(tokens[1])
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])
                elif key == 'turns':
                    self.turns = int(tokens[1])
        self.map = [[LAND for col in range(self.cols)]
                    for row in range(self.rows)]
        self._set_view_mask()

    def update(self, data):
        '''
        Parse engine input and update the game state.
        '''
        # start timer
        self.turn_start_time = time.clock()

        # reset vision
        self.vision = None

        # clear hill, ant and food data
        self.hill_list = {}
        for row, col in self.ant_list.keys():
            self.map[row][col] = LAND
        self.ant_list = {}
        for row, col in self.dead_list.keys():
            self.map[row][col] = LAND
        self.dead_list = defaultdict(list)
        for row, col in self.food_list:
            self.map[row][col] = LAND
        self.food_list = []

        # update map and create new ant and food lists
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                if len(tokens) >= 3:
                    row = int(tokens[1])
                    col = int(tokens[2])
                    if tokens[0] == 'w':
                        self.map[row][col] = WATER
                    elif tokens[0] == 'f':
                        self.map[row][col] = FOOD
                        self.food_list.append((row, col))
                    else:
                        owner = int(tokens[3])
                        if tokens[0] == 'a':
                            self.map[row][col] = owner
                            self.ant_list[(row, col)] = owner
                        elif tokens[0] == 'd':
                            # food could spawn on a spot where an ant just died
                            # don't overwrite the space unless it is land
                            if self.map[row][col] == LAND:
                                self.map[row][col] = DEAD
                            # but always add to the dead list
                            self.dead_list[(row, col)].append(owner)
                        elif tokens[0] == 'h':
                            owner = int(tokens[3])
                            self.hill_list[(row, col)] = owner

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

    def my_hills(self):
        '''
        Return location of player's hills.
        '''
        return [loc for loc, owner in self.hill_list.items()
                    if owner == MY_ANT]

    def enemy_hills(self):
        '''
        Return location and owner of opponents' hills.
        '''
        return [(loc, owner) for loc, owner in self.hill_list.items()
                    if owner != MY_ANT]

    def my_ants(self):
        '''
        Return a list of all player's ants.
        '''
        return [(row, col) for (row, col), owner in self.ant_list.items()
                    if owner == MY_ANT]

    def enemy_ants(self):
        '''
        Return a list of (location, owner) for all visible enemy ants.
        '''
        return [((row, col), owner)
                    for (row, col), owner in self.ant_list.items()
                    if owner != MY_ANT]

    def food(self):
        '''
        Return a list of all food locations.
        '''
        return self.food_list[:]

    def passable(self, loc):
        '''
        Return True if the location is free to walk on it (=no water).
        '''
        row, col = loc
        return self.map[row][col] > WATER

    def unoccupied(self, loc):
        '''
        Return True if no ants are at the location.
        '''
        row, col = loc
        return self.map[row][col] in (LAND, DEAD)

    def destination(self, loc, direction):
        '''
        Return target location given the direction. Wrap/warp correctly.
        '''
        row, col = loc
        d_row, d_col = AIM[direction]
        return ((row + d_row) % self.rows, (col + d_col) % self.cols)

    def manhattan(self, loc1, loc2):
        '''
        Return the distance between two location in taxicab geometry.
        '''
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row + d_col

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

    def visible(self, loc):
        '''
        Return which squares are visible to the given player.
        '''
        if self.vision == None:
            # set all spaces as not visible
            self.vision = [[False]*self.cols for row in range(self.rows)]
            # loop through ants and set squares around them as visible
            for ant in self.my_ants():
                a_row, a_col = ant
                for v_row, v_col in self.vision_offsets_2:
                    self.vision[a_row+v_row][a_col+v_col] = True
        row, col = loc
        return self.vision[row][col]

    def render_text_map(self):
        '''
        Return a pretty string representing the map.
        '''
        tmp = ''
        for row in self.map:
            tmp += '# %s\n' % ''.join([MAP_RENDER[col] for col in row])
        return tmp

    def _set_view_mask(self):
        '''
        Precalculate a 'mask' of tiles that define the view field of an ant.
        '''
        self.vision_offsets_2 = []
        mx = int(self.viewradius2**0.5)
        for d_row in range(-mx, mx+1):
            for d_col in range(-mx, mx+1):
                d = d_row**2 + d_col**2
                if d <= self.viewradius2:
                    self.vision_offsets_2.append((
                        d_row % self.rows - self.rows,
                        d_col % self.cols - self.cols
                    ))


def run(bot):
    '''
    Parse input, update game state and call the bot classes do_turn method.
    '''
    ants = Ants()
    map_data = ''
    while(True):
        try:
            current_line = sys.stdin.readline().rstrip()
            if current_line == 'ready':
                ants.setup(map_data)
                bot.do_setup(ants)
                ants.finish_turn()
                map_data = ''
            elif current_line == 'go':
                ants.update(map_data)
                bot.do_turn(ants)
                ants.finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'
        except EOFError:
            break
        except KeyboardInterrupt:
            raise
        except:
            # don't raise error or return so that bot attempts to stay alive
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

