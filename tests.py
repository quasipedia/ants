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


class TestWorld(unittest.TestCase):

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
            text = '''turn 0
                      loadtime 3000
                      turntime 1000
                      rows 20
                      cols 30
                      turns 10
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
        self.assertEqual(self.world.turns, 10)
        self.assertEqual(self.world.viewradius2, 10)
        self.assertEqual(self.world.attackradius2, 5)
        self.assertEqual(self.world.spawnradius2, 1)
        self.assertEqual(self.world.player_seed, 42)
        # check the map size has been correctly set
        # in the following line "assertEqual" would throw an exception as the
        # == operator between arrays return an array with boolean values in it.
        self.assertTrue((self.world.world_size == np.array((30, 20))).all())
        # check the viewmask is correctly shaped
        expected = (np.array([-3, -3, -3, -2, -2, -2, -2, -2, -1, -1, -1,
                              -1, -1, -1, -1,  0,  0,  0,  0,  0,  0,  0,
                               1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,
                               2,  3,  3,  3]),
                    np.array([-1,  0,  1, -2, -1,  0,  1,  2, -3, -2, -1,
                               0,  1,  2,  3, -3, -2, -1,  0,  1,  2,  3,
                              -3, -2, -1,  0, 1,  2,  3, -2, -1,  0,  1,
                               2, -1,  0,  1]))
        self.assertTrue((self.world.view_mask[0] == expected[0]).all())
        self.assertTrue((self.world.view_mask[1] == expected[1]).all())

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
        self.world._update(data)
        # food
        expected = (np.array([5]), np.array([6]))
        found = np.where(self.world.map[:, :, world.FOOD])
        self.assertTrue((expected == found), msg='FOOD')
        # water
        expected = (np.array([6]), np.array([7]))
        found = np.where(self.world.map[:, :, world.WATER])
        self.assertTrue((expected == found), msg='WATER')
        # own_ants
        expected = (np.array([8, 9]), np.array([10, 10]))
        found = np.where(self.world.map[:, :, world.OWN_ANTS])
        self.assertTrue((expected[0] == found[0]).all() and
                        (expected[1] == found[1]).all(), msg='OWN ANTS')
        e = world.EXPLORER
        self.assertEqual({(8, 10): e, (9, 10): e}, self.world.own_ants)
        # enemy_ants
        expected = (np.array([9]), np.array([7]))
        found = np.where(self.world.map[:, :, world.ENEMY_ANTS])
        self.assertTrue((expected[0] == found[0]).all() and
                        (expected[1] == found[1]).all(), msg='ENEMY ANTS %s')
        self.assertEqual({(9, 7): 1}, self.world.enemy_ants)
        # own_hills
        expected = (np.array([5]), np.array([10]))
        found = np.where(self.world.map[:, :, world.OWN_HILLS])
        self.assertTrue((expected == found), msg='OWN HILLS')
        self.assertEqual({(5, 10): world.PREVIOUSLY_SEEN},
                         self.world.own_hills)
        # enemy_hills
        expected = (np.array([12]), np.array([7]))
        found = np.where(self.world.map[:, :, world.ENEMY_HILLS])
        self.assertTrue((expected == found), msg='ENEMY HILLS')
        self.assertEqual({(12, 7): [world.PREVIOUSLY_SEEN, 1]},
                         self.world.enemy_hills)
        # own_dead
        expected = (np.array([10]), np.array([10]))
        found = np.where(self.world.map[:, :, world.OWN_DEAD])
        self.assertTrue((expected == found), msg='OWN DEAD')
        # enemy_dead
        expected = (np.array([9]), np.array([8]))
        found = np.where(self.world.map[:, :, world.ENEMY_DEAD])
        self.assertTrue((expected == found), msg='ENEMY DEAD')

    def test_is_tile_visible(self):
        TURN =  'a 10 10 0\n'
        self._perform_world_setup()
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        self.assertTrue(self.world.is_tile_visible((11, 11)))
        self.assertFalse(self.world.is_tile_visible((1, 11)))

    def test_is_tile_passable(self):
        TURN =  ''''a 10 10 0
                    h 11 11 0
                    d 11 12 0
                    d 11 13 1
                    a 11 14 1
                    h 11 15 1
                    w 11 16
                    f 11 17
                '''
        self._perform_world_setup()
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        self.assertTrue(self.world.is_tile_passable((11, 11)), msg='own hill')
        self.assertTrue(self.world.is_tile_passable((12, 11)), msg='own dead')
        self.assertTrue(self.world.is_tile_passable((13, 11)), msg='e. dead')
        self.assertFalse(self.world.is_tile_passable((14, 11)), msg='e. ant')
        self.assertTrue(self.world.is_tile_passable((15, 11)), msg='e. hill')
        self.assertFalse(self.world.is_tile_passable((16, 11)), msg='water')
        self.assertFalse(self.world.is_tile_passable((17, 11)), msg='food')

    def test_issue_order(self):
        KNOWN = [((np.array((24, 12)), 'n'), 'o 12 24 n'),
                 ((np.array((4, 2)), 'e'), 'o 2 4 e'),
                 ((np.array((2, 1)), 's'), 'o 1 2 s'),
                 ((np.array((33, 77)), 'w'), 'o 77 33 w')]
        for order, outcome in KNOWN:
            self.world.issue_order(order)
            self.assertEqual(outcome, self._read_output()[0])

    def test_finish_turn(self):
        self.world.turn_start_time = 0
        self.world.finish_turn()
        self.assertEqual('go', self._read_output()[0])

    def test_time_remaining(self):
        self.world.turn = 1
        self.world.turntime = 50
        self.world.turn_start_time = time.time()
        time.sleep(0.010)
        self.assertTrue(50 > self.world.time_remaining() > 0)
        time.sleep(0.050)
        self.assertTrue(self.world.time_remaining() < 0)

    def test_manhattan(self):
        self.world.world_size = np.array((6, 8))  #0 to 5 and 0 to 7!!
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

    def test_get_legalmoves(self):
        TURN =  '''f 9 6
                   a 8 5 1
                   a 9 5 0
                   w 9 4
                '''
        EXPECTED = [[(5, 9), 0], [(5, 10), 's'], [(5, 8), 'n']]
        self._perform_world_setup()
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        to_set = lambda li : set(tuple(el) for el in li)
        result = self.world.get_legal_moves((5, 9))
        self.assertEqual(to_set(EXPECTED), to_set(result))

    def test_get_scent_strengths(self):
        TURN =  '''f 10 7
                   a 11 9 0
                '''
        EXPECTED = [[(8, 11), 'w'], [(9, 10), 'n'],
                    [(9, 12), 's'], [(10, 11), 'e']]
        self._perform_world_setup()
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        self.world.diffuse()
        result = self.world.get_scent_strengths((9, 11), world.H_HARVEST)
        # Since the food emitting force may change in the future, we only want
        # to test the directions are right, not the abs value of the scent...
        self.assertEqual(EXPECTED, [el[1:] for el in result])

    def test_get_stuff_in_sight(self):
        SETUP = '''turn 0
                   loadtime 3000
                   turntime 1000
                   rows 20
                   cols 30
                   turns 10
                   viewradius2 10
                   attackradius2 5
                   spawnradius2 1
                   player_seed 42
                '''
        TURN =  '''a 11 9 0
                   f 10 7
                   f 19 1
                   a 13 10 1
                   a 0 0 1
                   h 13 8 1
                   h 19 19 1
                '''
        EXPECTED = {world.FOOD: (7, 10),
                    world.ENEMY_ANTS: (10, 13),
                    world.ENEMY_HILLS: (8, 13)}
        self._perform_world_setup(SETUP)
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        for layer in EXPECTED:
            result = self.world.get_stuff_in_sight((9, 11), layer)
            self.assertTrue(len(result) == 1)
            self.assertEqual(EXPECTED[layer], tuple(result[0]))

    def test_get_in_attackradius(self):
        SETUP = '''turn 0
                   loadtime 3000
                   turntime 1000
                   rows 20
                   cols 30
                   turns 10
                   viewradius2 10
                   attackradius2 5
                   spawnradius2 1
                   player_seed 42
                '''
        TURN =  '''a 11 9 0
                   a 11 8 1
                   a 11 7 1
                   a 11 6 1
                   a 11 10 1
                   a 11 11 1
                   a 11 12 1
                   a 10 9 1
                   a 9 9 1
                   a 8 9 1
                   a 12 9 1
                   a 13 9 1
                   a 14 9 1
                '''
        EXPECTED = set([(8, 11), (7, 11), (10, 11), (11, 11),
                        (9, 10), (9, 9), (9, 12), (9, 13)])
        self._perform_world_setup(SETUP)
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        result = self.world.get_in_attackradius((9, 11))
        result = set([tuple(arr) for arr in result])
        self.assertEqual(EXPECTED, result)

    def test_get_engageable(self):
        SETUP = '''turn 0
                   loadtime 3000
                   turntime 1000
                   rows 20
                   cols 30
                   turns 10
                   viewradius2 10
                   attackradius2 5
                   spawnradius2 1
                   player_seed 42
                '''
        TURN =  '''a 11 9 1
                   a 11 8 0
                   a 11 7 0
                   a 11 6 0
                   a 11 5 0
                   a 11 4 0
                   a 11 10 0
                   a 11 11 0
                   a 11 12 0
                   a 11 13 0
                   a 11 14 0
                   a 10 9 0
                   a 9 9 0
                   a 8 9 0
                   a 7 9 0
                   a 6 9 0
                   a 12 9 0
                   a 13 9 0
                   a 14 9 0
                   a 15 9 0
                   a 16 9 0
                '''
        EXPECTED = set([(6, 11), (5, 11), (12, 11), (13, 11),
                        (9, 8), (9, 7), (9, 14), (9, 15)])
        self._perform_world_setup(SETUP)
        data = [line.strip() for line in TURN.split('\n') if line.strip()]
        self.world._update(data)
        result = self.world.get_engageable((9, 11))
        result = set([tuple(arr) for arr in result])
        self.assertEqual(EXPECTED, result)
