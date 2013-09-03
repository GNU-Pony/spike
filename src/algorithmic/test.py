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
from sha3sum import *
from scrlver import *


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



__ = lambda x : [] if x == '' else x.split(' ')
def _(p, deps, reqs):
    data[p] = (set(__(deps)), __(reqs))
rc, lostrc, data = [], [], {}
_('a', 'b', '')
_('b', 'c d', '')
_('d', 'c e', '')
_('e', 'x', 'x')
_('x', 'y', '')
_('y', 'x', 'x')
_('c', '', '')
got = tsort([], [], data)
error('algospike.tsort, unsortable, does not work', got == False)

data = {}
_('a', 'b', '')
_('b', 'c d', '')
_('d', 'c e', '')
_('e', 'x', 'x')
_('x', 'y', '')
_('y', 'x', '')
_('c', '', '')
got = tsort(rc, lostrc, data)
error('algospike.tsort, sortable, does not work', got and len(lostrc) == 0 and len(rc) == 7)
if got and len(lostrc) == 0 and len(rc) == 7:
    cycles = len(list(filter(lambda x : x[1] is not None, rc)))
    data = {}
    for (p, c) in rc:
        data[p] = c
    order = ''
    for (p, _) in rc:
        order += p
    xy = (data['x'] == ['y']) if order.find('x') < order.find('y') else (data['y'] == ['x'])
    order_ok = True
    for first_last in 'ba db cb cd ed xe'.split(' '):
        first, last = first_last[0], first_last[1]
        if order.find(first) > order.find(last):
            order_ok = False
            break
    error('algospike.tsort, sortable, does not work', cycles == 1 and xy and order_ok)



sha3 = SHA3()
got = sha3.digest_file('../../LICENSE')
ref = '827821773FDCE6F142E8C0446530DA596369AB63D5230E2A7D786AEAC0BDC406F1A50D8550F718A70384526980FEEADBF43348ADDBC50A13478B1A958C0E9218DC172DA2CB7591ED'
error('sha3sum does not work', got == ref)



scroll = ScrollVersion('test=1')
error('scrlver.ScrollVersion.__init__, full, does not work', scroll.full == 'test=1')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__str__, does not work', str(scroll) == scroll.full)
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, upper, does not work', scroll.upper == scroll.lower)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '1')
    error('scrlver.ScrollVersion.Version.__init__, epoch, does not work', scroll.lower.epoch == 0)
    error('scrlver.ScrollVersion.Version.__init__, release, does not work', scroll.lower.release == -1)
    error('scrlver.ScrollVersion.Version.__init__, parts, does not work', scroll.lower.parts == ['1'])


scroll = ScrollVersion('test<>4:1.2-3')
error('scrlver.ScrollVersion.__init__, full, does not work', scroll.full == 'test<>4:1.2-3')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__str__, does not work', str(scroll) == scroll.full)
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, upper, does not work', scroll.upper is not None)
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, upper, does not work', scroll.upper.version == scroll.lower.version)
    error('scrlver.ScrollVersion.__init__, upper, does not work', scroll.upper.open == scroll.lower.open)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == True)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '4:1.2-3')
    error('scrlver.ScrollVersion.Version.__init__, epoch, does not work', scroll.lower.epoch == 4)
    error('scrlver.ScrollVersion.Version.__init__, release, does not work', scroll.lower.release == 3)
    error('scrlver.ScrollVersion.Version.__init__, parts, does not work', scroll.lower.parts == ['1', '2'])


scroll = ScrollVersion('test>2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '2')


scroll = ScrollVersion('test>=2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '2')


scroll = ScrollVersion('test<2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.upper.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


scroll = ScrollVersion('test<=2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.upper.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


scroll = ScrollVersion('test>1<2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '1')
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


scroll = ScrollVersion('test>1<=2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '1')
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.upper.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


scroll = ScrollVersion('test>=1<2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '1')
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.upper.open == True)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


scroll = ScrollVersion('test>=1<=2')
error('scrlver.ScrollVersion.__init__, name, does not work', scroll.name == 'test')
error('scrlver.ScrollVersion.__init__, lower, does not work', scroll.lower is not None)
error('scrlver.ScrollVersion.__init__, uper, does not work', scroll.upper is not None)
error('scrlver.ScrollVersion.__init__, complement, does not work', scroll.complement == False)
if scroll.lower is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.lower.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.lower.version == '1')
if scroll.upper is not None:
    error('scrlver.ScrollVersion.__init__, version open, does not work', scroll.upper.open == False)
    error('scrlver.ScrollVersion.Version.__init__, version, does not work', scroll.upper.version == '2')


def _(_a, op, _b, test, expect):
    a = ScrollVersion.Version(_a.replace('*', ''), '*' in _a)
    b = ScrollVersion.Version(_b.replace('*', ''), '*' in _b)
    error('scrlver.ScrollVersion.Version, %s %s %s, does not work' % (_a, op, _b), test(a, b) == expect)

_('1', '==', '1', lambda a, b : a == b, True)
_('1', '==', '2', lambda a, b : a == b, False)
_('1', '==', '1*', lambda a, b : a == b, False)
_('1*', '==', '1', lambda a, b : a == b, False)
_('1*', '==', '1*', lambda a, b : a == b, False)
_('1-1', '==', '1-1', lambda a, b : a == b, True)
_('1-1', '==', '1-2', lambda a, b : a == b, False)
_('1-1', '==', '1', lambda a, b : a == b, True)
_('1-2', '==', '1', lambda a, b : a == b, True)
_('1', '==', '1-2', lambda a, b : a == b, True)
_('1*', '==', '1-2', lambda a, b : a == b, False)
_('1*', '==', '1-2*', lambda a, b : a == b, False)
_('1', '==', '1-2*', lambda a, b : a == b, False)
_('1', '==', '0:1', lambda a, b : a == b, True)
_('0:1', '==', '1', lambda a, b : a == b, True)
_('1:1', '==', '1', lambda a, b : a == b, False)
_('1', '==', '1:1', lambda a, b : a == b, False)
_('1:1', '==', '1:1', lambda a, b : a == b, True)
_('1:1', '==', '1:1*', lambda a, b : a == b, False)
_('1:1-4', '==', '1:1-4', lambda a, b : a == b, True)
_('1:1-4', '==', '1:2-4', lambda a, b : a == b, False)
_('1:1-4', '==', '1:1-3', lambda a, b : a == b, False)
_('1:1-4', '==', '2:1-4', lambda a, b : a == b, False)
_('1:1-4', '==', '1:1-4*', lambda a, b : a == b, False)
_('1', '==', '1.1', lambda a, b : a == b, False)
_('1.1', '==', '1.1', lambda a, b : a == b, True)
_('1.1', '==', '1', lambda a, b : a == b, False)
_('1.1', '==', '1.1*', lambda a, b : a == b, False)
_('1:1.2-4', '==', '1:1.2-4', lambda a, b : a == b, True)
_('1:1.2-4', '==', '1:1.2-4*', lambda a, b : a == b, False)

_('1', '!=', '1', lambda a, b : a != b, False)
_('1', '!=', '2', lambda a, b : a != b, True)
_('1', '!=', '1*', lambda a, b : a != b, True)
_('1*', '!=', '1', lambda a, b : a != b, True)
_('1*', '!=', '1*', lambda a, b : a != b, True)
_('1-1', '!=', '1-1', lambda a, b : a != b, False)
_('1-1', '!=', '1-2', lambda a, b : a != b, True)
_('1-1', '!=', '1', lambda a, b : a != b, False)
_('1-2', '!=', '1', lambda a, b : a != b, False)
_('1', '!=', '1-2', lambda a, b : a != b, False)
_('1*', '!=', '1-2', lambda a, b : a != b, True)
_('1*', '!=', '1-2*', lambda a, b : a != b, True)
_('1', '!=', '1-2*', lambda a, b : a != b, True)
_('1', '!=', '0:1', lambda a, b : a != b, False)
_('0:1', '!=', '1', lambda a, b : a != b, False)
_('1:1', '!=', '1', lambda a, b : a != b, True)
_('1', '!=', '1:1', lambda a, b : a != b, True)
_('1:1', '!=', '1:1', lambda a, b : a != b, False)
_('1:1', '!=', '1:1*', lambda a, b : a != b, True)
_('1:1-4', '!=', '1:1-4', lambda a, b : a != b, False)
_('1:1-4', '!=', '1:2-4', lambda a, b : a != b, True)
_('1:1-4', '!=', '1:1-3', lambda a, b : a != b, True)
_('1:1-4', '!=', '2:1-4', lambda a, b : a != b, True)
_('1:1-4', '!=', '1:1-4*', lambda a, b : a != b, True)
_('1', '!=', '1.1', lambda a, b : a != b, True)
_('1.1', '!=', '1.1', lambda a, b : a != b, False)
_('1.1', '!=', '1', lambda a, b : a != b, True)
_('1.1', '!=', '1.1*', lambda a, b : a != b, True)
_('1:1.2-4', '!=', '1:1.2-4', lambda a, b : a != b, False)
_('1:1.2-4', '!=', '1:1.2-4*', lambda a, b : a != b, True)




if error_ == 0:
    print('\033[32m%s\033[00m' % 'Everyting seems to be working')
exit(1 if error_ else 0)

