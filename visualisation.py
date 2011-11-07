#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file contains a visualiser that dumps the representation the robot have of
the map in image files.
'''

import cairo as cr
import numpy as np
from random import random

import world

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


TILE_SIZE = 10

COLOURS = {world.LAND : '#B8860B',          # brown
           world.FOOD : '#FF81FC',          # pink
           world.WATER : '#0000FF',         # blue
           world.OWN_ANT : '#007700',       # dark green
           world.OWN_ANT + 1 : '#BB0000',   # dark red
           world.OWN_HILL : '#00FF00',      # bright green
           world.OWN_HILL - 1 : '#FF0000',  # bright red
           world.OWN_DEAD : '#003A00',      # deep green
           world.OWN_DEAD + 1: '#3A0000'}   # deep red

# Convert colour strings to a list of floats ranging 0-1 [cairo format].
for k, v in COLOURS.items():
    COLOURS[k] = [int(v[1+i:3+i], 16) / 256.0 for i in range(0, 5, 2)]


class Visualiser(object):

    '''
    The main visualiser.
    '''

    def __init__(self, cols=40, rows=40):
        self.surface = cr.ImageSurface(cr.FORMAT_ARGB32, cols * TILE_SIZE,
                                                         rows * TILE_SIZE)
        self.ctx = cr.Context(self.surface)
        self.reset()

    def reset(self):
        '''
        Reset the image to full black.
        '''
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.paint()

    def render_map(self, world_map):
        '''
        Render a world map to image.
        '''
        # Tiles to check with equality
        for value in [world.LAND, world.WATER, world.FOOD, world.OWN_ANT,
                      world.OWN_HILL, world.OWN_DEAD]:
            locations = zip(*np.where(world_map[:, :, 0] == value))
            for location in locations:
                self._draw_tile(location, COLOURS[value])
        # Enemy hills
        locations = zip(*np.where(world_map[:, :, 0] < world.OWN_HILL))
        for location in locations:
            self._draw_tile(location, COLOURS[world.OWN_HILL - 1])
        # Enemy ants
        locations = zip(*np.where(world_map[:, :, 0] > world.OWN_ANT))
        for location in locations:
            self._draw_tile(location, COLOURS[world.OWN_ANT + 1])
        # Enemy dead
        locations = zip(*np.where((world_map[:, :, 0] > world.OWN_DEAD) &
                        (world_map[:, :, 0] < world.OWN_ANT)))
        for location in locations:
            self._draw_tile(location, COLOURS[world.OWN_DEAD + 1])

    def render_visibility(self, world_map):
        '''
        Display the areas currently visible by the ants.
        '''
        locations = np.transpose(np.where(world_map[:, :, 1] == 0))
        for location in locations:
            self._draw_tile(location, COLOURS[world.LAND])

    def render_scent(self, world_map):
        '''
        Display the scent distribution on the map.
        '''
        max_scent = max([abs(e) for e in world.SCENTS.values()])
        cols, rows = world_map.shape[:2]
        for col in range(cols):
            for row in range(rows):
                alpha = world_map[col, row, world.SCENT] / max_scent
                # red = go | blue = no-go
                colour = (1, 0, 0, alpha) if alpha > 0 else (0, 0, 1, -alpha)
                self._draw_tile((col, row), colour)
        locations = zip(*np.where(world_map[:, :, 0] == world.OWN_ANT))
        for location in locations:
            self._draw_tile(location, COLOURS[world.OWN_ANT])

    def save(self, frame):
        '''
        Save the visualisation to file.
        '''
        self.surface.write_to_png('visualisations/%03d.png' % frame)

    def _draw_tile(self, loc, colour):
        '''
        Draw a tile at a given location in a given colour.
        '''
        scale = lambda x : x * TILE_SIZE
        x, y = map(scale, loc)
        self.ctx.set_source_rgba(*colour)
        self.ctx.rectangle(x + 1, y + 1, TILE_SIZE - 1, TILE_SIZE - 1)
        self.ctx.fill()

