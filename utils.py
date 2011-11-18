#!/usr/bin/env python
# -*- coding: utf-8  -*-

'''
Contest entry for the Fall 2011 challenge on http://aichallenge.org

This file contains general-iterest utilities, mostly linked to numpy.
'''


from numpy import array, empty_like, zeros, where, ndindex
from numpy import bool as np_bool


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"
__all__ = ['fastroll', 'get_circular_mask', 'get_circular_mask_bis']


def fastroll(array, dist, axis):
    '''
    Numpy's np.roll is implemented extremely inefficiently. This is a 2-10x
    faster replacement! Kudos to tmc from the forums!
    '''
    prefix = [slice(None)] * axis
    dist %= array.shape[axis]
    ret = empty_like(array)
    # ret[... dist:] = ret[... :-dist]
    ret[prefix + [slice(dist, None)]] = array[prefix + [slice(None, -dist)]]
    # ret[... :dist] = ret[... -dist:]
    ret[prefix + [slice(0, dist)]] = array[prefix + [slice(-dist, None)]]
    return ret

def get_circular_mask(radius2):
    '''
    Return a tuple of two arrays, corresponding to the offsets of the tiles
    within radius relative to a given centre point (0, 0).
        These kind of masks are used to quickly find out which coordindates
    are within view or attack radii from an ant, or similar.
    '''
    radius = int(radius2 ** 0.5)
    side = radius * 2 + 1
    tmp = zeros((side, side), dtype=np_bool)
    for d_row in range(-radius, radius+1):
        for d_col in range(-radius, radius+1):
            if d_row**2 + d_col**2 <= radius2:
                tmp[radius+d_col][radius+d_row] = True
    # At this point `tmp` contains a representation of the field of view,
    # what we want is coordinate offsets from the ant position
    tmp = where(tmp)
    return tuple([value - radius for value in tmp])

def get_circular_mask_bis(radius2):
    radius = int(radius2 ** 0.5)
    diameter = radius * 2 + 1
    disc = zeros((diameter, diameter), dtype = np_bool)
    for y, x in ndindex(*disc.shape):
        if (radius - y) ** 2 + (radius - x) ** 2 <= radius2:
            disc[y, x] = True
    tmp = where(disc)
    return tuple([value - radius for value in tmp])
