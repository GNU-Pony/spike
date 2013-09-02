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
from dragonsuite import *



class Claimer():
    '''
    Module for libspike for claiming files
    '''
    
    @staticmethod
    def get_files(files, recursive):
        '''
        Gets all files to be claimed with asbolute paths
        
        @param   files:list<str>  Files, may or may not be absolute paths
        @param   recursive:bool   Whether the files are to be recursively claimed
        @return  :list<str>?      All files to be claimed with asbolute paths, `None` on error code 12
        '''
        files = [os.path.abspath(file) for file in files]
        for file in files:
            if not os.path.lexists(file):
                return None
        if recursive:
            files = find(files)
        return files
    
    
    @staticmethod
    def check_entire_conflicts(files, private, DB):
        '''
        Checks that the files are not owned by a recursively owned directory
        
        @param   files:list<str>  The file to claim
        @param   private:bool     Whether the pony is user private rather the user shared
        @param   DB:DBCtrl        Database controller
        @return  :list<int>       Conflicting file ID:s
        '''
        dirs = []
        has_root = len(filter(lambda file : file.startswith(os.sep), files)) == len(files)
        for file in files:
            parts = (file[1:] if has_root else file).split(os.sep)
            for i in range(len(parts) - 1):
                dirs.append(os.sep.join(parts[:i + 1]))
        dirs.sort()
        dirs = unique(dirs)
        if has_root:
            dirs = [os.sep] + [os.sep + dir for dir in dirs]
        db = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID)
        ids = db.fetch([], dirs)
        db = DB.open_db(private, DB_FILE_ID, DB_FILE_ENTIRE)
        return DBCtrl.get_existing([], db.fetch([], ids))

