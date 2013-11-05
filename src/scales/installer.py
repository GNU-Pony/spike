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
from algorithmic.algospike import *
from algorithmic.scrlver import *
from auxiliary.scrollmagick import *
from auxiliary.auxfunctions import *



# Constants
store_fields = 'pkgname pkgver pkgrel epoch arch freedom private conflicts replaces'
store_fields += ' provides extension variant patch patchbefore patchafter groups'
store_fields += ' depends makedepends checkdepends optdepends'
store_fields = store_fields.split(' ')

scrl_fields = 'conflicts replaces provides extension patches patchbefore patchafter'
scrl_fields += ' depends makedepends checkdepends optdepends'
scrl_fields = set(scrl_fields.split(' '))



class Installer():
    '''
    Module for libspike for installing scrolls
    '''
    
    class Scroll():
        '''
        Scroll information
        
        @variable  file:str              The scroll file
        @variable  name:str              The scroll name
        @variable  version:str           The scroll version
        @variable  scroll:ScrollVersion  The scroll with version
        '''
        
        def __init__(self, scrollfile, globals):
            '''
            Constructor
            
            @param  scrollfile:str          The scroll file
            @param  globals:dict<str, any>  Should be `globals()`
            '''
            # Store fields
            self.fields = {}
            for field in store_fields:
                value = globals[field]
                if (field in scrl_fields) and (value is not None):
                    if value == '':
                        value = None
                    elif isinstance(value, str):
                        value = ScrollVersion(value)
                    else:
                        value = [ScrollVersion(val) for val in value]
                self.fields[field] = value
            
            # Set simple attributes
            self.file = scrollfile
            self.name = self.fields['pkgname']
            self.version = (self.fields['epoch'], self.fields['pkgver'], self.fields['pkgrel'])
            self.version = '%i:%s-%i' % self.version
            self.scroll = ScrollVersion('%s=%s' % (self.name, self.version))
        
        
        
        def __getitem__(self, field):
            '''
            Gets a field in the scroll
            
            @param   field:str  The name of the field
            @return  :¿E?       The scrolls information in the feild
            '''
            return self.fields[field]
    
    
    
    @staticmethod
    def load_information(scrollfile):
        '''
        Load information about a scroll
        
        @param   scrollfile:str  The scroll file
        @return  :Scroll         The scroll information
        '''
        ScrollMagick.export_environment()
        
        globs = globals()
        ScrollMagick.init_fields(globs)
        ScrollMagick.execute_scroll(scrollfile, globs)
        
        return Installer.Scroll(scrollfile, globs)
    
    
    @staticmethod
    def transpose_fields(scroll, map):
        '''
        Fill a map with field → value → scroll data
        
        @param  scroll:Scroll                           Scroll information
        @param  map:dict<str, dict<¿E?, list<Scroll>>>  Map to fill with field → value → scroll mapping
        '''
        for field in store_fields:
            value = scroll[field]
            if field not in map:
                map[field] = {}
            fmap = map[field]
            if value is not None:
                for val in value if isinstance(value, list) else [value]:
                    if val is not None:
                        dict_append(map, val, scroll)
    
    
    @staticmethod
    def check_conflicts(scroll_infos, installed, provided):
        '''
        Check for conflicts
        
        @param   scroll_infos:itr<dict<ScrollVersion, Scroll>>  Scrolls to check
        @param   installed:set<ScrollVersion>                   Set to fill with installed packages
        @param   provided:set<ScrollVersion>                    Set to fill with provided packages
        @return  :bool                                          Whether there are not conflicts
        '''
        checked = set()
        conflicts = set()
        for scroll_info in scroll_infos:
            for scroll in scroll_info:
                scroll = scroll_info[scroll]
                vscroll = scroll.scroll
                if vscroll.name in checked:
                    continue
                checked.add(vscroll.name)
                if vscroll in installed:
                    continue
                if vscroll in conflicts:
                    return False
                vscroll.union_add(installed)
                for provides in scroll['provides']:
                    provides.union_add(provided)
                for conflict in scroll['conflicts']:
                    if (conflict in installed) or (conflict in provided):
                        return False
                    conflict.union_add(conflicts)
        return True
    
    
    @staticmethod
    def find_dependencies(scroll_info, needed, requirer, installed, provided, empty_dep_evaluator):
        '''
        Identify missing dependencies
        
        @param   scroll_info:dict<ScrollVersion, Scroll>  The scrolls
        @param   needed:set<ScrollVersion>                Missing dependencies, will be filled
        @param   requirer:dict<str, list<ScrollVersion>>  Mapping from scroll name to scrolls that requires the scroll, will be filled
        @param   empty_dep_evaluator:(Scroll)→bool        Function that evaluates if the empty dependency exists (a package manager with the same name)
        @return  :int                                     Value for indentified error, zero if none
        '''
        for scroll in scroll_info:
            scroll = scroll_info[scroll]
            makedepends = scroll['makedepends']
            depends     = scroll['depends']
            for deps in makedepends + depends:
                if deps is None:
                    if not empty_dep_evaluator(scroll):
                        return 9
                else:
                    if (deps not in installed) and (deps not in provided):
                        if (ScrollVersion(deps.name) in needed) and (deps not in needed):
                            return 8
                        deps.intersection_add(needed)
                        dict_append(requirer, deps.name, scroll.scroll)
        return 0
    
    
    @staticmethod
    def replacements(scroll_info, installed_info, field_installed, uninstall, aggregator):
        '''
        Identify and handle replacement scrolls
        
        @param  scroll_info:dict<ScrollVersion, Scroll>              The scrolls that are being installed
        @param  installed_info:dict<ScrollVersion, Scroll>           The scrolls that are installed
        @param  field_installed:dict<str, dist<¿E?, list<Scroll>>>   Field → value → installed scroll mapping
        @param  uninstall:append(str)→void                           List to fill with scroll what are being uninstalled
        @param  aggregator:(replacee:str, int=5, replacer:str)→void  Function being called when a scroll is being flagged to be replaced
        '''
        install_remove = []
        for scroll in scroll_info:
            scroll = scroll_info[scroll]
            for replaces in scroll['replaces']:
                if replaces in installed_info:
                    uninstall.append(replaces)
                    del installed_info[replaces]
                    for field in field_installed:
                        for value in field_installed[field]:
                            if replaces in field_installed[field][value]:
                                field_installed[field][value].remove(replaces)
                    aggregator(replaces.name, 5, scroll.name)
                if replaces in installing:
                    install_remove.append[replaces]
        for replaces in install_remove:
            del scroll_info[replaces]
    
    
    @staticmethod
    def update_types(scroll_info, installed_versions, fresh_installs, reinstalls, update, downgrading, skipping):
        '''
        Identify what type of installation is being done with each scroll
        
        @param  scroll_info:dict<ScrollVersion, Scroll>      The scrolls that are being installed
        @param  installed_versions:dict<Str, ScrollVersion>  Map from scroll name to scroll version of installed scrolls
        @param  fresh_installs:append(str)→void              List to fill with scroll what are being freshly installed
        @param  reinstalls:append(str)→void                  List to fill with scroll what are being reinstalled
        @param  update:append(str)→void                      List to fill with scroll what are being updated
        @param  downgrading:append(str)→void                 List to fill with scroll what are being downgraded
        @param  skipping:append(str)→void                    List to fill with scroll what are being skipped
        '''
        for scroll in scroll_info:
            scroll = scroll_info[scroll]
            scroll_version = '%s=%s' % (scroll.name, scroll.version)
            if scroll.named not in installed_versions:
                fresh_installs.append(scroll_version)
            else:
                if scroll.scroll.lower == installed_versions[scroll.name].lower:
                    reinstalls.append(scroll_version)
                elif scroll.scroll.lower < installed_versions[scroll.name].lower:
                    downgrading.append(scroll_version)
                else:
                    update.append(scroll_version)
    
    
    @staticmethod
    def tsort_scrolls(scroll_info):
        '''
        Topologically sort scrolls
        
        @param   scroll_info:dict<ScrollVersion, Scroll>  The scrolls that are being installed
        @return  :list<(Scroll, list<ScrollVersion>?)>?   List of scrolls in topological order, `None` if not possible.
                                                          Accompanied with each scroll is either `None` or a list of scrolls that is require buts must be installed later (cyclic dependency).
        '''
        tsorted, tsortdata = [], {}
        for scroll in scroll_info:
            scroll = scroll_info[scroll]
            deps, makedeps = set(), set()
            # TODO providers
            for dep in scroll['depends']:
                deps.add(dep)
            for dep in scroll['makedepends']:
                deps.add(dep)
                makedeps.add(dep)
            tsortdata[scroll.scroll] = (deps, makedeps)
        successful = tsort(tsorted, [], tsortdata)
        if not successful:
            return None
        return [(scroll_info[elem[0]], elem[1]) for elem in tsorted]

