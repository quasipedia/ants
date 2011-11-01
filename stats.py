#!/usr/bin/env python3

import pstats
p = pstats.Stats('last_run.profile')
p.strip_dirs().sort_stats('time', 'name').print_stats(10)
