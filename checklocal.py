#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contains the check to discover if the bot is running locally or not (based on
the presence of the file ``do_profiling`` in the bot directory. This check has
been isolated to solve circular reference imports.
'''

from time import time

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


PROFILING_DIR = 'profiling'
FULL_LOOP_F = '%s/bot.log' % PROFILING_DIR
FULL_LOOP_OLD = '%s/last.bot.log' % PROFILING_DIR
BOT_DO_TURN_F = '%s/do_turn' % PROFILING_DIR
WORLD_UPDATE_F = '%s/update_world' % PROFILING_DIR

# Set the ``RUNS_LOCALLY`` flag and set the logger
try:
    f = open('do_profile')
    f.close()
    RUNS_LOCALLY = True
    from os import rename, remove
    from os.path import exists, getsize
    if exists(FULL_LOOP_F) and getsize(FULL_LOOP_F) > 0:
        if exists(FULL_LOOP_OLD):
            remove(FULL_LOOP_OLD)
        rename(FULL_LOOP_F, FULL_LOOP_OLD)
    import logging
    log = logging.getLogger('main')
    handler_file = logging.FileHandler(FULL_LOOP_F)
    log.addHandler(handler_file)
    log.setLevel(logging.DEBUG)
except IOError:
    RUNS_LOCALLY = False
