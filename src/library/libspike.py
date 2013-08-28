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
import inspect
# TODO use git in commands

from scales.installer import *
from scales.bootstrapper import *
from scales.scrollfinder import *
from scales.ownerfinder import *
from database.spikedb import *
from database.dbctrl import *
from algorithmic.algospike import *
from algorithmic.scrlver import *
from algorithmic.sha3sum import *
from auxiliary.scrollmagick import *
from auxiliary.auxfunctions import *
from library.libspikehelper import *
from dragonsuite import *



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
                 29 - Circular make dependency
                254 - User aborted
                255 - Unknown error
    '''
    
    @staticmethod
    def initialise(shred = False):
        '''
        Perform initalisations
        
        @param  shred:bool  Whether to preform secure removal when possible
        '''
        util = lambda u : SPIKE_PATH + 'src/util-replacements/' + u
        export('SPIKE_SHRED_OPTS', '-n 3 -z -u')
        if shred:
            export('shred', get('SPIKE_SHRED_OPTS'))
        optlibexec = SPIKE_PATH + 'add-on/libexec'
        if os.path.exists(optlibexec) and os.path.isdir(optlibexec):
            export('PATH', '%s:%s' % (optlibexec, get('PATH')))
        if os.path.exists(util('common')) and os.path.isdir(util('common')):
            export('PATH', '%s:%s' % (util('common'), get('PATH')))
        LibSpike.__load_addons()
        if shred:
            export('PATH', '%s:%s' % (util('shred'), get('PATH')))
        export('SPIKE_OLD_PATH', get('PATH'))
    
    
    @staticmethod
    def terminate():
        '''
        Perform terminations
        '''
        LibSpike.unlock()
    
    
    @staticmethod
    def __load_addons():
        '''
        Load add-ons
        '''
        if os.path.isdir(SPIKE_PATH + 'add-on'):
            for addon in os.listdir(SPIKE_PATH + 'add-on'):
                addon = SPIKE_PATH + 'add-on/' + addon
                if (addon[-1] != '~') and os.path.isfile(addon) and os.access(addon, os.R_OK | os.X_OK):
                    try:
                        code = None
                        with open(addon, 'rb') as file:
                            code = file.read().decode('utf8', 'replace') + '\n'
                            code = compile(code, addon, 'exec')
                        exec(code, globals())
                    except:
                        pass
    
    
    @staticmethod
    def bootstrap(aggregator, verify):
        '''
        Update the spike and the scroll archives
        
        @param   aggregator:(str, int)→void
                     Feed a directory path and 0 when a directory is enqueued for bootstraping.
                     Feed a directory path and 1 when a directory bootstrap process is beginning.
                     Feed a directory path and 2 when a directory bootstrap process has ended.
        
        @param   verify:bool  Whether to verify signatures
        @return  :byte        Exit value, see description of `LibSpike`, the possible ones are: 0, 12, 24
        '''
        LibSpike.lock(True)
        if not os.path.exists(SPIKE_PATH):
            return 12
        
        update = []
        repositories = set()
        
        # List Spike for update if not frozen
        Bootstrapper.queue(SPIKE_PATH, repositories, update, aggregator)
        
        # Look for repositories and list, for update, those that are not frozen
        Bootstrapper.queue_repositores([SPIKE_PATH + 'repositories'] + get_confs('repositories'), repositories, update, aggregator)
        
        # Update Spike and repositories, those that are listed
        for repo in update:
            aggregator(repo, 1)
            if not Bootstrapper.update(repo, verify):
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
        LibSpike.lock(False)
        
        patterns = ScrollFinder.simplify_pattern(patterns)
        
        # Get repository names and (path, found):s
        repositories = {}
        for superrepo in ['installed' if installed else None, 'repositories' if notinstalled else None]:
            if superrepo is not None:
                for file in [SPIKE_PATH + superrepo] + get_confs(superrepo):
                    ScrollFinder.get_repositories(repositories, file)
        
        ScrollFinder.match_repositories(repositories, patterns)
        categories = ScrollFinder.get_categories(repositories)
        ScrollFinder.match_categories(repositories, categories)
        ScrollFinder.flatten_categories(categories)
        scrolls = ScrollFinder.get_scrolls(categories)
        ScrollFinder.match_and_report(categories, scrolls, aggregator)
        
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
        LibSpike.lock(False)
        origfiles = make_dictionary([(os.path.abspath(file), file) for file in files])
        files = [os.path.abspath(file) for file in files]
        DB = DBCtrl(SPIKE_PATH)
        
        # Fetch filename to pony mapping
        dirs = {}
        found = set()
        owners = {}
        error = OwnerFinder.get_file_pony_mapping(files, dirs, found, owners, lambda file, scroll : aggregator(origfiles[file], scroll))
        
        if (error != 0) and (len(dirs.keys()) > 0):
            # Rekey superpaths to use ID rather then filename and discard unfound superpath
            error = OwnerFinder.use_id(DB, dirs)
            if error != 0:
                return error
            
            # Determine if superpaths are --entire claimed and store information
            did_find = set()
            OwnerFinder.filter_entire_claimed(DB, dirs, did_find, found)
            
            # Report all non-found files
            OwnerFinder.report_nonfound(files, found, lambda file : aggregator(origfiles[file], None))
            
            # Determine owner of found directories and send ownership
            def agg(dirid, scroll):
                if scroll is None:
                    error = 27
                else:
                    for file in dirs[dirid]:
                        if (file not in owners) or (scroll not in owners[file]):
                            aggregator(file, scroll)
                            dict_add(owners, file, scroll)
            _error = LibSpikeHelper.joined_lookup(agg, list(did_find), [DB_FILE_ID, DB_PONY_ID, DB_PONY_NAME])
            error = max(error, _error)
        
        return error
    
    
    @staticmethod
    def write(aggregator, scrolls, root = '/', private = False, explicitness = 0, nodep = False, force = False):
        '''
        Install ponies from scrolls
        
        @param   aggregator:(str?, int, [*])→(void|bool|str|int?)
                     Feed a scroll (`None` only at state 0, 3, 6, 7 and 9) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - inspecting installed scrolls
                                     1 - proofreading
                                     2 - scroll added because of being updated
                                     3 - resolving conflicts
                                     4 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     5 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     6 - verify installation. Additional parameters: fresh_installs:list<str>, reinstalls:list<str>, update:list<str>, downgrading:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     7 - inspecting non-install scrolls for providers
                                     8 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     9 - select when to build ponies which require interaction. Additional parameters: interactive:list<str>, allowed:int
                                                                                                Return: when:excl-flag? `None` if aborted
                                    10 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                    11 - verifying source. Additional parameters: progress state:int, progress end:int
                                    12 - compiling
                                    13 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    14 - installing files: Additional parameters: progress state:int, progress end:int
                     when:excl-flag values: 0 - Build whenever
                                            1 - Build early
                                            2 - Build early and fetch separately
                                            3 - Build late
                     allowed:int values: The union of all `1 << when` with allowed `when`
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 8, 9, 22, 29, 254, 255 (TODO)
        '''
        ## TODO checkdepends
        LibSpike.lock(True)
        # Set root
        if root is not None:
            if root.endswith('/'):
                root = root[:-1]
            SPIKE_PATH = root + SPIKE_PATH
        
        # Information needed in the progress and may only be extended
        installed_info = {}
        scroll_info = {}
        field_installed = {}
        field_scroll = {}
        installed_versions = {}
        providers = None
        provider_files = None
        not_found = set()
        uninstall = []
        
        scroll_field = {}
        installing = {}
        
        new_scrolls = {}
        for scroll in scrolls:
            new_scrolls[scroll] = None
        
        # Load information about already installed scrolls
        # TODO this should be better using spikedb
        aggregator(scroll, 0)
        for scrollfile in locate_all_scrolls(True, None if private else False):
            try:
                scrollinfo = Installer.load_information(scrollfile)
                Installer.transpose_fields(scrollinfo, field_installed)
                installed_info[scrollinfo.scroll] = scrollinfo
                installed_versions[scrollinfo.name] = scrollinfo.scroll
            except:
                return 255 # So how did we install it...
        
        while True:
            # Proofread scrolls
            def agg(scroll, state, *_):
                if state == 0:
                    aggregator(scroll, 1)
            error = proofread(agg, new_scrolls)
            if error != 0:
                return error
            
            # Report that we are looking for conflicts
            aggregator(None, 3)
            
            # Get scroll fields
            for scroll in new_scrolls.key():
                scrollfile = locate_scroll(scroll) if scroll[new_scrolls] is None else scroll[new_scrolls]
                if scrollfile is None:
                    return 255 # but, the proofreader already found them...
                else:
                    try:
                        scrollinfo = Installer.load_information(scrollfile)
                        Installer.transpose_fields(scrollinfo, field_scroll)
                        scroll_info[scrollinfo.scroll] = scrollinfo
                    except:
                        return 255 # but, the proofreader did not have any problem...
            
            # Identify scrolls that may not be installed at the same time
            if not Installer.check_conflicts([scroll_info, installed_info]):
                return 8
            
            # Look for missing dependencies
            needed = set()
            requirer = {}
            error = find_dependencies(scroll_info, needed, requirer, lambda scroll : (scroll.name == 'spike') and os.path.exists(SPIKE_PATH) and os.path.isdir(SPIKE_PATH))
            if error != 0:
                return error
            
            # Locate the missing dependencies
            new_scrolls = {}
            for scroll in needed:
                path = locate_scroll(scroll.name, False)
                if path is None:
                    not_found.add(scroll)
                else:
                    new_scrolls[scroll] = path
                    aggregator(scroll.name, 4, requirer[scroll.name])
            
            # Remove replaced ponies
            Installer.replacements(scroll_info, installed_info, field_installed, uninstall, aggregator)
            
            # Loop if we got some additional scrolls
            if len(new_scrolls.keys()) > 0:
                continue
            
            # We as for confirmation first because if optimisation is not done, finding provider can take some serious time
            fresh_installs, reinstalls, update, downgrading, skipping = [], [], [], [], []
            Installer.update_types(scroll_info, installed_versions, fresh_installs, reinstalls, update, downgrading, skipping)
            if not aggregator(None, 6, fresh_installs, reinstalls, update, downgrading, skipping):
                return 254
            
            # Select providers and loop if any was needed
            if len(not_found) > 0:
                # Read all scrolls so we can find providers
                # TODO this should be better using spikedb
                if providers is None:
                    aggregator(None, 7)
                    providers = {}
                    provider_files = {}
                    for scrollfile in locate_all_scrolls(False):
                        scroll = Installer.load_information(scrollfile)
                        for provides in scroll['provides']:
                            provides.slice_map(providers, scroll.scroll)
                            provider_file[scroll.scroll.full] = scroll.file
                
                # Select provider
                for scroll in not_found:
                    options = ScrollVersion(scroll).get_all(providers)
                    if len(options) == 0:
                        return 9
                    option = aggregator(scroll, 8, [opt.scroll.full for opt in options])
                    if option is None:
                        return 254
                    option = ScrollVersion(option)
                    new_scrolls[option.name] = provider_file[option]
                not_found = set()
            else:
                break
        
        # TODO at any time make dependencies have not yet been installed
        #      all compiled scroll are to be installed. If an interactive scroll is non-installed
        #      make dependancies whose scroll is not interactive, `when` make only be 0, or 3
        #      if they are all at the end of the t:sorted list.
        
        # Topologically sort scrolls
        tsorted = Installer.tsort_scrolls(scroll_info)
        if tsorted is None:
            return 29
        
        # Separate scrolls that need itneraction from those that do not
        interactively_installed = []
        noninteractively_installed = []
        for (scroll, _) in tsorted:
            if scroll['interactive']:
                interactively_installed.append(scroll)
            else:
                noninteractively_installed.append(scroll)
        
        # Select when to build scrolls that need interaction
        when = 0
        allowed_when = (1 << 4) - 1
        if len(interactively_installed) > 0:
            when = aggregator(None, 9, [scroll.scroll.full for scroll in interactively_installed], allowed_when)
            if when is None:
                return 254
            if (0 < when) or (((1 << when) & allowed_when) == 0):
                return 255
        
        # Get order to download and build scrolls
        first_download, second_download = tsorted, []
        first_build, second_build = first_download, second_build
        if when == 1:
            first_download, second_download = interactively_installed, noninteractively_installed
        elif when == 2:
            first_download, second_download = interactively_installed, noninteractively_installed
            first_build, second_build = first_download, second_download
        elif when == 3:
            first_download, second_download = noninteractively_installed, interactively_installed
        
        # Download and verify sources and compile
        for (download_list, build_list) in [(first_download, first_build), (second_download, second_build)]:
            # Download sources
            for scroll in download_list:
                pass ## TODO download
            
            # Verify sources
            ## TODO verify
            
            # Compile
            for scroll in build_list:
                pass ## TODO build
        
        # Check for file conflicts
        if not force:
            pass ## TODO check for file conflicts
        
        ## TODO install
        
        return 0
    
    
    @staticmethod
    def update(aggregator, root = '/', ignores = [], private = False):
        '''
        Update installed ponies
        
        @param   aggregator:(str?, int, [*])→(void|bool|str|int?)
                     Feed a scroll (`None` only at state 0, 3, 6, 7 and 9) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - inspecting installed scrolls
                                     1 - proofreading
                                     2 - scroll added because of being updated
                                     3 - resolving conflicts
                                     4 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     5 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     6 - verify installation. Additional parameters: fresh_installs:list<str>, reinstalls:list<str>, update:list<str>, downgrading:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     7 - inspecting non-install scrolls for providers
                                     8 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     9 - select when to build ponies which require interaction. Additional parameters: interactive:list<str>, allowed:int
                                                                                                Return: when:excl-flag? `None` if aborted
                                    10 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                    11 - verifying source. Additional parameters: progress state:int, progress end:int
                                    12 - compiling
                                    13 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    14 - installing files: Additional parameters: progress state:int, progress end:int
                     when:excl-flag values: 0 - Build whenever
                                            1 - Build early
                                            2 - Build early and fetch separately
                                            3 - Build late
                     allowed:int values: The union of all `1 << when` with allowed `when`
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   private:bool       Whether to update user private packages
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        LibSpike.lock(True)
        # Set root
        if root is not None:
            if root.endswith('/'):
                root = root[:-1]
            SPIKE_PATH = root + SPIKE_PATH
        
        return 0
    
    
    @staticmethod
    def erase(aggregator, ponies, root = '/', private = False):
        '''
        Uninstall ponies
        
        @param   aggregator:(str, int, int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is cleared for removal, when all is enqueued the removal begins.
        
        @param   ponies:list<str>  Ponies to uninstall
        @param   root:str          Mounted filesystem from which to perform uninstallation
        @param   private:bool      Whether to uninstall user private ponies rather than user shared ponies
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 14(internal bug), 20, 23, 27, 28, 255
        '''
        # TODO also remove dependencies, but verify
        
        LibSpike.lock(True)
        error = 0
        try:
            # Set root
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
                        update(DB.open_db(private, DB_FILE_ID, DB_PONY_ID), [], shared, pairs)
                    
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
                update(db, [], list(deps), pairs)
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
        LibSpike.lock(False)
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
                        LibSpike.unlock()
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
        LibSpike.lock(False)
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
        # TODO add required by (manditory, optional, make, check) and whether there exists an example shot
        # TODO display `metalicense`
        
        LibSpike.lock(False)
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
                                value = ScrollMagick.field_display_convert(field, value)
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
        LibSpike.lock(True)
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
        LibSpike.lock(True)
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
            update(db, sink, [_id], pairs)
        
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
            update(db, [], list(files), pairs)
        
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
        LibSpike.lock(False)
        return 0
    
    
    @staticmethod
    def rollback(aggregator, archive, keep = False, skip = False, gradeness = 0):
        '''
        Roll back to an archived state
        
        @param   aggregator:(str, int, int, int, int)→void
                     Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
        
        @param   archive:str    Archive to roll back to
        @param   keep:bool      Keep non-archived installed ponies rather than uninstall them
        @param   skip:bool      Skip rollback of non-installed archived ponies
        @param   gradeness:int  -1 for downgrades only, 1 for upgrades only, 0 for rollback regardless of version
        @return  :byte          Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        LibSpike.lock(True)
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
        # TODO proofread `metalicense` and check for conflicts in `freedom`
        LibSpike.lock(False)
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
                for c in range(ord(start), ord(end) + 1):
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
                    
                    ScrollMagick.check_is_list_format('freedom', False, int, lambda x : 0 <= x < (1 << 8))
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
                            raise Exception('Destination file in field \'source\' may not be empty')
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
                    
                    # Proofread using extensions
                    ScrollMagick.addon_proofread(scroll, scrollfile)
                    
                except Exception as err:
                    error = max(error, 22)
                    aggregator(scroll, 1, str(err))
        return error
    
    
    @staticmethod
    def clean(aggregator, private = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   aggregator:(str, int, int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
        
        @param   private:bool  Whether to uninstall user private ponies rather than user shared ponies
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0, 6, 7, 14(internal bug), 20, 23, 27, 28, 255
        '''
        LibSpike.lock(True)
        # TODO do not clean optionally required packages
        
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
        return erase(agg, queue, private = private)
    
    
    @staticmethod
    def example_shot(aggregator, scrolls):
        '''
        Fetch example shots file for scrolls
        
        @param   aggregator:(str, str?)→void
                     Feed a scroll and its example shot file when found, or the scroll and `None` if there is not example shot.
        
        @param   scrolls:itr<str>  Scroll of which to display example shots
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0, 6
        '''
        for scroll in scrolls:
            shot = locate_scroll(scroll)
            if shot is None:
                return 6
            else:
                shot += '.png'
                aggregator(scroll, shot if os.path.exists(shot) else None)
        return 0
    
    
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
            if (not os.path.exists(filename)) or (not os.path.isfile(filename)):
                aggregator(filename, None)
                if error == 0:
                    error = 12 if not os.path.exists(filename) else 26
            else:
                aggregator(filename, sha3.digest_file(filename));
                sha3.reinitialise()
        return error

