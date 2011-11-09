#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contains a few helper funcions to be called when the bot is first activated.
'''

import sys

from world import World
from MyBot import Bot
from checklocal import RUNS_LOCALLY, BOT_DO_TURN_F, WORLD_UPDATE_F

if RUNS_LOCALLY:
    import visualisation
    import cProfile
    from overlay import overlay
    from time import time

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


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
            w = bot.world
            vis = visualisation.Visualiser(cols=w.cols, rows=w.rows)
            vis.render_scent(w.map)
            vis.save(w.turn)
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
    bot = Bot(world)
    # The following calls are not conditional to RUNS_LOCALLY as they do stuff
    # either way...
    set_world_profiling(world)
    set_bot_profiling(bot)
    if RUNS_LOCALLY:
        import logging
        log = logging.getLogger('main')
        # the overlay works like the logging: the overlay.overlay object is
        # the Overlay() intantiation
        overlay.target_bot(bot)
    data = []
    while(True):
        try:
            current_line = sys.stdin.readline().strip().lower()
            if not current_line:
                continue  #skip empty lines
            if current_line == 'ready':
                world.setup(data)
                bot.do_setup()
                world.finish_turn()
                data = []
            elif current_line == 'go':
                world.update(data)
                bot.do_turn()
                world.finish_turn()
                data = []
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
        finally:
            if RUNS_LOCALLY:
                logging.shutdown()
