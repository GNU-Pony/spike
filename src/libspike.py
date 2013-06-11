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
import os
# TODO use git in commands

from gitcord import *
from sha3sum import *
from spikedb import *
from algospike import *
from dragonsuite import *



SPIKE_PATH = '${SPIKE_PATH}'
'''
Spike's location
'''

SPIKE_PROGNAME = 'spike'
'''
The program name of Spike
'''



CONVERT_NONE = 0
'''
Do not convert database values
'''

CONVERT_INT = 1
'''
Do not convert database values as if numerical
'''

CONVERT_STR = 2
'''
Do not convert database values as if text
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



class LibSpike():
    '''
    Advanced programming interface for Spike
    
    Exit values:  0 - Successful
                  4 - Invalid option argument
                  5 - Root does not exist
                  6 - Scroll does not exist
                  7 - Pony is not installed
                  8 - Pony conflict
                  9 - Dependency does not exist
                 10 - File is already claimed
                 11 - File was claimed for another pony
                 12 - File does not exist
                 13 - File already exists
                 14 - Information field is not definied
                 16 - Compile error
                 17 - Installation error, usually because --private or root is needed
                 18 - Private installation is not supported
                 19 - Non-private installation is not supported
                 20 - Scroll error
                 21 - Pony ride error
                 22 - Proofread found scroll error
                 23 - File access denied # TODO this is never check for
                 24 - Cannot pull git repository
                 25 - Cannot checkout git repository
                 26 - File is of wrong type, normally a directory or regular file when the other is expected
                 27 - Corrupt database
                255 - Unknown error
    '''
    
    
    @staticmethod
    def parse_filename(filename):
        '''
        Parse a filename encoded with environment variables
        
        @param   filename:str  The encoded file name
        @return  :str          The target file name, None if the environment variables are not declared
        '''
        if '$' in filename:
            buf = ''
            esc = False
            var = None
            for c in filename:
                if esc:
                    buf += c
                    esc = False
                elif var is not None:
                    if c == '/':
                        var = os.environ[var] if var in os.environ else ''
                        if len(var) == 0:
                            return None
                        buf += var + c
                        var = None
                    else:
                        var += c
                elif c == '$':
                    var = ''
                elif c == '\\':
                    esc = True
                else:
                    buf += c
            return buf
        return filename
    
    
    @staticmethod
    def get_confs(conffile):
        '''
        Get a filename for a configuration file for Spike
        
        @param   conffile:str  Configuration file
        @return  :list<str>    File names
        '''
        rc = set()
        dirs = ['$XDG_CONFIG_HOME/', '$HOME/.config/', '$HOME/.', SPIKE_PATH, '$vardir/', '/var/', '$confdir/']
        if 'XDG_CONFIG_DIRS' in os.environ:
            for dir in os.environ['XDG_CONFIG_DIRS'].split(':'):
                if len(dir) > 0:
                    dirs.append((dir + '/').replace('//', '/'))
        dirs.append('/etc/')
        for dir in dirs:
            file = __parse_filename(dir + SPIKE_PROGNAME + '/' + conffile)
            if (file is not None) and os.path.exists(file):
                rc.add(os.path.realpath(file))
        return list(rc)
    
    
    @staticmethod
    def bootstrap(aggregator):
        '''
        Update the spike and the scroll archives
        
        @param   aggregator:(str, int)→void
                     Feed a directory path and 0 when a directory is enqueued for bootstraping.
                     Feed a directory path and 1 when a directory bootstrap process is beginning.
                     Feed a directory path and 2 when a directory bootstrap process has ended.
        
        @return  :byte  Exit value, see description of `LibSpike`, the possible ones are: 0, 12, 24
        '''
        if not os.path.exists(SPIKE_PATH):
            return 12
        
        update = []
        repositories = set()
        
        if not os.path.exists(SPIKE_PATH + '.git/frozen.spike'):
            repositories.add(os.path.realpath(SPIKE_PATH))
            update.append(SPIKE_PATH)
            aggregator(SPIKE_PATH, 0)
        
        for file in [SPIKE_PATH + 'repositories'] + get_confs('repositories'):
            if os.path.isdir(file):
                for repo in os.listdir(file):
                    repo = os.path.realpath(file + '/' + repo)
                    if repo not in repositories:
                        repositories.add(repo) 
                        if not os.path.exists(repo + '/.git/frozen.spike'):
                            update.append(SPIKE_PATH[:-1])
                            aggregator(SPIKE_PATH[:-1], 0)
        
        for repo in update:
            aggregator(repo, 1)
            if not Gitcord(repo).updateBranch():
                return 24
            aggregator(repo, 2)
        
        return 0
    
    
    @staticmethod
    def find_scroll(aggregator, patterns, installed = True, notinstalled = True):
        '''
        Search for a scroll
        
        @param   aggregator:(str)→void
                     Feed a scroll when one matching one of the patterns has been found.
        
        @param   patterns:list<str>  Regular expression search patterns
        @param   installed:bool      Look for installed packages
        @param   notinstalled:bool   Look for not installed packages
        @return  :byte               Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def find_owner(aggregator, files):
        '''
        Search for a files owner pony, includes only installed ponies
        
        @param   aggregator:(str, str?)→void
                     Feed a file path and a scroll when an owner has been found.
                     Feed a file path and `None` when it as been determined that their is no owner.
        
        @param   files:list<str>  Files for which to do lookup
        @return  :byte            Exit value, see description of `LibSpike`, the possible ones are: 0, 27
        '''
        # TODO support claim --entire
        return joined_lookup(aggregator, 'file', 'scroll', files, DB_SIZE_SCROLL, CONVERT_STR)
    
    
    @staticmethod
    def write(aggregator, scrolls, root = '/', private = False, explicitness = 0, nodep = False, force = False, shred = False):
        '''
        Install ponies from scrolls
        
        @param   aggregator:(str?, int, [*])→(void|bool|str)
                     Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - proofreading
                                     1 - scroll added because of being updated
                                     2 - resolving conflicts
                                     3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     6 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                     8 - verifying source. Additional parameters: progress state:int, progress end:int
                                     9 - compiling
                                    10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                                    11 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    12 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def update(aggregator, root = '/', ignores = [], shred = False):
        '''
        Update installed ponies
        
        @param   aggregator:(str?, int, [*])→(void|bool|str)
                     Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - proofreading
                                     1 - scroll added because of being updated
                                     2 - resolving conflicts
                                     3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     6 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                     8 - verifying source. Additional parameters: progress state:int, progress end:int
                                     9 - compiling
                                    10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                                    11 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    12 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def erase(aggregator, ponies, root = '/', private = False, shred = False):
        '''
        Uninstall ponies
        
        @param   aggregator:(str, int, int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is cleared for removal, when all is enqueued the removal begins.
        
        @param   ponies:list<str>  Ponies to uninstall
        @param   root:str          Mounted filesystem from which to perform uninstallation
        @param   private:bool      Whether to uninstall user private ponies rather than user shared ponies
        @param   shred:bool        Whether to preform secure removal when possible
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def ride(pony, private = False):
        '''
        Execute pony after best effort
        
        @param   private:bool  Whether the pony is user private rather than user shared
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 21, 27, 255
        '''
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s_%s.%%i' % ('priv_' if private else '', 'scroll', 'id')), DB_SIZE_ID)
        sink = db.fetch([], [pony])
        if len(sink) > 1:
            return 27
        if len(sink) == 0:
            return 7
        try:
            global ride
            ride = None
            for (var, value) in [('ARCH', os.uname()[4]), ('HOST', '$ARCH-unknown-linux-gnu')]:
                value = os.getenv(var, value.replace('$ARCH', os.getenv('ARCH')))
                os.putenv(var, value)
                if var not in os.environ or os.environ[var] != value:
                    os.environ[var] = value
            code = None
            scroll = locate_scroll(pony)
            if scroll == None:
                return 6
            with open(scroll, 'rb') as file:
                code = file.read().decode('utf8', 'replace') + '\n'
                code = compile(code, scroll, 'exec')
            exec(code, globals())
            if ride is None:
                return 21
            else:
                try:
                    ride(private)
                except:
                    return 21
        except:
            return 255
        return 0
    
    
    @staticmethod
    def read_files(aggregator, ponies):
        '''
        List files installed for ponies
        
        @param   aggregator:(str, str?)→void
                     Feed the pony and the file when a file is detected,
                     but `None` as the file if the pony is not installed.
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0, 7, 27
        '''
        # TODO support claim --entire
        error = 0
        fileid_scrolls = {}
        class Agg:
            def __init__(self):
                pass
            def __call__(self, scroll_fileid):
                (scroll, fileid) = scroll_fileid
                if fileid is None:
                    aggregator(scroll, None)
                    error = 7
                else:
                    if fileid in fileid_scrolls:
                        fileid_scrolls[fileid].append(scroll)
                    else:
                        fileid_scrolls[fileid] = [scroll]
        error = max(error, joined_lookup(Agg(), 'scroll', 'fileid', files, DB_SIZE_FILEID, CONVERT_INT))
        sink = []
        fileid_file = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s_%s.%%i' % ('fileid', 'file')), DB_SIZE_FILELEN)
        fileid_file.fetch(sink, fileid_scrolls.keys())
        fileid_file = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/priv_%s_%s.%%i' % ('fileid', 'file')), DB_SIZE_FILELEN)
        fileid_file.fetch(sink, fileid_scrolls.keys())
        file_fileid = {}
        nones = set()
        for (fileid, file) in sink:
            if file is None:
                if file in nones:
                    error = 27
                else:
                    nones.add(file)
                continue
            _file = ''
            for c in file:
                _file += chr(c)
            file = int(_file)
            if file in file_fileid:
                file_fileid[file].append(fileid)
            else:
                file_fileid[file] = [fileid]
        nones = set()
        for _file in file_fileid.keys():
            file = 0
            for d in _file:
                file = (file << 8) | int(d)
            class Sink:
                def __init__(self):
                    pass
                def append(self, _fileid__file):
                    (_fileid, _file) = _fileid__file
                    if _file is None:
                        if file in nones:
                            error = 27
                        else:
                            nones.add(file)
                        break
                    __file = ''
                    for c in _file:
                        if c == 0:
                            break
                        __file += chr(c)
                    for scroll in fileid_scrolls(_fileid):
                        aggregator(__file, scroll)
            fileid_file = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s_%s.%%i' % ('fileid', 'file%i' % file)), 1 << file)
            fileid_file.fetch(Sink(), file_fileid[file])
            fileid_file = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/priv_%s_%s.%%i' % ('fileid', 'file%i' % file)), 1 << file)
            fileid_file.fetch(Sink(), file_fileid[file])
        return error
    
    
    @staticmethod
    def read_info(aggregator, scrolls, field = None):
        '''
        List information about scrolls
        
        @param   aggregator:(str, str, str)→void
                     Feed the scroll, the field name and the information in the field when a scroll's information is read,
                     all (desired) fields for a scroll will come once, in an uninterrupted sequence.
        
        @param   scrolls:list<str>     Scrolls for which to list information
        @param   field:str?|list<str>  Information field or fields to fetch, `None` for everything
        @return  :byte                 Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def claim(aggregator, files, pony, recursiveness = 0, private = False, force = False):
        '''
        Claim one or more files as a part of a pony
        
        @param   aggregator:(str, str)→void
                     Feed a file and it's owner when a file is already claimed
        
        @param   files:list<str>    File to claim
        @param   pony:str           The pony
        @param   recursiveness:int  0 for not recursive, 1 for recursive, 2 for recursive at detection
        @param   private:bool       Whether the pony is user private rather the user shared
        @param   force:bool         Whether to extend current file claim
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0, 10, 11, 12, 27, 255
        '''
        for file in files:
            if not os.path.lexists(file):
                return 12
        if recursiveness == 1:
            files = find(files)
        if len(pony.encode('utf-8')) > DB_SIZE_SCROLL:
            return 255
        dirs = []
        has_root = (len(files) > 0) and files[0].startswith(os.sep)
        for file in files:
            parts = (file[1:] if has_root else file).split(os.sep)
            for i in range(len(parts)):
                dirs.append(os.sep.join(parts[:i + 1]))
        dirs.sort()
        dirs = unique(dirs)
        if has_root:
            dirs = [os.sep + dir for dir in dirs]
            dirs = [os.sep] + dirs
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'fileid_+')), 0)
        sink = db.fetch([], dirs)
        fileids = []
        for (fileid, _) in sink:
            if _ is not None:
                fileids.append(fileid)
                error = 10
        if len(fileids) > 0:
            error = max(error, joined_lookup(aggregator, 'fileid', 'scroll', fileids, DB_SIZE_SCROLL, CONVERT_STR))
        if error != 0:
            return error
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'scroll_id')), DB_SIZE_ID)
        sink = db.fetch([], [pony])
        if len(sink) != 1:
            return 27
        new = sink[0][1] is None
        if new:
            sink = db.list([])
        def conv(val):
            rc = 0
            for d in val:
                rc = (rc << 8) | int(d)
            return rc
        sink = [conv(item[1]) for item in sink]
        sink.sort()
        id = sink[len(sink) - 1]
        if new:
            id += 1
            if id >> (DB_SIZE_ID << 3) > 0:
                last = -1
                for id in sink:
                    if id > last + 1:
                        id = last + 1
                        break
                    last = id
        _id = ('0' * DB_SIZE_ID + str(id))[:DB_SIZE_ID]
        _id = bytes([int(d) for d in _id])
        _db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_id')), DB_SIZE_ID)
        file_scroll = []
        _db.fetch(file_scroll, files)
        error = 0
        scrolls = None
        for (file, scroll) in file_scroll:
            if scroll == _id:
                error = max(error, 10)
            else:
                error = 11
                if scrolls is None:
                    _db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'id_scroll')), DB_SIZE_SCROLL)
                    id_scroll = _db.list([])
                    scrolls = {}
                    for (scroll_id, scroll_name) in id_scroll:
                        scrolls[scroll_id] = scroll_name.replace('\0', '')
                aggregator(file, scrolls[conv(scroll)])
        if (not force) and (error == 11):
            return error
        if new:
            db.insert([(pony, _id)])
        id = str(id)
        if new:
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'id_scroll')), DB_SIZE_SCROLL)
            db.insert([id, (pony + '\0' * DB_SIZE_SCROLL)[DB_SIZE_SCROLL:]])
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_id')), DB_SIZE_ID)
        db.insert([(file, _id) for file in files])
        sink = []
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_fileid')), DB_SIZE_FILEID)
        db.fetch(sink, files)
        (file_id, files_withoutid) = ([], [])
        for (file, fileid) in sink:
            if fileid is None:
                files_withoutid.append(file)
            else:
                file_id.append((file, fileid))
        new_files = []
        def value(val, len):
            rc = []
            for i in range(len):
                rc.append(val & 255)
                val = val >> 8
            return bytes(reversed(rc))
        if len(files_withoutid) > 0:
            fileid_len = []
            len_fileid_name = {}
            _db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'id_fileid')), DB_SIZE_FILEID)
            ids = [fileid for (_, fileid) in _db.list([])]
            ids.sort()
            ids = unique(ids)
            fid = ids[len(ids) - 1] + 1
            (last, jump) = (-1, 0)
            for file in files_withoutid:
                if (last != -1) or (fid >> (DB_SIZE_FILEID << 3) > 0):
                    if fid >> (DB_SIZE_FILEID << 3) > 0:
                        last = -1
                        jump = 0
                    for fid in ids[jump:]:
                        jump += 1
                        if fid > last + 1:
                            fid = last + 1
                            break
                        last = fid
                file_id.append((file, fid))
                fid += 1
                n = lb32(len(file)) # limiting to 1,6 million bytes rather than 1,8 duodecillion bytes (long scale)
                name = file.encode('utf-8')
                name += '\0' * ((1 << n) - len(name))
                fileid_len.append((file, n, name))
                if n not in len_fileid_name:
                    len_fileid_name[n] = []
                len_fileid_name[n].append((fileid, name))
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_fileid')), DB_SIZE_FILEID)
            db.insert([(file, value(fileid, DB_SIZE_FILEID)) for (file, fileid) in new_files])
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'fileid_file')), DB_SIZE_FILELEN)
            db.insert([(fileid, value(n, DB_SIZE_FILELEN)) for (fileid, n) in fileid_len])
            for n in len_fileid_name.keys():
                db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'fileid_file%i' % n)), 1 << n)
                db.insert([(fileid, name) for (fileid, name) in len_fileid_name[n]])
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'id_fileid')), DB_SIZE_FILEID)
        db.insert((id, value(fileid)) for (file, fileid) in file_id])
        if recursiveness == 3:
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'fileid_+')), 0)
            _ = bytes([])
            db.insert((fileid, _) for (file, fileid) in file_id])
        inserts = [(file, _id) for (file, fileid) in file_id]
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_id')), DB_SIZE_ID)
        if force:
            db.fetch(sink, files)
            for (a, b) in sink:
                if b is not None:
                    inserts.append((a, b))
            db.remove([], files)
        db.insert(inserts)
        return error
    
    
    @staticmethod
    def disclaim(files, pony, recursive = False, private = False):
        '''
        Disclaim one or more files as a part of a pony
        
        @param   files:list<str>    File to disclaim
        @param   pony:str           The pony
        @param   recursive:bool     Whether to disclaim directories recursively
        @param   private:bool       Whether the pony is user private rather the user shared
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0, 27
        '''
        # TODO support claim --entire
        file_scrolls = {}
        class Agg:
            def __init__(self):
                pass
            def __call__(self, file, scroll):
                if scroll is not None:
                    if file not in file_scrolls:
                        file_scrolls[file] = [scroll]
                    else:
                        file_scrolls[file].append(scroll)
        error = joined_lookup(Agg(), 'file', 'scroll', files, DB_SIZE_SCROLL, CONVERT_STR, private = private)
        error_sink = []
        if error != 0:
            return error
        (exclusive, shared) = ([], [])
        for file in file_scrolls.keys():
            if pony in file_scrolls[file]:
                if len(file_scrolls[file]) == 1:
                    exclusive.add(file)
                else:
                    shared.add(file)
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'scroll_id')), DB_SIZE_ID)
        sink = []
        db.fetch(sink, [pony])
        if len(sink) != 1:
            return 27
        id = sink[0][1]
        if len(exclusive) > 0:
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_fileid')), DB_SIZE_FILEID)
            (sink, fileids) = ([], [])
            db.fetch(sink, exclusive)
            raw_ids = set()
            for fileid in unique(sorted([item[1] for item in sink])):
                _fileid = ''
                for c in fileid:
                    if (c != '0') or (len(_fileid) > 0):
                        _fileid += chr(c)
                if _fileid == '':
                    _fileid = '0'
                raw_ids.add(fileid)
                fileids.append(_fileid)
            removes = [('file_fileid', DB_SIZE_FILEID, exclusive), ('file_id', DB_SIZE_ID, exclusive), ('fileid_file', DB_SIZE_FILELEN, fileids)]
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'fileid_file')), DB_SIZE_FILELEN)
            sink = []
            db.fetch(sink, fileids)
            ns = {}
            for (fileid, _n) in sink:
                n = 0
                for d in _n:
                    n = (n << 8) | int(d)
                if n not in ns:
                    ns[n] = [fileid]
                else:
                    ns[n].append(fileid)
            for n in ns.keys():
                removes.append(('fileid_file%i' % n, 1 << n, ns[n]))
            for (_db, _len, _list) in removes:
                db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', _db)), _len)
                db.remove(error_sink, _list)
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'id_fileid')), DB_SIZE_FILEID)
            sink = []
            _id = ''
            for c in id:
                if (c != '0') or (len(_id) > 0):
                    _id += chr(c)
            if _id == '':
                _id = '0'
            db.fetch(sink, [_id])
            pairs = []
            for id_fileid in sink:
                if id_fileid[1] not in raw_ids:
                    pairs.append(id_fileid)
            db.remove(sink, [_id])
            db.insert(pairs)
        if len(shared) > 0:
            db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'file_id')), DB_SIZE_ID)
            sink = []
            db.fetch(sink, shared)
            pairs = []
            files = set()
            for (file, _id) in sink:
                if _id is None:
                    error_sink.append((file, _id))
                elif _id != id:
                    pairs.append((file, _id))
                    files.add(file)
            db.remove(list(files))
            db.insert(pairs)
        return 0 if len(error_sink) == 0 else 27
    
    
    @staticmethod
    def archive(aggregator, archive, scrolls = False):
        '''
        Archive the current system installation state
        
        @param   aggregator:(str, int, int, int, int)→void
                     Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
        
        @param   archive:str   The archive file to create
        @param   scrolls:bool  Whether to only store scroll states and not installed files
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def rollback(aggregator, archive, keep = False, skip = False, gradeness = 0, shred = False):
        '''
        Roll back to an archived state
        
        @param   aggregator:(str, int, int, int, int)→void
                     Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
        
        @param   archive:str    Archive to roll back to
        @param   keep:bool      Keep non-archived installed ponies rather than uninstall them
        @param   skip:bool      Skip rollback of non-installed archived ponies
        @param   gradeness:int  -1 for downgrades only, 1 for upgrades only, 0 for rollback regardless of version
        @param   shred:bool     Whether to preform secure removal when possible
        @return  :byte          Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def proofread(aggregator, scrolls):
        '''
        Look for errors in a scrolls
        
        @param   aggregator:(str, int, [*])→void
                     Feed a scroll, 0, scroll index:int, scroll count:int when a scroll proofreading begins
                     Feed a scroll, 1, error message:str when a error is found
        
        @param   scrolls:list<str>  Scrolls to proofread
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 22
        '''
        (error, n) = (0, len(scrolls))
        scrollfiles = [(scrolls[i], locate_scroll(scrolls[i]), i) for i in range(n)]
        for (scroll, scrollfile, i) in scrollfiles:
            aggregator(scroll, 0, i, n)
            if scrollfile is None:
                error = max(error, 6)
                aggregator(scroll, 1, 'Scroll not found')
            else:
                try:
                    pass # TODO proofread `scrollfile`
                except Exception as err:
                    error = max(error, 22)
                    aggregator(scroll, 1, str(err))
        return error
    
    
    @staticmethod
    def clean(aggregator, private = False, shred = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   aggregator:(str, int, int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
        
        @param   shred:bool    Whether to preform secure removal when possible
        @param   private:bool  Whether to uninstall user private ponies rather than user shared ponies
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0, 27 (TODO same as `erase`)
        '''
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'scroll_id')), DB_SIZE_ID)
        sink = db.list([])
        id_scroll = {}
        for (scroll, id) in sink:
            id_scroll[id] = scroll
        queue = []
        newqueue = []
        def found(id):
            queue.append(id)
            newqueue.append(id)
            aggregator(id_scroll[id], 0, 1)
        db = SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s.%%i' % ('priv_' if private else '', 'deps_id')), DB_SIZE_ID)
        sink = db.list([])
        deps_id = {}
        for (deps, id) in sink:
            if deps not in id_scroll:
                return 27
            if deps not in deps_id:
                deps_id[deps] = set()
            _id = 0
            for d in id:
                _id = (_id << 8) | int(d)
            deps_id[deps].add(_id)
        remove = []
        for deps in deps_id.keys():
            if deps in deps_id[deps]:
                remove.append(deps)
        for deps in remove:
            del deps_id[dels]
        def get_clique(deps, clique, visited):
            if deps in visited:
                return None
            else:
                visited.add(deps)
            ids = deps_id[deps]
            for id in ids:
                if id not in deps_id:
                    return None
            clique.add(deps)
            for id in ids:
                if id not in clique:
                    if get_clique(id, clique, visited) is None:
                        return None
            return clique
        while True:
            newqueue[:] = []
            for deps in deps_id.keys():
                if len(deps_id[deps]) == 0:
                    found(deps)
            if len(newqueue) == 0:
                visited = set()
                for deps in deps_id.keys():
                    if deps not in visited:
                        clique = get_clique(deps, set(), visited)
                        if clique is not None:
                            newqueue.expand(list(clique))
                            break
                if len(newqueue) == 0:
                    break
            for deps in newqueue:
                del deps_id[deps]
        class Agg:
            def __init__(self):
                pass
            def __call__(self, scroll, state, end):
                if state != 0:
                    aggregator(scroll, state, end)
        return erase(Agg(), queue, private = private, shred = shred)
    
    
    @staticmethod
    def sha3sum(aggregator, files):
        '''
        Look for errors in a scrolls
        
        @param   aggregator:(str, str?)→void
                     Feed a file and its checksum when one has been calculated.
                    `None` is returned as the checksum if it is not a regular file or does not exist.
        
        @param   files:list<str>  Files for which to calculate the checksum
        @return  :byte            Exit value, see description of `LibSpike`, the possible ones are: 0, 12, 16
        '''
        error = 0
        sha3 = SHA3()
        for filename in files:
            if not os.path.exists(filename):
                aggregator(filename, None)
                if error == 0:
                    error = 12
            elif not os.path.isfile(filename):
                aggregator(filename, None)
                if error == 0:
                    error = 16
            else:
                aggregator(filename, sha3.digestFile(filename));
                sha3.reinitialise()
        return error
    
    
    @staticmethod
    def joined_lookup(aggregator, fromName, toName, fromInput, toSize, toConv = CONVERT_NONE, midName = 'id', midSize = DB_SIZE_ID, private = None):
        '''
        Perform a joined database lookup from on type to another, joined using an intermediary
        
        @param  aggregator:(str, str?)→void
                    Feed a input with its output when an output value has been found,
                    but with `None` as output if there is no output
        
        @param   fromName:str   The input type
        @param   toName:str     The output type
        @param   fromInput:str  Input
        @param   toSize:str     The output type size
        @param   toConv:int     How to convert the size
        @param   midName:str    The intermediary type, must be numeric
        @param   midSize:str    The intermediary type size
        @param   private:bool?  Whether to look in the private files rather then the public, `None` for both
        @return  :byte          Exit value, see description of `LibSpike`, the possible ones are: 0, 27
        '''
        pres = ([''] if ((not private) or (private is None)) else []) else (['priv_'] if (private or (private is None)) else [])
        from_mid = [SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s_%s.%%i' % (pre, fromName, midName)), midSize) for pre in pres]
        mid_to   = [SpikeDB(SPIKE_PATH.replace('%', '%%') + ('var/%s%s_%s.%%i' % (pre, midName,   toName)),  toSize) for pre in pres]
        sink = []
        ab_as = {}
        for _from_mid in from_mid:
            _from_mid.fetch(sink, fromInput)
        nones = {}
        for (a, ab) in sink:
            if ab is None:
                if a in nones:
                    nones[a] += 1
                else:
                    nones[a] = 1
                if nones[a] == len(pres):
                    aggregator(a, None)
            else:
                _ab = ''
                for c in ab:
                    if (c != '0') or (len(_ab) > 0):
                        _ab += chr(c)
                if _ab == '':
                    _ab = '0'
                if _ab in ab_as:
                    ab_as[_ab].append(a)
                else:
                    ab_as[_ab] = [a]
        nones = {}
        error = 0
        class Agg:
            def __init__(self):
                pass
            def append(self, ab_b):
                (ab, b) = ab_b
                if b is None:
                    if ab in nones:
                        nones[ab] += 1
                    else:
                        nones[ab] = 1
                        if nones[ab] == len(pres):
                            error = 27
                    break
                _b = ''
                if toConv == CONVERT_STR:
                    for c in b:
                        if c == 0:
                            break
                        _b += chr(c)
                elif toConv == CONVERT_INT:
                    for c in b:
                        if (c != '0') or (len(_b) > 0):
                            _b += chr(c)
                    if _b == '':
                        _b = '0'
                else:
                    for c in b:
                        _b += chr(c)
                for a in ab_as[ab]:
                    aggregator(a, _b)
        for _mid_to in mid_to:
            _mid_to.fetch(Agg(), ab_as.keys())
        return error
    
    
    @staticmethod
    def locate_scroll(scroll):
        '''
        Locate the file for a scroll
        
        @param   scroll:str  The scroll
        @return  :str        The file of the scroll
        '''
        repositories = {}
        for file in [SPIKE_PATH + 'repositories'] + get_confs('repositories'):
            if os.path.isdir(file):
                for repo in os.listdir(file):
                    reponame = repo
                    repo = os.path.realpath(file + '/' + repo)
                    if os.path.isdir(repo) and (reponame not in repositories):
                        repositories[reponame] = repo
        (cat, scrl) = (None, None)
        parts = scroll.split('/')
        if len(parts) == 1:
            scrl = parts[0]
        elif len(parts) == 2:
            (cat, scrl) = parts
        elif len(parts) == 3:
            (repo, cat, scrl) = parts
            if repo not in repositories:
                return None
            repositories = {repo : repositories[repo]}
        else:
            return None
        paths = []
        if cat not is None:
            for repo in repositories:
                paths.append('%s/%s' % (repositories[repo], cat))
        else:
            for repo in repositories:
                repo = repositories[repo]
                for cat in os.listdir(repo):
                    path = '%s/%s' % (repo, cat)
                    if os.path.isdir(path):
                        paths.append(path)
        paths = ['%s/%s.scroll' % (path, scrl) for path in paths]
        rc = []
        for path in paths:
            if os.path.lexists(path) and os.path.isfile(path):
                rc.append(path)
        if len(rc) > 1:
            printerr('%s: \033[01;31m%s\033[00m' % (SPIKE_PROGNAME, 'Multiple scrolls found, there should only be one!'));
        return rc[0] if len(rc) == 1 else None



SPIKE_PATH = LibSpike.parse_filename(SPIKE_PATH)
if not SPIKE_PATH.endswith('/'):
    SPIKE_PATH += '/'

