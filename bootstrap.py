#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contains a few helper funcions to be called when the bot is first activated.
'''

import sys

from world import World
from MyBot import Bot

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


PROFILING_DIR = 'profiling'
FULL_LOOP_F = '%s/full_loops' % PROFILING_DIR
BOT_DO_TURN_F = '%s/do_turn' % PROFILING_DIR
WORLD_UPDATE_F = '%s/update_world' % PROFILING_DIR

# Set the ``RUNS_LOCALLY`` flag
try:
    f = open('do_profile')
    f.close()
    import visualisation
    import cProfile
    from time import time
    RUNS_LOCALLY = True
except IOError:
    RUNS_LOCALLY = False


def set_bot_profiling(bot):
    '''
    Set the bot to be profiled.
    '''
    if RUNS_LOCALLY:
        profiler = cProfile.Profile()
        def profiled_turn(*args, **kwargs):
            profiler.runcall(bot._do_turn, *args, **kwargs)
            profiler.dump_stats(BOT_DO_TURN_F)
            # Dumping the scent visualisation
            #w = args[0]
            #vis = visualisation.Visualiser(cols=w.cols, rows=w.rows)
            #vis.render_scent(w.map)
            #vis.save(w.turn)
        bot.do_turn = profiled_turn
    else:
        bot.do_turn = bot._do_turn


def set_world_profiling(world):
    '''
    Set the world to be profiled.
    '''
    if RUNS_LOCALLY:
        profiler = cProfile.Profile()
        def profiled_update(*args, **kwargs):
            profiler.runcall(world._update, *args, **kwargs)
            profiler.dump_stats(WORLD_UPDATE_F)
        world.update = profiled_update
    else:
        world.update = world._update


def run():
    '''
    The main program loop. Manage the interface between the bot and the game
    engine.
    '''
    world = World()
    set_world_profiling(world)
    bot = Bot(world)
    set_bot_profiling(bot)
    data = []
    if RUNS_LOCALLY:
        timings = open(FULL_LOOP_F, 'w')

    def finish():
        world.finish_turn()
        data[:] = []  #data = [] would be considered local within "finish()"
        if RUNS_LOCALLY:
            timings.write('TURN %3d : %.3f\n' %
                         (world.turn, (time() - world.turn_start_time)))
            timings.flush()

    while(True):
        try:
            current_line = sys.stdin.readline().strip().lower()
            if not current_line:
                continue  #skip empty lines
            if current_line == 'ready':
                world.setup(data)
                bot.do_setup()
                finish()
            elif current_line == 'go':
                world.update(data)
                bot.do_turn()
                finish()
            else:
                data.append(current_line)
        except EOFError:  # game is over or game engine has crashed
            break
        except KeyboardInterrupt:  # local user is stopping the game
            print('\nEXECUTION STOPPED BY USER\n')
        except:  # try to stay alive! [don't raise or exit]
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    timings.close()
