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
import sys

from spike import *



class Owlowiscious(Spike):
    '''
    Owlowiscious is the night time alternative to Spike, he is
    nocturnal in constrast to the, although eversleepy, diurnal Spike.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        Spike.__init__(self)



if __name__ == '__main__': # sic
    owlowiscious = Owlowiscious()
    owlowiscious.mane(sys.argv)

