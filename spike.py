#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
spike – a package manager running on top of git

Copyright © 2012  Mattias Andrée (maandree@kth.se)

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
import os


class Spike():
    '''
    Spike is your number one package manager
    '''
    def __init__(self):
        '''
        Constructor
        '''
        pass

    
    def mane(self, args):
        '''
        Run this method to invoke Spike as if executed from the shell
        
        @param  args:list<str>  Command line arguments, including invoked program alias ($0)
        '''
        usage = 'spike [command [option]... [FILE... SCROLL | SCROLL...]]'
        usage = usage.replace('spike',   '\033[35m' 'spike'   '\033[39m')
        usage = usage.replace('command', '\033[33m' 'command' '\033[39m')
        usage = usage.replace('option',  '\033[33m' 'option'  '\033[39m')
        usage = usage.replace('FILE',    '\033[04m' 'FILE'    '\033[24m')
        usage = usage.replace('SCROLL',  '\033[04m' 'SCROLL'  '\033[24m')
        if linuxvt:
            usage = usage.replace('\033[04m', '\033[34m')
            usage = usage.replace('\033[24m', '\033[39m')
        
        usage = usage.replace('\033[', '\0')
        for sym in ('[', ']', '(', ')', '|', '...', '*'):
            usage = usage.replace(sym, '\033[02m' + sym + '\033[22m')
        usage = usage.replace('\0', '\033[')
        
        opts = ArgParser('spike', 'a package manager running on top of git', usage,
                         'spike is used to spike your system with new ponies or and new versions\n'
                         'of ponies (known on other systems as packages). spike the capaility of\n'
                         'not only installing ponies, but also archive an installation and\n'
                         'simply roll back to it in case the system broke, an must have feature\n'
                         'on unstable OS:es. spike uses so called scrolls to install ponies,\n'
                         'these are written, for maximum simplicity and portability, in Python 3\n'
                         'and a collection of these are distributed with spike and updated when\n'
                         'spike is updated. But you can add scroll repositories to spike on your\n'
                         'local installation.')
        
        opts.add_argumentless(['-v', '--version'],                    help = 'Print program name and version')
        opts.add_argumentless(['-h', '--help'],                       help = 'Print this help')
        opts.add_argumentless(['-c', '--copyright'],                  help = 'Print copyright information')
        
        opts.add_argumentless(['-B', '--bootstrap'],                  help = 'Update spike and scroll repositories')
        opts.add_argumentless(['-P', '--proofread'],                  help = 'Verify that a scroll is correct')
        opts.add_argumentless(['-F', '--find'],                       help = 'Find a scroll either by name or by ownership\n'
                                                             'slaves: [--owner | --written=]')
        opts.add_argumentless(['-W', '--write'],                      help = 'Install a pony (package) from scroll\n'
                                                             'slaves: [--pinpal=] [--private] [--asdep | --asexplicit] [--nodep] [--force]')
        opts.add_argumentless(['-U', '--upgrade'],                    help = 'Upgrade to new versions of the installed ponies\n'
                                                             'slaves: [--pinpal=] [--ignore=]...')
        opts.add_argumentless(['-E', '--erase'],                      help = 'Uninstall a pony\n'
                                                             'slaves: [--pinpal=] [--private]')
        opts.add_argumented(  ['-X', '--ride'],      arg = 'SCROLL',  help = 'Execute a scroll after best effort\n'
                                                             'slaves: [--private]')
        opts.add_argumentless(['-R', '--read'],                       help = 'Get scroll information\n'
                                                             'slaves: [--list | --info=]')
        opts.add_argumentless(['-C', '--claim'],                      help = 'Claim one or more files as owned by a pony\n'
                                                             'slaves: [--recursive | --entire] [--private] [--force]')
        opts.add_argumentless(['-D', '--disclaim'],                   help = 'Disclaim one or more files as owned by a pony\n'
                                                             'slaves: [--recursive] [--private]')
        opts.add_argumented(  ['-A', '--archive'],   arg = 'ARCHIVE', help = 'Create an archive of everything that is currently installed.\n'
                                                             'slaves: [--scrolls]')
        opts.add_argumented(  ['--restore-archive'], arg = 'ARCHIVE', help = 'Rollback to an archived state of the system\n'
                                                             'slaves: [--shared | --full | --old] [--downgrade | --upgrade]')
        opts.add_argumentless(['-N', '--clean'],                      help = 'Uninstall unneeded ponies')
        opts.add_argumentless(['-I', '--interactive'],                help = 'Start in interative graphical terminal mode\n'
                                                                             '(supports installation and uninstallation only)')
        
        opts.add_argumentless(['-o', '--owner'],                      help = 'Find owner pony for file')
        opts.add_argumented(  ['-w', '--written'],   arg = 'boolean', help = 'Search only for installed ("yes") or not installed ("no") ponies')
        opts.add_argumented(  [      '--pinpal'],    arg = 'ROOT',    help = 'Mounted system for which to do installation or unstallation')
        opts.add_argumentless(['-u', '--private'],                    help = 'Private pony installation')
        opts.add_argumentless([      '--asdep'],                      help = 'Install pony as implicitly installed (a dependency)')
        opts.add_argumentless([      '--asexplicit'],                 help = 'Install pony as explicitly installed (no longer a dependency)')
        opts.add_argumentless([      '--nodep'],                      help = 'Do not install dependencies')
        opts.add_argumentless([      '--force'],                      help = 'Ignore file claims')
        opts.add_argumentless(['-i', '--ignore'],                     help = 'Ignore update of a pony')
        opts.add_argumentless(['-l', '--list'],                       help = 'List files claimed (done at installation) for a pony')
        opts.add_argumented(  ['-f', '--info'],      arg = 'FIELD',   help = 'Retrieve a specific scroll information field')
        opts.add_argumentless([      '--recursive'],                  help = 'Recursively claim or disclaim directories')
        opts.add_argumentless([      '--entire'],                     help = 'Recursively claim directories and their future content')
        opts.add_argumentless([      '--scrolls'],                    help = 'Do only archive scrolls, no installed files')
        opts.add_argumentless([      '--shared'],                     help = 'Reinstall only ponies that are currently installed and archived')
        opts.add_argumentless([      '--full'],                       help = 'Uninstall ponies that are not archived')
        opts.add_argumentless([      '--old'],                        help = 'Reinstall only ponies that are currently not installed')
        opts.add_argumentless([      '--downgrade'],                  help = 'Do only perform pony downgrades')
        opts.add_argumentless([      '--upgrade'],                    help = 'Do only perform pony upgrades')
        
        opts.help()




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
    def __init__(self, program, description, usage, longdescription = None):
        '''
        Constructor.
        The short description is printed on same line as the program name
        
        @param  program:str           The name of the program
        @param  description:str       Short, single-line, description of the program
        @param  usage:str             Formated, multi-line, usage text
        @param  longdescription:str?  Long, multi-line, description of the program, may be `None`
        '''
        self.__program = program
        self.__description = description
        self.__usage = usage
        self.__longdescription = longdescription
        self.__arguments = []
        self.opts = {}
        self.optmap = {}
    
    
    def add_argumentless(self, alternatives, help = None):
        '''
        Add option that takes no arguments
        
        @param  alternatives:list<str>  Option names
        @param  help:str?                Short description, use `None` to hide the option
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
        @param  help:str?                Short description, use `None` to hide the option
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
        @param  help:str?                Short description, use `None` to hide the option
        '''
        self.__arguments.append((VARIADIC, alternatives, arg, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, VARIADIC)
    
    
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
        print('\033[1m%s\033[21m %s %s' % (self.__program, '-' if linuxvt else '—', self.__description))
        print()
        if self.__longdescription is not None:
            print(self.__longdescription)
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
                    print('%s' % (line), end='\033[21;39m\n')
                else:
                    print('%s\033[%sm%s\033[39m' % (' ' * col, colour, line))
            index += 1
        
        print()



linuxvt = ('TERM' in os.environ) and (os.environ['TERM'] == 'linux')
if __name__ == '__main__': # sic
    spike = Spike()
    spike.mane(sys.argv)

