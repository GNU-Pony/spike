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
    
    @variable  full:str         The scroll with its version range represent as a string
    @variable  name:str         The name of the scroll
    @variable  lower:Version?   The lower bound in the version range
    @variable  upper:Version?   The upper bound in the version range
    @variable  complement:bool  Whether the range is stored in its complement, can only be true one exact version is specified
    
    @author  Mattias Andrée (maandree@member.fsf.org)
    '''
    
    def __init__(self, scroll):
        '''
        Constructor
        
        @param  scroll:version  Scroll with version range
        '''
        parts = scroll.replace('<', '\0<\0').replace('>', '\0>\0').replace('=', '\0=\0').replace('\0\0', '').split('\0')
        self.full = scroll
        self.name = None
        self.lower = None
        self.upper = None
        self.complement = False
        
        if len(parts) == 1:
            self.name = parts[0]
        elif len(parts) == 3:
            if part[1] not in ('<', '<=', '>', '>=', '=', '<>'):
                return
            self.name = parts[0]
            ver = __Version(parts[2], '=' not in parts[1])
            islower = '>' in parts[1]
            isupper = '<' in parts[1]
            if islower == isupper:
                self.complement = islower and isupper
                ver.isopen = False
                (self.lower, self.upper) = (ver, ver)
            elif islower:
                self.lower = ver
            else:
                self.upper = ver
        elif len(parts) == 5:
            if (part[1] not in ('>', '>=')) or (part[3] not in ('<', '<=')):
                return
            self.name = parts[0]
            self.lower = __Version(parts[2], '=' not in parts[1])
            self.upper = __Version(parts[4], '=' not in parts[3])
    
    
    class __Version():
        '''
        A scroll version, not a range and not a scroll name, but with other or not it is open
        '''
        
        def __init__(self, version, open):
            '''
            Constructor
            
            @param  version:str  The version represented in text
            '''
            self.epoch = 0
            self.release = -1
            self.parts = []
            if ':' in version:
                self.epoch = int(version[:version.find(':')])
                version[version.find(':') + 1:]
            if '-' in version:
                self.release = int(version[version.find('-') + 1:])
                version[:version.find('-')]
            self.parts = version.split('-')
            self.open = open
        
        
        def __cmp(self, other):
            '''
            Preforms a comparison of two version numbers, does not compare release number
            
            @param   other:__Version  The other version number
            @return  :int             negative if `self` is less, zero if `self` equals `other`, and positive if `other` is less
            '''
            if self.epoch != other.epoch:
                return self.epoch - other.epoch
            
            (n, m) = (len(self.parts), len(other.parts))
            for i in range(min(n, m)):
                (a, b) = (self.parts[i], other.parts[i])
                if a == b:
                    continue
                (_a, _b) = ([], [])
                if len(a) > 0:
                    buf = ''
                    for j in range(len(a)):
                        isnum = '0' <= a[j] <= '9'
                        wantnum = (len(_a) & 1) == 1
                        if isnum != wantnum:
                            _a.append(buf)
                            buf = a[j]
                        else:
                            buf += a[j]
                    _a.append(buf)
                if len(b) > 0:
                    buf = ''
                    for j in range(len(b)):
                        isnum = '0' <= a[j] <= '9'
                        wantnum = (len(_b) & 1) == 1
                        if isnum != wantnum:
                            _b.append(buf)
                            buf = b[j]
                        else:
                            buf += b[j]
                    _b.append(buf)
                (_n, _m) = (len(_a), len(_b))
                for j in range(min(_n, _m)):
                    (a, b) = (_a[j], _b[j])
                    if a != b:
                        if (j & 1) == 1:
                            return int(a) - int(b)
                        else:
                            return -1 if a < b else 1
                if _n != _m:
                    return _n - _m
            
            return n - m
        
        
        def __lt__(self, other):
            '''
            Operator: <
            '''
            return (self <= other) and not (self == other)
        
        
        def __le__(self, other):
            '''
            Operator: <=
            '''
            cmp = self.__cmp(other)
            if cmp != 0:
                return cmp < 0
            if (self.release < 0) or (other.release < 0):
                return not (self.open or other.open)
            if self.open or other.open:
                return self.release < other.release
            else:
                return self.release <= other.release
        
        
        def __eq__(self, other):
            '''
            Operator: ==
            '''
            cmp = self.__cmp(other)
            if cmp != 0:
                return False
            if (self.release < 0) or (other.release < 0):
                return not (self.open or other.open)
            if self.open or other.open:
                return False
            else:
                return self.release == other.release
        
        
        def __ne__(self, other):
            '''
            Operator: !=
            '''
            return not (self == other)
        
        
        def __gt__(self, other):
            '''
            Operator: >
            '''
            return other < self
        
        
        def __ge__(self, other):
            '''
            Operator: >=
            '''
            return other <= self
    
    
    def __hash__(self):
        '''
        Returns hash of the scroll name
        
        @return  The hash of the scroll name
        '''
        return hash(self.name)
    
    
    def __contains__(self, other):
        '''
        Checks if two scrolls intersects
        
        @param   other:ScrollVersion  The other scroll
        @return  :bool                Whether the two scrolls have the same name and their version ranges intersects
        '''
        if self.name != other.name:
            return False
        
        if ((other.lower is None) and (other.upper is None)) or ((self.lower is None) and (self.upper is None)):
            return True
        elif ((self.lower is None) and (other.lower is None)) or ((self.upper is None) and (other.upper is None)):
            return True
        elif self.complement and other.complement:
            return True
        elif  self.lower is None:  return other.complement or (other.lower <= self.upper)
        elif  self.upper is None:  return other.complement or (other.upper >= self.lower)
        elif other.upper is None:  return  self.complement or (other.lower <= self.upper)
        elif other.lower is None:  return  self.complement or (other.upper >= self.lower)
        elif other.complement:     return ( self.lower !=  self.upper) or (self.lower != other.lower)
        elif  self.complement:     return (other.lower != other.upper) or (self.lower != other.lower)
        else:
            return (self.lower <= other.lower <= self.upper) or (self.lower <= other.upper <= self.upper)
    
    
    def __eq__(self, other):
        '''
        Operator: ==
        
        Implemented as a synomym for `other in self`, checking if they intersect
        '''
        return other in self
    
    
    def __str__(self):
        '''
        Return the object as a string
        
        @return  The object as a string
        '''
        return self.full

