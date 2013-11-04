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
import sys

from auxiliary.printhacks import *



ARGUMENTLESS = 0
'''
Option takes no arguments
'''

ARGUMENTED = 1
'''
Option takes one argument per instance
'''

VARIADIC = 2
'''
Option consumes all following arguments
'''



class ArgParser():
    '''
    Simple argument parser, cannibalised from ponysay where it was cannibalised from paradis
    '''
    
    def __init__(self, program, description, usage, long_description = None, tty = True):
        '''
        Constructor.
        The short description is printed on same line as the program name
        
        @param  program:str            The name of the program
        @param  description:str        Short, single-line, description of the program
        @param  usage:str              Formated, multi-line, usage text
        @param  long_description:str?  Long, multi-line, description of the program, may be `None`
        @param  tty:bool               Whether the terminal is an not so capable virtual terminal
        '''
        self.__program = program
        self.__description = description
        self.__usage = usage
        self.__long_description = long_description
        self.__arguments = []
        self.opts = {}
        self.optmap = {}
        self.__tty = tty
    
    
    
    def add_argumentless(self, alternatives, help = None):
        '''
        Add option that takes no arguments
        
        @param  alternatives:list<str>  Option names
        @param  help:str?               Short description, use `None` to hide the option
        '''
        self.__arguments.append((ARGUMENTLESS, alternatives, None, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, ARGUMENTLESS)
    
    
    def add_argumented(self, alternatives, arg, help = None):
        '''
        Add option that takes one argument
        
        @param  alternatives:list<str>  Option names
        @param  arg:str                 The name of the takes argument, one word
        @param  help:str?               Short description, use `None` to hide the option
        '''
        self.__arguments.append((ARGUMENTED, alternatives, arg, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, ARGUMENTED)
    
    
    def add_variadic(self, alternatives, arg, help = None):
        '''
        Add option that takes all following argument
        
        @param  alternatives:list<str>  Option names
        @param  arg:str                 The name of the takes arguments, one word
        @param  help:str?               Short description, use `None` to hide the option
        '''
        self.__arguments.append((VARIADIC, alternatives, arg, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, VARIADIC)
    
    
    
    def test_exclusiveness(self, execprog, exclusives, longmap, do_exit = False):
        '''
        Test for option conflicts
        
        @param   execprog:str            The program command
        @param   exclusives:set<str>     Exclusive options
        @param   longmap:dict<str, str>  Map from short to long
        @param   do_exit:bool            Exit program on conflict
        @return  :bool                   Whether at most one exclusive option was used
        '''
        used = []
        
        for opt in self.opts:
            if (self.opts[opt] is not None) and (opt in exclusives):
                used.append((opt, longmap[opt] if opt in longmap else None))
        
        if len(used) > 1:
            msg = execprog + ': conflicting options:'
            for opt in used:
                if opt[1] is None:
                    msg += ' ' + opt[0]
                else:
                    msg += ' ' + opt[0] + '(' + opt[1] + ')'
            printerr(msg)
            if do_exit:
                exit(1)
            return False
        return True
    
    
    def test_allowed(self, execprog, allowed, longmap, do_exit = False):
        '''
        Test for out of context option usage
        
        @param   execprog:str            The program command
        @param   allowed:set<str>        Allowed options
        @param   longmap:dict<str, str>  Map from short to long
        @param   do_exit:bool            Exit program on incorrect usage
        @return  :bool                   Whether only allowed options was used
        '''
        for opt in self.opts:
            if (self.opts[opt] is not None) and (opt not in allowed):
                msg = execprog + ': option used out of context: ' + opt
                if opt in longmap:
                    msg += '(' + longmap[opt] + ')'
                printerr(msg)
                if do_exit:
                    exit(1)
                return False
        return True
    
    
    def test_files(self, execprog, min_count, max_count, do_exit = False):
        '''
        Test the correctness of the number of used non-option arguments
        
        @param   execprog:str    The program command
        @param   min_count:int   The minimum allowed number of files
        @param   max_count:int?  The maximum allowed number of files, `None` for unlimited
        @param   do_exit:bool    Exit program on incorrectness
        @return  :bool           Whether the usage was correct
        '''
        n = len(self.files)
        rc = min_count <= n
        msg = execprog + ': too few unnamed arguments: %i but %i needed' % (n, min_count)
        if rc and (max_count is not None):
            rc = n <= max_count
            if not rc:
                msg = execprog + ': too many unnamed arguments: %i but only %i allowed' % (n, max_count)
        if do_exit and not rc:
            exit(1)
        return rc
    
    
    
    def parse(self, argv = sys.argv):
        '''
        Parse arguments
        
        @param   args:list<str>  The command line arguments, should include the execute file at index 0, `sys.argv` is default
        @return  :bool           Whether no unrecognised option is used
        '''
        self.argcount = len(argv) - 1
        self.files = []
        
        argqueue = []
        optqueue = []
        deque = []
        for arg in argv[1:]:
            deque.append(arg)
        
        dashed = False
        tmpdashed = False
        get = 0
        dontget = 0
        self.rc = True
        
        def unrecognised(arg):
            '''
            Warn about unrecognised option
            
            @param  arg:str  The option
            '''
            sys.stderr.write('%s: warning: unrecognised option %s\n' % (self.__program, arg))
            self.rc = False
        
        while len(deque) != 0:
            arg = deque[0]
            deque = deque[1:]
            if (get > 0) and (dontget == 0):
                get -= 1
                argqueue.append(arg)
            elif tmpdashed:
                self.files.append(arg)
                tmpdashed = False
            elif dashed:        self.files.append(arg)
            elif arg == '++':   tmpdashed = True
            elif arg == '--':   dashed = True
            elif (len(arg) > 1) and (arg[0] in ('-', '+')):
                if (len(arg) > 2) and (arg[:2] in ('--', '++')):
                    if dontget > 0:
                        dontget -= 1
                    elif (arg in self.optmap) and (self.optmap[arg][1] == ARGUMENTLESS):
                        optqueue.append(arg)
                        argqueue.append(None)
                    elif '=' in arg:
                        arg_opt = arg[:arg.index('=')]
                        if (arg_opt in self.optmap) and (self.optmap[arg_opt][1] >= ARGUMENTED):
                            optqueue.append(arg_opt)
                            argqueue.append(arg[arg.index('=') + 1:])
                            if self.optmap[arg_opt][1] == VARIADIC:
                                dashed = True
                        else:
                            unrecognised(arg)
                    elif (arg in self.optmap) and (self.optmap[arg][1] == ARGUMENTED):
                        optqueue.append(arg)
                        get += 1
                    elif (arg in self.optmap) and (self.optmap[arg][1] == VARIADIC):
                        optqueue.append(arg)
                        argqueue.append(None)
                        dashed = True
                    else:
                        unrecognised(arg)
                else:
                    sign = arg[0]
                    i = 1
                    n = len(arg)
                    while i < n:
                        narg = sign + arg[i]
                        i += 1
                        if (narg in self.optmap):
                            if self.optmap[narg][1] == ARGUMENTLESS:
                                optqueue.append(narg)
                                argqueue.append(None)
                            elif self.optmap[narg][1] == ARGUMENTED:
                                optqueue.append(narg)
                                nargarg = arg[i:]
                                if len(nargarg) == 0:
                                    get += 1
                                else:
                                    argqueue.append(nargarg)
                                break
                            elif self.optmap[narg][1] == VARIADIC:
                                optqueue.append(narg)
                                nargarg = arg[i:]
                                argqueue.append(nargarg if len(nargarg) > 0 else None)
                                dashed = True
                                break
                        else:
                            unrecognised(arg)
            else:
                self.files.append(arg)
        
        i = 0
        n = len(optqueue)
        while i < n:
            opt = optqueue[i]
            arg = argqueue[i]
            i += 1
            opt = self.optmap[opt][0]
            if (opt not in self.opts) or (self.opts[opt] is None):
                self.opts[opt] = []
            self.opts[opt].append(arg)
        
        for arg in self.__arguments:
            if (arg[0] == VARIADIC):
                varopt = self.opts[arg[1][0]]
                if varopt is not None:
                    additional = ','.join(self.files).split(',') if len(self.files) > 0 else []
                    if varopt[0] is None:
                        self.opts[arg[1][0]] = additional
                    else:
                        self.opts[arg[1][0]] = varopt[0].split(',') + additional
                    self.files = []
                    break
        
        self.message = ' '.join(self.files) if len(self.files) > 0 else None
        
        return self.rc
    
    
    
    def help(self):
        '''
        Prints a colourful help message
        '''
        print('\033[1m%s\033[21m %s %s' % (self.__program, '-' if self.__tty else '—', self.__description))
        print()
        if self.__long_description is not None:
            print(self.__long_description)
        print()
        
        print('\033[1mUSAGE:\033[21m', end='')
        first = True
        for line in self.__usage.split('\n'):
            if first:
                first = False
            else:
                print('    or', end='')
            print('\t%s' % (line))
        print()
        
        print('\033[1mSYNOPSIS:\033[21m')
        (lines, lens) = ([], [])
        for opt in self.__arguments:
            opt_type = opt[0]
            opt_alts = opt[1]
            opt_arg = opt[2]
            opt_help = opt[3]
            if opt_help is None:
                continue
            (line, l) = ('', 0)
            first = opt_alts[0]
            last = opt_alts[-1]
            alts = ('  ', last) if first is last else (first, last)
            for opt_alt in alts:
                if opt_alt is alts[-1]:
                    line += '%colour%' + opt_alt
                    l += len(opt_alt)
                    if   opt_type == ARGUMENTED:  line += ' \033[4m%s\033[24m'      % (opt_arg);  l += len(opt_arg) + 1
                    elif opt_type == VARIADIC:    line += ' [\033[4m%s\033[24m...]' % (opt_arg);  l += len(opt_arg) + 6
                else:
                    line += '    \033[2m%s\033[22m  ' % (opt_alt)
                    l += len(opt_alt) + 6
            lines.append(line)
            lens.append(l)
        
        col = max(lens)
        col += 8 - ((col - 4) & 7)
        index = 0
        for opt in self.__arguments:
            opt_help = opt[3]
            if opt_help is None:
                continue
            first = True
            colour = '36' if (index & 1) == 0 else '34'
            print(lines[index].replace('%colour%', '\033[%s;1m' % (colour)), end=' ' * (col - lens[index]))
            for line in opt_help.split('\n'):
                if first:
                    first = False
                    print('%s' % (line), end='\033[00m\n') # 21;39m
                else:
                    print('%s\033[%sm%s\033[00m' % (' ' * col, colour, line)) # 39m
            index += 1
        
        print()

