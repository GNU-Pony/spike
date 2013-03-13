#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

def fetch(db, values):
    return []

def make(pairs):
    pass


if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make([(comb[:comb.find(' ')], comb[comb.find(' ') + 1:]) for comb in data])
else:
    for pair in fetch('testdb', sort(sys.args[1:])):
        print('%s --> %s' % pair)

