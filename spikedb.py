#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

INITIALS_LEN = 4

# TODO insert and remove is needed
# TODO paths should be db separated into groups by the binary logarithm of the length of their paths


# keep in mind that it we sould not depend on sort() using a stabil sort


def fetch(db, maxlen, values):
    buckets = {}
    for path in sort(values):
        pos = 0
        initials = ''
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
        buckets[ivalue].append(value)
    rc = []
    with open(db, 'rb') as file:
        offset = 0
        position = 0
        amount = 0
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        masterseek = file.read(masterseeklen)
        for initials in sort(buckets.keys()):
            if position >= initials:
                position = 0
                offset = 0
                amount = 0
            while position <= initials:
                offset += amount
                amount = [int(b) for b in list(masterseek[3 * position : 3 * (position + 1)])]
                amount = (amount[0] << 16) + (amount[1] << 8) + amount[2]
                position += 1
            file.seek(offset = masterseeklen + offset * (maxlen + 3), whence = 0) # 0 means from the start of the stream
    return rc


def make(db, maxlen, pairs):
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
    counts = []
    with open(db, 'wb') as file:
        wbuf = [0] * (1 << (INITIALS_LEN << 2))
        for i in range(3):
            file.write(zbuf)
        wbuf = None
        for initials in sort(buckets.keys()):
            bucket = buckets[initials]
            for pair in bucket:
                (filepath, package) = pair
                filepath = filepath + '\0' * (maxlen - len(filepath))
                filepath = filepath.encode('utf8')
                package = bytes([b & 255 for b in [package >> 16, package >> 8, package]])
                file.write(filepath)
                file.write(package)
            counts.append((initials, len(bucket)))
        file.flush()
        for (initials, count) in counts:
            file.seek(offset = 3 * initials, whence = 0) # 0 means from the start of the stream
            wbuf = bytes([b & 255 for b in [count >> 16, count >> 8, count]])
            file.write(wbuf)
        file.flush()



if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make('testdb', 50, [(comb[comb.find(' ') + 1:], hash(comb[:comb.find(' ')]) & 0xFFFFFF) for comb in data])
else:
    for pair in fetch('testdb', 50, sort([os.path.realpath(f)[:50] for f in sys.args[1:]])):
        print('%s --> %s' % pair)

