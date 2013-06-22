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



class LibSpikeHelper():
    '''
    Helper for LibSpike
    
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
    def locate_scroll(scroll, installed = False, private = None):
        '''
        Locate the file for a scroll
        
        @param   scroll:str      The scroll
        @parm    installed:bool  Whether the scroll is installed
        @parm    private:bool?   Whether the scroll is installed privately, `None` for whatever
        @return  :str            The file of the scroll
        '''
        # Get repository names and paths
        repositories = {}
        superrepo = 'installed' if installed else 'repositories'
        home = os.environ[HOME].replace(os.sep, '/') + '/'
        while '//' in home:
            home = home.replace('//', '/')
        for file in [SPIKE_PATH + superrepo] + get_confs(superrepo):
            if private is not None:
                if file.startswith(home) != private:
                    continue
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
        if cat is not None:
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



if 'SPIKE_PATH' not in os.environ:
    spike_path = os.path.realpath(sys.argv[0])
    spike_path = os.path.dirname(os.path.dirname(spike_path))
    os.environ['SPIKE_PATH'] = spike_path
SPIKE_PATH = LibSpikeHelper.parse_filename(SPIKE_PATH)
if not SPIKE_PATH.endswith('/'):
    SPIKE_PATH += '/'

