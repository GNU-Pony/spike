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
    
    @param  rc:append((int, int))→void     Object to which to append found items, the append items are of tuple (itemIndex:int, listIndex:int)
    @param  list:[int]→¿E?;__len__()→int   Sorted list in which to search, the number of elements is named ‘n’ in the complexity analysis
    @param  items:[int]→¿E?;__len__()→int  Sorted list of items for which to search, the number of elements is named ‘m’ in the complexity analysis
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


def lb128(x):
    '''
    Calculates the floored binary logarithm of an integer that is at most 128 bits
    
    @param   x:int  The input number
    @return  :int   The floored binary logarithm of the input number
    '''
    rc = 0
    if (x & 0xFFFFFFFFFFFFFFFF0000000000000000) != 0:  rc += 64 ;  x >>= 64
    if (x & 0x0000000000000000FFFFFFFF00000000) != 0:  rc += 32 ;  x >>= 32
    if (x & 0x000000000000000000000000FFFF0000) != 0:  rc += 16 ;  x >>= 16
    if (x & 0x0000000000000000000000000000FF00) != 0:  rc +=  8 ;  x >>=  8
    if (x & 0x000000000000000000000000000000F0) != 0:  rc +=  4 ;  x >>=  4
    if (x & 0x0000000000000000000000000000000C) != 0:  rc +=  2 ;  x >>=  2
    if (x & 0x00000000000000000000000000000002) != 0:  rc +=  1
    return rc


def lb64(x):
    '''
    Calculates the floored binary logarithm of an integer that is at most 64 bits
    
    @param   x:int  The input number
    @return  :int   The floored binary logarithm of the input number
    '''
    rc = 0
    if (x & 0xFFFFFFFF00000000) != 0:  rc += 32 ;  x >>= 32
    if (x & 0x00000000FFFF0000) != 0:  rc += 16 ;  x >>= 16
    if (x & 0x000000000000FF00) != 0:  rc +=  8 ;  x >>=  8
    if (x & 0x00000000000000F0) != 0:  rc +=  4 ;  x >>=  4
    if (x & 0x000000000000000C) != 0:  rc +=  2 ;  x >>=  2
    if (x & 0x0000000000000002) != 0:  rc +=  1
    return rc


def lb32(x):
    '''
    Calculates the floored binary logarithm of an integer that is at most 32 bits
    
    @param   x:int  The input number
    @return  :int   The floored binary logarithm of the input number
    '''
    rc = 0
    if (x & 0xFFFF0000) != 0:  rc += 16 ;  x >>= 16
    if (x & 0x0000FF00) != 0:  rc +=  8 ;  x >>=  8
    if (x & 0x000000F0) != 0:  rc +=  4 ;  x >>=  4
    if (x & 0x0000000C) != 0:  rc +=  2 ;  x >>=  2
    if (x & 0x00000002) != 0:  rc +=  1
    return rc


def tsort(rc, lostrc, data):
    '''
    Sorts a data set on topologically
    Cyclic dependencies are optimised to be break so that each break queues a item before as few transveral dependencies
    as possible. That does not been that the total of each break is optimised, just each break.
    
    @param   rc:append((¿E?, list<¿E?>?))→void     Feed the items on topological order, accompanied by all items a list
                                                   cyclic dependencies it has that has yes not been feed. Instead of a
                                                   empty list it will feed `None` it the item is not used to break a cycle.
    @param   lostrc:append((¿E?, ¿E?))→void        Feed a dependency and what requires it when a dependency cannot be found
    @param   data:dict<¿E?, (set<¿E?>, itr<¿E?>)>  Dictionary from item to dependencies and those of them that are absolute
    @return  :bool                                 Whether the sort can be resolved without breaking an absolute cycle,
                                                   if not, all item while not have been feed to `rc` or `lostrc`.
    '''
    # Find, report and remove missing dependencies
    removed = {}
    for req in data.keys():
        for dep in data[req][0]:
            if dep not in data:
                lostrc.append((dep, req))
                if dep not in removed:
                    removed[dep] = []
                removed[dep].append(req)
    for remove in removed.keys():
        for req in removed[remove]:
            data[req][0].remove(remove)
    
    # Sort cyclic graph topologically
    removed = [None]
    while len(removed) > 0:
        # Sort acyclic graph topologically
        while len(removed) > 0:
            removed = []
            # Report and remove items with no unresolved dependency
            for item in list(data):
                if len(data[item][0]) == 0:
                    rc.append((item, None))
                    removed.append(item)
                    del data[item]
            # Remove reported items from dependency lists
            for item in data:
                deps = data[item][0]
                for old in removed:
                    if old in deps:
                        deps.remove(old)
        
        # Break one cycle with as few transversial dependencies as possible
        if len(data) > 0:
            best = None
            # Find best cycle break
            for item in data:
                deps = set()
                queue = list(data[item][0])
                deps.add(item)
                absolute = set(data[item][1])
                bad = False
                while len(queue) > 0:
                    dep = queue[0]
                    if dep in absolute:
                        bad = True
                        break
                    queue[:] = queue[1:]
                    if dep in deps:
                        continue
                    deps.add(dep)
                    queue += list(data[dep][0])
                    for abs in data[dep][1]:
                        absolute.add(abs)
                if bad:
                    continue
                deps.remove(item)
                if (best is None) or (len(best[0]) > len(deps)):
                    best = (item, list(deps))
            # Report cycle break and remove item
            if best is None:
                return False
            rc.append(best)
            bestitem = best[0]
            removed.append(bestitem)
            del data[bestitem]
            # Remove item from dependency lists
            for item in data:
                if bestitem in data[item][0]:
                    data[item][0].remove(bestitem)
    return True

