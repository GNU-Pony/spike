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

'''
Auxililary functions (auxfunctions)

This module contains small functions used in libspike to
produce cleaner code
'''


def dict_append(dictionary, key, value):
    '''
    Appends a value to a list of value for a key in a dictionary and creates the list is necessary
    
    @param  dictionary:dict<¿K?, ¿V?>  The dictionary
    @param  key:¿K?                    The key
    @param  value:¿V?                  The value
    '''
    if key not in dictionary:
        dictionary[key] = [value]
    else:
        dictionary[key].append(value)


def list_split(values, list_lambda, ignore_lambda = None):
    '''
    Splits up a list into multiple lists
    
    @param  values:itr<¿E?>                     Values to split up
    @param  list_lambda:(value:¿E?)→list<¿E?>   Function that gets the list to which to add the value
    @param  ignore_lambda:(value:¿E?)?→boolean  Function that gets whether not to add the value to a list
    '''
    if ignore_lambda is None:
        for value in values:
            list = list_lambda(value)
            if list is not None:
                list.append(value)
    else:
        for value in values:
            if ignore_lambda(value):
                continue
            list = list_lambda(value)
            if list is not None:
                list.append(value)
