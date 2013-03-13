#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

def fetch(db, values):
    return []


if len(sys.args) == 1:
    pass
else:
    for pair in fetch('testdb', sort(sys.args[1:])):
        print('%s --> %s' % pair)

