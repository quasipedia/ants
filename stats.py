#!/usr/bin/env python
# Simple script to visualise the information about profiling the bot.

import pstats

from bootstrap import FULL_LOOP_F, BOT_DO_TURN_F, WORLD_UPDATE_F

# FULL LOOP LENGTH
lines = open(FULL_LOOP_F).readlines()
times = []
for line in lines:
    print(line.strip())
    times.append(line.split().pop())
print('\n')
n_times = [float(t) for t in times]
print('Turn zero length    :   %.3f' % n_times.pop(0))
print('Average regular turn length :   %.3f' % (sum(n_times) / len(n_times)))
print('Longest regular turn length :   %.3f' % max(n_times))
print('\n')

# BOT's DO_TURN LENGTH
p = pstats.Stats(BOT_DO_TURN_F)
p.strip_dirs().sort_stats('time', 'name').print_stats(10)

# WORLD's UPDATE LENGTH
p = pstats.Stats(WORLD_UPDATE_F)
p.strip_dirs().sort_stats('time', 'name').print_stats(10)
