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
import re as regex
import grp as groupmodule
import pwd as usermodule
from subprocess import Popen, PIPE


'''
Dragon Suite

A collection of utilities mimicing standard unix commands, however not full-blown
'''


_dragonsuite_directory_stack = []
'''
Keeps track of `pushd`:s
'''

_dragonsuite_verbose = True
'''
Whether to be verbose
'''

_dragonsuite_output = None
'''
Output channel for dragonsuite
'''


def __print(text):
    '''
    Print what is happening
    
    @param  text:__str__()→str  The string to print
    '''
    if _dragonsuite_output is not None:
        _dragonsuite_output.write(('\033[34m' + str(text) + '\033[00m\n').encode('utf-8'))
        _dragonsuite_output.flush()


def pipe(data, *commands):
    '''
    Process data through a filter pipeline
    
    @param   data:?           Input data
    @param   commands:*(?)→?  List of functions
    @return  :?               Output data
    '''
    if (len(commands) == 1) and (isinstance(commands[0], list) or isinstance(commands[0], tuple)):
        commands = commands[0]
    rc = data
    for command in commands:
        rc = command(rc)
    return rc


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


def uniq(items, is_sorted = True):
    '''
    Remove duplicates
    
    @param   items:itr<¿E?>   An iteratable of items
    @param   is_sorted:bool   Whether the items are already sorted, otherwise a standard sort is preform
    @return  :list<¿E?>       A list with the input items but without duplicates
    '''
    if len(items) == 0:
        return []
    rc = [items[0]]
    last = items[0]
    sorteditems = items if is_sorted else sorted(items)
    for item in sorteditems:
        if item != last:
            rc.append(item)
            last = item
    return rc


def sort(items, reverse = True):
    '''
    Sort a list of items
    
    @param   items:list<¿E?>  Unsorted list of items
    @param   reverse:bool     Whether to sort in descending order
    @return  :list<¿E?>       Sort list of items
    '''
    return sorted(items, reverse = reverse)


def tac(items):
    '''
    Reverse a list of items
    
    @param   items:list<¿E?>  The list of items
    @return  :list<¿E?>       The list of items in reversed order
    '''
    return reversed(items)


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


def cut(items, delimiter, fields, complement = False, only_delimited = False, output_delimiter = None):
    '''
    Remove sections of items by delimiters
    
    @param   items:itr<str>         The items to modify
    @param   delimiter:str          Delimiter
    @param   fields:int|list<int>   Fields to join, in joining order
    @param   complement:bool        Join the fields as in order when not in `fields`
    @param   only_delimited:bool    Whether to remove items that do not have the delimiter
    @param   output_delimiter:str?  Joiner, set to same as delimiter if `None`
    @return  :list<str>             The items after the modification
    '''
    rc = []
    od = delimiter if output_delimiter is None else output_delimiter
    f = fields if isinstance(fields, list) else [fields]
    if complement:
        f = set(f)
    for item in items:
        if only_delimited and delimiter not in item:
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


def pwd():
    '''
    Gets the current working directory
    
    @return  :str  The current working directory
    '''
    return os.getcwd()


def cd(path):
    '''
    Changes the current working directory
    
    @param  path:str  The new current working directory
    '''
    __print('cd ' + path)
    os.chdir(path)


def pushd(path):
    '''
    Stores the current working directory in a stack change it
    
    @param  path:str  The new current working directory
    '''
    __print('pushd ' + path)
    _dragonsuite_directory_stack.append(os.path.abspath(os.getcwd()))
    os.chdir(path)


def popd():
    '''
    Changes the current working directory to the one in the top of the `pushd` stack and pop it
    '''
    __print('popd')
    os.chdir(_dragonsuite_directory_stack.pop())


def umask(mask = 0o22):
    '''
    Sets the current umask and return the previous umask
    
    @param   mask:int  The new umask
    @return  :int      The previous umask
    '''
    __print('umask ' + oct(mask).replace('0o', ''))
    return os.umask(mask)


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


def unset(var):
    '''
    Deletes an environment variable
    
    @param  var:str  The environment variable
    '''
    __print('unset ' + var)
    os.unsetenv(var)
    if var in os.environ:
        del os.environ[var]


def export(var, value):
    '''
    Sets an environment variable
    
    @param  var:str     The environment variable
    @param  value:str?  The environment variable's new value, deletes it if `None`
    '''
    if value is None:
        unset(var)
    else:
        __print('export %s=%s' % (var, value))
        os.putenv(var, value)
        if var not in os.environ or os.environ[var] != value:
            os.environ[var] = value


def defvar(var, value):
    '''
    Sets an environment variable to a default value if it is empty or non-existant
    
    @param  var:str    The environment variable
    @param  value:str  The environment variable's default value
    '''
    if get(var, '') == '':
        export(var, value)


def get(var, default = ''):
    '''
    Gets an environment variable
    
    @param   var:str       The environment variable
    @param   default:str?  Default value to use if not defined
    @return  :str?         The environment variable's value
    '''
    return os.getenv(var, default)


def chmod(path, mode, mask = ~0):
    '''
    Changes the protection bits of one or more files
    
    @param  path:str|itr<str>  The file or files
    @param  mode:int           The desired protection bits
    @param  mask:int           The portions of `mode` to apply
    '''
    __print('chmod %s~%s %s' % (oct(mode).replace('0o', ''), oct(~mask).replace('0o', ''), str(path)))
    for p in ([path] if isinstance(path, str) else path):
        if mask == ~0:
            os.chmod(p, mode)
        else:
            cur = os.lstat(path).st_mode
            os.chmod(p, mode | (cur & ~mask))


def chown(path, owner = -1, group = -1):
    '''
    Changes the owner or group of one or more files
    
    @param  path:str|itr<str>  The file or files
    @param  owner:int|str      The new owner, `-1` for ignored
    @param  group:int|str      The new group, `-1` for ignored, `-2` to select by owner
    '''
    __print('lchown %s:%s %s' % (str('' if isinstance(owner, int) and (owner == -1) else owner), str(('' if group == -1 else ('$' if group == -2 else group)) if isinstance(group, int) else group), str(path)))
    u = owner if isinstance(owner, int) else usermodule.getpwnam(owner).pw_uid
    g = group if isinstance(group, int) else groupmodule.getgrnam(group).gr_gid
    for p in ([path] if isinstance(path, str) else path):
        os.lchown(p, u, usermodule.getpwuid(os.lstat(path).st_uid).pw_gid if g == -2 else g)


def chgrp(path, group):
    '''
    Changes the group of one or more files
    
    @param  path:str|itr<str>  The file or files
    @param  group:int|str      The new group
    '''
    chown(path, group = group)


def ln(source, link, hard = False):
    '''
    Create a symbolic or hard link
    
    @param  source:str  The target of the new link
    @param  link:str    The path of the new link
    @param  hard:bool   Whether to create a hard link
    '''
    if os.path.lexists(link) and os.path.isdir(link):
        link += os.sep + basename(source)
    if hard:
        __print('ln --hard %s %s' % (source, link))
        os.link(source, link)
    else:
        __print('ln --symbolic %s %s' % (source, link))
        if os.path.lexists(link) and os.path.islink(link):
            if os.readlink(link) == source:
                return
        os.symlink(source, link)


def touch(path, settime = False):
    '''
    Create one or more files if missing
    
    @param  path:str|itr<str>  The file of files
    @param  settime:bool       Whether to set the timestamps on the files if they already exists
    '''
    __print('touch %s' + str(path))
    for p in ([path] if isinstance(path, str) else path):
        if os.path.lexists(p):
            if settime:
                os.utime(p, None)
        else:
            open(p, 'a').close()


def rm(path, recursive = False, directories = False):
    '''
    Remove one or more file
    
    @param  path:str|itr<str>  Files to remove
    @param  recursive:bool     Remove directories recursively
    @param  directories:bool   Attempt to remove directories with rmdir, this is forced for recursive removes
    '''
    __print(('rm -r' if recursive else 'rm') + (' ' if directories else ' --directories ') + str(path))
    for p in ([path] if isinstance(path, str) else path):
        if not recursive:
            if directories and os.path.isdir(p):
                os.rmdir(p)
            elif get('shred', None) is not None:
                execute(get('shred').split(' ') + [p], fail = True)
            else:
                os.remove(p)
        else:
            rm(tac(find(p)), directories = True)


def rm_r(path):
    '''
    Remove a file or recursively a directory, multile are also possible
    
    @param  path:str|itr<str>  The files to remove
    '''
    rm(path, recursive = True)


def rmdir(path):
    '''
    Remove one or more directories
    
    @param  path:str|itr<str>  The directories to remove
    '''
    __print('rmdir' + str(path))
    for p in ([path] if isinstance(path, str) else path):
        os.rmdir(p)


def mkdir(path, recursive = False):
    '''
    Create one or more directories, it will not fail if the path already exists and is a directory
    
    @param  path:str|itr<str>  The directories to create
    @param  recursive:bool     Whether to create all missing intermediate-level directories
    '''
    __print('mkdir' + (' -p ' if recursive else ' ') + str(path))
    for p in ([path] if isinstance(path, str) else path):
        if not recursive:
            if not (os.path.lexists(p) and os.path.isdir(p)):
                os.mkdir(p)
        else:
            ps = p.split(os.sep)
            pp = ps[0]
            if len(pp) > 0:
                if not (os.path.lexists(pp) and os.path.isdir(pp)):
                    os.mkdir(pp)
            for _p in ps[1:]:
                pp += os.sep + _p
                if not (os.path.lexists(pp) and os.path.isdir(pp)):
                    os.mkdir(pp)


def mkdir_p(path):
    '''
    Create on ore more directories, and create all missing intermediate-level directories
    
    @param  path:str|itr<str>  The directories to create
    '''
    mkdir(path, recursive = True)


def mkcd(path, recursive = False):
    '''
    Create a directory and `cd` into it, it will not fail if the path already exists and is a directory
    
    @param  path:str        The directory to create and move into
    @param  recursive:bool  Whether to create all missing intermediate-level directories
    '''
    mkdir(path, recursive)
    cd(path)


def git(*params):
    '''
    Execute git
    
    @param  params:*str  Arguments for the command
    '''
    if (len(params) == 1) and (isinstance(params[0], list) or isinstance(params[0], tuple)):
        params = params[0]
    execute(['git'] + list(params), fail = True)


def curl(*params):
    '''
    Execute curl
    
    @param  params:*str  Arguments for the command
    '''
    if (len(params) == 1) and (isinstance(params[0], list) or isinstance(params[0], tuple)):
        params = params[0]
    execute(['curl'] + list(params), fail = True)


def wget(*params):
    '''
    Execute wget
    
    @param  params:*str  Arguments for the command
    '''
    if (len(params) == 1) and (isinstance(params[0], list) or isinstance(params[0], tuple)):
        params = params[0]
    execute(['wget'] + list(params), fail = True)


def make(*params):
    '''
    Execute make
    
    @param  params:*str  Arguments for the command
    '''
    if (len(params) == 1) and (isinstance(params[0], list) or isinstance(params[0], tuple)):
        params = params[0]
    execute(['make'] + list(params), fail = True)


def rename(path, expression, replacement):
    '''
    Rename multiple files with a pattern using util-linux's command rename
    
    @param  path:str|list<str>  File or files to rename
    @param  expression:str      Matching expression
    @param  replacement:str     Replacement
    '''
    files = [path] if isinstance(path, str) else path
    execute(['rename', '--', expression, replacement] + files, fail = True)


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


def strip(path, *params):
    '''
    Strip symbols from binaries and libraries using the command strip
    
    @param  path:str|list<str>  The files to compress
    @param  params:*str         Arguments for strip
    '''
    if (len(params) == 1) and (isinstance(params[0], list) or isinstance(params[0], tuple)):
        params = params[0]
    cmd = ['strip'] + list(params) + (['--', path] if isinstance(path, str) else (['--'] + path))
    execute(cmd, fail = False)


def install_info(path, infodir = None):
    '''
    Update info/dir entries
    
    @param  path:str|list<str>  New or updated entries
    @param  infodir:str?        Directory for info manuals
    '''
    if infodir is None:
        infodir = get('infodir', '%susr%sshare%sinfo%s' % (os.sep, os.sep, os.sep, os.sep))
        infodir = get('PINPAL') + infodir
    if infodir.endswith(os.sep):
        infodir += 'dir'
    else:
        infodir += os.sep + 'dir'
    for p in ([path] if isinstance(path, str) else path):
        execute(['install-info', '--dir-file', infodir, '--', p], fail = False)


def uninstall_info(path, infodir = None):
    '''
    Delete info/dir entries
    
    @param  path:str|list<str>  Removed entries
    @param  infodir:str?        Directory for info manuals
    '''
    if infodir is None:
        infodir = get('infodir', '%susr%sshare%sinfo%s' % (os.sep, os.sep, os.sep, os.sep))
        infodir = get('PINPAL') + infodir
    if infodir.endswith(os.sep):
        infodir += 'dir'
    else:
        infodir += os.sep + 'dir'
    for p in ([path] if isinstance(path, str) else path):
        execute(['install-info', '--delete', '--dir-file', infodir, '--', p], fail = False)


def mv(source, destination):
    '''
    Move one or more files
    
    @param  source:str|itr<str>  The files to move
    @param  destination:str      The destination, either directory or new file
    '''
    __print('mv %s %s' % (str(source), destination))
    ps = [source] if isinstance(source, str) else source
    d = destination if destination.endswith(os.sep) else (destination + os.sep)
    if len(ps) == 1:
        if os.path.lexists(destination) and os.path.isdir(destination):
            os.rename(source, d + basename(source))
        else:
            os.rename(source, destination)
    else:
        if not os.path.lexists(destination):
            raise OSError('Destination %s does not exist but must be a directory' % destination)
        elif not os.path.isdir(destination):
            raise OSError('Destination %s exists and is not a directory' % destination)
        else:
            for p in ps:
                os.rename(p, d + basename(p))


def echo(text, newline = True, stderr = False):
    '''
    Display a line of text
    
    @param  text:str|list<str>  The text
    @param  newline:bool        Whether to end with a line break
    @param  stderr:bool         Whether to print to stderr
    '''
    s = sys.stdout.buffer if not stderr else sys.stderr.buffer
    if isinstance(text, str):
        s.write((text + ('\n' if newline else '')).encode('utf-8'))
    else:
        s.write(('\n'.join(text) + ('\n' if newline else '')).encode('utf-8'))


def msg(text, submessage = False):
    '''
    Display status message
    
    @param  text:str         The message
    @param  submessage:bool  Whether this is a submessage
    '''
    message = '\033[01;3%im%s\033[00;01m %s\033[00m\n'
    message %= (2, ' -->', text) if submessage else (4, '==>', text)
    sys.stdout.buffer.write(message.encode('utf-8'))


def cp(source, destination, recursive = True):
    '''
    Copies files and directories, note that you can do so much more with GNU ocreutils's cp
    
    @param  source:str|itr<str>   Files to copy
    @param  destination:str       Destination filename or directory
    '''
    install(source, destination, parents = False, recursive = recursive, savemode = True)


def cp_r(source, destination):
    '''
    Copies files and directories, recursively
    
    @param  source:str|itr<str>   Files to copy
    @param  destination:str       Destination filename or directory
    '''
    cp(source, destination, True)


def install(source, destination, owner = -1, group = -1, mode = -1, strip = False, directory = False, parents = True, recursive = True, savemode = True):
    '''
    Copies files and set attributes
    
    @param  source:str|itr<str>   Files to copy
    @param  destination:str       Destination filename or directory
    @param  owner:int|str         The new owner, `-1` for preserved
    @param  group:int|str         The new group, `-1` for preserved, `-2` to select by owner
    @param  mode:int              The desired protection bits, `-1` for preserved
    @param  strip:bool            Whether to strip symbol table
    @param  directory:bool        Whether treat all source files is directory names
    @param  parents:bool          Whether create missing directories
    @param  recursive:bool        Copy directories resursively
    @param  savemode:bool         Whether to use the protection bits of already installed versions
    '''
    _print_info = (destination,
                   ' -D' if parents else '',
                   ' -r' if recursive else '',
                   ' -s' if strip else '',
                   ' --savemode' if savemode else '',
                   ('' if mode == -1 else (' -m ' + oct(mode).replace('0o', ''))) if isinstance(mode, int) else (' -m ' + mode),
                   ('' if owner == -1 else (' -u ' + str(owner))) if isinstance(owner, int) else (' -u ' + owner),
                   ('' if group == -1 else (' -g $' if group == -2 else (' -g ' + str(group)))) if isinstance(group, int) else (' -g ' + group),
                   ' -d' if directory else '',
                   str(source))
    __print('install -T %s%s%s%s%s%s%s%s%s %s' % _print_info)
    ps = [source] if isinstance(source, str) else source
    d = destination if destination.endswith(os.sep) else (destination + os.sep)
    pairs = None
    if len(ps) == 1:
        if os.path.lexists(destination) and os.path.isdir(destination):
            if directory:
                pairs = [(s, d + s) for s in ps]
            else:
                pairs = [(s, d + basename(s)) for s in ps]
        else:
            pairs = [(s, destination) for s in ps]
    else:
        if not os.path.lexists(destination):
            if parents:
                mkdir_p(destination)
            else:
                raise OSError('Destination %s does not exist but must be a directory' % destination)
        elif not os.path.isdir(destination):
            raise OSError('Destination %s exists and is not a directory' % destination)
        if directory:
            pairs = [(p, d + p) for p in ps]
        else:
            pairs = [(p, d + basename(p)) for p in ps]
    for (src, dest) in pairs:
        protection = mode
        if savemode and os.path.lexists(dest):
            protection = os.lstat(dest).st_mode
        elif isinstance(mode, int) and (mode < 0):
            protection = 0o755 if directory else os.lstat(src).st_mode
        if directory or os.path.isdir(src):
            if parents:
                mkdir_p(dest)
            else:
                mkdir(dest)
        elif os.path.islink(src):
            ln(os.readlink(src), dest)
        else:
            blksize = 8192
            try:
                blksize = os.stat(os.path.realpath(ifile)).st_blksize
            except:
                pass
            with open(src, 'rb') as ifile:
                if parents and not os.path.lexists(dirname(dest)):
                    mkdir_p(dirname(dest))
                with open(dest, 'wb') as ofile:
                    while True:
                        chunk = ifile.read(blksize)
                        if len(chunk) == 0:
                            break
                        ofile.write(chunk)
        (u, g) = (owner, group)
        if (isinstance(u, str) or (u != -1) or isinstance(g, str) or (g != -1)):
            stat = os.lstat(dest) if directory else os.lstat(src)
            u = u if isinstance(u, str) or (u != -1) else stat.st_uid
            g = g if isinstance(g, str) or (g != -1) else stat.st_gid
            chown(dest, u, g)
        if not os.path.islink(dest):
            os.chmod(dest, protection)
        if strip and not directory:
            strip(dest)
        if recursive and os.path.isdir(src) and not directory:
            d = src if src.endswith(os.sep) else (src + os.sep)
            sources = [d + f for f in os.listdir(d)]
            install(sources, dest, owner, group, mode, strip, False, False, True, savemode)


def find(path, maxdepth = -1, hardlinks = True):
    '''
    Gets all existing subfiles, does not follow links including hardlinks
    
    @param   path:str|itr<str>  Search root or roots
    @param   maxdepth:int       Maximum search depth, `-1` for unbounded
    @param   hardlinks:bool     Whether to list all files with same inode number rather than just the first
    @return  :list<str>         Found files
    '''
    rc = []
    visited = set()
    stack = [path] if isinstance(path, str) else path
    stack = [(e, 0) for e in stack]
    while len(stack) > 0:
        (f, d) = stack.pop()
        if os.path.lexists(f):
            f = f if not f.endswith(os.sep) else f[:-1]
            if (not os.path.islink(f)) and os.path.isdir(f):
                inode = os.lstat(f).st_ino
                if inode not in visited:
                    visited.add(inode)
                    f += os.sep
                    if d != maxdepth:
                        d += 1
                        for sf in sorted(os.listdir(f)):
                            stack.append((f + sf, d))
                elif not hardlinks:
                    continue
            elif not hardlinks:
                inode = os.lstat(f).st_ino
                if inode in visited:
                    continue
                visited.add(inode)
            rc.append(f)
    return rc


def l(elements):
    '''
    Encapsulates string and integers in lists and converts iteratables to lists
    
    @param   elements:¿E?=str|¿E?=list|itr<¿E?>  The elements to make sure they are in a list
    @return  elements:list<¿E?>                  The elements in a list
    '''
    if isinstance(elements, str) or isinstance(elements, int):
        return [elements]
    return list(elements)


def path_escape(*filename):
    '''
    Escape a filename for dynamic include in a `path` expression without the risk of it being parsed as an expression, but rather be verbatim
    
    @param   filename:*str    The filename or filenames
    @return  :str|tuple<str>  The filename or filenames escaped, will be a list if a list or other iteratable type was used in the paramter
    '''
    if len(filename) == 1:
        filename = filename[0]
    files = [filename] if isinstance(filename, str) else filename
    rc = []
    for file in files:
        for c in '\\.^+$[]|(){}*?@~':
            file = file.replace(c, '\\' + c)
        rc.append(file)
    if isinstance(filename, str):
        return rc[0]
    else:
        return tuple(rc)


def path(exprs, existing = False):
    '''
    Gets files matching a pattern, and expand ~
    
    Here     => Regular expression
    {a,b,c}  => (a|b|c)
    {a..g}   => [ag]
    {1..11}  => (1|2|3|4|5|6|7|8|9|10|11)
    *        => .*
    ?        => .
    TODO: add other expressions but for alternative function epath:
        [abc]    => (a|b|c)
        [a-g]    => [ag]
        [a-zA-Z] => ([az]|[AZ])
        ?(a)     => (a|)
        @(a|b|c) => (a|b|c)
        However they are only expanded if matched to an file
    
    Everything else is matched verbosely and the matching is closed (regex: ^pattern$),
    and \ is used to escape characters do that they are matched verbosely instead of
    getting a special meaning.
    Ending the pattern with / specified that it should be a directory.
    
    @param   exprs:str|itr<str>  Expressions
    @param   existing:bool       Whether to only match to existing files
    @return  :str|list<str>      Matching files
    '''
    def __(expr):
        ps = ['']
        esc = False
        buf = ''
        d = 0
        for c in expr.replace('\0', '').replace('/', ('\\' if os.sep in '?*{},.\\' else '') + os.sep):
            if esc:
                esc = False
                if d > 0:
                    buf += '\\'
                buf += c
            elif c == '\\': esc = True
            elif c == '?':  buf += '\0?' if d == 0 else '?'
            elif c == '*':  buf += '\0*' if d == 0 else '*'
            elif c == ',':  buf += '\0,' if d == 1 else ','
            elif c == '.':  buf += '\0.' if d == 1 else '.'
            elif c == '{':
                if d == 0:
                    ps = [p + buf for p in ps]
                    buf = ''
                else:
                    buf += '{'
                d += 1
            elif c == '}':
                if d == 1:
                    flatten = [__(tp) for tp in buf.split('\0,')]
                    t = []
                    for f in flatten:
                        t += f
                    pz = []
                    for a in ps:
                        for b in t:
                            if '\0.' not in b:
                                pz.append(a + b)
                            elif (len(b) - len(b.replace('\0.', '')) != 4) and ('\0.\0.' not in b):
                                pz.append(a + b.replace('\0.', '.'))
                            elif b.startswith('\0.') or b.endswith('\0.'):
                                pz.append(a + b.replace('\0.', '.'))
                            else:
                                (l, r) = b.split('\0.\0.')
                                if len(string.strip(l + r, '0123456789')) == 0:
                                    step = 1 if int(l) <= int(r) else -1
                                    x = int(l) if step == 1 else int(r)
                                    n = int(r) if step == 1 else int(l)
                                    while x != n:
                                        pz.append(a + str(x))
                                        x += step
                                    pz.append(a + str(x))
                                elif len(l) == 1 and len(r) == 1:
                                    step = 1 if ord(l) <= ord(r) else -1
                                    x = ord(l) if step == 1 else ord(r)
                                    n = ord(r) if step == 1 else ord(l)
                                    while x != n:
                                        pz.append(a + chr(x))
                                        x += step
                                    pz.append(a + chr(x))
                                else:
                                    pz.append(a + b.replace('\0.', '.'))
                    ps = pz
                    pz = None
                    buf = ''
                else:
                    buf += '}'
                d -= 1
            else:
                buf += c
        return [p + buf for p in ps]
    rc = []
    for expr in ([exprs] if isinstance(exprs, str) else exprs):
        for p in __(expr):
            tilde = get('HOME')
            f = ''
            if p.startswith('~'):
                f = tilde
                p = p[1:]
            if '\0' not in p:
                rc.append(f + p)
            else:
                f = [f]
                if os.sep == '?': p = p.replace('\0?', '\0a')
                if os.sep == '*': p = p.replace('\0*', '\0b')
                parts = p.split(os.sep)
                if os.sep == '?': parts = [p.replace('\0a', '\0?') for p in parts]
                if os.sep == '*': parts = [p.replace('\0b', '\0*') for p in parts]
                for p in parts:
                    if len(p) == 0:
                        f = [(os.sep if len(_) == 0 else _) for _ in f]
                    elif p == '.':
                        f = [(os.curdir if len(_) == 0 else _) for _ in f]
                    elif p == '..':
                        _f = []
                        for _ in f:
                            if len(_) == 0:
                                _ = os.pardir
                            elif _ == os.pardir or _.endswith(os.sep + os.pardir):
                                _ += os.sep + os.pardir
                            else:
                                _ = _[:_.rfind('/')]
                            _f.append(_)
                        f = _f
                    elif '\0' not in p:
                        f = [(p if len(_) == 0 else (_ + os.sep + p)) for _ in f]
                    else:
                        _f = []
                        for _ in f:
                            root = os.curdir if len(_) == 0 else _
                            if os.path.lexists(root) and not os.path.isdir(root):
                                break
                            subs = os.listdir(root)
                            matches = []
                            s = p
                            for c in '\\.^+$[]|(){}':
                                s = s.replace(c, '\\' + c)
                            _ = ''
                            esc = False
                            for c in s:
                                if esc:
                                    _ += {'*' : '.*',  '?' : '.'}[c]
                                    esc = False
                                elif c == '\0':
                                    esc = True
                                elif c == '?':
                                    _ += '\\?'
                                elif c == '*':
                                    _ += '\\*'
                                else:
                                    _ += c
                            s = '^' + _ + '$'
                            matcher = regex.compile(s, regex.DOTALL)
                            for s in subs:
                                if matcher.match(s) is not None:
                                    matches.append(s)
                            _ = root
                            if len(_) > 0:
                                _ += os.sep
                            for m in matches:
                                _f.append(_ + m)
                        f = _f
                rc += f
    if existing:
        nrc = []
        for p in rc:
            if os.path.lexists(p) and ((not p.endswith(os.sep)) or os.path.isdir(p)):
                nrc.append(p)
        rc = nrc
    return rc[0] if len(rc) == 1 else rc


def decompress(path, format = None):
    '''
    Decompres and extract archives
    
    Recognised formats, all using external programs:
    gzip*, bzip2*, xz*, lzma*, lrzip*, lzip*, lzop*, zip, shar, tar, cpio, squashfs
    Formats marked with and asteriks are recognised compressions for tar and cpio.

    @param  path:str|itr<str>  The file or files
    @param  format:str?        The format, `None` for automatic detection (currently uses file extension)
    '''
    __print('decompress%s %s' % ('' if format is None else ('--format=' + format), str(path)))
    for p in ([path] if isinstance(path, str) else path):
        fmt = format
        if fmt is None:
            fmt = p[p.rfind(os.sep) + 1:]
            if '.tar.' in fmt:
                fmt = fmt[:fmt.rfind(os.extsep):] + fmt[fmt.rfind(os.extsep) + 1:]
            fmt = fmt[fmt.rfind(os.extsep) + 1:]
        p = '\'' + p.replace('\'', '\'\\\'\'') + '\''
        havecpio = False
        for d in get('PATH').split(os.pathsep):
            if not d.endswith(os.sep):
                d += os.sep
            if os.path.lexists(d + 'cpio'):
                havecpio = True
                break
        fmt = {'gz' : 'gzip -d %s',
               'bz' : 'bzip2 -d %s',
               'bz2' : 'bzip2 -d %s',
               'xz' : 'xz -d %s',
               'lzma' : 'lzma -d %s',
               'lrz' : 'lrzip -d %s',
               'lz' : 'lzip -d %s',
               'lzop' : 'lzop -d %s',
               'z' : 'unzip %s',
               'tar' : 'tar --get < %s',
               'tgz' : 'tar --gzip --get < %s',
               'targz' : 'tar --gzip --get < %s',
               'tarbz' : 'tar --bzip2 --get < %s',
               'tarbz2' : 'tar --bzip2 --get < %s',
               'tarxz' : 'tar --xz --get < %s',
               'tarlzma' : 'tar --lzma --get < %s',
               'tarlz' : 'tar --lzip --get < %s',
               'tarlzop' : 'tar --lzop --get < %s',
               'tarlrz' : 'lzrip -d < %s | tar --get',
               'cpio' : 'cpio --extract < %s',
               'cpiogz' : 'gzip -d < %s | cpio --extract',
               'cpiobz' : 'bzip2 -d < %s | cpio --extract',
               'cpiobz2' : 'bzip2 -d < %s | cpio --extract',
               'cpioxz' : 'xz -d < %s | cpio --extract',
               'cpiolzma' : 'lzma -d < %s | cpio --extract',
               'cpiolz' : 'lzip -d < %s | cpio --extract',
               'cpiolzop' : 'lzop -d < %s | cpio --extract',
               'cpiolrz' : 'lrzip -d < %s | cpio --extract',
               'shar' : 'sh %s',
               'sfs' : 'unsquashfs %s',
               'squashfs' : 'unsquashfs %s'}[fmt.lower().replace(os.extsep, '').replace('zip', 'z')]
        if not havecpio:
            fmt = fmt.replace('cpio', 'bsdcpio')
        bash(fmt % p, fail = True)


def chroot(directory, function):
    '''
    Change root directory
    
    Changes made by the function will only stay in affect during the chroot, they,
    will be reverted when the function exit; you may store information in the
    directory for temporary data.
    
    @param   directory:str     The directory to set to root
    @param   function:()→void  Function to invoke with the new root
    @param   :int              Zero on success
    '''
    __print('chroot ' + directory)
    pid = os.fork()
    if pid == 0:
        os.chroot(directory)
        os.chdir(directory)
        function()
        exit(0)
    else:
        rc = os.waitpid(pid, 0)[1]
        __print('unchroot')
        return rc


def execute_pipe(command, fail = False, *command_):
    '''
    Execute a command
    
    @param   command:str   Command line arguments, including the command
    @param   fail:bool     Whether to raise an exception if the command fails
    @return  :list<str>    Standard output lines
    
    -- OR --
    
    @param   command:*str  Command line arguments, including the command
    @return  :list<str>    Standard output lines
    '''
    command = list([command] if isinstance(command, str) else command) + ([fail] if isinstance(fail, str) else []) + list(command_)
    __print('Executing external command: ' + str(command))
    proc = Popen(command, stdin = sys.stdin, stdout = PIPE, stderr = sys.stderr)
    output = proc.communicate()[0]
    if fail and (proc.returncode != 0):
        raise Exception('%s exited with error code %i' % (str(command), proc.returncode))
    output = output.decode('utf-8', 'replace')
    if output.endswith('\n'):
        output = output[:-1]
    output = output.split('\n')
    return output


def execute(command, fail = True, *command_):
    '''
    Execute a command
    
    @param  command:str   Command line arguments, including the command
    @param  fail:bool     Whether to raise an exception if the command fails
    
    -- OR --
    
    @param  command:*str  Command line arguments, including the command
    '''
    command = list([command] if isinstance(command, str) else command) + ([fail] if isinstance(fail, str) else []) + list(command_)
    __print('Executing external command: ' + str(command))
    proc = Popen(command, stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr)
    output = proc.communicate()[0]
    if fail and (proc.returncode != 0):
        raise Exception('%s exited with error code %i' % (str(command), proc.returncode))


def bash_pipe(command, fail = True):
    '''
    Execute a shell command, in GNU Bash
    
    @param  command:str  The shell command
    @param  fail:bool    Whether to raise an exception if the command fails
    '''
    return execute_pipe(['bash', '-c', command], fail)


def bash(command, fail = True):
    '''
    Execute a shell command, in GNU Bash
    
    @param  command:str  The shell command
    @param  fail:bool    Whether to raise an exception if the command fails
    '''
    execute(['bash', '-c', command], fail)


def bash_escape(*word):
    '''
    Escape one or more words for `bash()`
    
    @param   word:*str        The words to escape
    @return  :str|tuple<str>  The words escaped, will be a string if the input was a string
    '''
    if len(word) == 1:
        word = word[0]
    if isinstance(word, str):
        return '\'' + word.replace('\'', '\'\\\'\'') + '\''
    else:
        rc = []
        for w in word:
            rc.append('\'' + w.replace('\'', '\'\\\'\'') + '\'')
        return tuple(rc)


def sha3sum(files):
    '''
    Calculate the Keccak[] sum of one or more files
    
    @param   files:str|itr<str>  The files
    @return  :str|list<str>      The sums, will be an string if the input as a string
    '''
    sha3 = SHA3()
    if isinstance(files, str):
        return sha3.digest_file(files)
    elif len(files) == 0:
        return []
    else:
        rc = [sha3.digest_file(files[0])]
        for file in files[1:]:
            sha3.reinitialise()
            rc.append(sha3.digest_file(file))
        return rc


def patch(patches, strip = 1, forward = True):
    '''
    Apply one or more patches
    
    @param  patches:str|itr<str>  Patch files to apply
    @param  strip:int             The number of prefix directories to strip away in file names
    @param  forward:bool          Whether to include the -N/--forward option
    '''
    __print('patch%s -p%i %s' % (' -N' if forward else '', strip, str(patches)))
    patches = [patches] if isinstance(patches, str) else patches
    for p in patches:
        execute(('patch -%sp%i -i' % ('N' if forward else '', strip)).split(' ') + [p], fail = True)


def unpatch(patches, strip = 1, forward = True):
    '''
    Revert one or more patches
    
    @param  patches:str|itr<str>  Patch files to apply
    @param  strip:int             The number of prefix directories to strip away in file names
    @param  forward:bool          Whether to include the -N/--forward option
    '''
    __print('unpatch%s -p%i %s' % (' -N' if forward else '', strip, str(patches)))
    patches = [patches] if isinstance(patches, str) else patches
    for p in patches:
        execute(('patch -%sp%i -R -i' % ('N' if forward else '', strip)).split(' ') + [p], fail = True)


def sed(scripts, path):
    '''
    Edit one or more file with `sed`
    
    @param  scripts:str|itr<str>  `sed` scripts
    @param  path:str|itr<str>     Files to modify
    '''
    __print('sed -e %s -i %s' % (str(scripts), str(path)))
    cmd = ['sed']
    for script in [scripts] if isinstance(scripts, str) else scripts:
        cmd.append('-e')
        cmd.append(script)
    cmd.append('-i')
    for p in [path] if isinstance(path, str) else path:
        execute(cmd + [p], fail = True)


def sed_script(pattern, replacement, selection = None, transliterate = False, multiline = False, index = 0):
    '''
    Generate a sed script
    
    Patterns are written as in sed, escape, % is used instead of \, and %% instead of %
    
    @param   pattern:str         The replacee pattern
    @param   replacement:str     The replacement pattern
    @param   selection:str?      Pattern to find to qualify a line for modification
    @param   transliterate:bool  Whether to translate character rather the using regular expression
    @param   multiline:bool      Whether patterns can span multiple lines
    @param   index:int           Index per match on a line to replace, 0 for all
    @return  :str                The sed script
    '''
    pattern = pattern.replace('\\', '\\\\').replace('/', '\\/')
    pattern = pattern.replace('%%', '\0').replace('%', '\\').replace('\0', '%')
    replacement = replacement.replace('\\', '\\\\').replace('/', '\\/')
    replacement = replacement.replace('%%', '\0').replace('%', '\\').replace('\0', '%')
    script = '%s/%s/%s/' % ('y' if transliterate else 's', pattern, replacement)
    if (not transliterate):
        if index == 0:
            script += 'g'
        else:
            script += str(index)
    if selection is not None:
        selection = selection.replace('\\', '\\\\').replace('/', '\\/')
        selection = selection.replace('%%', '\0').replace('%', '\\').replace('\0', '%')
        script = '/%s/%s' % (selection, script)
    if multiline:
        script = ':a;N;$!ba;' + script
    return script


def filter_locale(i_use_locale, pkgdir, prefix, localedir = '/share/locale'):
    '''
    Remove undesired locale files
    
    @param  i_use_locale:str  Comma separated list of locales to keep, just '*' for all locales
    @param  pkgdir:str        The `pkgdir` pass to `package` in the scroll
    @param  prefix:str?       The packages's prefix path
    @param  localedir:str     The path, excluding prefix, for locales
    '''
    if i_use_locale == '*':
        return
    if prefix is not None:
        if prefix.replace('/', '') == '':
            prefix = '/usr'
        localedir = pkgdir + prefix + localedir
    else:
        localedir = pkgdir + localedir
    if os.path.exists(localedir) and os.path.isdir(localedir):
        localedir_bak = localedir + '-'
        while os.path.exists(localedir_bak):
            localedir_bak += '-'
        mv(localedir_bak, localedir)
        recreated = False
        for locale in i_use_locale.split(''):
            if len(locale) == 0:
                continue
            if os.path.exists('%s/%s' % (localedir_bak, locale)):
                if not recreated:
                    recreated = True
                    mkdir(localedir)
                mv('%s/%s' % (localedir_bak, locale), '%s/%s' % (localedir, locale))
        rm_r(localedir_bak)


def post_install_info(rootdir, installedfiles, private, i_use_info):
    '''
    Perform post-install actions for info manuals
    
    @param  rootdir         The root directory for the installation
    @param  installedfiles  The installed files
    @param  private         Whether the install is a private install
    @param  i_use_info      Whether to install info manuals
    '''
    if i_use_info:
        for _prefix in ([path('~/.local')] if private else ['/usr', '/usr/local']):
            _infodir = rootdir + _prefix + '/share/info/'
            files = []
            for file in installedfiles:
                if file.startswith(_infodir) and os.path.lexists(file):
                    files.append(file)
            install_info(files, _infodir[:-1])


def pre_upgrade_info(rootdir, installedfiles, private):
    '''
    Perform pre-upgrade actions for info manuals
    
    @param  rootdir         The root directory for the installation
    @param  installedfiles  The installed files
    @param  private         Whether the install is a private install
    '''
    pre_uninstall_info(rootdir, installedfiles, private)


def post_upgrade_info(rootdir, installedfiles, private, i_use_info):
    '''
    Perform post-upgrade actions for info manuals
    
    @param  rootdir         The root directory for the installation
    @param  installedfiles  The installed files
    @param  private         Whether the install is a private install
    '''
    post_install_info(rootdir, installedfiles, private, i_use_info)


def pre_uninstall_info(rootdir, installedfiles, private):
    '''
    Perform pre-uninstall actions for info manuals
    
    @param  rootdir         The root directory for the installation
    @param  installedfiles  The installed files
    @param  private         Whether the install is a private install
    @param  i_use_info      Whether to install info manuals
    '''
    for _prefix in ([path('~/.local')] if private else ['/usr', '/usr/local']):
        _infodir = rootdir + _prefix + '/share/info/'
        files = []
        for file in installedfiles:
            if file.startswith(_infodir) and os.path.lexists(file):
                files.append(file)
        uninstall_info(files, _infodir[:-1])

