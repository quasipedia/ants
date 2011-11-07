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


def set_profiling(bot):
    '''
    Establish if the bot is running locally, in which case we want to have
    profiling and logging enabled. Profiling is done if the file named
    ``do_profile`` is present in the directoy where the code is ran.
    '''
    try:
        f = open('do_profile')
        f.close()
        # Imports
        import visualisation
        import cProfile
        from time import time
        # Timing turns
        timings = open('%s/turns_lengths' % PROFILING_DIR, 'w')
        # Profiling the code
        profiler = cProfile.Profile()
        def profiled_turn(*args, **kwargs):
            start = time()
            profiler.runcall(bot._do_turn, *args, **kwargs)
            timings.write('%.3f ' % (time() - start))
            timings.flush()
            profiler.dump_stats('%s/last_run' % PROFILING_DIR)
            # Dumping the scent visualisation
            #w = args[0]
            #vis = visualisation.Visualiser(cols=w.cols, rows=w.rows)
            #vis.render_scent(w.map)
            #vis.save(w.turn)
        bot.do_turn = profiled_turn
    except IOError:
        bot.do_turn = bot._do_turn


def run():
    '''
    The main program loop. Manage the interface between the bot and the game
    engine.
    '''
    world = World()
    bot = Bot(world)
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

