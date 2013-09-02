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

from dragonsuite import *



class Claimer():
    '''
    Module for libspike for claiming files
    '''
    
    @staticmethod
    def get_files(files, recursive):
        '''
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

