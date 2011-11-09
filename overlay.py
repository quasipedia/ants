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


class Overlay(object):

    '''
    Define new representable entities and commodity functions.
    Note that the js visualiser API requires coordinates in the form (row, col)
    rather than (col, row).
    '''

    def target_bot(self, bot):
        self.bot = bot
        self.world = bot.world

    def show_own_dead(self):
        '''
        Own dead ants: white empty circle
        '''
        dead = self.world.own_dead
        for (col, row), counter in dead:
            sys.stdout.write('v circle %d %d 1.2 false\n' % (row, col))

    def show_all(self):
        self.show_own_dead()

overlay = Overlay()
