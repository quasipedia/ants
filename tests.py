#!/usr/bin/env python
# -*- coding: utf-8  -*-

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

    def _perform_world_setup(self, text=None):
        '''
        Helper function that perform a standard setup of the world.
        '''
        if text == None:
            text = '''loadtime 3000
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
        TURN =  ''' f 6 5
                    w 7 6
                    a 7 9 1
                    a 10 8 0
                    a 10 9 0
                    h 7 12 1
                    h 10 5 0
                    d 8 9 1
                    d 10 10 0
                '''
        self._perform_world_setup()
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world.update(data)
        # food
        expected = (np.array([5]), np.array([6]))
        found = np.where(self.world.map[:, :, 0] == world.FOOD)
        self.assertTrue((expected == found), msg='FOOD')
        # water
        expected = (np.array([6]), np.array([7]))
        found = np.where(self.world.map[:, :, 0] == world.WATER)
        self.assertTrue((expected == found), msg='WATER')
        # own_ants
        expected = (np.array([8, 9]), np.array([10, 10]))
        found = np.where(self.world.map[:, :, 0] == world.OWN_ANT)
        self.assertTrue((expected[0] == found[0]).all() and
                        (expected[1] == found[1]).all(), msg='OWN ANTS')
        # enemy_ants
        expected = (np.array([9]), np.array([7]))
        found = np.where(self.world.map[:, :, 0] > world.OWN_ANT)
        self.assertTrue((expected == found), msg='ENEMY ANTS')
        # own_hills
        expected = (np.array([5]), np.array([10]))
        found = np.where(self.world.map[:, :, 0] == world.OWN_HILL)
        self.assertTrue((expected == found), msg='OWN HILLS')
        # enemy_hills
        expected = (np.array([12]), np.array([7]))
        found = np.where(self.world.map[:, :, 0] < world.OWN_HILL)
        self.assertTrue((expected == found), msg='ENEMY HILLS')
        # own_dead
        expected = (np.array([10]), np.array([10]))
        found = np.where(self.world.map[:, :, 0] == world.OWN_DEAD)
        self.assertTrue((expected == found), msg='OWN DEAD')
        # enemy_dead
        expected = (np.array([9]), np.array([8]))
        found = np.where((self.world.map[:, :, 0] > world.OWN_DEAD) &
                         (self.world.map[:, :, 0] < world.OWN_ANT))
        self.assertTrue((expected == found), msg='ENEMY DEAD')

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


