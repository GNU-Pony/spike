#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

INITIALS_LEN = 5


def fetch(db, values):
    return []

def make(db, pairs):
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
        elif len(initials) < INITIALS_LEN:
            initials += '\0'


if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make('testdb', [(comb[comb.find(' ') + 1:], comb[:comb.find(' ')]  ) for comb in data])
else:
    for pair in fetch('testdb', sort([os.path.realpath(f) for f in sys.args[1:]])):
        print('%s --> %s' % pair)

