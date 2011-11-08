#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contains the check to discover if the bot is running locally or not (based on
the presence of the file ``do_profiling`` in the bot directory. This check has
been isolated to solve circular reference imports.
'''

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# Set the ``RUNS_LOCALLY`` flag and set the logger
try:
    f = open('do_profile')
    f.close()
    RUNS_LOCALLY = True
    from os import remove
    try:
        remove('profiling/bot.log')
    except OSError:
        pass  # the file is not there already
    import logging
    log = logging.getLogger('main')
    handler_file = logging.FileHandler('profiling/bot.log')
    log.addHandler(handler_file)
    log.setLevel(logging.DEBUG)
except IOError:
    RUNS_LOCALLY = False
