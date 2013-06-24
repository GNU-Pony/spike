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

