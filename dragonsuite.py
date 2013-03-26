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
import grp as groupmodule
import pwd as usermodule
from subprocess import Popen, PIPE



_dragonsuite_directory_stack = []

class DragonSuite():
    '''
    A collection of utilities mimicing standard unix commands, however not full-blown
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
            return path[path.rfind(os.sep) + 1:] if os.sep in path else path
        else:
            return [(p[p.rfind(os.sep) + 1:] if os.sep in p else p) for p in path]
    
    
    @staticmethod
    def dirname(path):
        '''
        Strip last component from one or more filenames
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        def _dirname(p):
            if os.sep in p[:-1]:
                rc = p[:p[:-1].rfind(os.sep)]
                return rc[:-1] if p.endswith(os.sep) else rc
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
    
    
    @staticmethod
    def cat(files, encoding = None):
        '''
        Read one or more files a create a list of all their combined LF lines in order
        
        @param   files:str|itr<str>  The file or files to read
        @param   encoding:str?       The encoding to use, default if `None`
        @return  :list<str>          All lines in all files
        '''
        rc = []
        mode = 'r' if encoding is None else 'rb'
        fs = [files] if isinstance(files, str) else files
        for f in fs:
            with open(f, mode):
                if encoding is None:
                    rc += f.read().split('\n')
                else:
                    rc += f.read().encode(encoding, 'replace').split('\n')
        return rc
    
    
    @staticmethod
    def pwd():
        '''
        Gets the current working directory
        
        @return  :str  The current working directory
        '''
        return os.getcwd()
    
    
    @staticmethod
    def cd(path):
        '''
        Changes the current working directory
        
        @param  path:str  The new current working directory
        '''
        os.chdir(path)
    
    
    @staticmethod
    def pushd(path):
        '''
        Stores the current working directory in a stack change it
        
        @param  path:str  The new current working directory
        '''
        _dragonsuite_directory_stack.append(os.getcwd())
        os.chdir(path)
    
    
    @staticmethod
    def popd():
        '''
        Changes the current working directory to the one in the top of the `pushd` stack and pop it
        '''
        os.chdir(_dragonsuite_directory_stack.pop())
    
    
    @staticmethod
    def umask(mask = 0o22):
        '''
        Sets the current umask and return the previous umask
        
        @param   mask:int  The new umask
        @return  :int      The previous umask
        '''
        return os.umask(mask)
    
    
    @staticmethod
    def comm(list1, list2, mode):
        '''
        Compare two list
        
        @param   list1:itr<¿E?>  The first list
        @param   list2:itr<¿E?>  The second list
        @param   mode:int        0: Keep elements that do not appear in both lists
                                 1: Keep elements that only appear in the first list
                                 2: Keep elements that only appear in the second list
                                 3: Keep elements that only appear in both lists
        @return  :list<¿E?>      The result it will be sorted and contain no duplicates
        '''
        items = [(e, 1) for e in list1] + [(e, 2) for e in list2]
        items = sorted(rc, key = lambda x : x[0])
        last = items[0]
        (rc, tmp) = ([], [])
        for item in items:
            if item[0] == last[0]:
                tmp.pop()
                tmp.append((item[0], item[1] | last[1]))
            else:
                tmp.append(item)
        mode0 = mode == 0;
        for item in tmp:
            if item[1] == mode:
                rc.append(item[0])
            elif mode0 and item[1] != 3:
                rc.append(item[0])
        return rc
    
    
    @staticmethod
    def unset(var):
        '''
        Deletes an environment variable
        
        @param  var:str  The environment variable
        '''
        os.unsetenv(var)
        if var in os.environ:
            del os.environ[var]
    
    
    @staticmethod
    def export(var, value):
        '''
        Sets an environment variable
        
        @param  var:str     The environment variable
        @param  value:str?  The environment variable's new value, deletes it if `None`
        '''
        if value is None:
            unset(var)
        else:
            os.putenv(var, value)
            if var not in os.environ or os.environ[var] != value:
                os.environ[var] = value
    
    
    @staticmethod
    def get(var, default = ''):
        '''
        Gets an environment variable
        
        @param   var:str       The environment variable
        @param   default:str?  Default value to use if not defined
        @return  :str?         The environment variable's value
        '''
        return os.getenv(var, default)
    
    
    @staticmethod
    def chmod(path, mode, mask = ~0):
        '''
        Changes the protection bits of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  mode:int           The desired protection bits
        @param  mask:int           The portions of `mode` to apply
        '''
        for p in ([path] if isinstance(path, str) else path):
            if mask == ~0:
                os.lchmod(p, mode)
            else:
                cur = os.stat(path).st_mode
                os.lchmod(p, mode | (cur & ~mask))
    
    
    @staticmethod
    def chown(path, owner = -1, group = -1):
        '''
        Changes the owner or group of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  owner:int|str      The new owner, `-1` for ignored
        @param  group:int|str      The new group, `-1` for ignored, `-2` to select by owner
        '''
        o = owner if isinstance(owner, int) else usermodule.getpwnam(owner).pw_uid
        g = group if isinstance(group, int) else groupmodule.getgrnam(group).gr_gid
        for p in ([path] if isinstance(path, str) else path):
            if g == -2:
                x = usermodule.getpwuid(os.stat(path).st_uid).pw_gid
                os.lchown(p, o, x)
            else:
                os.lchown(p, o, g)
    
    
    @staticmethod
    def chgrp(path, group):
        '''
        Changes the group of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  group:int|str      The new group
        '''
        chown(path, group = group)
    
    
    @staticmethod
    def ln(source, link, hard = False):
        '''
        Create a symbolic or hard link
        
        @param  source:str  The target of the new link
        @param  link:str    The path of the new link
        @param  hard:bool   Whether to create a hard link
        '''
        if hard:
            os.link(source, link)
        else:
            os.symlink(source, link)
    
    
    @staticmethod
    def touch(path, settime = False):
        '''
        Create one or more files if missing
        
        @param  path:str|itr<str>  The file of files
        @param  settime:bool       Whether to set the timestamps on the files if they already exists
        '''
        for p in ([path] if isinstance(path, str) else path):
            if os.path.exists(p):
                if settime:
                    os.utime(p, None)
            else:
                open(p, 'a').close()
    
    
    @staticmethod
    def rm(path, recursive = False, directories = False):
        '''
        Remove one or more file
        
        @param  path:str|itr<str>  Files to remove
        @param  recursive:bool     Remove directories recursively
        @param  directories:bool   Attempt to remove directories with rmdir, this is forced for recursive removes
        '''
        for p in ([path] if isinstance(path, str) else path):
            if not recursive:
                if dirs and os.path.isdir(p):
                    os.rmdir(p)
                elif get('shred', None) is not None:
                    execute(get('shred').split(' ') + [p], fail = True)
                else:
                    os.remove(p)
            else:
                rm(tac(find(p)), directories = True)
    
    
    @staticmethod
    def rm_r(path):
        '''
        Remove a file or recursively a directory, multile are also possible
        
        @param  path:str|itr<str>  The files to remove
        '''
        rm(path, recursive = True)
    
    
    @staticmethod
    def rmdir(path):
        '''
        Remove one or more directories
        
        @param  path:str|itr<str>  The directories to remove
        '''
        for p in ([path] if isinstance(path, str) else path):
            os.rmdir(p)
    
    
    @staticmethod
    def mkdir(path, recursive = False):
        '''
        Create one or more directories, it will not fail if the path already exists and is a directory
        
        @param  path:str|itr<str>  The directories to create
        @param  recursive:bool     Whether to create all missing intermediate-level directories
        '''
        for p in ([path] if isinstance(path, str) else path):
            if not recursive:
                if not (os.path.exists(p) and os.path.isdir(p)):
                    os.mkdir(p)
            else:
                ps = p.split(os.sep)
                pp = ps[0]
                for _p in ps[1:]:
                    pp += os.sep + _p
                    if not (os.path.exists(pp) and os.path.isdir(pp)):
                        os.mkdir(pp)
    
    
    @staticmethod
    def mkdir_p(path):
        '''
        Create on ore more directories, and create all missing intermediate-level directories
        
        @param  path:str|itr<str>  The directories to create
        '''
        mkdir(path, recursive = True)
    
    
    @staticmethod
    def mkcd(path, recursive = False):
        '''
        Create a directory and `cd` into it, it will not fail if the path already exists and is a directory
        
        @param  path:str        The directory to create and move into
        @param  recursive:bool  Whether to create all missing intermediate-level directories
        '''
        mkdir(path, recursive)
        cd(path)
    
    
    @staticmethod
    def git(*params):
        '''
        Execute git
        
        @param  params:*str  Arguments for the command
        '''
        execute(['git'] + params, fail = True)
    
    
    @staticmethod
    def curl(*params):
        '''
        Execute curl
        
        @param  params:*str  Arguments for the command
        '''
        execute(['curl'] + params, fail = True)
    
    
    @staticmethod
    def wget(*params):
        '''
        Execute wget
        
        @param  params:*str  Arguments for the command
        '''
        execute(['wget'] + params, fail = True)
    
    
    @staticmethod
    def make(*params):
        '''
        Execute make
        
        @param  params:*str  Arguments for the command
        '''
        execute(['make'] + params, fail = True)
    
    
    @staticmethod
    def rename(path, expression, replacement):
        '''
        Rename multiple files with a pattern using util-linux's command rename
        
        @param  path:str|list<str>  File or files to rename
        @param  expression:str      Matching expression
        @param  replacement:str     Replacement
        '''
        files = [path] if isinstance(path, str) else path
        execute(['rename', '--', expression, replacement] + files, fail = True)
    
    
    @staticmethod
    def upx(path, level = 8, overlay = 1, brute = 0):
        '''
        Compress one or more files using the command upx
        
        @param  path:str|list<str>  The files to compress
        @param  level:int           Compression level, [1; 10], 10 for --best
        @param  overlay:int         0: --overlay=skip
                                    1: --overlay=copy
                                    2: --overlay=strip
        @param  brute:int           0: no addition parameter
                                    1: --brute
                                    2: --ultra-brute
        '''
        params = ['upx', '-%i' % level if level < 10 else '--best']
        if overlay == 0:  params += ['--overlay=skip']
        if overlay == 2:  params += ['--overlay=strip']
        if brute == 1:  params += ['--brute']
        if brute == 2:  params += ['--ultra-brute']
        params += ['--', path] if isinstance(path, str) else (['--'] + path)
        execute(params, fail = False)
    
    
    @staticmethod
    def strip(path, *params):
        '''
        Strip symbols from binaries and libraries using the command strip
        
        @param  path:str|list<str>  The files to compress
        @param  params:*str         Arguments for strip
        '''
        cmd = ['strip'] + params + (['--', path] if isinstance(path, str) else (['--'] + path))
        execute(cmd, fail = False)
    
    
    @staticmethod
    def installinfo(path):
        '''
        Update info/dir entries
        
        @param  path:str|list<str>  New or updated entries
        '''
        r = get('root', '/')
        i = get('infodir', '/usr/share/info')
        if not r.endswith('/'): r += '/'
        if i.startswith('/'): i = i[1:]
        if not i.endswith('/') and len(i) > 0: i += '/'
        d = r + i + 'dir'
        for p in (['--', path] if isinstance(path, str) else (['--'] + path)):
            execute(['install-info', '--', p, d], fail = False)


