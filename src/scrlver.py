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

'''
Scroll Version (scrlver)

This module contains function that has to do with scroll version
'''


class ScrollVersion():
    '''
    Scroll with name and version range
    
    @variable  name:str         The name of the scroll
    @variable  lower:Version?   The lower bound in the version range
    @variable  upper:Version?   The upper bound in the version range
    @variable  open_lower:bool  Whether the lower bound is open
    @variable  open_upper:bool  Whether the upper bound is open
    @variable  complement:bool  Whether the range is stored in its complement
    '''
    
    def __init__(self, scroll):
        '''
        Constructor
        
        @param  scroll:version  Scroll with version range
        '''
        parts = scroll.replace('<', '\0<\0').replace('>', '\0>\0').replace('=', '\0=\0').replace('\0\0', '').split('\0')
        self.name = None
        self.lower = None
        self.upper = None
        self.open_lower = False
        self.open_upper = False
        self.complement = False
        
        if len(parts) == 1:
            self.name = parts[0]
        elif len(parts) == 3:
            if part[1] not in ('<', '<=', '>', '>=', '=', '<>'):
                return
            self.name = parts[0]
            ver = __Version(parts[2])
            islower = '>' in parts[1]
            isupper = '<' in parts[1]
            closed = '=' in parts[1]
            if islower == isupper:
                self.complement = islower and isupper
                (self.lower, self.upper) = (ver, ver)
            elif islower:
                self.lower = ver
                self.open_lower = not closed
            else:
                self.upper = ver
                self.open_upper = not closed
        elif len(parts) == 5:
            if (part[1] not in ('>', '>=')) or (part[3] not in ('<', '<=')):
                return
            self.name = parts[0]
            self.lower = __Version(parts[2])
            self.upper = __Version(parts[4])
            self.open_lower = '=' not in parts[1]
            self.open_upper = '=' not in parts[3]
    
    
    class __Version():
        '''
        A scroll version, not a range and not a scroll name
        '''
        
        def __init__(self, version):
            self.epoch = 0
            self.release = 1
            self.parts = []
            if ':' in version:
                self.epoch = int(version[:version.find(':')])
                version[version.find(':') + 1:]
            if '-' in version:
                self.release = int(version[version.find('-') + 1:])
                version[:version.find('-')]
            self.parts = version.split('-')

