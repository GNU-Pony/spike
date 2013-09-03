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


errno = 0
def error(message, ok = False):
    global errno
    if not ok:
        errno = 2
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


def _(_a_op__b, expect, expect_2 = None):
    (_a, op, _b) = _a_op__b.split(' ')
    a = ScrollVersion.Version(_a.replace('*', ''), '*' in _a)
    b = ScrollVersion.Version(_b.replace('*', ''), '*' in _b)
    test = None
    if   op == '<':   test = lambda x, y : x <  y
    elif op == '<=':  test = lambda x, y : x <= y
    elif op == '==':  test = lambda x, y : x == y
    elif op == '!=':  test = lambda x, y : x != y
    elif op == '>':   test = lambda x, y : x >  y
    elif op == '>=':  test = lambda x, y : x >= y
    passed = test(a, b) == expect
    error('scrlver.ScrollVersion.Version, %s, does not work' % _a_op__b, passed)
    if passed:
        if op == '==':  _('%s %s %s' % (_a, '!=', _b), not expect)
        if op == '<':   _('%s %s %s' % (_b, '>', _a), expect)
        if op == '<=':  _('%s %s %s' % (_b, '>=', _a), expect)
    if expect_2 is not None:
        if op == '<':   _('%s %s %s' % (_a, '<=', _b), expect_2)
        if op == '>':   _('%s %s %s' % (_a, '>=', _b), expect_2)

_('1 == 1', True)
_('1 == 2', False)
_('1 == 1*', False)
_('1* == 1', False)
_('1* == 1*', False)
_('1-1 == 1-1', True)
_('1-1 == 1-2', False)
_('1-1 == 1', True)
_('1-2 == 1', True)
_('1 == 1-2', True)
_('1* == 1-2', False)
_('1* == 1-2*', False)
_('1 == 1-2*', False)
_('1 == 0:1', True)
_('0:1 == 1', True)
_('1:1 == 1', False)
_('1 == 1:1', False)
_('1:1 == 1:1', True)
_('1:1 == 1:1*', False)
_('1:1-4 == 1:1-4', True)
_('1:1-4 == 1:2-4', False)
_('1:1-4 == 1:1-3', False)
_('1:1-4 == 2:1-4', False)
_('1:1-4 == 1:1-4*', False)
_('1 == 1.1', False)
_('1.1 == 1.1', True)
_('1.1 == 1', False)
_('1.1 == 1.1*', False)
_('1:1.2-4 == 1:1.2-4', True)
_('1:1.2-4 == 1:1.2-4*', False)

def __(test, cc_cce, co_coe = None, oc_oce = None, oo_ooe = None):
    (A, op, B) = test.split(' ')
    a = A + '*'
    b = B + '*'
    if co_coe is None: co_coe = cc_cce
    if oc_oce is None: oc_oce = co_coe
    if oo_ooe is None: oo_ooe = co_coe
    if isinstance(cc_cce, bool):  cc_cce = (cc_cce, cc_cce)
    if isinstance(co_coe, bool):  co_coe = (co_coe, co_coe)
    if isinstance(oc_oce, bool):  oc_oce = (oc_oce, oc_oce)
    if isinstance(oo_ooe, bool):  oo_ooe = (oo_ooe, oo_ooe)
    _('%s %s %s' % (A, op, B), cc_cce[0], cc_cce[1])
    _('%s %s %s' % (A, op, b), co_coe[0], co_coe[1])
    _('%s %s %s' % (a, op, B), oc_oce[0], oc_oce[1])
    _('%s %s %s' % (a, op, b), oo_ooe[0], oo_ooe[1])

true = (False, True)
__('1 < 1', true, False)
__('1 < 1-1', true, False)
__('1-1 < 1', true, False)
__('1-1 < 1-1', true, False)
__('1 < 0:1', true, False)
__('0:1 < 1', true, False)
__('0:1 < 0:1', true, False)
__('1 < 1:1', True)
__('1:1 < 1', False)
__('1:1 < 1:1', true, False)
__('1:1 < 2:1', True)
__('2:1 < 1:1', False)
__('1-1 < 1-2', True)
__('1-2 < 1-1', False)
__('1-1 < 3:1-2', True)
__('1-2 < 3:1-1', True)
__('3:1-1 < 1-2', False)
__('3:1-2 < 1-1', False)
__('3:1-1 < 3:1-2', True)
__('3:1-2 < 3:1-1', False)
__('1 < 2', True)
__('2 < 1', False)
__('2:1 < 2', False)
__('2:2 < 1', False)
__('1 < 2:2', True)
__('2 < 2:1', True)
__('1 < 1.2', True)
__('1.1 < 1.2', True)
__('1.2 < 1.1', False)
__('1.2 < 1.2', true, False)
__('1.2 < 1', False)
__('1.2 < 2.1', True)



def _(_a, _b, expect):
    a = ScrollVersion(_a)
    b = ScrollVersion(_b)
    contains = a in b
    equals = a == b
    contains_ = b in a
    equals_ = b == a
    same_hash = hash(a) == hash(b)
    error('hash(scrlver.ScrollVersion), does not work', same_hash or not contains)
    error('scrlver.ScrollVersion, ==, does not work', contains == equals)
    error('scrlver.ScrollVersion, in, does not work', contains == expect)
    error('scrlver.ScrollVersion, == (mirrored), does not work', contains == equals_)
    error('scrlver.ScrollVersion, in (mirrored), does not work', contains == contains_)
    passed = (same_hash or not contains) and contains == equals and contains == expect
    if not passed:
        print('  \033[33mFor:  %s\033[00m' % '%s ~ %s' % (_a, _b))

_('test', 'test', True)
_('test', 'test=1', True)
_('test', 'test=1-1', True)
_('test', 'test=1:1', True)
_('test', 'test=1:1-1', True)
_('test', 'xyz', False)
_('test', 'test<>1', True)
_('test', 'test<1', True)
_('test', 'test<=1', True)
_('test', 'test>1', True)
_('test', 'test>=1', True)
_('test', 'test=2', True)
_('test', 'test=2-2', True)
_('test', 'test=2:2', True)
_('test', 'test=2:2-2', True)
_('test', 'test<>2', True)
_('test', 'test<2', True)
_('test', 'test<=2', True)
_('test', 'test>2', True)
_('test', 'test>=2', True)
_('test', 'test>1<2', True)
_('test', 'test>1<=2', True)
_('test', 'test>=1<2', True)
_('test', 'test>=1<=2', True)

_('test=1', 'test', True)
_('test=1', 'test=1', True)
_('test=1', 'test=1-1', True)
_('test=1', 'test=1:1', False)
_('test=1', 'test=1:1-1', False)
_('test=1', 'xyz', False)
_('test=1', 'test<>1', False)
_('test=1', 'test<1', False)
_('test=1', 'test<=1', True)
_('test=1', 'test>1', False)
_('test=1', 'test>=1', True)
_('test=1', 'test=2', False)
_('test=1', 'test=2-2', False)
_('test=1', 'test=2:2', False)
_('test=1', 'test=2:2-2', False)
_('test=1', 'test<>2', True)
_('test=1', 'test<2', True)
_('test=1', 'test<=2', True)
_('test=1', 'test>2', False)
_('test=1', 'test>=2', False)
_('test=1', 'test>1<2', False)
_('test=1', 'test>1<=2', False)
_('test=1', 'test>=1<2', True)
_('test=1', 'test>=1<=2', True)

_('test=1.1', 'test', True)
_('test=1.1', 'test=1', False)
_('test=1.1', 'test=1-1', False)
_('test=1.1', 'test=1:1', False)
_('test=1.1', 'test=1:1-1', False)
_('test=1.1', 'xyz', False)
_('test=1.1', 'test<>1', True)
_('test=1.1', 'test<1', False)
_('test=1.1', 'test<=1', False)
_('test=1.1', 'test>1', True)
_('test=1.1', 'test>=1', True)
_('test=1.1', 'test=2', False)
_('test=1.1', 'test=2-2', False)
_('test=1.1', 'test=2:2', False)
_('test=1.1', 'test=2:2-2', False)
_('test=1.1', 'test<>2', True)
_('test=1.1', 'test<2', True)
_('test=1.1', 'test<=2', True)
_('test=1.1', 'test>2', False)
_('test=1.1', 'test>=2', False)
_('test=1.1', 'test>1<2', True)
_('test=1.1', 'test>1<=2', True)
_('test=1.1', 'test>=1<2', True)
_('test=1.1', 'test>=1<=2', True)

_('test=1-1', 'test', True)
_('test=1-1', 'test=1', True)
_('test=1-1', 'test=1-1', True)
_('test=1-1', 'test=1:1', False)
_('test=1-1', 'test=1:1-1', False)
_('test=1-1', 'xyz', False)
_('test=1-1', 'test<>1', False)
_('test=1-1', 'test<1', False)
_('test=1-1', 'test<=1', True)
_('test=1-1', 'test>1', False)
_('test=1-1', 'test>=1', True)
_('test=1-1', 'test=2', False)
_('test=1-1', 'test=2-2', False)
_('test=1-1', 'test=2:2', False)
_('test=1-1', 'test=2:2-2', False)
_('test=1-1', 'test<>2', True)
_('test=1-1', 'test<2', True)
_('test=1-1', 'test<=2', True)
_('test=1-1', 'test>2', False)
_('test=1-1', 'test>=2', False)
_('test=1-1', 'test>1<2', False)
_('test=1-1', 'test>1<=2', False)
_('test=1-1', 'test>=1<2', True)
_('test=1-1', 'test>=1<=2', True)

_('test=1:1', 'test', True)
_('test=1:1', 'test=1', False)
_('test=1:1', 'test=1-1', False)
_('test=1:1', 'test=1:1', True)
_('test=1:1', 'test=1:1-1', True)
_('test=1:1', 'xyz', False)
_('test=1:1', 'test<>1', True)
_('test=1:1', 'test<1', False)
_('test=1:1', 'test<=1', False)
_('test=1:1', 'test>1', True)
_('test=1:1', 'test>=1', True)
_('test=1:1', 'test=2', False)
_('test=1:1', 'test=2-2', False)
_('test=1:1', 'test=2:2', False)
_('test=1:1', 'test=2:2-2', False)
_('test=1:1', 'test<>2', True)
_('test=1:1', 'test<2', False)
_('test=1:1', 'test<=2', False)
_('test=1:1', 'test>2', True)
_('test=1:1', 'test>=2', True)
_('test=1:1', 'test>1<2', False)
_('test=1:1', 'test>1<=2', False)
_('test=1:1', 'test>=1<2', False)
_('test=1:1', 'test>=1<=2', False)

_('test<>1', 'test', True)
_('test<>1', 'test=1', False)
_('test<>1', 'test=1-1', False)
_('test<>1', 'test=1:1', True)
_('test<>1', 'test=1:1-1', True)
_('test<>1', 'xyz', False)
_('test<>1', 'test<>1', True)
_('test<>1', 'test<1', True)
_('test<>1', 'test<=1', True)
_('test<>1', 'test>1', True)
_('test<>1', 'test>=1', True)
_('test<>1', 'test=2', True)
_('test<>1', 'test=2-2', True)
_('test<>1', 'test=2:2', True)
_('test<>1', 'test=2:2-2', True)
_('test<>1', 'test<>2', True)
_('test<>1', 'test<2', True)
_('test<>1', 'test<=2', True)
_('test<>1', 'test>2', True)
_('test<>1', 'test>=2', True)
_('test<>1', 'test>1<2', True)
_('test<>1', 'test>1<=2', True)
_('test<>1', 'test>=1<2', True)
_('test<>1', 'test>=1<=2', True)

_('test<1', 'test<1', True)
_('test<1', 'test<=1', True)
_('test<=1', 'test<1', True)
_('test<=1', 'test<=1', True)
_('test<1', 'test>1', False)
_('test<1', 'test>=1', False)
_('test<=1', 'test>1', False)
_('test<=1', 'test>=1', True)
_('test>1', 'test<1', False)
_('test>1', 'test<=1', False)
_('test>=1', 'test<1', False)
_('test>=1', 'test<=1', True)
_('test>1', 'test>1', True)
_('test>1', 'test>=1', True)
_('test>=1', 'test>1', True)
_('test>=1', 'test>=1', True)

def __(a, b, cc = None, co = None, oc = None, oo = None):
    if cc is not None:  _(a, b, cc)
    if co is not None:  _(a.replace('<=', '<'), b, co)
    if oc is not None:  _(a.replace('>=', '>'), b, oc)
    if oo is not None:  _(a.replace('=', ''),   b, oo)

__('test>=2<=4', 'test>=0<=1', False, False, False, False)
__('test>=2<=4', 'test>=0<1', False, False, False, False)
__('test>=2<=4', 'test>0<=1', False, False, False, False)
__('test>=2<=4', 'test>0<1', False, False, False, False)
__('test>=2<=4', 'test>=0<=2', True, True, False, False)
__('test>=2<=4', 'test>=0<2', False, False, False, False)
__('test>=2<=4', 'test>0<=2', True, True, False, False)
__('test>=2<=4', 'test>0<2', False, False, False, False)
__('test>=2<=4', 'test>=0<=3', True, True, True, True)
__('test>=2<=4', 'test>=0<3', True, True, True, True)
__('test>=2<=4', 'test>0<=3', True, True, True, True)
__('test>=2<=4', 'test>0<3', True, True, True, True)
__('test>=2<=4', 'test>=0<=4', True, True, True, True)
__('test>=2<=4', 'test>=0<4', True, True, True, True)
__('test>=2<=4', 'test>0<=4', True, True, True, True)
__('test>=2<=4', 'test>0<4', True, True, True, True)
__('test>=2<=4', 'test>=0<=5', True, True, True, True)
__('test>=2<=4', 'test>=0<5', True, True, True, True)
__('test>=2<=4', 'test>0<=5', True, True, True, True)
__('test>=2<=4', 'test>0<5', True, True, True, True)
__('test>=2<=4', 'test>=1<=2', True, True, False, False)
__('test>=2<=4', 'test>=1<2', False, False, False, False)
__('test>=2<=4', 'test>1<=2', True, True, False, False)
__('test>=2<=4', 'test>1<2', False, False, False, False)
__('test>=2<=4', 'test>=1<=3', True, True, True, True)
__('test>=2<=4', 'test>=1<3', True, True, True, True)
__('test>=2<=4', 'test>1<=3', True, True, True, True)
__('test>=2<=4', 'test>1<3', True, True, True, True)
__('test>=2<=4', 'test>=1<=4', True, True, True, True)
__('test>=2<=4', 'test>=1<4', True, True, True, True)
__('test>=2<=4', 'test>1<=4', True, True, True, True)
__('test>=2<=4', 'test>1<4', True, True, True, True)
__('test>=2<=4', 'test>=1<=5', True, True, True, True)
__('test>=2<=4', 'test>=1<5', True, True, True, True)
__('test>=2<=4', 'test>1<=5', True, True, True, True)
__('test>=2<=4', 'test>1<5', True, True, True, True)
__('test>=2<=4', 'test>=2<=3', True, True, True, True)
__('test>=2<=4', 'test>=2<3', True, True, True, True)
__('test>=2<=4', 'test>2<=3', True, True, True, True)
__('test>=2<=4', 'test>2<3', True, True, True, True)
__('test>=2<=4', 'test>=2<=4', True, True, True, True)
__('test>=2<=4', 'test>=2<4', True, True, True, True)
__('test>=2<=4', 'test>2<=4', True, True, True, True)
__('test>=2<=4', 'test>2<4', True, True, True, True)
__('test>=2<=4', 'test>=2<=5', True, True, True, True)
__('test>=2<=4', 'test>=2<5', True, True, True, True)
__('test>=2<=4', 'test>2<=5', True, True, True, True)
__('test>=2<=4', 'test>2<5', True, True, True, True)
__('test>=2<=4', 'test>=3<=4', True, True, True, True)
__('test>=2<=4', 'test>=3<4', True, True, True, True)
__('test>=2<=4', 'test>3<=4', True, True, True, True)
__('test>=2<=4', 'test>3<4', True, True, True, True)
__('test>=2<=4', 'test>=3<=5', True, True, True, True)
__('test>=2<=4', 'test>=3<5', True, True, True, True)
__('test>=2<=4', 'test>3<=5', True, True, True, True)
__('test>=2<=4', 'test>3<5', True, True, True, True)
__('test>=2<=4', 'test>=4<=5', True, False, True, False)
__('test>=2<=4', 'test>=4<5', True, False, True, False)
__('test>=2<=4', 'test>4<=5', False, False, False, False)
__('test>=2<=4', 'test>4<5', False, False, False, False)
__('test>=2<=4', 'test>=5<=6', False, False, False, False)
__('test>=2<=4', 'test>=5<6', False, False, False, False)
__('test>=2<=4', 'test>5<=6', False, False, False, False)
__('test>=2<=4', 'test>5<6', False, False, False, False)



def _(_a, _b, expect_u, expect_i):
    _a = 'test' + _a
    _b = 'test' + _b
    expect_u = None if expect_u is None else 'test' + expect_u
    expect_i = None if expect_i is None else 'test' + expect_i
    a = ScrollVersion(_a)
    b = ScrollVersion(_b)
    got_u = a.union(b).full
    got_i = a.intersection(b)
    got_u_ = b.union(a).full
    got_i_ = b.intersection(a)
    got_i = got_i if got_i is None else got_i.full
    got_i_ = got_i_ if got_i_ is None else got_i_.full
    union = '%s union %s == %s' % (_a, _b, expect_u)
    intersection = '%s intersection %s == %s' % (_a, _b, expect_i)
    error('scrlver.ScrollVersion.union, %s, does not work' % union, got_u == expect_u)
    error('scrlver.ScrollVersion.intersection, %s, does not work' % intersection, got_i == expect_i)
    error('scrlver.ScrollVersion.union, mirror of %s, does not work' % union, got_u_ == got_u)
    if not got_u_ == got_u:
        print('  \033[33mGot %s but for %s in mirror\033[00m' % (got_u, got_u_))
    error('scrlver.ScrollVersion.intersection, mirror of %s, does not work' % intersection, got_i_ == got_i)
    if not got_i_ == got_i:
        print('  \033[33mGot %s but for %s in mirror\033[00m' % (got_i, got_i_))

_('', '=1', '', '=1')
_('=1-1', '=1', '=1', '=1-1')
_('<>2', '<>1', '', None)
_('>1', '<2', '', '>1<2')
_('>1', '>2', '>1', '>2')
_('>1', '>=1', '>=1', '>1')
_('<1', '<2', '<2', '<1')
_('<1', '<=1', '<=1', '<1')
_('>1<2', '>=0<=2', '>=0<=2', '>1<2')
_('>1<2', '>=1<2', '>=1<2', '>1<2')
_('>1<2', '>1<=2', '>1<=2', '>1<2')
_('>1<2', '>0<3', '>0<3', '>1<2')
_('>1<2', '>0<1.1', '>0<2', '>1<1.1')
_('>1<2', '>1.1<3', '>1<3', '>1.1<2')
_('>1<2', '>1.1', '>1', '>1.1<2')
_('>1<2', '>0', '>0', '>1<2')
_('>1<2', '<1.1', '<2', '>1<1.1')
_('>1<2', '<2', '<2', '>1<2')
_('>1<2', '<>3', '<>3', '>1<2')
_('>1', '<>3', '', '>1')
_('<4', '<>3', '', '<4')
_('>=3', '<>3', '', '>=3')
_('<=3', '<>3', '', '<=3')
_('>=1<2', '>1<=2', '>=1<=2', '>1<2')



def _(_a, _b, expect):
    _a = 'test' + _a
    _b = 'test' + _b
    expect = None if expect is None else 'test' + expect
    a = ScrollVersion(_a)
    b = ScrollVersion(_b)
    joinable = a.joinable_with(b)
    joinable_ = b.joinable_with(a)
    error('scrlver.ScrollVersion.joinable_with, does not work', joinable == (expect is not None))
    error('scrlver.ScrollVersion.joinable_with, mirror, does not work', joinable == joinable_)
    if joinable and (expect is not None):
        join = a.join(b)
        join_ = b.join(a)
        error('scrlver.ScrollVersion.join, does not work', join.full == expect)
        error('scrlver.ScrollVersion.join, mirror, does not work', join.full == join_.full)

_('=1', '=2', None)
_('=1', '=1', None)
_('=1', '<>1', '')
_('=1', '<>2', None)
_('<>1', '<>2', None)
_('=1', '>1', '>=1')
_('=1', '<1', '<=1')
_('>1<2', '>=2', '>1')
_('>1<2', '>=2<3', '>1<3')
_('>=1', '<1', '')
_('>1', '<=1', '')
_('>=1', '<=1', None)
_('>1<2', '>2', None)
_('>1<2', '>=2', '>1')
_('>1<2', '=1', '>=1<2')



union = set()
ScrollVersion('=1').union_add(union)
ScrollVersion('=2').union_add(union)
ScrollVersion('<>1').union_add(union)
got = str([str(e) for e in list(union)])
error('scrlver.ScrollVersion.union_add, does not work', got == "['']")

union = set()
ScrollVersion('=1').union_add(union)
ScrollVersion('=2').union_add(union)
ScrollVersion('=2').union_add(union)
got = str([str(e) for e in list(union)])
error('scrlver.ScrollVersion.union_add, does not work', got == "['=1', '=2']" or got == "['=2', '=1']")
ScrollVersion('>1<2').union_add(union)
got = str([str(e) for e in list(union)])
ScrollVersion('>1.1<1:1').union_add(union)
got = str([str(e) for e in list(union)])
error('scrlver.ScrollVersion.union_add, does not work', got == "['>=1<1:1']")



intersection = set()
ScrollVersion('').intersection_add(intersection)
got = str([str(e) for e in list(intersection)])
error('scrlver.ScrollVersion.intersection_add, does not work', got == "['']")
ScrollVersion('>1<2').intersection_add(intersection)
got = str([str(e) for e in list(intersection)])
error('scrlver.ScrollVersion.intersection_add, does not work', got == "['>1<2']")
ScrollVersion('>1.1<3').intersection_add(intersection)
got = str([str(e) for e in list(intersection)])
error('scrlver.ScrollVersion.intersection_add, does not work', got == "['>1.1<2']")
ScrollVersion('>3<4').intersection_add(intersection)
got = str([str(e) for e in list(intersection)])
error('scrlver.ScrollVersion.intersection_add, does not work', got == "['>1.1<2', '>3<4']" or got == "['>3<4', '>1.1<2']")
ScrollVersion('>=1.2<=3.2').intersection_add(intersection)
got = str([str(e) for e in list(intersection)])
error('scrlver.ScrollVersion.intersection_add, does not work', got == "['>=1.2<2', '>3<=3.2']" or got == "['>3<=3.2', '>=1.2<2']")



if errno == 0:
    print('\033[32m%s\033[00m' % 'Everyting seems to be working')
exit(errno)

