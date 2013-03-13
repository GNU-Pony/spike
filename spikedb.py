#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

INITIALS_LEN = 4

# TODO insert and remove is needed
# TODO paths should be db separated into groups by the binary logarithm of the length of their paths


def fetch(db, maxlen, values):
    return []

def make(db, maxlen, pairs): # keep in mind that it we sould not depend on sort() using a stabil sort
    buckets = {}
    for pair in sort(pairs, key = lambda x : x[0]):
        pos = 0
        initials = ''
        (path, package) = pair
        while '/' in path[pos : -1]:
            pos = path.find('/') + 1
            initials += path[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += path[pos]
        if len(initials) > INITIALS_LEN:
            initials += initials[:INITIALS_LEN]
        initials = [(ord(c) & 15) for c in initials]
        ivalue = 0
        for initial in initials:
            ivalue = (ivalue << 4) | ivalue
        if ivalue not in buckets:
            buckets[ivalue] = []
        buckets[ivalue].append(pair)
    for initials in sort(buckets.keys()):
        for pair in buckets[initials]:
            pass


if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make('testdb', 50, [(comb[comb.find(' ') + 1:], comb[:comb.find(' ')]  ) for comb in data])
else:
    for pair in fetch('testdb', 50, sort([os.path.realpath(f) for f in sys.args[1:]])):
        print('%s --> %s' % pair)

