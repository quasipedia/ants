#!/usr/bin/env python
# Simple script to visualise the information about profiling the bot.

import pstats
import re

from checklocal import FULL_LOOP_OLD, BOT_DO_TURN_F, WORLD_UPDATE_F

# REGEX
RE_DIFFUSE_STEPS = r'(\d+) passes'
RE_TURN_LENGTH= r'DURATION : (\d+) ms'

# FULL LOOP LENGTH
file_content = open(FULL_LOOP_OLD).read()
diffuse_steps = re.findall(RE_DIFFUSE_STEPS, file_content)
n_steps = [int(t) for t in diffuse_steps]
turn_times = re.findall(RE_TURN_LENGTH, file_content)
n_times = [int(t) for t in turn_times]
print('Game length                    : %d turns' % len(turn_times))
print('Turn zero length               : %d\n' % n_times.pop(0))
print('Turn lengths (min/avg/max)     : %.d  /  %.d  /  %.d' %
     (min(n_times), sum(n_times) / len(n_times), max(n_times)))
print('Diffusion steps (min/avg/max)  : %.d  /  %.d  /  %.d\n' %
     (min(n_steps), sum(n_steps) / len(n_steps), max(n_steps)))

# BOT's DO_TURN LENGTH
p = pstats.Stats(BOT_DO_TURN_F)
p.strip_dirs().sort_stats('time', 'name').print_stats(10)

# WORLD's UPDATE LENGTH
p = pstats.Stats(WORLD_UPDATE_F)
p.strip_dirs().sort_stats('time', 'name').print_stats(10)
