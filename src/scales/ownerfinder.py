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

from database.dbctrl import *
from library.libspikehelper import *
from auxiliary.auxfunctions import *



class OwnerFinder():
    '''
    Module for libspike for finding file owners
    '''
    
    @staticmethod
    def get_file_pony_mapping(files, dirs, found, aggregator):
        '''
        Fetch filename to pony mapping
        
        @param   files:list<str>             The files of whose owner is to be identified
        @param   dirs:dict<str, str>         Mapping, to fill, from superdirectories to files without found scroll
        @param   found:set<str>              Set to fill with files whose owner has been found
        @param   owners:dict<str, set<str>>  Mapping from files to owners to fill
        @param   aggregator:(str, str)→void  Feed a file–scroll pair when an ownership has been identified
        @return  :byte                       Error code, 0 if none
        '''
        def agg(file, scroll):
            if scroll is not None:
                # Send and store found file
                aggregator(file, scroll)
                found.add(file)
                dict_add(owners, file, scroll)
            else:
                # List all superpaths to files without found scroll, so we can check the directories if they are recursive
                has_root = file.startswith(os.sep)
                parts = (file[1:] if has_root else file).split(os.sep)
                if has_root:
                    dict_append(dirs, os.sep, file)
                for i in range(len(parts) - 1):
                    dir = (os.sep + os.sep.join(parts[:i + 1])) if has_root else os.sep.join(parts[:i + 1])
                    dict_append(dirs, dir, file)
        return LibSpikeHelper.joined_lookup(agg, files, [DB_FILE_NAME(-1), DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
    
    
    @staticmethod
    def use_id(DB, dirs):
        '''
        Rekey superpaths to use ID rather then filename and discard unfound superpath
        
        @param   DB:DBCtrl                Database controller
        @param   dirs:dict<str⇒int, str>  The superpaths for remaining files
        @return  :byte                    Error code, 0 if none
        '''
        # Fetch file ID for filenames
        sink = fetch(DB, DB_FILE_NAME, DB_FILE_ID, [], dirs.keys())
        
        # Rekey superpaths to use ID rather then filename and discard unfound superpath
        nones = set()
        for (dirname, dirid) in sink:
            if dirid is None:
                if dirname not in nones:
                    nones.add(dirname)
                    continue
            else:
                dirid = DBCtrl.value_convert(dirid, CONVERT_INT)
                if dirid in dirs:
                    return 27
                dirs[dirid] = dirs[dirname]
            del dirs[dirname]
        return 0
    
    
    @staticmethod
    def filter_entire_claimed(DB, dirs, did_find, found):
        '''
        Determine if superpaths are --entire claimed and store information
        
        @param  DB:DBCtrl            Database control
        @param  dirs:dict<int, str>  Superpath ID to file mapping
        @param  did_find:set<int>    Superpath ID:s with found owner, will be filled with dictionaries
        @param  found:set<str>       Files with found owner, will be filled with addition files
        '''
        class Sink():
            def __init__(self):
                pass
            def append(self, dir_entire):
                (dir, entire) = dir_entire
                if entire is not None:
                    did_find.add(dir)
                    for file in dirs[dir]:
                        found.add(file)
        fetch(DB, DB_FILE_ID, DB_FILE_ENTIRE, Sink(), dirs.keys())
    
    
    @staticmethod
    def report_nonfound(files, found, aggregator):
        '''
        Report all non-found files
        
        @param  found:set<str>         Files whose owners has been found
        @parma  aggregator:(str)→void  Feed a file when it is determined what it has no identifiable owner
        '''
        for file in files:
            if file not in found:
                aggregator(file)
    
    
    @staticmethod
    def report_entire(did_found, owners, dirs, aggregator):
        '''
        Determine owner of found directories and send ownership
        
        @param   did_find:set<int>           Superpath ID:s with found owner
        @param   owners:dict<str, set<str>>  Mapping from files to owners
        @param   dirs:dict<str, str>         Mapping from superdirectories to files without found scroll
        @param   aggregator:(str, str)→void  Feed a file–scroll pair when an ownership has been identified
        @return  :byte                       Error code, 0 if none
        '''
        error = 0
        def agg(dirid, scroll):
            if scroll is None:
                error = 27
            else:
                for file in dirs[dirid]:
                    if (file not in owners) or (scroll not in owners[file]):
                        aggregator(file, scroll)
                        dict_add(owners, file, scroll)
        _error = LibSpikeHelper.joined_lookup(agg, list(did_find), [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        return max(error, _error)

