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
from subprocess import Popen, PIPE



class Gitcord():
    '''
    Gitcord has awesome magic for manipulating the realms (git repositories)
    '''
    
    def __init__(self, directory):
        '''
        Constructor
        
        @param  directory:str  The git repository (or any subdirectory that is not a repository itself), or the parent folder of a new repository
        '''
        self.dir = directory
    
    
    @staticmethod
    def version():
        '''
        Obtain the version of git in the user's path
        
        @return  :list<int>  The version numbers of git, with the major version at index 0
        '''
        try:
            proc = Popen(['git', '--version'], stdin = PIPE, stdout = PIPE, stderr = None)
            proc.wait()
            output = proc.stdout.read().decode('utf-8', 'replace') # 'git version 0.0.0.0\n'
        except:
            return []
        if proc.returncode != 0:
            return []
        version = output.split()[2]
        return [int(n) for n in version.split('.')]
    
    
    @staticmethod
    def check_version(*needed):
        '''
        Check whether the version of git in the user's path is of a specific version or any newer version
        
        @param   needed:*int  The needed version
        @return  :bool        Whether the installed version is at least as new as the specified version
        '''
        installed = version() + [-1];
        for i in range(len(needed)):
            (need, have) = (needed[i], installed[i])
            if need != have:
                return need < have
        return True
    
    
    def __exec(self, command):
        '''
        Execute an exterminal command and wait for it to finish, and print output to stderr
        
        @param   command:list<str>  The command
        @return  :int               Exit value
        '''
        proc = None
        try:
            proc = Popen(command, cwd = self.dir, stdout = sys.stderr, stdin = sys.stdin, stderr = sys.stderr)
            proc.wait()
            return proc.returncode
        except:
            if proc is not None:
                return 255 if proc.returncode == 0 else proc.returncode
            else:
                return 255
    
    
    def update_branch(self, verify):
        '''
        Update the current branch in the repository. If git is new enough (>=1.8.2.4), support signature verification.
        
        @param   verify:bool  Whether to verify signatures, this is important that it could be skipped
                              because somepony may have missed it and it would not get signed before next tag
        @return  :bool        Whether the spell casting was successful
        '''
        args = ['git', 'pull']
        if verify and check_version(1, 8, 2, 4):
            args.append('--verify-signatures')
        return 0 == self.__exec(args)
    
    
    def change_branch(self, branch):
        '''
        Change current branch in the repository
        
        @param   branch:str  The new current branch
        @return  :bool       Whether the spell casting was successful
        '''
        return 0 == self.__exec(['git', 'checkout', branch])
    
    
    def clone(self, repository, directory, branch = None):
        '''
        Clone a remote repository
        
        @param   repository:str  The URL of the repository to clone
        @param   directory:str   The directory of the local clone
        @param   branch:str?     The branch to download
        @return  :bool           Whether the spell casting was successful
        '''
        if branch is None:
            return 0 == self.__exec(['git', 'clone', repository, directory])
        else:
            return 0 == self.__exec(['git', 'clone', '--branch', branch, '--single-branch', repository, directory])
    
    
    def create_repository(self, directory):
        '''
        Create a new repository
        
        @param   directory:str   The directory of the local repository
        @return  :bool           Whether the spell casting was successful
        '''
        lastdir = self.dir
        if not self.dir.endswith('/'):
            self.dir += '/'
        self.dir += directory
        os.makedirs(self.dir)
        rc = 0 == self.__exec(['git', 'init'])
        self.dir = lastdir
        return rc
    
    
    def remove_file(self, filename, shred = None):
        '''
        Remove a file from the repository
        
        @param   filename:str      The file to remove
        @param   shred:list<str>?  Option to used with shred, if secure file remove is needed (probably not as it is probably already in the git tree,) `None` if not needed
        @return  :bool             Whether the spell casting was successful
        '''
        if shred is not None:
            if 0 != (self.__exec(['shred'] + shred + [filename])):
                return False
        return 0 == self.__exec(['git', 'rm', '--force', filename])
    
    
    def obliterate_file(self, filenames, shred = None, tag_name_filter = 'cat'):
        '''
        WARNING: this is a powerful spell that rewrites history, and there is not magical mystery cure for it
        ———————
        Remove a file from all commits the the current branch of a repository
        
        @param   filename:str|itr<str>  The files to remove
        @param   shred:list<str>?       Option to used with shred, if secure file remove is needed (probably not as it is probably already in the git tree,) `None` if not needed
        @param   tag_name_filter:str?   Command used to name the new tags, leave to default to override old tags, and set to None if you do not want to create new tags
        @return  :bool                  Whether the spell casting was successful
        '''
        files = ' '.join(['\'' + f.replace('\'', '\'\\\'\'') + '\'' for f in filename])
        index_filter = 'git rm --ignore-unmatch -r --cached -- %s' % files
        if shred is not None:
            shred_opts = shred[:]
            while '-u' in shred_opts:
                shred_opts.remove('-u')
            while '--remove' in shred_opts:
                shred_opts.remove('--remove')
            shred_opts = ' '.join(['\'' + o.replace('\'', '\'\\\'\'') + '\'' for o in shred_opts])
            shred_file = '[ ! -L "$file" ] && [ -f "$file" ]; then shred %s -- "$file";' % shred_opts
            shred_dir  = '[ ! -L "$file" ] && [ -d "$file" ]; then find -mount -- "$file" | while read file; do if %s fi; done' % shred_file
            index_filter = 'for file in %s; do if %s elif %s fi; done; %s' % (files, shred_file, shred_dir, index_filter)
        command = ['git', 'filter-branch', '--force', '--index-filter', index_filter, '--prune-empty']
        if tag_name_filter is not None:
            command.append('--tag-name-filter')
            command.append(tag_name_filter)
        return 0 == self.__exec(command + ['--', '--all'])
    
    
    def stage_file(self, filename):
        '''
        Add a new file for stage changes made to a file to the repository
        
        @param   filename:str  The file to stage
        @return  :bool         Whether the spell casting was successful
        '''
        return 0 == self.__exec(['git', 'add', '--force', filename])
    
    
    def commit(self, message, signoff, gpg_sign): ## TODO the user should be able to select a message to use and whether to sign off or sign
        '''
        Commit changes in the repository
        
        @param   message:str?   The commit message, `None` for to open editor
        @param   signoff:bool   Whether to add a sign-off tag to the commit message
        @param   gpg_sign:str?  `None`, if not to signed with GPG, empty for implied key ID or the key ID with which to sign
        @return  :bool          Whether the spell casting was successful
        '''
        cmd = ['git', 'commit']
        if signoff:
            cmd += ['--signoff']
        if gpgsign is not None:
            if len(gpgsign) == 0:
                cmd += '--gpg-sign'
            else:
                cmd += '--gpg-sign=' + gpg_sign
        if message is not None:
            cmd += ['--message', message]
        return 0 == self.__exec(cmd)
    
    
    def download(self, repository, directory = None, branch = None):
        '''
        Download the tip of a remote repository
        
        @param   repository:str  The URL of the repository to clone
        @param   directory:str   The directory of the local clone
        @param   branch:str?     The branch to download
        @return  :bool           Whether the spell casting was successful
        '''
        params = ['git', 'clone', '--single-branch', '--depth', '1']
        if branch is not None:
            params += ['--branch', branch]
        params.append(repository)
        if directory is not None:
            params.append(directory)
        return 0 == self.__exec(params)
    
    
    def stash(self):
        '''
        Stash all uncommited staged changes
        
        @return  :bool  Whether the spell casting was successful, not it is successful even if there was
                        nothing to stash and no object has been added to the stash stack
        '''
        return 0 == self.__exec(['git', 'stash'])
    
    
    def pop_stash(self):
        '''
        Pop and apply the top of the stash stack
        
        @return  :bool  Whether the spell casting was successful
        '''
        return 0 == self.__exec(['git', 'stash', 'pop'])
    
    
    def apply_stash(self):
        '''
        Peek and apply the top of the stash stack
        
        @return  :bool  Whether the spell casting was successful
        '''
        return 0 == self.__exec(['git', 'stash', 'apply'])
    
    
    def drop_stash(self):
        '''
        Pop but do not apply the top of the stash stack
        
        @return  :bool  Whether the spell casting was successful
        '''
        return 0 == self.__exec(['git', 'stash', 'drop'])
    
    
    def list_stash(self):
        '''
        Get all items in the stash stack, you can use this to determine of a stash operation created and object
        
        @return  :list<str>?  All times in the stash stack, `None` on error
        '''
        proc = None
        out = None
        try:
            command = 'git stash list'.split(' ')
            proc = Popen(command, cwd = self.dir, stdout = PIPE, stdin = sys.stdin, stderr = sys.stderr)
            out = proc.communicate()[0].decode('utf-8', 'replace')
            if proc.returncode != 0:
                return None
        except:
            return None
        while out.endswith('\n'):
            out = out[:-1]
        return out.split('\n')
    
    
    def where_am_i(self):
        '''
        Get the hash of the current commit
        
        @return  :str?  Get the hash of the current commit, `None` on error
        '''
        proc = None
        out = None
        try:
            command = 'git log --pretty=format:%H'.split(' ')
            proc = Popen(command, cwd = self.dir, stdout = PIPE, stdin = sys.stdin, stderr = sys.stderr)
            out = proc.communicate()[0].decode('utf-8', 'replace')
            if proc.returncode != 0:
                return None
        except:
            return None
        return out.split('\n')[0]
    
    
    def what_changed(self, since):
        '''
        Get changes since another commit
        
        @param   since:str?                                            The other commit, `None` if since and including the first commit
        @return  :list<[filename:str, old_mode:int?, new_mode:int?]>?  Updated files, `None` on error
        '''
        proc = None
        out = None
        try:
            command = 'git whatchanged --pretty=format:%H'.split(' ')
            proc = Popen(command, cwd = self.dir, stdout = PIPE, stdin = sys.stdin, stderr = sys.stderr)
            out = proc.communicate()[0].decode('utf-8', 'replace')
            if proc.returncode != 0:
                return None
        except:
            return None
        if since is None:
            since = '*'
        out = out.split('\n')
        changes = []
        for line in out:
            if line == since:
                break
            if line.startswith(':'):
                changes.append(line[1:])
        have = {}
        _rc = []
        for line in reversed(changes):
            sep = line.find('  ')
            (old_mode, new_mode, _1, _2, action) = line[:sep].split(' ')
            filename = line[sep + 2:]
            if '\"' in filename:
                filename = eval(filename)
            old_mode = None if action == 'A' else int(old_mode)
            new_mode = None if action == 'D' else int(new_mode)
            if filename in have:
                have[filename][2] = new_mode
            else:
                entry = [filename, old_mode, new_mode]
                have[filename] = entry
                _rc.append(entry)
        rc = []
        for entry in _rc:
            if entry.old_mode is None:
                if entry.new_mode is None:
                    continue
            rc.append(entry)
        return rc

