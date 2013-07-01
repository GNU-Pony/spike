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


class ScrollMagick():
    '''
    Functions for playing with scrolls
    
    @author  Mattias Andrée (maandree@member.fsf.org)
    '''
    
    
    @staticmethod
    def export_environment():
        '''
        Export environment variables for the scrolls
        '''
        # Set $ARCH and $HOST
        for (var, value) in [('ARCH', os.uname()[4]), ('HOST', '$ARCH-unknown-linux-gnu')]:
            value = os.getenv(var, value.replace('$ARCH', os.getenv('ARCH', '')))
            os.putenv(var, value)
            if var not in os.environ or os.environ[var] != value:
                os.environ[var] = value
    
    
    @staticmethod
    def execute_scroll(scroll):
        '''
        Opens, compiles and executes a scroll
        
        @param  scroll:str  The scroll file
        '''
        code = None
        with open(scroll, 'rb') as file:
            code = file.read().decode('utf8', 'replace') + '\n'
            code = compile(code, scroll, 'exec')
        exec(code, globals())
    
    
    @staticmethod
    def init_fields():
        '''
        Initialise or reset scroll fields, they will be set to global variables
        '''
        vars = 'pkgname pkgver pkgdesc upstream arch freedom license private extension variant patch reason source sha3sums'
        for var in vars.split(' '):
            globals()[var] = None
        
        vars = 'conflicts replaces provides patchbefore patchafter groups depends makedepends checkdepends optdepends noextract options'
        for var in vars.split(' '):
            globals()[var] = []
        
        globals()['pkgrel'] = 1
        globals()['epoch'] = 0
        globals()['interactive'] = False
    
    
    @staticmethod
    def init_methods():
        '''
        Initialise or reset scroll methods, they will be set to global variables
        '''
        vars = 'ride build check package patch_build patch_check patch_package pre_install post_install pre_upgrade post_upgrade'
        for var in vars.split(' '):
            globals()[var] = None
    
    
    @staticmethod
    def check_type(field, withnone, *withclasses):
        '''
        Checks that the value of a field is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  withnone:bool       Whether the value may be `None`
        @param  withclasses:*type   The classes of the value
        '''
        for f in [field] if isinstance(field, str) else field:
            value = globals()[f]
            if not withnone:
                if value is None:
                    raise Exception('Field \'%s\' may not be `None`' % f)
            isclass = type(value)
            if isclass not in set(withclasses):
                allowed = ', '.join([c.__name__ for c in withclasses])
                if ', ' in allowed:
                    allowed = allowed[:allowed.rfind(', ')] + ' and ' + allowed[allowed.rfind(', ') + 2:]
                raise Exception('Field \'%s\' is restricted to %s' % (f, allowed))
    
    
    @staticmethod
    def check_is_list(field, withnone, *withclasses):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  withnone:bool       Whether the elements may be `None`
        @param  withclasses:*type   The classes of the elements
        '''
        withclasses = set(withclasses)
        for f in [field] if isinstance(field, str) else field:
            value = globals()[f]
            if value is None:
                raise Exception('Field \'%s\' must be a list' % f)
            if not isinstance(value, list):
                raise Exception('Field \'%s\' must be a list' % f)
            for elem in value:
                if not withnone:
                    if elem is None:
                        raise Exception('Field \'%s\' may not contain `None`' % f)
                isclass = type(elem)
                if isclass not in withclasses:
                    allowed = ', '.join([c.__name__ for c in withclasses])
                    if ', ' in allowed:
                        allowed = allowed[:allowed.rfind(', ')] + ' and ' + allowed[allowed.rfind(', ') + 2:]
                    raise Exception('Field \'%s\' is restricted to %s elements' % (f, allowed))
    
    
    @staticmethod
    def check_elements(field, values):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  values:itr<¿E?>     The allowed elements
        '''
        values = set(values)
        for f in [field] if isinstance(field, str) else field:
            value = globals()[f]
            for elem in value:
                if elem not in values:
                    raise Exception('Field \'%s\' may not contain the value \'%s\'' % (f, str(elem)))
    
    
    @staticmethod
    def check_format(field, checker):
        '''
        Checks that a non-`None` value satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  checker:(¿E?)→bool  Value checker
        '''
        for f in [field] if isinstance(field, str) else field:
            value = globals()[f]
            if value is not None:
                if not checker(value):
                    raise Exception('Field \'%s\' is of bady formated value \'%s\'' % (f, value))
    
    
    @staticmethod
    def check_element_format(field, checker):
        '''
        Checks that non-`None` elements in a list satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  checker:(¿E?)→bool  List element checker
        '''
        for f in [field] if isinstance(field, str) else field:
            value = globals()[f]
            for elem in value:
                if elem is not None:
                    if not checker(elem):
                        raise Exception('Field \'%s\' contains badly formated value \'%s\'' % (f, elem))
    
    
    @staticmethod
    def check_type_format(field, withnone, withclass, checker):
        '''
        Checks that the value of a field is of a specific class and that a non-`None` value satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  withnone:bool       Whether the value may be `None`
        @param  withclass:type      The class of the value
        @param  checker:(¿E?)→bool  Value checker
        '''
        for f in [field] if isinstance(field, str) else field:
            check_type(f, withnone, withclass)
            check_format(f, checker)
    
    
    @staticmethod
    def check_is_list_format(field, withnone, withclass, checker):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class and that non-`None` elements in a list satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  withnone:bool       Whether the elements may be `None`
        @param  withclass:type      The class of the elements
        @param  checker:(¿E?)→bool  List element checker
        '''
        for f in [field] if isinstance(field, str) else field:
            check_is_list(f, withnone, withclass)
            check_element_format(ff, checker)

