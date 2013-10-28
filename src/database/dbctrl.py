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
import os

from database.spikedb import *
import dragonsuite



CONVERT_NONE = 0
'''
Do not convert database values
'''

CONVERT_INT = 1
'''
Convert database values as if numerical
'''

CONVERT_STR = 2
'''
Convert database values as if text
'''



DB_SIZE_ID = 4
'''
The maximum length of scroll ID
'''

DB_SIZE_SCROLL = 64
'''
The maximum length of scroll name
'''

DB_SIZE_FILEID = 8
'''
The maximum length of file ID
'''

DB_SIZE_FILELEN = 1
'''
The maximum length of lb(file name length)
'''


## Value/key type, these are (type_name:str, value_size:int, value_type:int)-tuples

DB_FILE_NAME   = lambda n : ('file'          if n < 0 else ('file%i' % n),
                             DB_SIZE_FILELEN if n < 0 else (1 << n),
                             CONVERT_INT     if n < 0 else CONVERT_STR)
'''
Value/key type for file name or file name length.
Call with a negative value for file name length, and with the value
fetch using that value/key type for file name
'''

DB_FILE_ID     = ('fileid', DB_SIZE_FILEID,  CONVERT_INT)
'''
Value/key type for file ID
'''

DB_FILE_ENTIRE = ('+',      0,               CONVERT_NONE)
'''
Value/key type for file claimed recursively at detection time
'''

DB_PONY_NAME   = ('scroll', DB_SIZE_SCROLL,  CONVERT_STR)
'''
Value/key type for pony name
'''

DB_PONY_ID     = ('id',     DB_SIZE_ID,      CONVERT_INT)
'''
Value/key type for pony ID
'''

DB_PONY_DEPS   = ('deps',   DB_SIZE_ID,      CONVERT_INT)
'''
Value/key type for pony ID dependency
'''



class DBCtrl():
    '''
    Advanced programming interface for Spike's database
    '''
    
    def __init__(self, spike_path):
        '''
        Constructor
        
        @param  spike_path:str  The path for Spike
        '''
        self.path = (spike_path + os.sep + 'var/').replace('%', '%%')
        if not os.path.exists(self.path):
            dragonsuite.mkdir_p(self.path)
    
    
    def open_db(self, private, key, value):
        '''
        Open a database
        
        @param   private:bool           Whether to open a private database
        @param   key:(str, int, int)    The key type of the database
        @param   value:(str, int, int)  The value type of the database
        @return  :SpikeDB               The database instance
        '''
        pre = '' if not private else 'priv_'
        db  = '%s%s_%s.%%i' % (pre, key[0], value[0])
        return SpikeDB(self.path + db, value[1])
    
    
    def joined_fetch(self, aggregator, input, types, private = None):
        '''
        Perform a database lookup by joining tables
        
        @param  aggregator:(str, str?)→void
                    Feed a input with its output when an output value has been found,
                    but with `None` as output if there is no output
        
        @param   input:list<str>             Input
        @param   types:itr<(str, int, int)>  The type in order of fetch and join
        @param   private:bool?               Whether to look in the private files rather then the public, `None` for both
        @return  :bool                       Whether the fetch was successful, if not, the database is corrupt
        '''
        error = [False]
        tables = []
        transpositions = []
        
        # Open databases
        privs = [private] if private is not None else [False, True]
        for i in range(len(types) - 1):
            tables.append([self.open_db(priv, types[i], types[i + 1]) for priv in privs])
            transpositions.append({})
        
        # Fetch and transpose information for all tables except the last one
        def unprefix(data):
            for i in range(len(data)):
                if data[i] != 0:
                    return data[i:]
            return bytes([0])
        def unsuffix(data):
            last = data.find(0)
            return data if last < 0 else data[:last]
        class Agg():
            def __init__(self, table_index):
                self.nones = {}
                self.index = table_index
            def __call__(self, item):
                if item in self.nones:
                    self.nones[item] += 1
                else:
                    self.nones[item] = 1
                if self.index == 0:
                    if self.nones[item] == len(privs):
                        aggregator(item, None)
                else:
                    error[0] = True
        for i in range(len(tables)):
            sink = []
            for table in tables[i]:
                table.fetch(sink, input if i == 0 else transpositions[i - 1].keys())
            value_format = types[i + 1][2]
            if value_format == CONVERT_INT:
                sink = [(key, None if value is None else unprefix(value)) for (key, value) in sink]
            elif value_format == CONVERT_STR:
                sink = [(key, None if value is None else unsuffix(value)) for (key, value) in sink]
            DBCtrl.transpose(transpositions[i], sink, types[i], Agg(i), False)
        
        # Join transposed tables
        last_table = transpositions[0]
        for i in range(1, len(transpositions)):
            cur_table = {}
            table = transpositions[i]
            for key in table.keys():
                if key not in cur_table:
                    cur_table[key] = []
                for item in table[key]:
                    cur_table[key] += last_table[item]
            last_table = cur_table
        
        # Send transposition of joined table
        for value in last_table.keys():
            for key in last_table[value]:
                aggregator(key, value)
        
        return not error[0]
    
    
    @staticmethod
    def get_existing(rc, pairs):
        '''
        Get keys that have values, there will be duplicates if the are multiple values
        
        @param   rc:append(str)?→void   The list to which existing keys is added
        @param   pairs:itr<(str, ¿E?)>  Key–value pairs
        @return  rc:append(str)→void    `rc` is returned, if `None`, a list<str> is created
        '''
        if rc is None:
            rc = []
        for (key, value) in pairs:
            if value is not None:
                rc.append(key)
        return rc
    
    
    @staticmethod
    def get_nonexisting(rc, pairs):
        '''
        Get keys that does not have values
        
        @param   rc:append(str)?→void   The list to which existing keys is added
        @param   pairs:itr<(str, ¿E?)>  Key–value pairs
        @return  rc:append(str)→void    `rc` is returned, if `None`, a list<str> is created
        '''
        if rc is None:
            rc = []
        for (key, value) in pairs:
            if value is None:
                rc.append(key)
        return rc
    
    
    @staticmethod
    def transpose(rc, pairs, value, none_aggregator, aggregate_none = True):
        '''
        Create a transposed dictionary form a pair list, the value is converted
        
        @param   rc:dict<str, list<str>>?                The dictionary to which the data is added
        @param   pairs:itr<(str, bytes?)>                Key–value pairs
        @param   value:(str, int, int)                   The value type of the database
        @param   none_aggregator:(str)|(str, ¿E?)?→void  Object for which a key is passed when a key is no value
        @param   aggregate_none:bool                     Whether to also pass `None` to `none_aggregator`
        @return  rc:dict<str, list<str>>                 `rc` is returned, if `None`, it is created
        '''
        conv = value[1]
        if rc is None:
            rc = {}
        if none_aggregator is None:
            for (key, value) in pairs:
                if value is not None:
                    value = DBCtrl.value_convert(value, conv)
                    if value in rc:
                        rc[value].append(key)
                    else:
                        rc[value] = [key]
        elif aggregate_none:
            for (key, value) in pairs:
                if value is None:
                    none_aggregator(key, None)
                else:
                    value = DBCtrl.value_convert(value, conv)
                    if key in rc:
                        rc[value].append(key)
                    else:
                        rc[value] = [key]
        else:
            for (key, value) in pairs:
                if value is None:
                    none_aggregator(key)
                else:
                    value = DBCtrl.value_convert(value, conv)
                    if value in rc:
                        rc[value].append(key)
                    else:
                        rc[value] = [key]
        return rc
    
    
    @staticmethod
    def tablise(rc, pairs, value, none_aggregator, aggregate_none = True):
        '''
        Create a dictionary form a pair list, the value is converted
        
        @param   rc:dict<str, list<str>>?                The dictionary to which the data is added
        @param   pairs:itr<(str, bytes?)>                Key–value pairs
        @param   value:(str, int, int)                   The value type of the database
        @param   none_aggregator:(str)|(str, ¿E?)?→void  Object for which a key is passed when a key is no value
        @param   aggregate_none:bool                     Whether to also pass `None` to `none_aggregator`
        @return  rc:dict<str, list<str>>                 `rc` is returned, if `None`, it is created
        '''
        conv = value[1]
        if rc is None:
            rc = {}
        if none_aggregator is None:
            for (key, value) in pairs:
                if value is not None:
                    value = DBCtrl.value_convert(value, conv)
                    if key in rc:
                        rc[key].append(value)
                    else:
                        rc[key] = [value]
        elif aggregate_none:
            for (key, value) in pairs:
                if value is None:
                    none_aggregator(key, None)
                else:
                    value = DBCtrl.value_convert(value, conv)
                    if key in rc:
                        rc[key].append(value)
                    else:
                        rc[key] = [value]
        else:
            for (key, value) in pairs:
                if value is None:
                    none_aggregator(key)
                else:
                    value = DBCtrl.value_convert(value, conv)
                    if key in rc:
                        rc[key].append(value)
                    else:
                        rc[key] = [value]
        return rc
    
    
    @staticmethod
    def value_convert(value, method):
        '''
        Convert a value from bytes to string
        
        @param   value:bytes  The value
        @param   method:int   Convertion method
        @return  :str         The value as string
        '''
        rc = ''
        if method == CONVERT_STR:
            for c in value:
                if c == 0:
                    break
                rc += chr(c)
        elif method == CONVERT_INT:
            for c in value:
                if (c != 0) or (len(rc) > 0):
                    rc += chr(c)
            if rc == '':
                return '\0'
        else:
            for c in value:
                rc += chr(c)
        return rc
    
    
    @staticmethod
    def raw_int(raw):
        '''
        Convert a raw integer stored in a string to an integer object
        
        @param   raw:str  Raw string
        @return  :int     Integer
        '''
        rc = 0
        for d in raw:
            rc = (rc << 8) | ord(d)
        return rc
    
    
    @staticmethod
    def int_raw(value, len):
        '''
        Convert an integer object to a raw integer stored in a string
        
        @param   value:int  Integer
        @parma   len:int    The length of the raw string
        @return  :str       Raw string
        '''
        arr = []
        for i in range(len):
            arr.append(value & 255)
            value >>= 8
        arr = reversed(arr)
        rc = ''
        for c in arr:
            rc += chr(c)
        return rc
    
    
    @staticmethod
    def int_bytes(value, len):
        '''
        Convert an integer object to a raw integer stored in a byte array
        
        @param   value:int  Integer
        @parma   len:int    The length of the raw byte array
        @return  :bytes     Raw byte array
        '''
        rc = []
        for i in range(len):
            rc.append(value & 255)
            value >>= 8
        return bytes(reversed(rc))

