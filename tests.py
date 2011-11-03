#!/usr/bin/env python

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file contains the unit tests to verify the bot sanity.
'''

import unittest
import ants
import numpy as np

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class TestAnts(unittest.TestCase):

    '''
    Tests Ants class (interface layer between game engine and Bot AI).
    '''

    def setUp(self):
        self.ants = ants.Ants()

    def test_setup(self):
        text = '''turn 0
                  loadtime 3000
                  turntime 1000
                  rows 20
                  cols 30
                  turns 500
                  viewradius2 10
                  attackradius2 5
                  spawnradius2 1
                  player_seed 42
               '''
        data = [line.strip() for line in text.split('\n') if line.strip()]
        self.ants.setup(data)
        # check data has been loaded correctly
        self.assertEqual(self.ants.turn, 0)
        self.assertEqual(self.ants.loadtime, 3000)
        self.assertEqual(self.ants.turntime, 1000)
        self.assertEqual(self.ants.rows, 20)
        self.assertEqual(self.ants.cols, 30)
        self.assertEqual(self.ants.turns, 500)
        self.assertEqual(self.ants.viewradius2, 10)
        self.assertEqual(self.ants.attackradius2, 5)
        self.assertEqual(self.ants.spawnradius2, 1)
        self.assertEqual(self.ants.player_seed, 42)
        # check the map size has been correctly set
        # in the following line "assertEqual" would throw an exception as the
        # == operator between arrays return an array with boolean values in it.
        self.assertTrue((self.ants.map_size == np.array((30, 20))).all())
        # check the viewmask is correctly shaped
        expected = np.array(
            [[False, False,  True,  True,  True, False, False],
             [False,  True,  True,  True,  True,  True, False],
             [ True,  True,  True,  True,  True,  True,  True],
             [ True,  True,  True,  True,  True,  True,  True],
             [ True,  True,  True,  True,  True,  True,  True],
             [False,  True,  True,  True,  True,  True, False],
             [False, False,  True,  True,  True, False, False]], dtype=bool)
        self.assertTrue((self.ants.view_mask == expected).all())

    def test_update(self):
        self.assertTrue(False)

    def test_issue_order(self):
        self.assertTrue(False)

    def test_finish_turn(self):
        self.assertTrue(False)

    def test_time_remaining(self):
        self.assertTrue(False)

    def test_manhattan(self):
        self.ants.map_size = np.array((6, 8))  #0 to 5 and 0 to 7!!
        p1 = np.array((0, 0))
        p2 = np.array((1, 1))
        p3 = np.array((3, 3))
        p4 = np.array((5, 1))
        p5 = np.array((2, 6))
        p6 = np.array((4, 7))
        KNOWN = [(p1, p2, 2),
                 (p1, p5, 4),
                 (p1, p6, 3),
                 (p2, p4, 2),
                 (p3, p4, 4),
                 (p4, p6, 3),
                 (p5, p6, 3)]
        m = self.ants.manhattan
        for pa, pb, d in KNOWN:
            self.assertTrue(m(pa, pb) == m(pb, pa) == d,
                    msg='%s %s %d %d %d' % (pa, pb, m(pa, pb), m(pb, pa), d))

    def test_destination(self):
        self.assertTrue(False)

    def test_direction(self):
        self.assertTrue(False)


