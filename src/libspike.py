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
from dbctrl import *
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
    
    @author  Mattias Andrée (maandree@member.fsf.org)
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
        
        # List Spike for update if not frozen
        if not os.path.exists(SPIKE_PATH + '.git/frozen.spike'):
            repositories.add(os.path.realpath(SPIKE_PATH))
            update.append(SPIKE_PATH)
            aggregator(SPIKE_PATH, 0)
        
        # Look for repositories and list, for update, those that are not frozen
        for file in [SPIKE_PATH + 'repositories'] + get_confs('repositories'):
            if os.path.isdir(file):
                for repo in os.listdir(file):
                    repo = os.path.realpath(file + '/' + repo)
                    if repo not in repositories:
                        repositories.add(repo) 
                        if not os.path.exists(repo + '/.git/frozen.spike'):
                            update.append(SPIKE_PATH[:-1])
                            aggregator(SPIKE_PATH[:-1], 0)
        
        # Update Spike and repositories, those that are listed
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
        files = [os.path.abspath(file) for file in files]
        has_root = (len(files) > 0) and files[0].startswith(os.sep)
        dirs = {}
        found = {}
        class Agg():
            def __init__(self):
                pass
            def __call__(self, file, scroll):
                if scroll is not None:
                    aggregator(file, scroll)
                    found[file] = [scroll]
                else:
                    parts = (file[1:] if has_root else file).split(os.sep)
                    if has_root:
                        if os.dep not in dirs:
                            dirs[os.dep] = [file]
                        else:
                            dirs[os.dep].append(file)
                    for i in range(len(parts) - 1):
                        dir = (os.sep + os.sep.join(parts[:i + 1])) if has_root else os.sep.join(parts[:i + 1])
                        if dir not in dirs:
                            dirs[dir] = [file]
                        else:
                            dirs[dir].append(file)
        error = joined_lookup(Agg(), files, [DB_FILE_NAME(-1), DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        if error != 0:
            return error
        if len(dirs.keys()) > 0:
            sink = DBCtrl(SPIKE_PATH).open_db(False, DB_FILE_NAME, DB_FILE_ID).fetch([], dirs.keys())
            sink = DBCtrl(SPIKE_PATH).open_db(True,  DB_FILE_NAME, DB_FILE_ID).fetch([], dirs.keys())
            ids = []
            nones = set()
            for (dirname, dirid) in sink:
                if dirid is None::
                    if dirname in nones:
                        return 27
                    else:
                        nones.add(dirname)
                if dirid in dirs:
                    return 27
                dirs[dirid] = dirs[dirname]
                del dirs[dirname]
            not_found = set()
            class Sink():
                def __init__(self):
                    pass
                def append(self, dir_scroll):
                    (dir, scroll) = dir_scroll
                    if scroll is None:
                        not_found.add(dir)
                    else:
                        if scroll in not_found:
                            del not_found[scroll]
                        for file in dirs[dir]:
                            if file not in found:
                                found[file] = set([scroll])
                                aggregator(file, scroll)
                            elif scroll not in found[file]:
                                found[file].add(scroll)
                                aggregator(file, scroll)
            DBCtrl(SPIKE_PATH).open_db(False, DB_FILE_ID, DB_FILE_ENTIRE).fetch(Sink(), dirs.keys())
            DBCtrl(SPIKE_PATH).open_db(True,  DB_FILE_ID, DB_FILE_ENTIRE).fetch(Sink(), dirs.keys())
            for dir in not_found:
                for file in not_found[dir]:
                    if file not in found:
                        aggregator(file, None)
        return 0
    
    
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
        # Verify that the scroll has been installed
        sink = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).fetch([], [pony])
        if len(sink) != 1:
            return 27
        if sink[0][1] is None:
            return 7
        
        try:
            # Set $ARCH
            for (var, value) in [('ARCH', os.uname()[4]), ('HOST', '$ARCH-unknown-linux-gnu')]:
                value = os.getenv(var, value.replace('$ARCH', os.getenv('ARCH')))
                os.putenv(var, value)
                if var not in os.environ or os.environ[var] != value:
                    os.environ[var] = value
            
            # Open scroll
            global ride
            (ride, code, scroll) = (None, None, locate_scroll(pony))
            if scroll == None:
                return 6
            with open(scroll, 'rb') as file:
                code = file.read().decode('utf8', 'replace') + '\n'
                code = compile(code, scroll, 'exec')
            
            # Ride pony
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
        
        @param   aggregator:(str, str?, [bool])→void
                     Feed the pony and the file when a file is detected,
                     but `None` as the file if the pony is not installed.
                     If `None` is not passed, an additional argument is
                     passed: False normally, and True if the file is
                     recursively claimed at detection time.
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0, 7, 27
        '''
        DB = DBCtrl(SPIKE_PATH)
        error = [0]
        
        # Files belonging to specified ponies and map pony → files
        fileid_scrolls = {}
        def agg(scroll_fileid):
            (scroll, fileid) = scroll_fileid
            if fileid is None:
                aggregator(scroll, None)
                error[0] = 7
            else:
                if fileid in fileid_scrolls:
                    fileid_scrolls[fileid].append(scroll)
                else:
                    fileid_scrolls[fileid] = [scroll]
        error = max(error[0], joined_lookup(agg, ponies, [DB_PONY_NAME, DB_PONY_ID, DB_FILE_ID]))
        
        # Fetch file name lengths for files
        sink = []
        DB.open_db(False, DB_FILE_ID, DB_FILE_NAME(-1)).fetch(sink, fileid_scrolls.keys())
        DB.open_db(True,  DB_FILE_ID, DB_FILE_NAME(-1)).fetch(sink, fileid_scrolls.keys())
        
        # Map file name length → file
        (file_fileid, nones) = ({}, set())
        for (fileid, file) in sink:
            if file is None:
                if file in nones:
                    error = 27
                else:
                    nones.add(file)
                continue
            file = DBCtrl.raw_int(DBCtrl.value_convert(file, CONVERT_INT))
            if file in file_fileid:
                file_fileid[file].append(fileid)
            else:
                file_fileid[file] = [fileid]
        
        # Fetch file names for files based on file name lengths
        nones = set()
        fileid_scroll_files = {}
        for file in file_fileid.keys():
            class Sink():
                def __init__(self):
                    pass
                def append(self, fileid__file):
                    (fileid, _file) = fileid__file
                    if _file is None:
                        if _file in nones:
                            error = 27
                        else:
                            nones.add(_file)
                        break
                    _file = convert_value(_file, CONVERT_STR)
                    for scroll in fileid_scrolls[fileid]:
                        if fileid not in fileid_scroll_files:
                            fileid_scroll_files[fileid] = []
                        fileid_scroll_files[fileid].append((scroll, _file))
            DB.open_db(False, DB_FILE_ID, DB_FILE_NAME(file)).fetch(Sink(), file_fileid[file])
            DB.open_db(True,  DB_FILE_ID, DB_FILE_NAME(file)).fetch(Sink(), file_fileid[file])
        
        # Identify --entire claims and send (pony, file name, entire)
        nones = set()
        fileid = fileid_scroll_files.keys()
        class Sink():
            def __init__(self):
                pass
            def append(self, fileid_entire):
                (fileid, entire) = fileid_entire
                if entire is None:
                    if fileid in nones:
                        aggregator(fileid_scroll_files)
                    else:
                        nones.add(fileid)
                else:
                    for (scroll, filename) in fileid_scroll_files[fileid]:
                        aggregator(scroll, filename, entire is not None)
        DB.open_db(False, DB_FILE_ID, DB_FILE_ENTIRE).fetch(Sink(), fileids)
        DB.open_db(True,  DB_FILE_ID, DB_FILE_ENTIRE).fetch(Sink(), fileids)
        
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
        DB = DBCtrl(SPIKE_PATH)
        files = [os.path.abspath(file) for file in files]
        for file in files:
            if not os.path.lexists(file):
                return 12
        if recursiveness == 1:
            files = find(files)
        if len(pony.encode('utf-8')) > DB_SIZE_SCROLL:
            return 255
        
        # Check that the files are not owned by a recursively owned directory
        dirs = []
        has_root = (len(files) > 0) and files[0].startswith(os.sep)
        for file in files:
            parts = (file[1:] if has_root else file).split(os.sep)
            for i in range(len(parts) - 1):
                dirs.append(os.sep.join(parts[:i + 1]))
        dirs.sort()
        dirs = unique(dirs)
        if has_root:
            dirs = [os.sep + dir for dir in dirs]
            dirs = [os.sep] + dirs
        db = DB.open_db(private, DB_FILE_ID, DB_FILE_ENTIRE)
        fileids = DBCtrl.get_existing([], db.fetch([], dirs))
        if len(fileids) > 0:
            error = 10
        
        # Fetch and send already claimed files
        if len(fileids) > 0:
            def agg(fileid, scroll):
                if scroll is not None:
                    aggregator(fileid, scroll)
            error = max(error, joined_lookup(agg, fileids, [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME]))
        if error != 0:
            return error
        
        # Get the ID of the pony
        db = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID)
        sink = db.fetch([], [pony])
        if len(sink) != 1:
            return 27
        new = sink[0][1] is None
        if new:
            sink = db.list([])
        sink = [DBCtrl.raw_int(item[1]) for item in sink]
        sink.sort()
        id = sink[-1]
        if new:
            id += 1
            # If the highest ID is used, find the first unused
            if id >> ((DB_SIZE_ID << 3) - (0 if private else 1)) > 0:
                last = ((1 << ((DB_SIZE_ID << 3) - 1)) if private else 0) - 1
                for id in sink:
                    if id > last + 1:
                        id = last + 1
                        break
                    last = id
        _id = DBCtrl.int_bytes(id, DB_SIZE_ID)
        
        # Identify unclaimable files and report them with their owners
        (scrolls, error) = ({}, [0])
        def agg(file, scroll):
            if scroll == _id:
                error[0] = max(error[0], 10)
            else:
                error[0] = 11
                if len(scrolls.keys()) == 0:
                    id_scroll = DB.open_db(private, DB_PONY_ID, DB_PONY_NAME).list([])
                    for (scroll_id, scroll_name) in id_scroll:
                        scrolls[scroll_id] = scroll_name.replace('\0', '')
                aggregator(file, scrolls[DBCtrl.raw_int(scroll)])
        DB.open_db(agg, files, [DB_FILE_NAME(-1), DB_FILE_ID, DB_PONY_ID], private)
        error = error[0]
        if (not force) and (error == 11):
            return error
        
        # Store scroll name → scroll id and scroll id → scroll name if the pony is not installed
        if new:
            DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).insert([(pony, _id)])
        id = DBCtrl.int_raw(id)
        if new:
            _pony = (pony + '\0' * DB_SIZE_SCROLL)[DB_SIZE_SCROLL:]
            DB.open_db(private, DB_PONY_ID, DB_PONY_NAME).insert([(id, _pony)])
        
        # Fetch file name → file ID and identify files without an assigned ID
        sink = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID).fetch([], files)
        (file_id, files_withoutid) = ([], [])
        for (file, fileid) in sink:
            if fileid is None:
                files_withoutid.append(file)
            else:
                file_id.append((file, fileid))
        
        # Store information about new files
        new_files = []
        if len(files_withoutid) > 0:
            # Assign ID to new files
            (fileid_len, len_fileid_name) = ([], {})
            db = DB.open_db(private, DB_PONY_ID, DB_FILE_ID)
            ids = [fileid for (_, fileid) in db.list([])]
            ids.sort()
            ids = unique(ids)
            fid = ids[-1] + 1
            start = ((1 << ((DB_SIZE_FILEID << 3) - 1)) if private else 0) -1 
            (last, jump) = (start, 0)
            for file in files_withoutid:
                # Look for unused ID:s if the highest is already used
                if (last != -1) or (fid >> ((DB_SIZE_FILEID << 3) - (0 if private else 1)) > 0):
                    if fid >> (DB_SIZE_FILEID << 3) > 0:
                        last = start
                        jump = 0
                    for fid in ids[jump:]:
                        jump += 1
                        if fid > last + 1:
                            fid = last + 1
                            break
                        last = fid
                file_id.append((file, fid))
                fid += 1
                
                # Map file name lenght → (file ID, file name) and list all (file name, file name length, storable value of file name)
                n = lb32(len(file)) # limiting to 4,3 milliard (2²³) bytes rather than 115,8 duodecilliard (2²⁵⁶) bytes
                name = file.encode('utf-8')
                name += '\0' * ((1 << n) - len(name))
                fileid_len.append((file, n, name))
                if n not in len_fileid_name:
                    len_fileid_name[n] = []
                len_fileid_name[n].append((fileid, name))
            
            # Store file name → file ID
            db = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID)
            db.insert([(file, DBCtrl.int_bytes(fileid, DB_SIZE_FILEID)) for (file, fileid) in new_files])
            
            # Store file ID → file name length
            db = DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(-1))
            db.insert([(fileid, DBCtrl.int_bytes(n, DB_SIZE_FILELEN)) for (fileid, n) in fileid_len])
            
            # Store file ID → file name based on file name length
            for n in len_fileid_name.keys():
                db = DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(-1)(n))
                db.insert([(fileid, name) for (fileid, name) in len_fileid_name[n]])
        
        # Store scroll ID → file name ID
        db = DB.open_db(private, DB_PONY_ID, DB_FILE_ID)
        db.insert([(id, DBCtrl.int_bytes(fileid, DB_SIZE_FILEID)) for (file, fileid) in file_id])
        
        # Store --entire information
        if recursiveness == 3:
            _ = bytes([])
            db = DB.open_db(private, DB_FILE_ID, DB_FILE_ENTIRE)
            db.insert([(fileid, _) for (file, fileid) in file_id])
        
        # Store file name → owner scroll ID
        inserts = [(fileid, _id) for (file, fileid) in file_id]
        db = DB.open_db(private, DB_FILE_ID, DB_PONY_ID)
        if force:
            # Keep previous owners if using --force
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
        files = [os.path.abspath(file) for file in files]
        DB = DBCtrl(SPIKE_PATH)
        
        # Fetch and map file name → scroll
        db = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID)
        fileid_file = DBCtrl.transpose({}, db.fetch([], files), DB_FILE_ID, None)
        sink = []
        def agg(file, scroll):
            sink.append(file, scroll))
        error = joined_lookup(agg, fileid_file.keys(), [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        if error != 0:
            return error
        file_scrolls = DBCtrl.transpose(None, sink, DB_PONY_NAME, None)
        
        # Split file names into group: files claimed to one pony (exclusive), files claimed to multiple ponies (shared)
        (exclusive, shared) = ([], [])
        for file in file_scrolls.keys():
            if pony in file_scrolls[file]:
                if len(file_scrolls[file]) == 1:
                    exclusive.add(file)
                else:
                    shared.add(file)
        
        # Get the ID of the specified pony
        sink = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).fetch([], [pony])
        if (len(sink) != 1) or (sink[0][1] is None):
            return 27
        id = sink[0][1]
        error_sink = []
        
        # Disclaim exclusive files
        if len(exclusive) > 0:
            exclusiveNames = [fileid_file[file] for file in exclusive]
            removes = [(DB_FILE_NAME(-1), DB_FILE_ID, exclusiveNames), (DB_FILE_ID, DB_PONY_ID, exclusive), (DB_FILE_ID, DB_FILE_NAME(-1), fileids)]
            
            # Fetch file ID → file names
            sink = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID).fetch([], exclusiveNames)
            (raw_ids, fileids) = (set(), [])
            for fileid in unique(sorted([item[1] for item in sink])):
                raw_ids.add(fileid)
                fileids.append(DBCtrl.value_convert(fileid, CONVERT_STR))
            
            # Fetch and map file name lenght → file ID:s
            db = DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(-1))
            sink = db.fetch([], fileids)
            ns = {}
            for (fileid, n) in sink:
                if n is None:
                    error_sink.append((fileid, n))
                else:
                    n = DBCtrl.raw_int(convert_value(n, CONVERT_INT))
                    if n not in ns:
                        ns[n] = [fileid]
                    else:
                        ns[n].append(fileid)
            
            # Remove files from databases
            for n in ns.keys():
                removes.append((DB_FILE_ID, DB_FILE_NAME(n), ns[n]))
            for (db_from, db_to, rm_list) in removes:
                DB.open_db(private, db_from, db_to).remove(error_sink, rm_list)
            
            # Remove files from listed as installed under their scrolls
            db = DB.open_db(private, DB_PONY_ID, DB_FILE_ID)
            _id = DBCtrl.value_convert(id, CONVERT_INT)
            sink = db.fetch([], [_id])
            pairs = []
            for id_fileid in sink:
                if id_fileid[1] not in raw_ids:
                    pairs.append(id_fileid)
            # but keep other files for the scrolls
            db.remove(sink, [_id])
            db.insert(pairs)
        
        # Disclaim shared files
        if len(shared) > 0:
            # Fetch ID of scrolls owning shared files
            db = DB.open_db(private, DB_FILE_ID, DB_PONY_ID)
            sink = db.fetch([], shared)
            
            # Get other owners of a file
            pairs = []
            files = set()
            for (file, _id) in sink:
                if _id is None:
                    error_sink.append((file, _id))
                elif _id != id:
                    pairs.append((file, _id))
                    files.add(file)
            
            # Remove the file from the pony, but not from the other ponies
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
        # Create id → scroll map
        DB = DBCtrl(SPIKE_PATH)
        sink = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).list([])
        id_scroll = {}
        for (scroll, id) in sink:
            id_scroll[id] = scroll
        
        # Queues for removable ponies
        queue = []
        newqueue = []
        def found(id):
            queue.append(id)
            newqueue.append(id)
            aggregator(id_scroll[id], 0, 1)
        
        # Get all ponies mapped to which packages have those as a dependency
        sink = DB.open_db(private, DB_PONY_DEP, DB_PONY_ID).list([])
        deps_id = {}
        for (deps, id) in sink:
            if deps not in id_scroll:
                return 27
            if deps not in deps_id:
                deps_id[deps] = set()
            deps_id[deps].add(DBCtrl.value_convert(id, CONVERT_INT))
        
        # Forget explicitly installed ponies
        remove = []
        for deps in deps_id.keys():
            if deps in deps_id[deps]:
                remove.append(deps)
        for deps in remove:
            del deps_id[dels]
        
        # Get minimal set of ponies that must be removed at the same time that can be cleaned (Not the normal meaning of 'clique')
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
        
        # Enqueue cleanable ponies
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
        
        # Erase ponies
        def agg(scroll, state, end):
            if state != 0:
                aggregator(scroll, state, end)
        return erase(agg, queue, private = private, shred = shred)
    
    
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
    def joined_lookup(aggregator, input, types, private = None):
        '''
        Perform a database lookup by joining tables
        
        @param  aggregator:(str, str?)→void
                    Feed a input with its output when an output value has been found,
                    but with `None` as output if there is no output
        
        @param   input:list<str>          Input
        @param   type:itr<(str,int,int)>  The type in order of fetch and join
        @param   private:bool?            Whether to look in the private files rather then the public, `None` for both
        @return  :byte                    Exit value, see description of `LibSpike`, the possible ones are: 0, 27
        '''
        return 0 if DBCtrl(SPIKE_PATH).joined_fetch(aggregator, input, types, private) else 27
    
    
    @staticmethod
    def locate_scroll(scroll):
        '''
        Locate the file for a scroll
        
        @param   scroll:str  The scroll
        @return  :str        The file of the scroll
        '''
        # Get repository names and paths
        repositories = {}
        for file in [SPIKE_PATH + 'repositories'] + get_confs('repositories'):
            if os.path.isdir(file):
                for repo in os.listdir(file):
                    reponame = repo
                    repo = os.path.realpath(file + '/' + repo)
                    if os.path.isdir(repo) and (reponame not in repositories):
                        repositories[reponame] = repo
        
        # Split scroll parameter into logical parts
        (cat, scrl) = (None, None)
        parts = scroll.split('/')
        if len(parts) == 1:
            scrl = parts[0]
        elif len(parts) == 2:
            (cat, scrl) = parts
        elif len(parts) == 3:
            (repo, cat, scrl) = parts
            # Limit to choosen repository
            if repo not in repositories:
                return None
            repositories = {repo : repositories[repo]}
        else:
            return None
        
        # Get category paths
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
        
        # Get scroll candidates
        paths = ['%s/%s.scroll' % (path, scrl) for path in paths]
        
        # Choose scroll file
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

