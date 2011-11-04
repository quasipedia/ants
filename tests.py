#!/usr/bin/env python

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file contains the unit tests to verify the bot sanity.
'''

import unittest
import sys
import StringIO
import time

import numpy as np

import world

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
    Tests World class (interface layer between game engine and Bot AI).
    '''

    def setUp(self):
        self.world = world.World()
        # Bot uses stdout, but so does nose...
        self.saved_stdout = sys.stdout
        self.fake_stdout = StringIO.StringIO()
        sys.stdout = self.fake_stdout

    def tearDown(self):
        sys.stdout = self.saved_stdout

    def _read_output(self):
        '''
        Helper function to read the bot output.
        '''
        self.fake_stdout.flush()
        data = self.fake_stdout.getvalue().strip().lower().split('\n')
        self.fake_stdout.truncate(0)
        return data

    def _perform_world_setup(self):
        '''
        Helper function that perform a standard setup of the world.
        '''
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
        self.world.setup(data)

    def test_setup(self):
        self._perform_world_setup()
        # check data has been loaded correctly
        self.assertEqual(self.world.turn, 0)
        self.assertEqual(self.world.loadtime, 3000)
        self.assertEqual(self.world.turntime, 1000)
        self.assertEqual(self.world.rows, 20)
        self.assertEqual(self.world.cols, 30)
        self.assertEqual(self.world.turns, 500)
        self.assertEqual(self.world.viewradius2, 10)
        self.assertEqual(self.world.attackradius2, 5)
        self.assertEqual(self.world.spawnradius2, 1)
        self.assertEqual(self.world.player_seed, 42)
        # check the map size has been correctly set
        # in the following line "assertEqual" would throw an exception as the
        # == operator between arrays return an array with boolean values in it.
        self.assertTrue((self.world.map_size == np.array((30, 20))).all())
        # check the viewmask is correctly shaped
        expected = np.array(
            [[False, False,  True,  True,  True, False, False],
             [False,  True,  True,  True,  True,  True, False],
             [ True,  True,  True,  True,  True,  True,  True],
             [ True,  True,  True,  True,  True,  True,  True],
             [ True,  True,  True,  True,  True,  True,  True],
             [False,  True,  True,  True,  True,  True, False],
             [False, False,  True,  True,  True, False, False]], dtype=bool)
        self.assertTrue((self.world.view_mask == expected).all())

    def test_update(self):
        self.assertTrue(False)

    def test_diffuse(self):
        self.assertTrue(False)

    def test_issue_order(self):
        KNOWN = [((np.array((24, 12)), 'n'), 'o 12 24 n'),
                 ((np.array((4, 2)), 'e'), 'o 2 4 e'),
                 ((np.array((2, 1)), 's'), 'o 1 2 s'),
                 ((np.array((33, 77)), 'w'), 'o 77 33 w')]
        for order, outcome in KNOWN:
            self.world.issue_order(order)
            self.assertEqual(outcome, self._read_output()[0])

    def test_finish_turn(self):
        self.world.finish_turn()
        self.assertEqual('go', self._read_output()[0])

    def test_time_remaining(self):
        self.world.turntime = 50
        self.world.turn_start_time = time.time()
        time.sleep(0.010)
        self.assertTrue(50 > self.world.time_remaining() > 0)
        time.sleep(0.050)
        self.assertTrue(self.world.time_remaining() < 0)

    def test_manhattan(self):
        self.world.map_size = np.array((6, 8))  #0 to 5 and 0 to 7!!
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
        m = self.world.manhattan
        for pa, pb, d in KNOWN:
            self.assertTrue(m(pa, pb) == m(pb, pa) == d,
                    msg='%s %s %d %d %d' % (pa, pb, m(pa, pb), m(pb, pa), d))

    def test_destination(self):
        self._perform_world_setup()  # map size: 30 cols x 20 rows
        KNOWN = [(np.array((5, 5)), 'n', np.array((5, 4))),
                 (np.array((5, 5)), 'e', np.array((6, 5))),
                 (np.array((5, 5)), 's', np.array((5, 6))),
                 (np.array((5, 5)), 'w', np.array((4, 5))),
                 (np.array((5, 0)), 'n', np.array((5, 19))),
                 (np.array((29, 5)), 'e', np.array((0, 5))),
                 (np.array((5, 19)), 's', np.array((5, 0))),
                 (np.array((0, 5)), 'w', np.array((29, 5)))]
        for location, direction, expected in KNOWN:
            self.assertTrue(
              (expected == self.world.destination(location, direction)).all(),
              msg='%s' % self.world.destination(location, direction))


