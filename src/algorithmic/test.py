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
Test for this directory
'''
from algospike import *


error_ = False
def error(message, ok = False):
    global error_
    if not ok:
        error_ = True
        print('\033[31m%s\033[00m' % message)




got = unique('a a d d d d d d d d d f i i i i i j j k k k l m n s s s s s s s s s v v'.split(' '))
error('algospike.unique does not work', got == 'a d f i j k l m n s v'.split(' '))



items = 'a a d d d d d d d d d f i i i i i j j k k k l m n s s s s s s s s s v v'.split(' ')
got = bin_search(items, 'i', 0, len(items) - 1)
error('algospike.bin_search, searching for multiexisting, does not work', 12 <= got <= 16)

got = bin_search(items, 'm', 0, len(items) - 1)
error('algospike.bin_search, searching for single existing, does not work', got == 23)

got = bin_search(items, ' ', 0, len(items) - 1)
error('algospike.bin_search, searching for single existing, first, does not work', got == ~0)

got = bin_search(items, 'z', 0, len(items) - 1)
error('algospike.bin_search, searching for single existing, last, does not work', got == ~len(items))

got = bin_search(items, 'g', 0, len(items) - 1)
error('algospike.bin_search, searching for non-existing, does not work', got == ~12)



got = []
items = 'a a d d d d d d d d d f i i i i i j j k k k l m n s s s s s s s s s v v'.split(' ')
multibin_search(got, items, [' ', 'd', 'i', 'g', 'k', 'm', 'z'])
got = [item[1] for item in sorted(got, key = lambda item : item[0])]
error('algospike.multibin_search, searching for non-existing, does not work',
      got[0] == ~0 and 2 <= got[1] <= 10 and 12 <= got[2] <= 16 and got[3] == ~12 and
      19 <= got[4] <= 21 and got[5] == 23 and got[6] == ~len(items))



items = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 100, 1000, 10000, 1 << 10, (1 << 20) + 4, (1 << 20) - 4, (1 << 32) - 1]
print(items)
got = [lb32(item) for item in items]
error('algospike.lb32 does not work', got == [0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 6, 9, 13, 10, 20, 19, 31])
got = [lb64(item) for item in items]
error('algospike.lb64 does not work', got == [0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 6, 9, 13, 10, 20, 19, 31])
got = [lb128(item) for item in items]
error('algospike.lb128 does not work', got == [0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 6, 9, 13, 10, 20, 19, 31])



items = [1 << 33, 1 << 40, 1 << 50, (1 << 50) - 10, (1 << 50) + 10, 1 << 60, (1 << 64) - 1]
got = [lb64(item) for item in items]
error('algospike.lb64 does not work', got == [33, 40, 50, 49, 50, 60, 63])
got = [lb128(item) for item in items]
error('algospike.lb128 does not work', got == [33, 40, 50, 49, 50, 60, 63])



items = [1 << 64, (1 << 64) + 1, (1 << 70) - 1, 1 << 70, 1 << 100, (1 << 127) + 1, (1 << 128) - 1]
got = [lb128(item) for item in items]
error('algospike.lb128 does not work', got == [64, 64, 69, 70, 100, 127, 127])




if error_ == 0:
    print('\033[32m%s\033[00m' % 'Everyting seems to be working')
exit(1 if error_ else 0)

