#!/usr/bin/env python3
# Simple script to visualise the information about profiling the bot.

# TURN LENGTH
times = open('turns_lengths.profile').read().split()
for time in times:
    print(time)
print('\n')
n_times = [float(t) for t in times]
print('Average turn length :   %.3f' % (sum(n_times) / len(n_times)))
print('Longest turn length :   %.3f' % max(n_times))
print('\n')

# CODE PROFILING
import pstats
p = pstats.Stats('last_run.profile')
p.strip_dirs().sort_stats('time', 'name').print_stats(10)
