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
import re
import inspect
# TODO use git in commands

from libspikehelper import *
from gitcord import *
from sha3sum import *
from spikedb import *
from dbctrl import *
from algospike import *
from dragonsuite import *
from scrlver import *
from scrollmagick import *
from auxfunctions import *



class LibSpike(LibSpikeHelper):
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
                 28 - Pony is required by another pony
                255 - Unknown error
    
    @author  Mattias Andrée (maandree@member.fsf.org)
    '''
    
    
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
        @return  :byte               Exit value, see description of `LibSpike`, the possible ones are: 0
        '''
        # Simplify patterns
        pats = []
        for pattern in patterns:
            slashes = len(pattern) - len(patterns.replace('/', ''))
            if slashes <= 2:
                pats.append(('/' * (2 - slashes) + pattern).split('/'))
        
        # Get repository names and (path, found):s
        repositories = {}
        for superrepo in ['installed' if installed else None, 'repositories' if notinstalled else None]:
            if superrepo is not None:
                for file in [SPIKE_PATH + superrepo] + get_confs(superrepo):
                    if os.path.isdir(file):
                        for repo in os.listdir(file):
                            reponame = repo
                            repo = os.path.realpath(file + '/' + repo)
                            if os.path.isdir(repo) and (reponame not in repositories):
                                repositories[reponame] = (repo, [])
        
        # Match repositories
        for pat in pats:
            r = pat[0]
            if len(r) == 0:
                for repo in repositories.keys():
                    repositories[repo][1].append(pat)
            else:
                for repo in repositories.keys():
                    if re.search(r, repo) is not None:
                        repositories[repo][1].append(pat)
        
        # Get categories
        categories = {}
        for repo in repositories.keys():
            rdir = repositories[repo][0]
            for category in os.listdir(rdir):
                cdir = '%s/%s' % (rdir, category)
                if os.path.isdir(cdir):
                    if repo not in categories:
                        categories[repo] = {}
                    categories[repo][category] = (cdir, [])
        
        # Match categories
        for repo in repositories.keys():
            pats = repositories[repo][1]
            out = categories[repo]
            cats = out.keys()
            for pat in pats:
                c = pat[1]
                if len(c) == 0:
                    for cat in cats:
                        out[cat][1].append(pat)
                else:
                    for cat in cats:
                        if re.search(c, cat) is not None:
                            out[cat][1].append(pat)
        
        # Flatten categories
        repos = categories.keys()
        for repo in repos:
            for cat in categories[repo].keys():
                cat = '%s/%s' % (repo, cat)
                categories[cat] = categories[repo]
            del categories[repo]
        
        # Get scrolls
        scrolls = {}
        for cat in categories.keys():
            cdir = categories[cat][0]
            for scroll in os.listdir(cdir):
                sfile = '%s/%s' % (cdir, scroll)
                if os.path.isfile(sfile) and scroll.endswith('.scroll') and not scroll.startswith('.'):
                    scroll = scroll[:-len('.scroll')]
                    dict_append(scrolls, cat, (scroll, '%s/%s' % (cat, scroll)))
        
        # Match and report
        for cat in categories.keys():
            pats = categories[cat][1]
            for pat in pats:
                if len(pat) == 0:
                    for scroll in scrolls[cat]:
                        aggregator(scroll[1])
                else:
                    p = pat[2]
                    for (scroll, full) in scrolls[cat]:
                        if re.search(p, scroll) is not None:
                            aggregator(full)
        
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
        DB = DBCtrl(SPIKE_PATH)
        
        # Fetch filename to pony mapping
        has_root = (len(files) > 0) and files[0].startswith(os.sep)
        dirs = {}
        found = set()
        def agg(file, scroll):
            if scroll is not None:
                # Send and store found file
                aggregator(file, scroll)
                found.add(file)
            else:
                # List all superpaths to files without found scroll
                parts = (file[1:] if has_root else file).split(os.sep)
                if has_root:
                    dict_append(dirs, os.dep, file)
                for i in range(len(parts) - 1):
                    dir = (os.sep + os.sep.join(parts[:i + 1])) if has_root else os.sep.join(parts[:i + 1])
                    dict_append(dirs, dir, file)
        error = joined_lookup(agg, files, [DB_FILE_NAME(-1), DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        if error != 0:
            return error
        
        if len(dirs.keys()) > 0:
            # Fetch file id for filenames
            sink = fetch(DB, DB_FILE_NAME, DB_FILE_ID, [], dirs.keys())
            
            # Rekey superpaths to use id rather then filename and discard unfound superpath
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
            
            # Determine if superpaths are --entire claimed and store information
            not_found = set()
            did_find = set()
            class Sink():
                def __init__(self):
                    pass
                def append(self, dir_entire):
                    (dir, entire) = dir_entire
                    if entire is None:
                        if dir not in did_find:
                            not_found.add(dir)
                    else:
                        did_find.add(dir)
                        if dir in not_found:
                            del not_found[dir]
                        for file in dirs[dir]:
                            found.add(file)
            fetch(DB, DB_FILE_ID, DB_FILE_ENTIRE, Sink(), dirs.keys())
            
            # Report all non-found files
            for dir in not_found:
                for file in not_found[dir]:
                    if file not in found:
                        aggregator(file, None)
            
            # Determine owner of found directories and send ownership
            def agg(dirid, scroll):
                if scroll is None:
                    error = 27
                else:
                    for file in dirs[dirid]:
                        aggregator(file, scroll)
            error = joined_lookup(agg, list(did_find), [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        
        return error
    
    
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
                                    10 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    11 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 8, 9, 22, 255 (TODO)
        '''
        # Set shred and root
        if shred:
            export('shred', 'yes')
        if root is not None:
            if root.endswith('/'):
                root = root[:-1]
            SPIKE_PATH = root + SPIKE_PATH
        
        # Constants
        store_fields = 'pkgname pkgvel pkgrel epoch arch freedom private conflicts replaces'
        store_fields += ' provides extension variant patch patchbefore patchafter groups'
        store_fields += ' depends makedepends checkdepends optdepends'
        store_fields = store_fields.split('')
        
        # Information needed in the progress and may only be extended
        installed_field = {}
        field_installed = {}
        already_installed = {}
        scroll_field = {}
        field_scroll = {}
        freshinstalls = []
        reinstalls = []
        update = []
        skipping = []
        uninstall = []
        
        # Load information about already installed scrolls
        # TODO this should be reported as separate part in the progress
        # TODO this should be better using spikedb
        installed_scrollfiles = locate_all_scrolls(True, None if private else False)
        for scrollfile in installed_scrollfiles:
            try:
                # Set environment variables (re-export before each scroll in case a scroll changes it)
                ScrollMagick.export_environment()
                
                # Read scroll
                ScrollMagick.init_fields()
                ScrollMagick.execute_scroll(scrollfile)
                
                # Get ScrollVersion
                scroll = [globals()[var] for var in ('pkgname', 'epoch', 'pkgver', 'pkgrel')]
                scroll = ScrollVersion('%s=%i:%s-%i' % scroll)
                already_installed[scroll] = scroll
                
                # Store fields and transposition
                fields = {}
                installed_field[scroll] = fields
                for field in store_fields:
                    value = globals()[field]
                    fields[field] = value
                    if field not in field_installed:
                        field_installed[field] = {}
                    map = field_installed[field]
                    if (value is not None) and (type(value) in (str, list)):
                        for val in value if isinstance(value, list) else [value]:
                            if val is not None:
                                dict_append(map, value, scroll)
            except:
                return 255 # So how did we install it...
        
        # Proofread scrolls
        def agg(scroll, state, *_):
            if state == 0:
                aggregator(scroll, 0)
        error = proofread(agg, scrolls)
        if error != 0:
            return error
        
        # Report that we are looking for conflicts
        aggregator(None, 2)
        
        # Get scroll fields
        for scroll in scrolls:
            scrollfile = locate_scroll(scroll)
            if scrollfile is None:
                return 255 # but, the proofreader already found them...
            else:
                try:
                    # Set environment variables (re-export before each scroll in case a scroll changes it)
                    ScrollMagick.export_environment()
                    
                    # Read scroll
                    ScrollMagick.init_fields()
                    ScrollMagick.execute_scroll(scrollfile)
                    
                    # Store fields and transposition
                    fields = {}
                    scroll_field[scroll] = fields
                    for field in store_fields:
                        value = globals()[field]
                        fields[field] = value
                        if field not in field_scroll:
                            field_scroll[field] = {}
                        map = field_scroll[field]
                        if (value is not None) and (type(value) in (str, list)):
                            for val in value if isinstance(value, list) else [value]:
                                if val is not None:
                                    dict_append(map, val, scroll)
                except:
                    return 255 # but, the proofreader did not have any problem...
        
        # Identify scrolls that may not be installed at the same time
        conflicts = set()
        installed = set()
        provided = set()
        for scrollset in [scroll_field, installed_field]:
            for scroll in scrollset:
                fields = scrollset[scroll]
                if not isinstance(scroll, ScrollVersion):
                    scroll = [fields[var] for var in ('pkgname', 'epoch', 'pkgver', 'pkgrel')]
                    scroll = ScrollVersion('%s=%i:%s-%i' % scroll)
                if scroll in installed:
                    continue
                if scroll in conflicts:
                    return 8
                scroll.union_add(installed)
                for provides in feilds['provides']:
                    ScrollVersion(provides).union_add(provided)
                for conflict in fields['conflicts']:
                    conflict = ScrollVersion(conflict)
                    if (conflict in installed) or (conflict in provided):
                        return 8
                    conflict.union_add(conflicts)
        
        # Look for missing dependencies
        needed = set()
        requirer = {}
        for scroll in scroll_field:
            fields = scrollset[scroll]
            makedepends = [None if dep == '' else ScrollVersion(deps) for deps in fields['makedepends']]
            depends     = [None if dep == '' else ScrollVersion(deps) for deps in fields['depends']]
            for deps in makedepends + depends:
                if dep is None:
                    if (not os.path.exists(SPIKE_PATH)) or (not os.path.isdir(SPIKE_PATH)):
                        return 9
                else:
                    if (deps not in installed) and (deps not in provided):
                        deps.union_add(needed)
                        dict_append(requirer, deps.name, scroll)
        
        # Locate the missing dependencies
        not_found = set()
        new_scrolls = {}
        for scroll in needed:
            path = locate_scroll(scroll.name, False)
            if path is None:
                not_found.add(scroll)
            else:
                new_scrolls[scroll] = path
                aggregator(scroll.name, 3, requirer[scroll.name])
        
        # Remove replaced ponies
        for scroll in scroll_field:
            fields = scrollset[scroll]
            replaces = [ScrollVersion(deps) for deps in fields['replaces']]
            if replaces in already_installed:
                uninstall.append(already_installed[replaces])
                del installed_field[replaces]
                for field in field_installed:
                    for value in field_installed[field]:
                        field_installed[field][value].remove(replaces)
                aggregator(replaces.name, 4, scroll)
        
        return 0
    
    
    @staticmethod
    def update(aggregator, root = '/', ignores = [], private = False, shred = False):
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
                                    10 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    11 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   private:bool       Whether to update user private packages
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        # Set shred and root
        if shred:
            export('shred', 'yes')
        if root is not None:
            if root.endswith('/'):
                root = root[:-1]
            SPIKE_PATH = root + SPIKE_PATH
        
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
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 14(internal bug), 20, 23, 27, 28, 255
        '''
        # TODO also remove dependencies, but verify
        
        error = 0
        try:
            # Set shred and root
            if shred:
                export('shred', 'yes')
            if root is not None:
                if root.endswith('/'):
                    root = root[:-1]
                SPIKE_PATH = root + SPIKE_PATH
            
            # Get scroll ID:s and map the transposition
            sink = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).fetch([], ponies)
            def noneagg(pony):
                error = 7
            id_scroll = transpose({}, sink, DB_PONY_ID, noneagg, False)
            if error != 0:
                return error
            
            # Check for database corruption
            found = set()
            for id in id_scroll.keys():
                if len(id_scroll[id]) != 1:
                    return 27
                id_scroll[id] = id_scroll[id][0]
                if id_scroll[id] in found:
                    return 27
                found.add(id_scroll[id])
            
            # Get backups
            backups = set()
            def backup(filename):
                if os.path.lexists('%s.spikesave' % filename):
                    mv(filename, '%s.spikesave' % filename)
                else:
                    no = 1
                    while os.path.lexists('%s.spikesave.%i' % (filename, no)):
                        no += 1
                    mv(filename, '%s.spikesave.%i' % (filename, no))
            def agg(pony, field, value, installed):
                if field is None:
                    error = 6
                if value is not None:
                    backup.add(value)
            error = max(error, read_info(agg, ponies, field = 'backup', installed = True, notinstalled = False))
            if error != 0:
                return error
            
            # Get files for each scroll and check for dependencies
            sink = DB.open_db(private, DB_PONY_ID, DB_FILE_ID).fetch([], id_scroll.key())
            id_fileid = transpose({}, sink, DB_FILE_ID, None)
            sink = DB.open_db(private, DB_PONY_DEPS, DB_PONY_ID).fetch([], id_scroll.key())
            deps = tablise({}, sink, DB_PONY_ID, None)
            for id in id_scroll.keys():
                if (id in deps) and (len(deps[id]) > 0):
                    return 28
                if id not in id_fileid:
                    id_fileid[id] = []
                    aggregator(id_scroll[id], 0, 7)
                else:
                    aggregator(id_scroll[id], 0, len(id_fileid[id]) + 7)
            
            # Erase ponies
            for id in id_scroll.keys():
                scroll = id_scroll[id]
                endstate = len(id_fileid[id]) + 7
                
                # Remove files and remove them from the databases
                if len(id_fileid[id]):
                    progress = 0
                    
                    # Get shared and exclusive files
                    sink = DB.open_db(private, DB_FILE_ID, DB_PONY_ID).fetch([], id_fileid[id])
                    table = tablise({}, sink, DB_PONY_ID, None)
                    (shared, exclusive) = ([], [])
                    list_split(table.keys(), lambda x : exclusive if len(x) == 1 else shared)
                    
                    # Disclaim shared files
                    if len(shared) > 0:
                        progress += len(shared)
                        aggregator(scroll, progress, endstate)
                        pairs = []
                        for fileid in shared:
                            for ponyid in table[fileid]:
                                if ponyid != id:
                                    pairs.append((fileid, ponyid))
                        DB.open_db(private, DB_FILE_ID, DB_PONY_ID).remove([], shared)
                        DB.open_db(private, DB_FILE_ID, DB_PONY_ID).insert(pairs)
                    
                    # Remove exclusive files
                    if len(exclusive) > 0:
                        # Get filenames
                        sink = DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(-1)).fetch([], exclusive)
                        table = transpose({}, sink, DB_FILE_NAME(-1), None)
                        filenames = []
                        for file in table.keys():
                            sink = DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(file)).fetch([], table[file])
                            for (fileid, filename) in sink:
                                if filename is None:
                                    continue
                                filename = DBCtrl.value_convert(filename, CONVERT_STR)
                                filenames.append((filename, fileid))
                        
                        # Remove files from disc
                        dirs = {}
                        for (filename, fileid) in filenames:
                            try:
                                if os.path.lexists(filename):
                                    if os.path.islink(filename) or not os.path.isdir(filename):
                                        if filename in backups:
                                            backup(filename)
                                        else:
                                            rm(filename)
                                        progress += 1
                                        aggregator(scroll, progress, endstate)
                                    elif len(os.listdir(filename)) == 0:
                                        if filename in backups:
                                            backup(filename)
                                        else:
                                            rm(filename, directories = True)
                                        progress += 1
                                        aggregator(scroll, progress, endstate)
                                    else:
                                        dirs[fileid] = filename
                            except:
                                error = max(error, 23)
                                progress += 1
                                aggregator(scroll, progress, endstate)
                        sink = DB.open_db(private, DB_FILE_ID, DB_FILE_ENTIRE).fetch([], dirs.keys())
                        for (dirid, entire) in sink:
                            if entire is None:
                                progress += 1
                                aggregator(scroll, progress, endstate)
                            else:
                                try:
                                    if filename in backups:
                                        backup(filename)
                                    else:
                                        rm(dirs[dirid], recursive = True)
                                except:
                                    error = max(error, 23)
                                progress += 1
                                aggregator(scroll, progress, endstate)
                        
                        # Remove from database
                        for to in (DB_PONY_ID, DB_FILE_ENTIRE, DB_FILE_NAME(-1)):
                            DB.open_db(private, DB_FILE_ID, to).remove([], exclusive)
                        for file in table.keys():
                            DB.open_db(private, DB_FILE_ID, DB_FILE_NAME(file)).remove([], table[file])
                        DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID).remove([], [name for (name, _) in filenames])
                aggregator(scroll, len(id_fileid[id]) + 1, endstate)
                
                # Remove file as a dependee in dependency → scroll database
                sink = DB.open_db(private, DB_PONY_ID, DB_PONY_DEPS).fetch([], [id])
                deps = []
                for (_, dep) in sink:
                    if dep is None:
                        continue
                    dep = DBCtrl.value_convert(dep, CONVERT_INT)
                    deps.append(dep)
                db = DB.open_db(private, DB_PONY_DEPS, DB_PONY_ID)
                sink = db.fetch([], deps)
                deps = set()
                pairs = []
                for (dependency, dependee) in sink:
                    if dependee is None:
                        continue
                    deps.add(dependency)
                    if DBCtrl.value_convert(dependee, CONVERT_INT) != id:
                        pairs.append((dependency, dependee))
                db.remove([], list(deps))
                db.insert(pairs)
                aggregator(scroll, len(id_fileid[id]) + 2, endstate)
                
                # Remove pony from database
                DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).remove([], [scroll])
                aggregator(scroll, len(id_fileid[id]) + 3, endstate)
                DB.open_db(private, DB_PONY_ID, DB_PONY_DEPS).remove([], [id])
                aggregator(scroll, len(id_fileid[id]) + 4, endstate)
                DB.open_db(private, DB_PONY_ID, DB_PONY_NAME).remove([], [id])
                aggregator(scroll, len(id_fileid[id]) + 5, endstate)
                DB.open_db(private, DB_PONY_ID, DB_FILE_ID).remove([], [id])
                aggregator(scroll, len(id_fileid[id]) + 6, endstate)
                
                # Remove save scroll file
                scrollfile = locate_scroll(scroll, True, private)
                if os.path.exists(scrollfile):
                    try:
                        rm(scrollfile)
                    except:
                        error = max(error, 23)
                aggregator(scroll, endstate, endstate)
        except:
            error = 255
        return error
    
    
    @staticmethod
    def ride(pony, private = False):
        '''
        Execute pony after best effort
        
        @param   private:bool  Whether the pony is user private rather than user shared
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 20, 21, 27, 255
        '''
        # Verify that the scroll has been installed
        sink = DB.open_db(private, DB_PONY_NAME, DB_PONY_ID).fetch([], [pony])
        if len(sink) != 1:
            return 27
        if sink[0][1] is None:
            return 7
        
        try:
            # Set environment variables
            ScrollMagick.export_environment()
            
            # Open scroll
            try:
                ScrollMagick.init_methods()
                scroll = locate_scroll(pony, True, private)
                if scroll is None:
                    return 6
                ScrollMagick.execute_scroll(scroll)
                
                # Ride pony
                if ride is None:
                    return 21
                else:
                    try:
                        ride(private)
                    except:
                        return 21
            except:
                return 20
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
                dict_append(fileid_scrolls, fileid, scroll)
        error = max(error[0], joined_lookup(agg, ponies, [DB_PONY_NAME, DB_PONY_ID, DB_FILE_ID]))
        
        # Fetch file name lengths for files
        sink = fetch(DB, DB_FILE_ID, DB_FILE_NAME(-1), [], fileid_scrolls.keys())
        
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
            fileid_scrolls(file_fileid, file, fileid)
        
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
                        return
                    _file = convert_value(_file, CONVERT_STR)
                    for scroll in fileid_scrolls[fileid]:
                        if fileid not in fileid_scroll_files:
                            fileid_scroll_files[fileid] = []
                        fileid_scroll_files[fileid].append((scroll, _file))
            fetch(DB, DB_FILE_ID, DB_FILE_NAME(file), Sink(), file_fileif[file])
        
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
        fetch(DB, DB_FILE_ID, DB_FILE_ENTIRE, Sink(), fileids)
        
        return error
    
    
    @staticmethod
    def read_info(aggregator, scrolls, field = None, installed = True, notinstalled = True):
        '''
        List information about scrolls
        
        @param   aggregator:(str, str?, str?, bool)→void
                     Feed the scroll, the field name and the information in the field when a scroll's information is read,
                     all (desired) fields for a scroll will come once, in an uninterrupted sequence. Additionally it is
                     feed whether or not the information concerns a installed or not installed scroll. The values for a
                     field is returned in an uninterrupted sequence, first the non-installed scroll, then the installed
                     scroll. If a scroll is not found the field name and the value is returned as `None`. If the field
                     name is not defined, the value is returned as `None`.
        
        @param   scrolls:list<str>     Scrolls for which to list information
        @param   field:str?|list<str>  Information field or fields to fetch, `None` for everything
        @param   installed:bool        Whether to include installed scrolls
        @param   notinstalled:bool     Whether to include not installed scrolls
        @return  :byte                 Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 14, 20, 255
        '''
        # TODO add required by (manditory, optional, make, check)
        
        # Fields
        preglobals = set(globals().keys())
        ScrollMagick.init_fields()
        postglobals = list(globals().keys())
        allowedfields = set()
        for globalvar in postglobals:
            if globalvar not in preglobals:
                allowedfields.add(globalvar)
        for var in ('noextract', 'source', 'sha3sums'):
            allowedfields.remove(var)
        for var in ('repository', 'category'):
            allowedfields.add(var)
        
        allfields = field is None
        fields = list(allowedfields) if allfields else ([field] if isinstance(field, str) else field)
        error = 0
        try:
            # Define arbitrary to str convertion function
            def convert(val, first = None):
                if val is None:
                    return '-'
                elif isinstance(val, bool):
                    return 'yes' if val else 'no'
                elif isinstance(val, int) or isinstance(val, float):
                    return str(val)
                elif isinstance(val, str):
                    return val
                elif (first is not None) and (len(first) > 0) and first[0]:
                    return convert(val[0], first[1:])
                else:
                    f = None if first is None else first[1:]
                    return [convert(v, f) for v in val]
            
            for scroll in scrolls:
                # Set environment variables (re-export before each scroll in case a scroll changes it)
                ScrollMagick.export_environment()
                
                # Locate installed and not installed version of scroll
                scroll_installed    = None if not    installed else locate_scroll(scroll, True)
                scroll_notinstalled = None if not notinstalled else locate_scroll(scroll, False)
                if (scroll_installed is None) and (scroll_notinstalled is None):
                    aggregator(scroll, None, None, installed)
                    error = max(error, 6)
                    continue
                
                report = {}
                for scrollfile in [scroll_installed, scroll_notinstalled]:
                    if scrollfile is not None:
                        try:
                            installed = scrollfile is scroll_installed
                            
                            # Initalise or reset fields to their default values
                            ScrollMagick.init_fields()
                            
                            # Scroll location
                            global repository, category
                            repository = scrollfile.split('/')[-3]
                            category = scrollfile.split('/')[-2]
                            
                            # Open installed scroll
                            if scrollfile == None:
                                return 6
                            # Fetch fields
                            ScrollMagick.execute_scroll(scrollfile)
                            
                            # Prepare for report
                            for field in fields:
                                if field not in allowedfields:
                                    aggregator(scroll, field, None, installed)
                                    continue
                                value = globals()[field]
                                value = convert(value)
                                if isinstance(value, str):
                                    value = [value]
                                else:
                                    value = [str(v) for v in value]
                                for v in value:
                                    if field not in report:
                                        report[field] = []
                                    report.append((v, installed))
                        except:
                            return 20
                
                # Report findings
                for field in report.keys():
                    for data in report[field]:
                        aggregator(scroll, field, date[0], date[1])
        except:
            error = 255
        return error
    
    
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
                        continue
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
                            continue
                        last = fid
                file_id.append((file, fid))
                fid += 1
                
                # Map file name lenght → (file ID, file name) and list all (file name, file name length, storable value of file name)
                n = lb32(len(file)) # limiting to 4,3 milliard (2²³) bytes rather than 115,8 duodecilliard (2²⁵⁶) bytes
                if (1 << n) > len(file):
                    n += 1
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
        files = [os.path.abspath(file) for file in files]
        DB = DBCtrl(SPIKE_PATH)
        
        # Fetch and map file name → scroll
        db = DB.open_db(private, DB_FILE_NAME(-1), DB_FILE_ID)
        fileid_file = DBCtrl.transpose({}, db.fetch([], files), DB_FILE_ID, None)
        sink = []
        def agg(file, scroll):
            sink.append((fileid_file[file], scroll))
        error = joined_lookup(agg, fileid_file.keys(), [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
        if error != 0:
            return error
        file_scrolls = DBCtrl.transpose(None, sink, DB_PONY_NAME, None)
        
        # Split file names into group: files claimed to one pony (exclusive), files claimed to multiple ponies (shared)
        (exclusive, shared) = ([], [])
        list_split(file_scrolls.keys(), lambda x : exclusive if len(file_scrolls[x]) == 1 else shared, lambda x : pony not in file_scrolls[x])
        
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
                    dict_append(ms, DBCtrl.raw_int(convert_value(n, CONVERT_INT)), fileid)
            
            # Remove files from databases
            for n in ns.keys():
                removes.append((DB_FILE_ID, DB_FILE_NAME(n), ns[n]))
            for (db_from, db_to, rm_list) in removes:
                DB.open_db(private, db_from, db_to).remove(error_sink, rm_list)
            DB.open_db(private, DB_FILE_ID, DB_FILE_ENTIRE).remove([], exclusive)
            
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
            db.remove([], list(files))
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
        if shred:
            export('shred', 'yes')
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
        
        allowed_options = 'strip docs info man licenses changelogs libtool docs= docs=gz docs=xz info= info=gz info=xz man= man=gz man=xz upx'.split(' ')
        method_specs = {'ride'           : 'private',
                        'build'          : 'startdir srcdir pkgdir private',
                        'check'          : 'startdir srcdir pkgdir private',
                        'package'        : 'startdir srcdir pkgdir private',
                        'patch_build'    : 'startdir srcdir pkgdir private',
                        'patch_check'    : 'startdir srcdir pkgdir private',
                        'patch_package'  : 'startdir srcdir pkgdir private',
                        'pre_install'    : 'tmpdir rootdir private',
                        'post_install'   : 'tmpdir rootdir installedfiles private',
                        'pre_upgrade'    : 'tmpdir rootdir installedfiles private',
                        'post_upgrade'   : 'tmpdir rootdir installedfiles private',
                        'pre_uninstall'  : 'tmpdir rootdir installedfiles private',
                        'post_uninstall' : 'tmpdir rootdir installedfiles private'}
        
        def ishex(x):
            for i in range(x):
                if x[i] not in '0123456789ABCDEFabcdef':
                    return False
            return True
        
        def ispony(x):
            chars = set(('-', '+'))
            for (start, end) in (('0', '9'), ('a', 'z')):
                for c in range(ord(start), ord(end) + 1)):
                    chars.add(chr(c))
            for i in range(x):
                if x[i] not in chars:
                    return False
            if x.startswith('.') or x.startswith('-'):
                return False
            return len(x) > 0
        
        def isscroll(x):
            s = ScrollVersion(x if ': ' not in x else x[:x.find(': ')])
            if s.name is None:
                return False
            return ispony(s.name)
        
        for (scroll, scrollfile, i) in scrollfiles:
            # Set environment variables (re-export before each scroll in case a scroll changes it)
            ScrollMagick.export_environment()
            
            aggregator(scroll, 0, i, n)
            if scrollfile is None:
                error = max(error, 6)
                aggregator(scroll, 1, 'Scroll not found')
            else:
                try:
                    # Read scroll
                    ScrollMagick.init_fields()
                    ScrollMagick.init_methods()
                    ScrollMagick.execute_scroll(scrollfile)
                    
                    # TODO look for autoconflicts
                    # Proofread scroll fields
                    ScrollMagick.check_type_format('pkgname', False, str, ispony)
                    ScrollMagick.check_type_format('pkgver', False, str, lambda x : isscroll('x=' + x))
                    ScrollMagick.check_type_format('pkgrel', False, int, lambda x : x >= 1)
                    ScrollMagick.check_type_format('epoch', False, int, lambda x : x >= 0)
                    
                    version_a = '%s=%i:%s-%i' % (pkgname, epoch, pkgver, pkgrel)
                    version_b = scrollfile.replace(os.sep, '/').split('/')[-1][:-len('.scroll')]
                    (version_a, version_b) = (ScrollVersion(version_a), ScrollVersion(version_b))
                    if (version_b.name is False) or ('<' in version_b.full) or ('>' in version_b.full):
                        raise Exception('Scroll file name is badly formated')
                    if version_a not in version_b:
                        raise Exception('Version and name fields conflicts with scroll file name')
                    
                    ScrollMagick.check_type_format(['pkgdesc', 'upstream'], True, str, lambda x : len(x) > 0)
                    ScrollMagick.check_is_list_format('arch', False, str, lambda x : len(x) > 0)
                    if len(arch) == 0:
                        raise Exception('Field \'arch\' may not be empty')
                    
                    ScrollMagick.check_is_list_format('freedom', False, int, lambda x : 0 <= x < (1 << 2))
                    ScrollMagick.check_is_list_format('license', False, str, lambda x : len(x) > 0)
                    ScrollMagick.check_is_list_format('private', False, int, lambda x : 0 <= x < 3)
                    ScrollMagick.check_type('interactive', False, bool)
                    ScrollMagick.check_is_list_format(['conflicts', 'replaces', 'provides'], False, str, isscroll)
                    ScrollMagick.check_type_format(['extension', 'variant', 'patch'], True, str, ispony)
                    ScrollMagick.check_type_format('reason', True, str, lambda x : len(x) > 0)
                    ScrollMagick.check_is_list_format(['patchbefore', 'patchafter'], False, str, isscroll)
                    ScrollMagick.check_is_list_format('groups', False, str, ispony)
                    ScrollMagick.check_is_list_format(['depends', 'makedepends', 'checkdepends', 'optdepends'], False, str, lambda x : len(x) == 0 or isscroll(x))
                    ScrollMagick.check_is_list('noextract', False, str)
                    
                    ScrollMagick.check_is_list('source', False, str, list)
                    elements = set()
                    for element in source:
                        if isinstance(element, list):
                            if len(element) < 2:
                                raise Exception('Lists in field \'source\' must be at least of length 2')
                            for elem in element:
                                if elem is None:
                                    raise Exception('Lists in field \'source\' may not contain `None`')
                                elif isinstance(elem, str):
                                    raise Exception('Lists in field \'source\' is restricted to str elements')
                            if len(element[0]):
                                raise Exception('Source file in field \'source\' may not be empty')
                            element = element[1]
                        if element:
                            raise Exception('destination file in field \'source\' may not be empty')
                        if element in elements:
                            raise Exception('Duplicate destination file \'%s\' in field \'source\'', element)
                        else:
                            elements.add(element)
                    
                    ScrollMagick.check_is_list_format('sha3sums', True, str, lambda x : len(x) == 144 and ishex(x))
                    if len(sha3sums) != len(source):
                        raise Exception('Fields \'sha3sums\' and \'source\' must be of same size')
                    
                    for field in ('noextract', 'backup'):
                        have = set()
                        value = globals()[field]
                        for element in value:
                            if element not in elements:
                                raise Exception('Field \'%s\' may only contain destination files from \'source\'' % field)
                            if element in have:
                                raise Exception('Field \'%s\' contains duplicate file \'%s\'', (field, element))
                            have.add(element)
                    
                    ScrollMagick.check_is_list_elements('options', False, str, allowed_options)
                    
                    # Proofread scroll methods
                    if ride is None:
                        raise Exception('Method \'ride\' should be default, in worst case just echo some information')
                    if package is None:
                        raise Exception('Method \'package\' must be default, even if does nothing')
                    
                    if method in method_specs.keys():
                        if globals()[method] is None:
                            continue
                        (args, varargs, keywords, defaults) = inspect.getargspec(globals()[method])
                        if varargs  is not None:  raise Exception('Methods should not use varargs (i.e. *variables)')
                        if keywords is not None:  raise Exception('Methods should not use keywords (i.e. **variables)')
                        if defaults is not None:  raise Exception('Methods should specify default values for parameters')
                        params_str = '(%s)' % method_specs[method].replace(' ', ', ')
                        params_list = list(method_specs[method].split(' '))
                        if list(args) != params_list:
                            raise Exception('Method \'%s\' should have the parameters %s with those exact names', (method, params_str))
                    
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
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 14(internal bug), 20, 23, 27, 28, 255
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
        iterator_remove(deps_id, lambda deps : deps_id[deps])
        
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
        @return  :byte            Exit value, see description of `LibSpike`, the possible ones are: 0, 12, 26
        '''
        (error, sha3) = (0, SHA3())
        for filename in files:
            if (not os.path.exists(filename)) or not (not os.path.isfile(filename)):
                aggregator(filename, None)
                if error == 0:
                    error = 12 if not os.path.exists(filename) else 26
            else:
                aggregator(filename, sha3.digestFile(filename));
                sha3.reinitialise()
        return error

