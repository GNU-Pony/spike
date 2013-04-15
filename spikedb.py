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
import sys
import os
from algospike from *



INITIALS_LEN = 4
'''
The number of characters accounted for in the initials which are used to speed up searches
'''

# TODO paths should be db separated into groups by the binary logarithm of the length of their paths


class SpikeDB():
    '''
    Spike Database
    
    List (not relational) database functions that can used for simple
    information storage through out Spike. Spike Database is simple,
    fast for large data, easy to use, posses no additional dependencies
    and will never ever fail because of backwards incapabilities with
    the storage files.
    
    Spike Database can only do act as a string to bytes map, with a fixed
    value size.
    '''
    
    def __lbblocksize(file):
        '''
        Gets the binary logarithm of the block size of the device a file is placed in
        
        @param   file:str  The filename of the file, do not need to be the canonical path
        @return  :int      The binary logarithm of the block size, fall back to a regular value if not possible to determine
        '''
        try:
            return lb128(os.stat(os.path.realpath(file)).st_blksize)
        except:
            return 13
    
    
    def __fileread(stream, n):
        '''
        Read an exact amount of bytes from a file stream independent on how the native stream
        actually works (it should to the same thing for regular files, but we need to be on
        the safe side.)
        
        @param  stream:istream  The file's input stream
        @param  n:int           The number of bytes to read
        @parma  :bytes()        The exactly `n` read bytes
        '''
        rc = []
        read = 0
        while read < n:
            rc.append(stream.read(n - read))
            read += len(rc[-1])
        if len(rc) == 1:
            return rc
        else:
            rcc = []
            for c in rc:
                rcc += list(c)
            return bytes(rrc)
    
    
    def __makebuckets(keys):
        '''
        Create key buckets
        
        @param   keys:list<str>         Keys for with which to create buckets
        @return  :dict<int, list<str>>  Map for key initials to key buckets
        '''
        buckets = {}
        for key in unique(sorted(keys)):
            pos = 0
            initials = ''
            while '/' in key[pos : -1]:
                pos = key.find('/') + 1
                initials += key[pos]
            while len(initials) < INITIALS_LEN:
                pos += 1
                if pos == len(initials):
                    break
                initials += keys[pos]
            if len(initials) > INITIALS_LEN:
                initials += initials[:INITIALS_LEN]
            initials = [(ord(c) & 15) for c in initials]
            ivalue = 0
            for initial in initials:
                ivalue = (ivalue << 4) | ivalue
            if ivalue not in buckets:
                buckets[ivalue] = []
            buckets[ivalue].append(key)
        return buckets
    
    
    def __makepairbuckets(pairs):
        '''
        Create key–value buckets
        
        @param   pairs:list<(str, bytes)>        Key–value-pair for with which to create buckets
        @return  :dict<int, list<(str, bytes)>>  Map for key initials to key–value buckets
        '''
        buckets = {}
        for pair in sorted(pairs, key = lambda x : x[0]):
            pos = 0
            initials = ''
            (key, value) = pair
            while '/' in key[pos : -1]:
                pos = key.find('/') + 1
                initials += key[pos]
            while len(initials) < INITIALS_LEN:
                pos += 1
                if pos == len(initials):
                    break
                initials += key[pos]
            if len(initials) > INITIALS_LEN:
                initials += initials[:INITIALS_LEN]
            initials = [(ord(c) & 15) for c in initials]
            ivalue = 0
            for initial in initials:
                ivalue = (ivalue << 4) | ivalue
            if ivalue not in buckets:
                buckets[ivalue] = []
            buckets[ivalue].append(pair)
        return buckets
    
    
    def __fetch(rc, db, maxlen, keys, valuelen):
        '''
        Looks up values in a file
        
        @param   rc:append((str, bytes?))→void  Sink to which to append found results
        @param   db:str                         The database file
        @param   maxlen:int                     The length of keys
        @param   keys:list<str>                 Keys for which to search
        @param   valuelen:int                   The length of values
        @return  rc:                            `rc` is returned, filled with `(key:str, value:bytes?)`-pairs. `value` is `None` when not found
        '''
        buckets = __makebuckets(keys)
        devblocksize = __lbblocksize(db)
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
            masterseek = __fileread(file, masterseeklen)
            keyvallen = maxlen + valuelen
            for initials in sorted(buckets.keys()):
                if position >= initials:
                    position = 0
                    offset = 0
                    amount = 0
                while position <= initials:
                    offset += amount
                    amount = [int(b) for b in list(masterseek[3 * position : 3 * (position + 1)])]
                    amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                    position += 1
                fileoffset = masterseeklen + offset * keyvallen
                bucket = buckets[initials]
                bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
                list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
                class Agg():
                    def __init__(self, sink, keyMap, valueMap, limit):
                        self.sink = sink
                        self.keyMap = keyMap;
                        self.valueMap = valueMap;
                        self.limit = limit;
                    def append(self, item):
                        val = item[1]
                        val = None if val < 0 else self.valueMap.getValue(val)
                        key = self.keyMap[item[0]]
                        _key = self.valueMap.getKey(val)
                        self.sink.append((key, val))
                        _val = val
                        val += 1
                        while val < self.limit:
                            if self.valueMap.getKey(val) != _key:
                                break
                            self.sink.append((key, val))
                            val += 1
                        val = _val - 1
                        while val >= 0:
                            if self.valueMap.getKey(val) != _key:
                                break
                            self.sink.append((key, val))
                            val -= 1
                multibinsearch(Agg(rc, bucket, list, amount), list, bbucket)
        return rc
    
    
    def __remove(rc, db, maxlen, keys, valuelen):
        '''
        Looks up values in a file
        
        @param   rc:append(str)→void  Sink on which to append unfound keys
        @param   db:str               The database file
        @param   maxlen:int           The length of keys
        @param   keys:list<str>       Keys for which to search
        @param   valuelen:int         The length of values
        @return  rc:                  `rc` is returned
        '''
        buckets = __makebuckets(keys)
        devblocksize = __lbblocksize(db)
        wdata = []
        with open(db, 'rb') as file:
            removelist = []
            diminish = []
            offset = 0
            position = 0
            amount = 0
            masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
            masterseek = list(__fileread(file, masterseeklen))
            keyvallen = maxlen + valuelen
            for initials in sorted(buckets.keys()):
                if position >= initials:
                    position = 0
                    offset = 0
                    amount = 0
                while position <= initials:
                    offset += amount
                    amount = [int(b) for b in masterseek[3 * position : 3 * (position + 1)]]
                    amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                    position += 1
                fileoffset = masterseeklen + offset * keyvallen
                bucket = buckets[initials]
                bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
                curremove = len(removelist)
                list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
                class Agg():
                    def __init__(self, sink, failsink, keyMap, valueMap):
                        self.sink = sink
                        self.failsink = failsink
                        self.keyMap = keyMap
                        self.valueMap = valueMap
                    def append(self, item):
                        val = item[1]
                        if val < 0:
                            self.failsink.append(self.keyMap[item[0]])
                        else:
                            self.sink.append(val)
                            _key = self.valueMap.getKey(val)
                            _val = val
                            val += 1
                            while val < self.limit:
                                if self.valueMap.getKey(val) != _key:
                                    break
                                self.sink.append(val)
                                val += 1
                            val = _val - 1
                            while val >= 0:
                                if self.valueMap.getKey(val) != _key:
                                    break
                                self.sink.append(val)
                                val -= 1
                multibinsearch(Agg(removelist, rc, bucket, list), list, bbucket)
                diminishamount = len(removelist) - curremove
                if diminishamount > 0:
                    diminish.append(position - 1, diminishamount))
            end = 0
            pos = 0
            while pos < masterseeklen:
                amount = [int(b) for b in masterseek[pos : pos + 3]]
                end += (amount[0] << 16) | (amount[1] << 8) | amount[2]
                pos += 3
            for (index, amount) in diminish:
                pos = 3 * index
                was = [int(b) for b in masterseek[pos : pos + 3]]
                was = (was[0] << 16) | (was[1] << 8) | was[2]
                amount = was - amount
                masterseek[pos : pos + 3] = [b & 255 for b in [amount >> 16, amount >> 8, amount]]
            masterseek = bytes(masterseek)
            wdata.append(masterseek)
            pos = 0
            removelist.sort()
            for indices in (removelist, [end]):
                for index in indices:
                    if pos != index:
                        file.seek(offset = masterseeklen + pos * keyvallen, whence = 0) # 0 means from the start of the stream
                        wdata.append(__fileread(file, (index - pos) * keyvallen))
                    pos = index + 1
        with open(db, 'wb') as file:
            for data in wdata:
                file.write(data)
        return rc
    
    
    def __insert(db, maxlen, pairs):
        '''
        Insert, but do not override, values in a database
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = __makepairbuckets(pairs)
        devblocksize = __lbblocksize(db)
        insertlist = []
        initialscache = {}
        masterseek = None
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        data = []
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseek = list(__fileread(file, masterseeklen))
            keyvallen = maxlen + valuelen
            for initials in sorted(buckets.keys()):
                if position >= initials:
                    position = 0
                    offset = 0
                    amount = 0
                while position <= initials:
                    offset += amount
                    if initials in initialscache:
                        amount = initialscache[initials]
                    else:
                        amount = [int(b) for b in masterseek[3 * position : 3 * (position + 1)]]
                        amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                        initialscache[initials] = amount
                    position += 1
                fileoffset = masterseeklen + offset * keyvallen
                bucket = buckets[initials]
                bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
                list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
                class Agg():
                    def __init__(self, sink, keyMap, posCalc, initials):
                        self.sink = sink
                        self.keyMap = keyMap
                        self.posCalc = posCalc
                        self.initials = initials
                    def append(self, item):
                        pos = item[1]
                        pos = ~pos if pos < 0 else pos
                        (key, val) = self.keyMap[item[0]]
                        self.sink.append((key, val, self.posCalc(pos), self.initials))
                multibinsearch(Agg(insertlist, bucket, lambda x : fileoffset + x * keyvallen, initials), list, bbucket)
            insertlist.sort(key = lambda x : x[2])
            end = 0
            pos = 0
            while pos < masterseeklen:
                amount = [int(b) for b in masterseek[pos : pos + 3]]
                end += (amount[0] << 16) | (amount[1] << 8) | amount[2]
                pos += 3
            end = masterseeklen + end * keyvallen
            for (_k, _v, _p, initials) in insertlist:
                initialscache[initials] += 1
            for initials in initialscache:
                count = initialscache[initials]
                count = [b & 255 for b in [count >> 16, count >> 8, count]]
                masterseek[3 * initials : 3 * (initials + 1)] = count
            masterseek = bytes(masterseek)
            data.append(masterseek)
            last = masterseeklen
            file.seek(offset = last, whence = 0) # 0 means from the start of the stream
            for (key, val, pos, _) in insertlist + [(None, None, end, None)]:
                if pos > last:
                    data.append(__fileread(file, pos - last))
                    last = pos
                if key is not None:
                    key = key + '\0' * (maxlen - len(key.encode('utf8')))
                    data.append(key.encode('utf8'))
                    data.append(value)
        with open(db, 'wb') as file:
            for d in data:
                file.write(d)
        return rc
    
    
    def __override(db, maxlen, pairs):
        '''
        Insert, but override even possible, values in a database
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = __makepairbuckets(pairs)
        devblocksize = __lbblocksize(db)
        insertlist = []
        initialscache = {}
        masterseek = None
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        data = []
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseek = list(__fileread(file, masterseeklen))
            keyvallen = maxlen + valuelen
            for initials in sorted(buckets.keys()):
                if position >= initials:
                    position = 0
                    offset = 0
                    amount = 0
                while position <= initials:
                    offset += amount
                    if initials in initialscache:
                        amount = initialscache[initials]
                    else:
                        amount = [int(b) for b in masterseek[3 * position : 3 * (position + 1)]]
                        amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                        initialscache[initials] = amount
                    position += 1
                fileoffset = masterseeklen + offset * keyvallen
                bucket = buckets[initials]
                bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
                list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
                class Agg():
                    def __init__(self, sink, keyMap, posCalc, initials):
                        self.sink = sink
                        self.keyMap = keyMap
                        self.posCalc = posCalc
                        self.initials = initials
                    def append(self, item):
                        pos = item[1]
                        (pos, inits) = (~pos, -1) if pos < 0 else (pos, self.initials)
                        (key, val) = self.keyMap[item[0]]
                        self.sink.append((key, val, self.posCalc(pos), inits))
                multibinsearch(Agg(insertlist, bucket, lambda x : fileoffset + x * keyvallen, initials), list, bbucket)
            insertlist.sort(key = lambda x : x[2])
            end = 0
            pos = 0
            while pos < masterseeklen:
                amount = [int(b) for b in masterseek[pos : pos + 3]]
                end += (amount[0] << 16) | (amount[1] << 8) | amount[2]
                pos += 3
            end = masterseeklen + end * keyvallen
            initialscache[-1] = 0
            for (_k, _v, _p, initials) in insertlist:
                initialscache[initials] += 1
            for initials in initialscache:
                if initials >= 0:
                    count = initialscache[initials]
                    count = [b & 255 for b in [count >> 16, count >> 8, count]]
                    masterseek[3 * initials : 3 * (initials + 1)] = count
            masterseek = bytes(masterseek)
            data.append(masterseek)
            last = masterseeklen
            file.seek(offset = last, whence = 0) # 0 means from the start of the stream
            for (key, val, pos, initials) in insertlist + [(None, None, end, None)]:
                if pos > last:
                    data.append(__fileread(file, pos - last))
                    last = pos
                if key is not None:
                    key = key + '\0' * (maxlen - len(key.encode('utf8')))
                    data.append(key.encode('utf8'))
                    data.append(value)
                    if initials >= 0:
                        last += keyvallen
        with open(db, 'wb') as file:
            for d in data:
                file.write(d)
        return rc
    
    
    def __make(db, maxlen, pairs):
        '''
        Build a database from the ground
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = __makepairbuckets(pairs)
        counts = []
        with open(db, 'wb') as file:
            wbuf = bytes([0] * (1 << (INITIALS_LEN << 2)))
            for i in range(3):
                file.write(wbuf)
            wbuf = None
            for initials in sorted(buckets.keys()):
                bucket = buckets[initials]
                for pair in bucket:
                    (key, value) = pair
                    key = key + '\0' * (maxlen - len(key.encode('utf8')))
                    key = key.encode('utf8')
                    file.write(key)
                    file.write(value)
                counts.append((initials, len(bucket)))
            file.flush()
            for (initials, count) in counts:
                file.seek(offset = 3 * initials, whence = 0) # 0 means from the start of the stream
                wbuf = bytes([b & 255 for b in [count >> 16, count >> 8, count]])
                file.write(wbuf)
            file.flush()



class Blocklist():
    '''
    A blockdevice representated as a list
    '''
    def __init__(self, file, lbdevblock, offset, blocksize, itemsize, length):
        '''
        Constructor
        
        @param  file:inputfile  The file, it must be seekable
        @param  lbdevblock:int  The binary logarithm of the device's block size
        @param  offset:int      The list's offset in the file
        @param  blocksize:int   The number of bytes between the start of elements
        @param  itemsize:int    The size of each element
        @param  length:int      The number of elements
        '''
        self.file = file
        self.lbdevblock = lbdevblock
        self.devblock = 1 << lbdevblock
        self.offset = offset
        self.blocksize = blocksize
        self.itemsize = itemsize
        self.position = -1
        self.length = length
        self.buffer = None
    
    def __getitem__(self, index):
        '''
        Gets an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The element
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lbdevblock:
            self.position = pos >> self.lbdevblock
            self.buffer = self.file.read(self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos : pos + itemsize]
    
    def getValue(self, index):
        '''
        Gets the associated value to an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The associated value
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lbdevblock:
            self.position = pos >> self.lbdevblock
            self.buffer = self.file.read(self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos + itemsize : pos + blocksize]
    
    def getKey(self, index):
        '''
        Gets the associated key to an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The associated key
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lbdevblock:
            self.position = pos >> self.lbdevblock
            self.buffer = self.file.read(self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos : pos + itemsize]
    
    def __len__(self):
        '''
        Gets the number of elements
        
        @return  :int  The number of elements
        '''
        return self.length


if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    def _bin(value):
        return bytes([b & 255 for b in [value >> 16, value >> 8, value]])
    make(rc, 'testdb', 50, [(comb[comb.find(' ') + 1:], _bin(hash(comb[:comb.find(' ')]) & 0xFFFFFF)) for comb in data])
else:
    rc = []
    for pair in fetch('testdb', 50, sorted(rc, [os.path.realpath(f)[:50] for f in sys.args[1:]])):
        print('%s --> %s' % pair)

