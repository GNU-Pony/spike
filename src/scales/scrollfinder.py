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
import re

from auxiliary.auxfunctions import *



class ScrollFinder():
    '''
    Module for libspike for finding scrolls
    '''
    @staticmethod
    def regex_match(needle, haystack):
        '''
        Tests if a pattern can be found in a text
        
        @param   needle:str    The pattern to search for
        @param   haystack:str  The text to search in
        @return  :bool         Whether the pattern can be found in the text
        '''
        return re.search(needle, haystack) is not None
    
    
    @staticmethod
    def simplify_patterns(patterns):
        '''
        Simplify patterns by splitting them into their three parts
        
        @param   patterns:itr<str>                       The patterns
        @return  :list<(repo:str, cat:str, scroll:str)>  The patterns simplified
        '''
        pats = []
        for pattern in patterns:
            pattern = ScrollFinder.simplify_pattern(pattern)
            if pattern is not None:
                pats.append(pattern)
        return pats
    
    
    @staticmethod
    def simplify_pattern(pattern):
        '''
        Simplify a pattern by splitting it into its three parts
        
        @param   pattern:str                        The pattern
        @return  :(repo:str, cat:str, scroll:str)?  The repository pattern, the category pattern and the scroll pattern, but `None` if there as too many parts in the pattern or if it is otherwise invalid
        '''
        slashes = len(pattern) - len(pattern.replace('/', ''))
        if slashes <= 2:
            return ('/' * (2 - slashes) + pattern).split('/')
        return None
    
    
    @staticmethod
    def get_repositories(repositories, file):
        '''
        Get repositories
        
        @param  repositories:dict<str, (str, list=[])>  Map to fill with repository name → (repository directory, empty list)
        @param  file:str                                Candidate file for containg repositories
        '''
        if os.path.isdir(file):
            for repo in os.listdir(file):
                reponame = repo
                repo = os.path.realpath(file + '/' + repo)
                if os.path.isdir(repo) and (reponame not in repositories):
                    repositories[reponame] = (repo, [])
    
    
    @staticmethod
    def match_repositories(repositories, patterns):
        '''
        Match patterns to repositories
        
        @param  repositories:dict<str, (str, list<(str, str, str)>)>  Map to fill with matching patterns
        @param  patterns:itr<(repo:str, str, str)>                    Patterns
        '''
        for pattern in patterns:
            r = pattern[0]
            if len(r) == 0:
                for repo in repositories.keys():
                    repositories[repo][1].append(pattern)
            else:
                for repo in repositories.keys():
                    if regex_match(r, repo):
                        repositories[repo][1].append(pattern)
    
    
    @staticmethod
    def get_categories(repositories):
        '''
        Get categories
        
        @param   repositories:dict<str, (str, list)>    Map of repositories
        @return  :dict<str, dict<str, (str, list=[])>>  Map to fill with repository name → category name → (category directory, empty list)
        '''
        categories = {}
        for repo in repositories.keys():
            rdir = repositories[repo][0]
            for category in os.listdir(rdir):
                cdir = '%s/%s' % (rdir, category)
                if os.path.isdir(cdir):
                    if repo not in categories:
                        categories[repo] = {}
                    categories[repo][category] = (cdir, [])
        return categories
        
    
    @staticmethod
    def match_categories(repositories, categories):
        '''
        Match patterns to categories
        
        @param  repositories:dict<str, (str, list)>                            Map of repositories
        @param  categories:dict<str, dict<str, (str, list<(str, str, str)>)>>  Map to fill with matching patterns
        '''
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
                        if regex_match(c, cat):
                            out[cat][1].append(pat)
    
    
    @staticmethod
    def flatten_categories(categories):
        '''
        Flatten the category map
        
        @param:in   categories:dict<str, dict<str, (str, list<(str, str, str)>)>>  The category map
        @param:out  categories:dict<str, (str, list<(str, str, str)>)>             Repository–category map
        '''
        repos = list(categories.keys())
        for repo in repos:
            r = categories[repo]
            for cat in r.keys():
                rc = '%s/%s' % (repo, cat)
                categories[rc] = r[cat]
            del categories[repo]
    
    
    @staticmethod
    def get_scrolls(categories):
        '''
        Get scrolls
        
        @param   categories:dict<str, (str, list<(str, str, str)>)>  The repository–category map
        @return  :dict<str, (str, str)>                              Repository–category → (scroll, scrollfile) map
        '''
        scrolls = {}
        for cat in categories.keys():
            cdir = categories[cat][0]
            for scroll in os.listdir(cdir):
                sfile = '%s/%s' % (cdir, scroll)
                if os.path.isfile(sfile) and scroll.endswith('.scroll') and not scroll.startswith('.'):
                    scroll = scroll[:-len('.scroll')]
                    dict_append(scrolls, cat, (scroll, '%s/%s' % (cat, scroll)))
        return scrolls
    
    
    @staticmethod
    def match_and_report(categories, scrolls, aggregator):
        '''
        Match scrolls to patterns and report them
        
        @param  categories:dict<str, (str, list<(str, str, str)>)>  Repository–category map
        @param  scrolls:dict<str, (str, str)>                       Repository–category → (scroll, scroll file) map
        @param  aggregator:(str)→void                               Function invoked with a scroll file when matched
        '''
        for cat in categories.keys():
            if cat in scrolls:
                for pat in categories[cat][1]:
                    p = pat[2]
                    for (scroll, full) in scrolls[cat]:
                        if regex_match(p, scroll):
                            aggregator(full)

