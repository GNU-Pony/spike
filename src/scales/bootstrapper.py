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


class Bootstrapper():
    '''
    Module for libspike for bootstrapping
    '''
    
    @staticmethod
    def queue(dir, repositories, update, aggregator):
        '''
        Queue a directory for bootstrapping
        
        @param  dir:str                        The directory
        @param  repositories:set<str>          Filled with visited directories
        @param  update:list<str>               Filled with queued directories
        @param  aggregator:(dir:, int=0)→void  Feed the directory if it gets queued
        '''
        dir += '' if dir.endswith('/') else '/'
        repositories.add(os.path.realpath(dir))
        if not os.path.exists(dir + '.git/frozen.spike'):
            update.append(dir)
            aggregator(dir, 0)
    
    
    @staticmethod
    def queue_repositores(dirs, repositories, update, aggregator):
        '''
        List, for update, directories that are not frozen
        
        @param  dirs:itr<str>                  The candidate directories
        @param  repositories:set<str>          Filled with visited directories
        @param  update:list<str>               Filled with queued directories
        @param  aggregator:(dir:, int=0)→void  Feed the directory if it gets queued
        '''
        for file in dirs:
            if os.path.isdir(file):
                for repo in os.listdir(file):
                    repo = os.path.realpath(file + '/' + repo)
                    if repo not in repositories:
                        Bootstrapper.queue(repo, repositories, update, aggregator)
    
    
    @staticmethod
    def update(repository, verify_signatures):
        '''
        @param   repository:str          The repository to update
        @param   verify_signatures:bool  Whether to verify signatures
        @return  :bool                   Whether the update was successful
        '''
        return Gitcord(repository).update_branch(verify_signatures)

