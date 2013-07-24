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
from algospike import *



INITIALS_LEN = 4
'''
The number of characters accounted for in the initials which are used to speed up searches
'''


class SpikeDB():
    '''
    Spike Database
    
    List (not relational) database functions that can used for simple
    information storage through out Spike. Spike Database is simple,
    fast for large data, easy to use, posses no additional dependencies
    and will never ever fail because of backwards incapabilities with
    the storage files.
    
    Spike Database can only do act as a string to bytes map, with
    a fixed value size.
    '''
    
    def __init__(self, file_pattern, value_len):
        '''
        Constructor
        
        @param  file_pattern:str  The pattern for the database files, all ‘%’ should be duplicated after which it should include a ‘%i’ for internal use
        @param  value_len:int     The length of values
        '''
        self.file_pattern = file_pattern
        self.value_len = value_len
    
    
    
    def destroy_database(self):
        '''
        Remove the entire database
        '''
        # Using DragonSuite.rm because it shred:s files if the user has enabled shred:ing
        from dragonsuite import DragonSuite
        for lblen in range(64):
            db = self.file_pattern % lblen
            if os.path.exists(db):
                DragonSuite.rm(db)
    
    
    def list(self, rc):
        '''
        List all stored values
        
        @param   rc:append((str, bytes))→void  Sink to which to append found key–value-pairs
        @return  rc:                           `rc` is returned, filled with `(key:str, value:bytes)`-pairs
        '''
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        for lblen in range(32):
            db = self.file_pattern % lblen
            if os.path.exists(db):
                devblocksize = SpikeDB.__lb_blocksize(db)
                with open(db, 'rb') as file:
                    keyvallen = 1 << lblen + vallen
                    amount = os.stat(os.path.realpath(db)).st_size
                    amount = (amount - masterseeklen) // keyvallen
                    list = Blocklist(file, devblocksize, masterseeklen, keyvallen, 1 << lblen, amount)
                    for i in range(amount):
                        rc.append((list.get_key(i), list.get_value(i)))
        return rc
    
    
    def files(self):
        '''
        Gets all files associated with the database
        
        @return  :list<str>  All files associated with the database
        '''
        rc = []
        for lblen in range(32):
            db = self.file_pattern % lblen
            if os.path.exists(db):
                rc.append(db)
        return rc
    
    
    def fetch(self, rc, keys):
        '''
        Looks up values in a file
        
        @param   rc:append((str, bytes?))→void  Sink to which to append found results
        @param-  db:str                         The database file
        @param-  maxlen:int                     The length of keys
        @param   keys:list<str>                 Keys for which to search
        @param-  valuelen:int                   The length of values
        @return  rc:                            `rc` is returned, filled with `(key:str, value:bytes?)`-pairs. `value` is `None` when not found
        '''
        buckets = {}
        for key in keys:
            lblen = lb32(len(key))
            if (1 << lblen) < len(key):
                lblen += 1
            if lblen in buckets:
                buckets[lblen] = [key]
            else:
                buckets[lblen].append(key)
        for lblen in buckets:
            filename = self.file_pattern % lblen
            if os.path.exists(filename):
                SpikeDB.__fetch(rc, filename, 1 << lblen, buckets[lblen], self.value_len)
            else:
                for key in buckets[lblen]:
                    rc.append((key, None))
        return rc
    
    
    def remove(self, rc, keys):
        '''
        Looks up values in a file
        
        @param    rc:append(str)→void  Sink on which to append unfound keys
        @param-   db:str               The database file
        @param-   maxlen:int           The length of keys
        @param    keys:list<str>       Keys for which to search
        @param-   valuelen:int         The length of values
        @return   rc:                  `rc` is returned
        '''
        buckets = {}
        for key in keys:
            lblen = lb32(len(key))
            if (1 << lblen) < len(key):
                lblen += 1
            if lblen in buckets:
                buckets[lblen] = [key]
            else:
                buckets[lblen].append(key)
        for lblen in buckets:
            filename = self.file_pattern % lblen
            if os.path.exists(filename):
                SpikeDB.__remove(rc, filename, 1 << lblen, buckets[lblen], self.value_len)
            else:
                for key in buckets[lblen]:
                    rc.append(key)
        return rc
    
    
    def insert(self, pairs):
        '''
        Insert, but do not override, values in a database
        
        @param-  db:str                    The database file
        @param-  maxlen:int                The length of keys
        @param   pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = {}
        for pair in pairs:
            lblen = lb32(len(pair[0]))
            if (1 << lblen) < len(pair[0]):
                lblen += 1
            if lblen in buckets:
                buckets[lblen] = [pair]
            else:
                buckets[lblen].append(pair)
        for lblen in buckets:
            filename = self.file_pattern % lblen
            if os.path.exists(filename):
                SpikeDB.__insert(filename, 1 << lblen, buckets[lblen])
            else:
                SpikeDB.__make(filename, 1 << lblen, buckets[lblen])
    
    
    def override(self, pairs):
        '''
        Insert, but override even possible, values in a database
        
        @param-  db:str                    The database file
        @param-  maxlen:int                The length of keys
        @param   pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = {}
        for pair in pairs:
            lblen = lb32(len(pair[0]))
            if (1 << lblen) < len(pair[0]):
                lblen += 1
            if lblen in buckets:
                buckets[lblen] = [pair]
            else:
                buckets[lblen].append(pair)
        for lblen in buckets:
            filename = self.file_pattern % lblen
            if os.path.exists(filename):
                SpikeDB.__override(filename, 1 << lblen, buckets[lblen])
            else:
                SpikeDB.__make(filename, 1 << lblen, buckets[lblen])
    
    
    def make(self, pairs):
        '''
        Build a database from the ground
        
        @param-  db:str                    The database file
        @param-  maxlen:int                The length of keys
        @param   pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = {}
        for pair in pairs:
            lblen = lb32(len(pair[0]))
            if (1 << lblen) < len(pair[0]):
                lblen += 1
            if lblen in buckets:
                buckets[lblen] = [pair]
            else:
                buckets[lblen].append(pair)
        for lblen in buckets:
            filename = self.file_pattern % lblen
            SpikeDB.__make(filename, 1 << lblen, buckets[lblen])
    
    
    
    @staticmethod
    def __lb_blocksize(file):
        '''
        Gets the binary logarithm of the block size of the device a file is placed in
        
        @param   file:str  The filename of the file, do not need to be the canonical path
        @return  :int      The binary logarithm of the block size, fall back to a regular value if not possible to determine
        '''
        try:
            return lb32(os.stat(os.path.realpath(file)).st_blksize)
        except:
            return 13
    
    
    @staticmethod
    def __make_buckets(keys):
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
    
    
    @staticmethod
    def __make_pair_buckets(pairs):
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
    
    
    @staticmethod
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
        buckets = SpikeDB.__make_buckets(keys)
        devblocksize = SpikeDB.__lb_blocksize(db)
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
            masterseek = __file_read(file, masterseeklen)
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
                    def __init__(self, sink, key_map, value_map, limit):
                        self.sink = sink
                        self.key_map = key_map;
                        self.value_map = value_map;
                        self.limit = limit;
                    def append(self, item):
                        val = item[1]
                        val = None if val < 0 else self.value_map.get_value(val)
                        key = self.key_map[item[0]]
                        _key = self.value_map.get_key(val)
                        self.sink.append((key, val))
                        _val = val
                        val += 1
                        while val < self.limit:
                            if self.value_map.get_key(val) != _key:
                                break
                            self.sink.append((key, val))
                            val += 1
                        val = _val - 1
                        while val >= 0:
                            if self.value_map.get_key(val) != _key:
                                break
                            self.sink.append((key, val))
                            val -= 1
                multibin_search(Agg(rc, bucket, list, amount), list, bbucket)
        return rc
    
    
    @staticmethod
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
        buckets = SpikeDB.__make_buckets(keys)
        devblocksize = SpikeDB.__lb_blocksize(db)
        wdata = []
        with open(db, 'rb') as file:
            removelist = []
            diminish = []
            offset = 0
            position = 0
            amount = 0
            masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
            masterseek = list(__file_read(file, masterseeklen))
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
                    def __init__(self, sink, failsink, key_map, value_map):
                        self.sink = sink
                        self.failsink = failsink
                        self.key_map = key_map
                        self.value_map = value_map
                    def append(self, item):
                        val = item[1]
                        if val < 0:
                            self.failsink.append(self.key_map[item[0]])
                        else:
                            self.sink.append(val)
                            _key = self.value_map.get_key(val)
                            _val = val
                            val += 1
                            while val < self.limit:
                                if self.value_map.get_key(val) != _key:
                                    break
                                self.sink.append(val)
                                val += 1
                            val = _val - 1
                            while val >= 0:
                                if self.value_map.get_key(val) != _key:
                                    break
                                self.sink.append(val)
                                val -= 1
                multibin_search(Agg(removelist, rc, bucket, list), list, bbucket)
                diminishamount = len(removelist) - curremove
                if diminishamount > 0:
                    diminish.append((position - 1, diminishamount))
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
                        wdata.append(__file_read(file, (index - pos) * keyvallen))
                    pos = index + 1
        with open(db, 'wb') as file:
            for data in wdata:
                file.write(data)
        return rc
    
    
    @staticmethod
    def __insert(db, maxlen, pairs):
        '''
        Insert, but do not override, values in a database
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = SpikeDB.__make_pair_buckets(pairs)
        devblocksize = SpikeDB.__lb_blocksize(db)
        insertlist = []
        initialscache = {}
        masterseek = None
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        data = []
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseek = list(__file_read(file, masterseeklen))
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
                    def __init__(self, sink, key_map, pos_calc, initials):
                        self.sink = sink
                        self.key_map = key_map
                        self.pos_calc = pos_calc
                        self.initials = initials
                    def append(self, item):
                        pos = item[1]
                        pos = ~pos if pos < 0 else pos
                        (key, val) = self.key_map[item[0]]
                        self.sink.append((key, val, self.pos_calc(pos), self.initials))
                multibin_search(Agg(insertlist, bucket, lambda x : fileoffset + x * keyvallen, initials), list, bbucket)
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
                    data.append(__file_read(file, pos - last))
                    last = pos
                if key is not None:
                    key = key + '\0' * (maxlen - len(key.encode('utf8')))
                    data.append(key.encode('utf8'))
                    data.append(value)
        with open(db, 'wb') as file:
            for d in data:
                file.write(d)
        return rc
    
    
    @staticmethod
    def __override(db, maxlen, pairs):
        '''
        Insert, but override even possible, values in a database
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = SpikeDB.__make_pair_buckets(pairs)
        devblocksize = SpikeDB.__lb_blocksize(db)
        insertlist = []
        initialscache = {}
        masterseek = None
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        data = []
        with open(db, 'rb') as file:
            offset = 0
            position = 0
            amount = 0
            masterseek = list(__file_read(file, masterseeklen))
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
                    def __init__(self, sink, key_map, pos_calc, initials):
                        self.sink = sink
                        self.key_map = key_map
                        self.pos_calc = pos_calc
                        self.initials = initials
                    def append(self, item):
                        pos = item[1]
                        (pos, inits) = (~pos, -1) if pos < 0 else (pos, self.initials)
                        (key, val) = self.key_map[item[0]]
                        self.sink.append((key, val, self.pos_calc(pos), inits))
                multibin_search(Agg(insertlist, bucket, lambda x : fileoffset + x * keyvallen, initials), list, bbucket)
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
                    data.append(__file_read(file, pos - last))
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
    
    
    @staticmethod
    def __make(db, maxlen, pairs):
        '''
        Build a database from the ground
        
        @param  db:str                    The database file
        @param  maxlen:int                The length of keys
        @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
        '''
        buckets = SpikeDB.__make_pair_buckets(pairs)
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
    def __init__(self, file, lb_devblock, offset, blocksize, itemsize, length):
        '''
        Constructor
        
        @param  file:inputfile   The file, it must be seekable
        @param  lb_devblock:int  The binary logarithm of the device's block size
        @param  offset:int       The list's offset in the file
        @param  blocksize:int    The number of bytes between the start of elements
        @param  itemsize:int     The size of each element
        @param  length:int       The number of elements
        '''
        self.file = file
        self.lb_devblock = lb_devblock
        self.devblock = 1 << lb_devblock
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
        if self.position != pos >> self.lb_devblock:
            self.position = pos >> self.lb_devblock
            self.buffer = __file_read(self.file, self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos : pos + itemsize]
    
    def get_value(self, index):
        '''
        Gets the associated value to an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The associated value
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lb_devblock:
            self.position = pos >> self.lb_devblock
            self.buffer = __file_read(self.file, self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos + itemsize : pos + blocksize]
    
    def get_key_binary(self, index):
        '''
        Gets the associated key to an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The associated key
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lb_devblock:
            self.position = pos >> self.lb_devblock
            self.buffer = __file_read(self.file, self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos : pos + itemsize]
    
    def get_key(self, index):
        '''
        Gets the associated key to an element by index
        
        @param   index:int  The index of the element
        @return  :str       The associated key
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lb_devblock:
            self.position = pos >> self.lb_devblock
            self.buffer = __file_read(self.file, self.devblock)
        pos &= self.devblock - 1
        key = self.buffer[pos : pos + itemsize]
        key = key[:key.find(0)]
        return key.decode('utf-8', 'replace')
    
    def __len__(self):
        '''
        Gets the number of elements
        
        @return  :int  The number of elements
        '''
        return self.length



@staticmethod
def __file_read(stream, n):
    '''
    Read an exact amount of bytes from a file stream independent on how the native stream
    actually works (it should to the same thing for regular files, but we need to be on
    the safe side.)
    
    @param  stream:istream  The file's input stream
    @param  n:int           The number of bytes to read
    @param  :bytes          The exactly `n` read bytes
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

