#!/usr/bin/env python

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file is needed by the online game engine, and it exposes the main bot
to the game API. It is based off the starter package available online.
'''

from ants import Ants, run
from random import shuffle, choice


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class MyBot:

    '''
    Main bot class
    '''

    def __init__(self):
        pass

    def do_setup(self, ants):
        pass

    def _do_turn(self, ants):

        '''
        This is the raw function invoked by the game engine at each turn.

        The game engine will actually invoke ``do_turn()`` rather than
        ``_do_turn()``, but the ``main()`` might wrap the turn into a profiler
        when played locally, hence this intermediate step.
        '''

        def do_move_direction(loc, direction):
            '''
            Order an ant to move towards a given direction. Return False
            if the move is impossible or unsafe to perform, True
            otherwise.
            '''
            new_loc = tuple(ants.destination(loc, direction))
            col, row = new_loc
            if ants.map[new_loc] >= 0 and ants.hud[new_loc] != 10 \
                                      and new_loc not in orders:
                ants.issue_order((loc, direction))
                orders[new_loc] = loc
                return True
            else:
                return False

        def do_move_location(loc, dest):
            '''
            Move the ants toward a location on the map.
            '''
            directions = ants.direction(loc, dest)
            for direction in directions:
                if do_move_direction(loc, direction):
                    targets[tuple(dest)] = loc
                    return True
            return False

        # track all moves, prevent collisions,
        # key=destination value=origin
        orders = {}
        # track food gathering, prevent more ants to go,
        # key=destination value=origin
        targets = {}

        # prevent stepping on own hill
        for hill_loc in ants.own_hills:
            orders[tuple(hill_loc)] = None

        # find close food
        ant_dist = []
        for food_loc in ants.food:
            for ant_loc in ants.my_ants():
                dist = ants.manhattan(ant_loc, food_loc)
                ant_dist.append((dist, ant_loc, food_loc))
        ant_dist.sort()
        for dist, ant_loc, food_loc in ant_dist:
            if food_loc not in targets and ant_loc not in targets.values():
                do_move_location(ant_loc, food_loc)

        # attack hills
        ant_dist = []
        for hill_loc in ants.enemy_hills:
            for ant_loc in ants.own_ants:
                if ant_loc not in orders.values():
                    dist = ants.manhattan(ant_loc, hill_loc)
                    ant_dist.append((dist, ant_loc))
        ant_dist.sort()
        for dist, ant_loc in ant_dist:
            do_move_location(ant_loc, hill_loc)

        # explore unseen areas
        directions = ['s','e','w','n']
        for loc in ants.own_ants:
            if tuple(loc) not in orders:
                do_move_direction(loc, choice(direction))
        #for loc in self.unseen[:]:
            #if ants.visible(loc):
                #self.unseen.remove(loc)
             ##could be a bottleneck so...
            #if ants.time_remaining() < 200:
                #break
        #for ant_loc in ants.my_ants():
            #if ants.time_remaining() < 30:
                #break
            #if ant_loc not in orders.values():
                #unseen_dist = []
                #for unseen_loc in self.unseen:
                    #dist = ants.manhattan(ant_loc, unseen_loc)
                    #unseen_dist.append((dist, unseen_loc))
                #unseen_dist.sort()
                #for dist, unseen_loc in unseen_dist:
                    #if do_move_location(ant_loc, unseen_loc):
                        #break

        # unblock own hill
        for hill_loc in ants.own_hills:
            if hill_loc in ants.own_ants :#\
                             #and not (tuple(hill_loc) in orders.values()):
                directions = ['s','e','w','n'][:]
                shuffle(directions)
                for direction in directions:
                    if do_move_direction(hill_loc, direction):
                        break


if __name__ == '__main__':

    # Psycho speedup (available on 32 bit only)
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    bot = MyBot()

    # Establish if the bot is running locally, in which case we want to have
    # profiling and logging enabled. Profiling is done if the file named
    # ``do_profile`` is present in the directoy where the code is ran.
    try:
        f = open('do_profile')
        f.close()
        from time import time
        timings = open('turns_lengths.profile', 'w')
        import cProfile
        profiler = cProfile.Profile()
        def profiled_turn(*args, **kwargs):
            start = time()
            profiler.runcall(bot._do_turn, *args, **kwargs)
            timings.write('%.3f ' % (time() - start))
            timings.flush()
            profiler.dump_stats('last_run.profile')
        bot.do_turn = profiled_turn
    except IOError:
        bot.do_turn = bot._do_turn

    # Activate the bot and start playing
    try:
        run(bot)
    except KeyboardInterrupt:
        print('ctrl-C, leaving ...')
