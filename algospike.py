#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
spike – a package manager running on top of git

Copyright © 2012, 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

'''
Algorithmic Spike (algospike)

This module contains non-ad hoc algorithmic functions that
can be used through out Spike.
'''


def unique(sorted):
    '''
    Duplicate a sorted list and remove all duplicates
    
    @param   sorted:list<¿E?>  A sorted list, without leading `None`:s, more precisely, all equals elements must be grouped
    @return  :list<¿E?>        `sorted` with all duplicates removed, for example: aaabbc → abc
    '''
    rc = []
    last = None
    for element in sorted:
        if element != last:
            last = element
            rc.append(element)
    return rc


def binsearch(list, item, min, max):
    '''
    Find the index of an item in a list, with time complexity 𝓞(log n) and memory complexity 𝓞(1)
    
    @param   list:[int]→¿E?  Sorted list in which to search
    @param   item:¿E?        Item for which to search
    @param   min:int         The index of the first element in `list` for which to serach
    @param   max:int         The index of the last element (inclusive) in `list` for which to serach
    @return  :int            The index of `item` in `list`, if missing `~x` is returned were `x` is the position it would have if it existed
    '''
    mid = 0
    while min <= max:
        mid = (min + max) >> 1
        elem = list[mid]
        if elem == item:
            return mid
        elif elem > item:
            max = mid - 1
        else:
            mid += 1
            min = mid
    return ~mid


def multibinsearch(rc, list, items):
    '''
    Find the indices of multiple items in a list, with time complexity 𝓞(log n + m) and memory complexity 𝓞(log m) 
    
    @param  rc:append((int, int))→void  Object to which to append found items, the append items are of tuple (itemIndex:int, listIndex:int)
    @param  list:[int]→¿E?;len()→int    Sorted list in which to search, the number of elements is named ‘n’ in the complexity analysis
    @param  items:[int]→¿E?;len()→int   Sorted list of items for which to search, the number of elements is named ‘m’ in the complexity analysis
    '''
    count = len(items)
    if count > 0:
        minomax = [(0, count - 1, 0, len(list) - 1)]
        while len(minomax) > 0:
            (min, max, lmin, lmax) = minomax.pop()
            while max != min:
                (lastmax, lastlmax) = (max, lmax)
                max = min + ((max - min) >> 1)
                lmax = binsearch(list, items[max], lmin, lmax)
                rc.append((max, lmax))
                if lmax < 0:
                    lmax = ~lmax
                minomax.append((max + 1, lastmax, lmax + 1, lastlmax))
        max = count - 1
        lmax = binsearch(list, items[max], lmin, lmax)
        rc.append((max, lmax))

