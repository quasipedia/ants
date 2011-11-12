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

from world import WATER, OWN_ANTS, ENEMY_ANTS, OWN_HILLS, ENEMY_HILLS, \
                  OWN_DEAD, ENEMY_DEAD, FOOD, H_EXPLORE, H_HARVEST, H_FIGHT, \
                  SCENTS

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


LAND = -666  # or whatever is not used by other constants!
TILE_SIZE = 5

COLOURS = {LAND : '#B8860B',             # brown
           FOOD : '#FF81FC',             # pink
           WATER : '#0000FF',            # blue
           OWN_ANTS : '#007700',         # dark green
           ENEMY_ANTS : '#BB0000',       # dark red
           OWN_HILLS : '#00FF00',        # bright green
           ENEMY_HILLS : '#FF0000',      # bright red
           OWN_DEAD : '#003A00',         # deep green
           ENEMY_DEAD: '#3A0000'}        # deep red

# Convert colour strings to a list of floats ranging 0-1 [cairo format].
for k, v in COLOURS.items():
    COLOURS[k] = [int(v[1+i:3+i], 16) / 256.0 for i in range(0, 5, 2)]


class Visualiser(object):

    '''
    The main visualiser.
    '''

    def dump(self, world):
        '''
        Dump the visual representation(s) of the world into files.
        '''
        # Initiate the surface
        self.world = world
        self.surface = cr.ImageSurface(cr.FORMAT_ARGB32,
                                       world.cols * TILE_SIZE,
                                       world.rows * TILE_SIZE)
        self.ctx = cr.Context(self.surface)
        self._reset()
        # Render the various part
        self._render_scent(H_EXPLORE)
        self._render_map()
        # Save the file
        self._save()

    def _render_map(self):
        '''
        Render a world map to image.
        '''
        # Tiles to check with equality
        layers_to_render = [WATER, FOOD, OWN_ANTS, OWN_HILLS, OWN_DEAD,
                            ENEMY_ANTS, ENEMY_HILLS, ENEMY_DEAD]
        for layer in layers_to_render:
            locations = zip(*np.nonzero(self.world.map[:, :, layer]))
            for location in locations:
                self._draw_tile(location, COLOURS[layer])

    def _render_visibility(self, world_map):
        '''
        Display the areas currently visible by the ants.
        '''
        locations = np.transpose(np.where(world_map[:, :, 1] == 0))
        for location in locations:
            self._draw_tile(location, COLOURS[world.LAND])

    def _render_scent(self, hormone):
        '''
        Display the scent distribution on the map for a given hormone.
        '''
        wmap = self.world.map
        max_intensity = np.max(wmap[..., hormone])
        cols, rows = wmap.shape[:2]
        for col in range(cols):
            for row in range(rows):
                alpha = wmap[col, row, hormone] / max_intensity
                # red = go | blue = no-go
                colour = (1, 0, 0, alpha) if alpha > 0 else (0, 0, 1, -alpha)
                self._draw_tile((col, row), colour)

    def _reset(self):
        '''
        Reset the image to full black.
        '''
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.paint()

    def _save(self):
        '''
        Save the visualisation to file.
        '''
        self.surface.write_to_png('visualisations/%03d.png' % self.world.turn)

    def _draw_tile(self, loc, colour):
        '''
        Draw a tile at a given location in a given colour.
        '''
        scale = lambda x : x * TILE_SIZE
        x, y = map(scale, loc)
        self.ctx.set_source_rgba(*colour)
        self.ctx.rectangle(x + 1, y + 1, TILE_SIZE - 1, TILE_SIZE - 1)
        self.ctx.fill()

