#!/usr/bin/env python
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
from subprocess import Popen, PIPE



class DragonSuite():
    '''
    A collection of utilities mimicing standard commands, however not full-blown
    '''
    
    @staticmethod
    def pipe(data, *commands):
        '''
        Process data through a filter pipeline
        
        @param   data:?           Input data
        @param   commands:*(?)→?  List of functions
        @return  :?               Output data
        '''
        rc = data
        for command in commands:
            rc = command(rc)
        return rc
    
    
    @staticmethod
    def basename(path):
        '''
        Strip the directory form one or more filenames
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        if isinstance(path, str):
            return path[path.rfind('/') + 1:] if '/' in path else path
        else:
            return [(p[p.rfind('/') + 1:] if '/' in p else p) for p in path]
    
    
    @staticmethod
    def dirname(path):
        '''
        Strip last component from one or more filenames
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        def _dirname(p):
            if '/' in p[:-1]:
                rc = p[:p[:-1].rfind('/')]
                return rc[:-1] if p.endswith('/') else rc
            else:
                return '.'
        if isinstance(path, str):
            return _dirname(path)
        else:
            return [_dirname(p) for p in path]
    
    
    @staticmethod
    def uniq(items, issorted = True):
        '''
        Remove duplicates
        
        @param   items:itr<¿E?>  An iteratable of items
        @param   issorted:bool   Whether the items are already sorted, otherwise a standard sort is preform
        @return  :list<¿E?>      A list with the input items but without duplicates
        '''
        if len(items) == 0:
            return []
        rc = [items[0]]
        last = items[0]
        sorteditems = items if issorted else sorted(items)
        for item in sorteditems:
            if item != last:
                rc.append(item)
                last = item
        return rc
    
    
    @staticmethod
    def sort(items, reverse = True):
        '''
        Sort a list of items
        
        @param   items:list<¿E?>  Unsorted list of items
        @param   reverse:bool     Whether to sort in descending order
        @return  :list<¿E?>       Sort list of items
        '''
        return sorted(items, reverse = reverse)
    
    
    @staticmethod
    def tac(items):
        '''
        Reverse a list of items
        
        @param   items:list<¿E?>  The list of items
        @return  :list<¿E?>       The list of items in reversed order
        '''
        return reversed(items)
    
    
    @staticmethod
    def readlink(path):
        '''
        Gets the file one or more link is directly pointing to, this is not the realpath, but if
        you do this recursively you should either get the realpath or get stuck in an infinite loop
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        if isinstance(path, str):
            return os.readlink(path)
        else:
            return [os.readlink(p) for p in path]
    
    
    @staticmethod
    def cut(items, delimiter, fields, complement = False, onlydelimited = False, outputdelimiter = None):
        '''
        Remove sections of items by delimiters
        
        @param   items:itr<str>        The items to modify
        @param   delimiter:str         Delimiter
        @param   fields:int|list<int>  Fields to join, in joining order
        @param   complement:bool       Join the fields as in order when not in `fields`
        @param   onlydelimited:bool    Whether to remove items that do not have the delimiter
        @param   outputdelimiter:str?  Joiner, set to same as delimiter if `None`
        @return  :list<str>            The items after the modification
        '''
        rc = []
        od = delimiter if outputdelimiter is None else outputdelimiter
        f = fields if isinstance(fields, list) else [fields]
        if complement:
            f = set(f)
        for item in items:
            if onlydelimited and delimiter not in item:
                continue
            item = item.split(delimiter)
            if complement:
                x = []
                for i in range(0, len(item)):
                    if i not in f:
                        x.append(item[x])
                item = x
            else:
                item = [item[i] for i in f]
            rc.append(od.join(item))
        return rc


