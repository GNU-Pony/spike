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
from subprocess import Popen, PIPE



class Gitcord():
    '''
    Gitcord has awesome magic for manipulating the realms (git repositories)
    '''
    
    def __init__(directory):
        '''
        Constructor
        
        @param  directory:str  The git repository (or any subdirectory that is not a repository itself), or the parent folder of a new repository
        '''
        self.dir = directory
    
    
    def __exec(command):
        '''
        Execute an exterminal command and wait for it to finish, and print output to stderr
        
        @param   command:list<str>  The command
        @return  :int               Exit value
        '''
        proc = None
        try:
            proc = Popen(command, cwd=self.dir, stdout=sys.stderr, stdin=sys.stdin, stderr=sys.stderr)
            return proc.returncode
        except:
            if proc is not None:
                return 255 if proc.returncode == 0 else proc.returncode
            else:
                return 255
    
    
    def updateBransh():
        '''
        Update the current bransh in the repository
        
        @return  :bool  Whether the spell casting was successful
        '''
        return 0 == __exec(['git', 'pull']) ## TODO add --verify-signatures at git 1.8.2-rc4
    
    
    def changeBransh(bransh):
        '''
        Change current bransh in the repository
        
        @param   bransh:str  The new current bransh
        @return  :bool       Whether the spell casting was successful
        '''
        return 0 == __exec(['git', 'checkout', bransh])
    
    
    def clone(repository, directory, branch = None):
        '''
        Change current bransh in the repository
        
        @param   repository:str  The URL of the repository to clone
        @param   directory:str   The directory of the local clone
        @param   branch:str?     The branch to download
        @return  :bool           Whether the spell casting was successful
        '''
        if branch is None:
            return 0 == __exec(['git', 'clone', repository, directory])
        else:
            return 0 == __exec(['git', 'clone', '--branch', branch, '--single-branch', repository, directory])
    
    
    def createRepository(directory):
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
        rc = 0 == __exec(['git', 'init'])
        self.dir = lastdir
        return rc
    
    
    def removeFile(filename):
        '''
        Remove a file from the repository
        
        @param   filename:str  The file to remove
        @return  :bool         Whether the spell casting was successful
        '''
        return 0 == __exec(['git', 'rm', '--force', filename])
    
    
    def stageFile(filename):
        '''
        Add a new file for stage changes made to a file to the repository
        
        @param   filename:str  The file to stage
        @return  :bool         Whether the spell casting was successful
        '''
        return 0 == __exec(['git', 'add', '--force', filename])
    
    
    def commit(message, signoff, gpgsign): ## TODO the user should be able to select a message to use and whether to sign off or sign
        '''
        Commit changes in the repository
        
        @param   message:str   The commit message
        @param   signoff:bool  Whether to add a sign-off tag to the commit message
        @param   gpgsign:str?  `None`, if not to signed with GPG, empty for implied key ID or the key ID with which to sign
        @return  :bool         Whether the spell casting was successful
        '''
        cmd = ['git', 'commit']
        if signoff:
            cmd += ['--signoff']
        if gpgsign is not None:
            if len(gpgsign) == 0:
                cmd += '--gpg-sign'
            else:
                cmd += '--gpg-sign=' + gpgsign
        cmd += ['--message', message]
        return 0 == __exec(cmd)

