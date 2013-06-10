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

from gitcord import *
from sha3sum import *



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
                 23 - File access denied
                 24 - Cannot pull git repository
                 25 - Cannot checkout git repository
                 26 - File is of wrong type, normally a directory or regular file when the other is expected
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
        @return  :byte            Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
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
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def read_files(aggregator, ponies):
        '''
        List files installed for ponies
        
        @param   aggregator:(str, str)→void
                     Feed the pony and the file when a file is detected
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
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
        @param   force:bool         Whether to override current file claim
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def disclaim(files, pony, recursive = False, private = False):
        '''
        Disclaim one or more files as a part of a pony
        
        @param   files:list<str>    File to disclaim
        @param   pony:str           The pony
        @param   recursive:bool     Whether to disclaim directories recursively
        @param   private:bool       Whether the pony is user private rather the user shared
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
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
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def clean(aggregator, shred = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   aggregator:(str, int, int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
        
        @param   shred:bool  Whether to preform secure removal when possible
        @return  :byte       Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
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
                aggregator(filename, None);
                if error == 0:
                    error = 12
            elif not os.path.isfile(filename):
                aggregator(filename, None);
                if error == 0:
                    error = 16
            else:
                aggregator(filename, sha3.digestFile(filename));
                sha3.reinitialise()
        return error



SPIKE_PATH = LibSpike.parse_filename(SPIKE_PATH)
if not SPIKE_PATH.endswith('/'):
    SPIKE_PATH += '/'

