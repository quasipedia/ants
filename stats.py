#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file contains a visualiser for log and profile information. It is not
part of the uploaded package. It is a devel's tool.

Some information on the format of the log file:
- Each line of data that is supposed to be parsed has the format:
  "DATA_ID : data0 label0, data1 label1, ... for example:
  DIFFUSE : 204 passes, 204 needed
  TURN DURATION : 315 ms
- Data that is for direct log inspection by a human is prefixed with at least
  one hash [#] sign.
'''

import pstats

from checklocal import FULL_LOOP_OLD, BOT_DO_TURN_F, WORLD_UPDATE_F

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Viewer(object):

    '''
    Container class providing all the methods needed to manipulate and
    visualise the log and profiling content.
    '''

    def __init__(self):
        processed_data = {}
        lines = open(FULL_LOOP_OLD).readlines()
        for line in lines:
            if line[0] == '#':
                continue
            dataid, data = [bit.strip() for bit in line.split(':')]
            data = [bit.strip() for bit in data.split(',')]
            data = [int(string.split()[0]) for string in data]
            if len(data) == 1:
                data = data[0]
            try:
                processed_data[dataid].append(data)
            except KeyError:
                processed_data[dataid] = [data]
        self.data = processed_data

    def turns(self):
        '''
        Provide stats on the turns.
        '''
        data = self.data['TURN DURATION']
        print('\n\n##### TURNS #####')
        print('Game length                    : %d turns' % (len(data) - 1))
        print('Turn zero length               : %d ms' % data.pop(0))
        print('Turn length (min/avg/max)      : %.d  /  %.d  /  %.d' %
                (min(data), sum(data) / len(data), max(data)))

    def diffusion(self):
        '''
        Provide stats about the diffusion process.
        '''
        data = self.data['DIFFUSE']
        abs_max = max([le for le, need in data])
        data = [le for le, need in data if le < need]
        print('\n\n##### DIFFUSION #####')
        if data:
            print('Diffusion steps (min/avg/max)  : %.d  /  %.d  /  %.d\n' %
                (min(data), float(sum(data)) / len(data), max(data)))
        else:
            print('All turn got complete diffusion!')
            print('Max number of steps was        : %.d' % abs_max)

    def profiling(self):
        '''
        Provide profiling data.
        '''
        print('\n\n')
        # BOT's DO_TURN LENGTH
        p = pstats.Stats(BOT_DO_TURN_F)
        p.strip_dirs().sort_stats('time', 'name').print_stats(10)
        # WORLD's UPDATE LENGTH
        p = pstats.Stats(WORLD_UPDATE_F)
        p.strip_dirs().sort_stats('time', 'name').print_stats(10)

    def print_all(self):
        '''
        Print all available information.
        '''
        self.turns()
        self.diffusion()
        self.profiling()

if __name__ == '__main__':

    v = Viewer()
    v.print_all()
