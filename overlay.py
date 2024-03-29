#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contains what it takes to display AI status on the enhanced js viewer.
See: http://aichallenge.org/forums/viewtopic.php?f=25&t=1633
and: https://github.com/j-h-a/aichallenge/tree/vis_overlay
'''

import sys

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


SUBTILES_INDEX = {'n': 'TM',
                  'e': 'MR',
                  's': 'BM',
                  'w': 'ML',
                  0  : 'MM' }

class Overlay(object):

    '''
    Define new representable entities and commodity functions.
    Note that the js visualiser API requires coordinates in the form (row, col)
    rather than (col, row).
    '''

    def target_bot(self, bot):
        self.bot = bot
        self.world = bot.world

    def show_battlegroups(self, own, enemies):
        '''
        Own and enemies who could get into a fight the next turn.
        '''
        sys.stdout.write('v setLineWidth 3\n')
        # OWN
        sys.stdout.write('v setLineColor 255 0 0 1.0\n')   #red
        for (col, row) in own:
            sys.stdout.write('v circle %d %d 1.2 false\n' % (row, col))
        # ENEMIES
        sys.stdout.write('v setLineColor 0 255 0 1.0\n')   #green
        for (col, row) in enemies:
            sys.stdout.write('v circle %d %d 1.2 false\n' % (row, col))

    def show_dangers(self, data):
        '''
        Map of "dangers" in moving a certain way (for engageable ants only)
        '''
        sys.stdout.write('v setLineWidth 1\n')
        sys.stdout.write('v setLineColor 255 0 0 1.0\n')   #red
        for enemy, moves in data.items():
            for ((col, row), odir), dangers in moves.items():
                for edest, edir in dangers:
                    subtile = SUBTILES_INDEX[edir]
                    sys.stdout.write('v tileSubTile %s %s %s\n' %
                                     (row, col, subtile))

overlay = Overlay()
