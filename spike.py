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
import os



SPIKE_VERSION = '0.1'
'''
This version of spike
'''

SPIKE_PATH = '${SPIKE_PATH}'
'''
Spike's location
'''



def print(text = '', end = '\n'):
    '''
    Hack to enforce UTF-8 in output (in the future, if you see anypony not using utf-8 in
    programs by default, report them to Princess Celestia so she can banish them to the moon)
    
    @param  text:str  The text to print (empty string is default)
    @param  end:str   The appendix to the text to print (line breaking is default)
    '''
    sys.stdout.buffer.write((str(text) + end).encode('utf-8'))
    sys.stdout.buffer.flush()


def printerr(text = '', end = '\n'):
    '''
    stderr equivalent to print()
    
    @param  text:str  The text to print (empty string is default)
    @param  end:str   The appendix to the text to print (line breaking is default)
    '''
    sys.stderr.buffer.write((str(text) + end).encode('utf-8'))
    sys.stderr.buffer.flush()



class Spike():
    '''
    Spike is your number one package manager
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.version = SPIKE_VERSION
        self.execprog = 'spike'

    
    def mane(self, args):
        '''
        Run this method to invoke Spike as if executed from the shell
        
        Exit values:  0 - Successful
                      1 - Option use error
                      2 - Non-option argument use error
                      3 - -h(--help) was used
                      4 - Invalid option argument
                      5 - Root does not exist
                      6 - Scroll does not exist
                      7 - Pony is not installed
                      8 - Pony conflict
                      9 - Dependency does not exist
                     10 - File is already claimed
                     11 - File was claimed for another pony
                     12 - File does not exist
                     13 - File already exists
                     14 - Information field is not definied
                     15 - Starting interactive mode from pipe
                     16 - Compile error
                     17 - Installation error, usually because --private or root is needed
                     18 - Private installation is not supported
                     19 - Non-private installation is not supported
                     20 - Scroll error
                     21 - Pony ride error
                     22 - Proofread found scroll error
                     23 - File access denied
                    255 - Unknown error
        
        @param  args:list<str>  Command line arguments, including invoked program alias ($0)
        '''
        self.execprog = args[0].split('/')[-1]
        
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
        opts.add_argumentless(['-F', '--find'],                       help = 'Find a scroll either by name or by ownership\n'
                                                             'slaves: [--owner | --written=]')
        opts.add_argumentless(['-W', '--write'],                      help = 'Install a pony (package) from scroll\n'
                                                             'slaves: [--pinpal= | --private] [--asdep | --asexplicit] [--nodep] [--force] [--shred]')
        opts.add_argumentless(['-U', '--update'],                     help = 'Update to new versions of the installed ponies\n'
                                                             'slaves: [--pinpal=] [--ignore=]... [--shred]')
        opts.add_argumentless(['-E', '--erase'],                      help = 'Uninstall a pony\n'
                                                             'slaves: [--pinpal= | --private] [--shred]')
        opts.add_argumented(  ['-X', '--ride'],      arg = 'SCROLL',  help = 'Execute a scroll after best effort\n'
                                                             'slaves: [--private]')
        opts.add_argumentless(['-R', '--read'],                       help = 'Get scroll information\n'
                                                             'slaves: [--list | --info=...]')
        opts.add_argumentless(['-C', '--claim'],                      help = 'Claim one or more files as owned by a pony\n'
                                                             'slaves: [--recursive | --entire] [--private] [--force]')
        opts.add_argumentless(['-D', '--disclaim'],                   help = 'Disclaim one or more files as owned by a pony\n'
                                                             'slaves: [--recursive] [--private]')
        opts.add_argumented(  ['-A', '--archive'],   arg = 'ARCHIVE', help = 'Create an archive of everything that is currently installed.\n'
                                                             'slaves: [--scrolls]')
        opts.add_argumented(  ['--restore-archive'], arg = 'ARCHIVE', help = 'Rollback to an archived state of the system\n'
                                                             'slaves: [--shared | --full | --old] [--downgrade | --upgrade] [--shred]')
        opts.add_argumentless(['-N', '--clean'],                      help = 'Uninstall unneeded ponies\n'
                                                             'slaves: [--shred]')
        opts.add_argumentless(['-P', '--proofread'],                  help = 'Verify that a scroll is correct')
        opts.add_argumentless(['-I', '--interactive'],                help = 'Start in interative graphical terminal mode\n'
                                                                             '(supports installation and uninstallation only)\n'
                                                                             'slaves: [--shred]')
        
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
        opts.add_argumentless(['-s', '--scrolls'],                    help = 'Do only archive scrolls, no installed files')
        opts.add_argumentless([      '--shared'],                     help = 'Reinstall only ponies that are currently installed and archived')
        opts.add_argumentless([      '--full'],                       help = 'Uninstall ponies that are not archived')
        opts.add_argumentless([      '--old'],                        help = 'Reinstall only ponies that are currently not installed')
        opts.add_argumentless([      '--downgrade'],                  help = 'Do only perform pony downgrades')
        opts.add_argumentless([      '--upgrade'],                    help = 'Do only perform pony upgrades')
        opts.add_argumentless([      '--shred'],                      help = 'Preform secure removal with `shred` when removing old files')
        
        if not opts.parse(args):
            printerr(self.execprog + ': use of unrecognised option')
            exit(1)
        
        longmap = {}
        longmap['-v'] = '--version'
        longmap['-h'] = '--help'
        longmap['-c'] = '--copyright'
        longmap['-B'] = '--bootstrap'
        longmap['-F'] = '--find'
        longmap['-W'] = '--write'
        longmap['-U'] = '--update'
        longmap['-E'] = '--erase'
        longmap['-X'] = '--ride'
        longmap['-R'] = '--read'
        longmap['-C'] = '--claim'
        longmap['-D'] = '--disclaim'
        longmap['-A'] = '--archive'
        longmap['-N'] = '--clean'
        longmap['-P'] = '--proofread'
        longmap['-I'] = '--interactive'
        longmap['-o'] = '--owner'
        longmap['-w'] = '--written'
        longmap['-u'] = '--private'
        longmap['-i'] = '--ignore'
        longmap['-l'] = '--list'
        longmap['-f'] = '--info'
        longmap['-s'] = '--scrolls'
        
        exclusives = set()
        for opt in 'vhcBFWUEXRCDANPI':
            exclusives.add('-' + opt)
        exclusives.add('--restore-archive')
        self.test_exclusiveness(opts.opts, exclusives, longmap, True)
        exclusives = set()
        
        for opt in opts.opts:
            if (opt != '-i') and (opt != '-f'): # --ignore, --info
                if (opts.opts[opt] is not None) and (len(opts.opts[opt]) > 1):
                    option = opt
                    if option in longmap:
                        option += '(' + longmap[option] + ')'
                    printerr('%s: %s is used multiple times' % (self.execprog, option))
                    exit(1)
        
        allowed = set()
        for opt in exclusives:
            if opts.opts[opt] is not None:
                allowed.add(opt)
                break
        
        
        exitValue = 0
        
        try:
            if opts.opts['-v'] is not None:
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                self.print_version()
            
            elif opts.opts['-h'] is not None:
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                opts.help()
                exitValue = 3
            
            elif opts.opts['-c'] is not None:
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                self.print_copyright()
            
            elif opts.opts['-B'] is not None:
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.bootstrap()
            
            elif opts.opts['-F'] is not None:
                exclusives.add('-o')
                exclusives.add('-w')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                self.test_allowed(opts.opts, allowed, longmap, True)
                allowed.add('-o')
                allowed.add('-w')
                if opts.opts['-w'] is not None:
                    if opts.opts['-w'][0] not in ('yes', 'no'):
                        printerr(self.execprog + ': only \'yes\' and \'no\' are allowed for -w(--written)')
                        exit(4)
                    exitValue = self.find_scroll(opts.files,
                                                 installed    = opts.opts['-w'][0] == 'yes',
                                                 notinstalled = opts.opts['-w'][0] == 'no')
                elif opts.opts['-o'] is not None:
                    self.test_files(opts.files, 2, True)
                    exitValue = self.find_owner(opts.files)
                else:
                    exitValue = self.find_scroll(opts.files, installed = True, notinstalled = True)
                
            elif opts.opts['-W'] is not None:
                exclusives.add('--pinpal')
                exclusives.add('-u')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                exclusives = set()
                exclusives.add('--asdep')
                exclusives.add('--asexplicit')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                allowed.add('--pinpal')
                allowed.add('-u')
                allowed.add('--asdep')
                allowed.add('--asexplicit')
                allowed.add('--nodep')
                allowed.add('--force')
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 2, True)
                exitValue = self.write(opt.files,
                                       root         = opts.opts['--pinpal'][0] if opts.opts['--pinpal'] is not None else '/',
                                       private      = opts.opts['-u'] is not None,
                                       explicitness = 1  if opts.opts['--asexplict'] is not None else
                                                      -1 if opts.opts['--asdep']     is not None else 0,
                                       nodep        = opts.opts['--nodep'] is not None,
                                       force        = opts.opts['--force'] is not None,
                                       shred        = opts.opts['--shred'] is not None)
                
            elif opts.opts['-U'] is not None:
                allowed.add('--pinpal')
                allowed.add('-i')
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.update(root    = opts.opts['--pinpal'][0] if opts.opts['--pinpal'] is not None else '/',
                                        ignores = opts.opts['-i'] if opts.opts['-i'] is not None else [],
                                        shred   = opts.opts['--shred'] is not None)
                
            elif opts.opts['-E'] is not None:
                exclusives.add('--pinpal')
                exclusives.add('-u')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                allowed.add('--pinpal')
                allowed.add('-u')
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 2, True)
                exitValue = self.erase(opt.files,
                                       root    = opts.opts['--pinpal'][0] if opts.opts['--pinpal'] is not None else '/',
                                       private = opts.opts['-u'] is not None,
                                       shred   = opts.opts['--shred'] is not None)
                
            elif opts.opts['-X'] is not None:
                allowed.add('-u')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 1, True)
                exitValue = self.ride(opt.files[0],
                                      private = opts.opts['-u'] is not None)
                
            elif opts.opts['-R'] is not None:
                exclusives.add('-l')
                exclusives.add('-f')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                allowed.add('-l')
                allowed.add('-f')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 1, True)
                if opts.opts['-l'] is not None:
                    exitValue = self.read_files(opt.files)
                else:
                    exitValue = self.read_info(opt.files, field = opts.opts['-f'])
                    
            elif opts.opts['-C'] is not None:
                exclusives.add('--recursive')
                exclusives.add('--entire')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                allowed.add('--recursive')
                allowed.add('--entire')
                allowed.add('-u')
                allowed.add('--force')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 3, True)
                exitValue = self.claim(opt.files[:-1], opt.files[-1],
                                       recursiveness = 1 if opts.opts['--recursive'] is not None else
                                                       2 if opts.opts['--entire']    is not None else 0,
                                       private       = opts.opts['-u'] is not None,
                                       force         = opts.opts['--force'] is not None)
                
            elif opts.opts['-D'] is not None:
                allowed.add('--recursive')
                allowed.add('-u')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 3, True)
                exitValue = self.disclaim(opt.files[:-1], opt.files[-1],
                                          recursive = opts.opts['--recursive'] is not None,
                                          private   = opts.opts['-u'] is not None)
                
            elif opts.opts['-A'] is not None:
                allowed.add('-s')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.archive(opts.opts['-A'][0], scrolls = opts.opts['-s'] is not None)
                
            elif opts.opts['--restore-archive'] is not None:
                exclusives.add('--shared')
                exclusives.add('--full')
                exclusives.add('--old')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                exclusives = set()
                exclusives.add('--downgrade')
                exclusives.add('--upgrade')
                self.test_exclusiveness(opts.opts, exclusives, longmap, True)
                allowed.add('--shared')
                allowed.add('--full')
                allowed.add('--old')
                allowed.add('--downgrade')
                allowed.add('--upgrade')
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.rollback(opts.opts['--restore-archive'][0],
                                          keep      = opts.opts['--full'] is None,
                                          skip      = opts.opts['--shared'] is not None,
                                          gradeness = -1 if opts.opts['--downgrade'] is not None else
                                                      1  if opts.opts['--upgrade']   is not None else 0,
                                          shred     = opts.opts['--shred'] is not None)
                
            elif opts.opts['-P'] is not None:
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 2, True)
                exitValue = self.proofread(opts.files)
            
            elif opts.opts['-N'] is not None:
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.clean(shred = opts.opts['--shred'] is not None)
            
            elif opts.opts['-I'] is not None:
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.interactive(shred = opts.opts['--shred'] is not None)
            
            else:
                allowed.add('--shred')
                self.test_allowed(opts.opts, allowed, longmap, True)
                self.test_files(opts.files, 0, True)
                exitValue = self.interactive(shred = opts.opts['--shred'] is not None)
        
        except Error as err:
            exitValue = 255
            print("%s: %s", self.execprog, str(err))
            
        exit(exitValue)
    
    
    
    def test_exclusiveness(self, opts, exclusives, longmap, do_exit = False):
        '''
        Test for option conflicts
        
        @param   opts:dict<str,list<str>>  Current options
        @param   exclusives:set<str>       Exclusive options
        @param   longmap:dict<str,str>     Map from short to long
        @param   do_exit:bool              Exit program on conflict
        @return  :bool                     Whether at most one exclusive option was used
        '''
        used = []
        
        for opt in opts:
            if (opts[opt] is not None) and (opt in exclusives):
                used.append((opt, longmap[opt] if opt in longmap else None))
        
        if len(used) > 1:
            msg = self.execprog + ': conflicting options:'
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
    
    
    def test_allowed(self, opts, allowed, longmap, do_exit = False):
        '''
        Test for out of context option usage
        
        @param   opts:dict<str,list<str>>  Current options
        @param   allowed:set<str>          Allowed options
        @param   longmap:dict<str,str>     Map from short to long
        @param   do_exit:bool              Exit program on incorrect usage
        @return  :bool                     Whether only allowed options was used
        '''
        for opt in opts:
            if (opts[opt] is not None) and (opt not in allowed):
                msg = self.execprog + ': option used out of context: ' + opt
                if opt in longmap:
                    msg += '(' + longmap(opt) + ')'
                printerr(msg)
                if do_exit:
                    exit(1)
                return False
        return True
    
    
    def test_files(self, files, mode, do_exit = False):
        '''
        Test the correctness of the number of used non-option arguments
        
        @param   files:list<str>    Non-option arguments
        @param   mode:int           Correctness mode: 0 - no arguments
                                                      1 - one argument
                                                      2 - atleast one argument
                                                      3 - atleast two arguments
                                                      n - atleast n − 1 arguments
                                                     −n - exactly n arguments
        @param   do_exit:bool       Exit program on incorrectness
        @return  :bool              Whether the usage was correct
        '''
        rc = True
        if mode == 0:
            rc = len(files) == 0
        elif mode == 1:
            rc = len(files) == 1
        elif mode > 1:
            rc = len(files) >= (mode - 1)
        else:
            rc = len(files) == -mode
        if do_exit and not rc:
            exit(1)
        return rc
    
    
    def print_version(self):
        '''
        Prints spike fellowed by a blank spacs and the version of spike to stdout
        '''
        print('spike ' + self.version)
    
    
    def print_copyright(self):
        '''
        Prints spike copyright notice to stdout
        '''
        print('spike – a package manager running on top of git\n'
              '\n'
              'Copyright © 2012, 2013  Mattias Andrée (maandree@member.fsf.org)\n'
              '\n'
              'This program is free software: you can redistribute it and/or modify\n'
              'it under the terms of the GNU General Public License as published by\n'
              'the Free Software Foundation, either version 3 of the License, or\n'
              '(at your option) any later version.\n'
              '\n'
              'This program is distributed in the hope that it will be useful,\n'
              'but WITHOUT ANY WARRANTY; without even the implied warranty of\n'
              'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n'
              'GNU General Public License for more details.\n'
              '\n'
              'You should have received a copy of the GNU General Public License\n'
              'along with this program.  If not, see <http://www.gnu.org/licenses/>.')
    
    
    
    def bootstrap(self):
        '''
        Update the spike and the scroll archives
        
        @return  :byte  Exit value, see description of `mane` 
        '''
        class Agg:
            '''
            aggregator:(str,int)→void
                Feed a directory path and 0 when a directory is enqueued for bootstraping.
                Feed a directory path and 1 when a directory bootstrap process is beginning.
                Feed a directory path and 2 when a directory bootstrap process has ended.
            '''
            def __init__(self):
                self.dirs = {}
                self.next = 0
                self.pos = 0
            def __call__(self, directory, state):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next++
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s' % {0 : (3, 'WAIT'), 1 : (4, 'WORK'), 2 : (2, 'DONE')}[state]
                print('[%s\033[00m] %s\n' % (s, directory))
                self.pos = p + 1
        
        return LibSpike.bootstrap(Agg())
    
    
    def find_scroll(self, patterns, installed = True, notinstalled = True):
        '''
        Search for a scroll
        
        @param   patterns:list<str>  Regular expression search patterns
        @param   installed:bool      Look for installed packages
        @param   uninstalled:bool    Look for not installed packages
        @return  :byte               Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str)→void
                Feed a scroll when one matching one of the patterns has been found.
            '''
            def __init__(self):
                pass
            def __call__(self, found):
                print('%s\n' % found)
        
        return LibSpike.find_scroll(Agg(), pattern, installed, notinstalled)
    
    
    def find_owner(self, files):
        '''
        Search for a files owner pony, includes only installed ponies
        
        @param   files:list<string>  Files for which to do lookup
        @return  :byte               Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,str?)→void
                Feed a file path and a scroll when an owner has been found.
                Feed a file path and `None` when it as been determined that their is no owner.
            '''
            def __init__(self):
                pass
            def __call__(self, filepath, owner):
                if owner is None:
                    print('%s is owner by %s\n' % (filepath, owner))
                else:
                    print('%s has not owner\n' % filepath)
        
        return LibSpike.find_owner(Agg(), files)
    
    
    def write(self, scrolls, root = '/', private = False, explicitness = 0, nodep = False, force = False, shred = False):
        '''
        Install ponies from scrolls
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str?,int,[*])→(void|bool|str)
                Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                The states are: 0 - proofreading
                                1 - scroll added because of being updated
                                2 - resolving conflicts
                                3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                         Return: accepted:bool
                                6 - select provider pony. Additional parameters: options:list<str>
                                                          Return: select provider:str? `None` if aborted
                                7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                8 - verifying source. Additional parameters: progress state:int, progress end:int
                                9 - compiling
                               10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                               11 - file conflict check: Additional parameters: progress state:int, progress end:int
                               12 - installing files: Additional parameters: progress state:int, progress end:int
            '''
            def __init__(self):
                self.updateadd = []
                self.depadd = {}
                self.replaceremove = {}
                self.skipping = []
                self.scrls = [[0, {}]] * 6
                self.scrls[0] = self.scrls[1]
            def __call__(self, scroll, state, *args):
                if state == 0:
                    print('Proofreading: %s' % scroll)
                elif state == 1:
                    self.updateadd.append(scroll)
                elif state == 2:
                    print('Resolving conflicts')
                elif state == 3:
                    if scroll in self.depadd:
                        self.depadd[scroll] += args[0]
                    else:
                        self.depadd[scroll] = args[0]
                elif state == 4:
                    if scroll in self.replaceremove:
                        self.replaceremove[scroll] += args[0]
                    else:
                        self.replaceremove[scroll] = args[0]
                elif state == 5:
                    self.skipping = args[3]
                    if len(self.skipping) > 0:
                        for re in self.skipping:
                            print('Skipping %s' % re)
                    elif len(args[0]) > 0:
                        for fresh in args[2]:
                            print('Installing%s' % fresh)
                    elif len(args[1]) > 0:
                        for re in args[2]:
                            print('Reinstalling %s' % re)
                    elif len(args[2]) > 0:
                        for update in args[2]:
                            print('Explicitly updating %s' % update)
                    elif len(self.updateadd) > 0:
                        for update in self.updateadd:
                            print('Updating %s' % update)
                    elif len(self.depadd) > 0:
                        for dep in self.depadd:
                            print('Adding %s, required by: %s' % (dep, ', '.join(self.depadd[dep])))
                    elif len(self.replaceremove) > 0:
                        for replacee in self.replaceremove:
                            print('Replacing %s with %s' % (replacee, ', '.join(self.replaceremove[replacee])))
                    print('\033[01mContinue? (y/n)\033[00m')
                    return input().lower().startswith('y')
                elif state == 6:
                    print('\033[01mSelect provider for virtual package: %s\033[00m' % scroll)
                    i = 0
                    for prov in args[0]:
                        i += 1
                        print('%i: %s' % (i, prov))
                    print('> ', end='')
                    sel = input()
                    try:
                        sel = int(sel)
                        if 1 <= sel <= len(args):
                            return args[0][sel - 1]
                    except:
                        if sel in args[0]:
                            return sel
                else:
                    if scroll not in self.scrls[state - 7][1]:
                        self.scrls[state - 7][0] += 1
                        self.scrls[state - 7][1][scroll] = self.scrls[state - 7][0]
                    (scrli, scrln) = (self.scrls[state - 7][1][scroll], self.scrls[state - 7][0])
                    if scrli != scrln:
                        if state != 9:
                            print('\033[%iAm', scrln - scrli)
                    if state == 7:
                        (source, progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Downloading %s: %s' % (bar, scrli, scrln, scroll, source))
                    elif state == 8:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Verifing %s' % (bar, scrli, scrln, scroll))
                    elif state == 9:
                        print('(%i/%i) Compiling %s' % (scrli + 1, scrln, scroll))
                    elif state == 10:
                        (filei, filen) = args
                        if filei == 0:
                            print('(%i/%i) Stripping symbols for %s' % (scrli, scrln, scroll))
                    elif state == 11:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Checking file conflicts for %s' % (bar, scrli, scrln, scroll))
                    elif state == 12:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Installing %s' % (bar, scrli, scrln, scroll))
                    if scrli != scrln:
                        if state != 9:
                            print('\033[%iBm', scrln - (scrli + 1))
                return None
                
        return LibSpike.write(Agg(), scrolls, root, private, explicitness, nodep, force, shred)
    
    
    def update(self, root = '/', ignores = [], shred = False):
        '''
        Update installed ponies
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str?,int,[*])→(void|bool|str)
                Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                The states are: 0 - proofreading
                                1 - scroll added because of being updated
                                2 - resolving conflicts
                                3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                         Return: accepted:bool
                                6 - select provider pony. Additional parameters: options:list<str>
                                                          Return: select provider:str? `None` if aborted
                                7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                8 - verifying source. Additional parameters: progress state:int, progress end:int
                                9 - compiling
                               10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                               11 - file conflict check: Additional parameters: progress state:int, progress end:int
                               12 - installing files: Additional parameters: progress state:int, progress end:int
            '''
            def __init__(self):
                self.updateadd = []
                self.depadd = {}
                self.replaceremove = {}
                self.skipping = []
                self.scrls = [[0, {}]] * 6
                self.scrls[0] = self.scrls[1]
            def __call__(self, scroll, state, *args):
                if state == 0:
                    print('Proofreading: %s' % scroll)
                elif state == 1:
                    self.updateadd.append(scroll)
                elif state == 2:
                    print('Resolving conflicts')
                elif state == 3:
                    if scroll in self.depadd:
                        self.depadd[scroll] += args[0]
                    else:
                        self.depadd[scroll] = args[0]
                elif state == 4:
                    if scroll in self.replaceremove:
                        self.replaceremove[scroll] += args[0]
                    else:
                        self.replaceremove[scroll] = args[0]
                elif state == 5:
                    self.skipping = args[3]
                    if len(self.skipping) > 0:
                        for re in self.skipping:
                            print('Skipping %s' % re)
                    elif len(args[0]) > 0:
                        for fresh in args[2]:
                            print('Installing%s' % fresh)
                    elif len(args[1]) > 0:
                        for re in args[2]:
                            print('Reinstalling %s' % re)
                    elif len(args[2]) > 0:
                        for update in args[2]:
                            print('Explicitly updating %s' % update)
                    elif len(self.updateadd) > 0:
                        for update in self.updateadd:
                            print('Updating %s' % update)
                    elif len(self.depadd) > 0:
                        for dep in self.depadd:
                            print('Adding %s, required by: %s' % (dep, ', '.join(self.depadd[dep])))
                    elif len(self.replaceremove) > 0:
                        for replacee in self.replaceremove:
                            print('Replacing %s with %s' % (replacee, ', '.join(self.replaceremove[replacee])))
                    print('\033[01mContinue? (y/n)\033[00m')
                    return input().lower().startswith('y')
                elif state == 6:
                    print('\033[01mSelect provider for virtual package: %s\033[00m' % scroll)
                    i = 0
                    for prov in args[0]:
                        i += 1
                        print('%i: %s' % (i, prov))
                    print('> ', end='')
                    sel = input()
                    try:
                        sel = int(sel)
                        if 1 <= sel <= len(args):
                            return args[0][sel - 1]
                    except:
                        if sel in args[0]:
                            return sel
                else:
                    if scroll not in self.scrls[state - 7][1]:
                        self.scrls[state - 7][0] += 1
                        self.scrls[state - 7][1][scroll] = self.scrls[state - 7][0]
                    (scrli, scrln) = (self.scrls[state - 7][1][scroll], self.scrls[state - 7][0])
                    if scrli != scrln:
                        if state != 9:
                            print('\033[%iAm', scrln - scrli)
                    if state == 7:
                        (source, progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Downloading %s: %s' % (bar, scrli, scrln, scroll, source))
                    elif state == 8:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Verifing %s' % (bar, scrli, scrln, scroll))
                    elif state == 9:
                        print('(%i/%i) Compiling %s' % (scrli + 1, scrln, scroll))
                    elif state == 10:
                        (filei, filen) = args
                        if filei == 0:
                            print('(%i/%i) Stripping symbols for %s' % (scrli, scrln, scroll))
                    elif state == 11:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Checking file conflicts for %s' % (bar, scrli, scrln, scroll))
                    elif state == 12:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Installing %s' % (bar, scrli, scrln, scroll))
                    if scrli != scrln:
                        if state != 9:
                            print('\033[%iBm', scrln - (scrli + 1))
                return None
        
        return LibSpike.update(Agg(), root, ignore, shred)
    
    
    def erase(self, ponies, root = '/', private = False, shred = False):
        '''
        Uninstall ponies
        
        @param   ponies:list<str>  Ponies to uninstall
        @param   root:str          Mounted filesystem from which to perform uninstallation
        @param   private:bool      Whether to uninstall user private ponies rather than user shared ponies
        @param   shred:bool        Whether to preform secure removal when possible
        @return  :byte             Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,int,int)→void
                Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                this begins by feeding the state 0 when a scroll is cleared for removal, when all is enqueued the removal begins.
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, progress, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next++
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] %s\n' % (s, directory))
                self.pos = p + 1
        
        return LibSpike.erase(Agg(), ponies, root, private, shred)
    
    
    def ride(self, pony, private = False):
        '''
        Execute pony after best effort
        
        @param   private:bool  Whether the pony is user private rather than user shared
        @return  :byte         Exit value, see description of `mane`
        '''
        return LibSpike.ride(pony, private)
    
    
    def read_files(self, ponies):
        '''
        List files installed for ponies
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,str)→void
                Feed the pony and the file when a file is detected
            '''
            def __init__(self):
                pass
            def __call__(self, owner, filename):
                print('%s: %s' % (owner, filename))
        
        return LibSpike.read_files(Agg(), ponies)
    
    
    def read_info(self, scrolls, field = None):
        '''
        List information about scrolls
        
        @param   scrolls:list<str>     Scrolls for which to list information
        @param   field:str?|list<str>  Information field or fields to fetch, `None` for everything
        @return  :byte                 Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,str,str)→void
                Feed the scroll, the field name and the information in the field when a scroll's information is read,
                all (desired) fields for a scroll will come once, in an uninterrupted sequence.
            '''
            def __init__(self):
                pass
            def __call__(self, scroll, meta, info):
                print('%s: %s: %s' % (scroll, meta, info))
        
        return LibSpike.read_info(Agg(), scrolls, field)
    
    
    def claim(self, files, pony, recursiveness = 0, private = False, force = False):
        '''
        Claim one or more files as a part of a pony
        
        @param   files:list<str>    File to claim
        @param   pony:str           The pony
        @param   recursiveness:int  0 for not recursive, 1 for recursive, 2 for recursive at detection
        @param   private:bool       Whether the pony is user private rather the user shared
        @param   force:bool         Whether to override current file claim
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,str)→void
                Feed a file and it's owner when a file is already claimed
            '''
            def __init__(self):
                pass
            def __call__(self, filename, owner):
                print('%s is already claimed by %s' % (filename, owner))
        
        return LibSpike.claim(Agg(), files, pony, recursiveness, private, force)
    
    
    def disclaim(self, files, pony, recursive = False, private = False):
        '''
        Disclaim one or more files as a part of a pony
        
        @param   files:list<str>    File to disclaim
        @param   pony:str           The pony
        @param   recursive:bool     Whether to disclaim directories recursively
        @param   private:bool       Whether the pony is user private rather the user shared
        @return  :byte              Exit value, see description of `mane`
        '''
        return LibSpike.disclaim(files, pony, recursive, private)
    
    
    def archive(self, archive, scrolls = False):
        '''
        Archive the current system installation state
        
        @param   archive:str   The archive file to create
        @param   scrolls:bool  Whether to only store scroll states and not installed files
        @return  :byte         Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,int,int,int,int)→void
                Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, scrolli, scrolln, progess, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next++
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] (%i/%i) %s\n' % (s, scrolli, scrolln, scroll))
                self.pos = p + 1
        
        return LibSpike.archive(Agg(), archive, scrolls)
    
    
    def rollback(self, archive, keep = False, skip = False, gradeness = 0, shred = False):
        '''
        Roll back to an archived state
        
        @param   archive:str    Archive to roll back to
        @param   keep:bool      Keep non-archived installed ponies rather than uninstall them
        @param   skip:bool      Skip rollback of non-installed archived ponies
        @param   gradeness:int  -1 for downgrades only, 1 for upgrades only, 0 for rollback regardless of version
        @param   shred:bool     Whether to preform secure removal when possible
        @return  :byte          Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,int,int,int,int)→void
                Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, scrolli, scrolln, progess, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next++
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] (%i/%i) %s\n' % (s, scrolli, scrolln, scroll))
                self.pos = p + 1
        
        return LibSpike.rollback(Agg(), archive, keep, skipe, gradeness, shred)
    
    
    def proofread(self, scrolls):
        '''
        Look for errors in a scrolls
        
        @param   scrolls:list<str>  Scrolls to proofread
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,int,[*])→void
                Feed a scroll, 0, scroll index:int, scroll count:int when a scroll proofreading begins
                Feed a scroll, 1, error message:str when a error is found
            '''
            def __init__(self):
                pass
            def __call__(self, scroll, err, *args):
                if err == 0:
                    index = args[0]
                    count = args[1]
                    print('(%i/%i) %s' % (index, count, scroll))
                else:
                    message = args[0]
                    print('Error: %s: %s' % (scroll, message))
        
        return LibSpike.proofread(Agg(), scrolls)
    
    
    def clean(self, shred = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   shred:bool  Whether to preform secure removal when possible
        @return  :byte        Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str,int,int)→void
                Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, progress, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next++
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] %s\n' % (s, directory))
                self.pos = p + 1
        
        return LibSpike.clean(Agg(), shred)
    
    
    def interactive(self, shred = False):
        '''
        Start interactive mode with terminal graphics
        
        @param   shred:bool  Whether to preform secure removal when possible
        @return  :byte       Exit value, see description of `mane`
        '''
        if not sys.stdout.isatty:
            printerr(self.execprog + ': trying to start interative mode from a pipe')
            return 15
        # TODO interactive mode
        return 0


class Gitcord():
    '''
    Gitcord has awesome magic for manipulating the realms (git repositories)
    '''
    
    def __init__(directory):
        '''
        Constructor
        
        @param  directory:str  The git repository (or any subdirectory that is not a repository itself), or the parent folder of a new repository
        '''
        self.dir = directory
    
    
    def updateBransh():
        '''
        Update the current bransh in the repository
        
        @return  :bool  Whether the spell casting was successful
        '''
        pass
    
    
    def changeBransh(bransh):
        '''
        Change current bransh in the repository
        
        @param   bransh:str  The new current bransh
        @return  :bool       Whether the spell casting was successful
        '''
        pass
    
    
    def clone(repository, directory):
        '''
        Change current bransh in the repository
        
        @param   repository:str  The URL of the repository to clone
        @param   directory:str   The directory of the local clone
        @return  :bool           Whether the spell casting was successful
        '''
        pass
    

    def createRepository(directory):
        '''
        Create a new repository
        
        @param   directory:str   The directory of the local repository
        @return  :bool           Whether the spell casting was successful
        '''
        pass
    
    
    def removeFile(filename):
        '''
        Remove a file from the repository
        
        @param   filename:str  The file to remove
        @return  :bool         Whether the spell casting was successful
        '''
        pass
    
    
    def stageFile(filename):
        '''
        Add a new file for stage changes made to a file to the repository
        
        @param   filename:str  The file to stage
        @return  :bool         Whether the spell casting was successful
        '''
        pass
    
    
    def commit(message, signoff): ## TODO the user should be able to select a message to use and whether to sign off
        '''
        Commit changes in the repository
        
        @param   message:str  The commit message
        @param   signoff:str  Whether to add a sign-off tag to the commit message
        @return  :bool        Whether the spell casting was successful
        '''
        pass


class LibSpike():
    '''
    Advanced programming interface for Spike
    
    Exit values:  0 - Successful
                  4 - Invalid option argument
                  5 - Root does not exist
                  6 - Scroll does not exist
                  7 - Pony is not installed
                  8 - Pony conflict
                  9 - Dependency does not exist
                 10 - File is already claimed
                 11 - File was claimed for another pony
                 12 - File does not exist
                 13 - File already exists
                 14 - Information field is not definied
                 16 - Compile error
                 17 - Installation error, usually because --private or root is needed
                 18 - Private installation is not supported
                 19 - Non-private installation is not supported
                 20 - Scroll error
                 21 - Pony ride error
                 22 - Proofread found scroll error
                 23 - File access denied
                255 - Unknown error
    '''
    
    @staticmethod
    def bootstrap(aggregator):
        '''
        Update the spike and the scroll archives
        
        @param   aggregator:(str,int)→void
                     Feed a directory path and 0 when a directory is enqueued for bootstraping.
                     Feed a directory path and 1 when a directory bootstrap process is beginning.
                     Feed a directory path and 2 when a directory bootstrap process has ended.
        
        @return  :byte  Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def find_scroll(aggregator, patterns, installed = True, notinstalled = True):
        '''
        Search for a scroll
        
        @param   aggregator:(str)→void
                     Feed a scroll when one matching one of the patterns has been found.
        
        @param   patterns:list<str>  Regular expression search patterns
        @param   installed:bool      Look for installed packages
        @param   uninstalled:bool    Look for not installed packages
        @return  :byte               Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def find_owner(aggregator, files):
        '''
        Search for a files owner pony, includes only installed ponies
        
        @param   aggregator:(str,str?)→void
                     Feed a file path and a scroll when an owner has been found.
                     Feed a file path and `None` when it as been determined that their is no owner.
        
        @param   files:list<string>  Files for which to do lookup
        @return  :byte               Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def write(aggregator, scrolls, root = '/', private = False, explicitness = 0, nodep = False, force = False, shred = False):
        '''
        Install ponies from scrolls
        
        @param   aggregator:(str?,int,[*])→(void|bool|str)
                     Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - proofreading
                                     1 - scroll added because of being updated
                                     2 - resolving conflicts
                                     3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     6 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                     8 - verifying source. Additional parameters: progress state:int, progress end:int
                                     9 - compiling
                                    10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                                    11 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    12 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def update(aggregator, root = '/', ignores = [], shred = False):
        '''
        Update installed ponies
        
        @param   aggregator:(str?,int,[*])→(void|bool|str)
                     Feed a scroll (`None` only at state 2 and 5) and a state (can be looped) during the process of a scroll.
                     The states are: 0 - proofreading
                                     1 - scroll added because of being updated
                                     2 - resolving conflicts
                                     3 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                     4 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                     5 - verify installation. Additional parameters: freshinstalls:list<str>, reinstalls:list<str>, update:list<str>, skipping:list<str>
                                                              Return: accepted:bool
                                     6 - select provider pony. Additional parameters: options:list<str>
                                                               Return: select provider:str? `None` if aborted
                                     7 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                                     8 - verifying source. Additional parameters: progress state:int, progress end:int
                                     9 - compiling
                                    10 - stripping symbols. Additional parameters: file index:int, file count:int (can be 0)
                                    11 - file conflict check: Additional parameters: progress state:int, progress end:int
                                    12 - installing files: Additional parameters: progress state:int, progress end:int
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   shred:bool         Whether to preform secure removal when possible
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def erase(aggregator, ponies, root = '/', private = False, shred = False):
        '''
        Uninstall ponies
        
        @param   aggregator:(str,int,int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is cleared for removal, when all is enqueued the removal begins.
        
        @param   ponies:list<str>  Ponies to uninstall
        @param   root:str          Mounted filesystem from which to perform uninstallation
        @param   private:bool      Whether to uninstall user private ponies rather than user shared ponies
        @param   shred:bool        Whether to preform secure removal when possible
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def ride(pony, private = False):
        '''
        Execute pony after best effort
        
        @param   private:bool  Whether the pony is user private rather than user shared
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def read_files(aggregator, ponies):
        '''
        List files installed for ponies
        
        @param   aggregator:(str,str)→void
                     Feed the pony and the file when a file is detected
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def read_info(aggregator, scrolls, field = None):
        '''
        List information about scrolls
        
        @param   aggregator:(str,str,str)→void
                     Feed the scroll, the field name and the information in the field when a scroll's information is read,
                     all (desired) fields for a scroll will come once, in an uninterrupted sequence.
        
        @param   scrolls:list<str>     Scrolls for which to list information
        @param   field:str?|list<str>  Information field or fields to fetch, `None` for everything
        @return  :byte                 Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def claim(aggregator, files, pony, recursiveness = 0, private = False, force = False):
        '''
        Claim one or more files as a part of a pony
        
        @param   aggregator:(str,str)→void
                     Feed a file and it's owner when a file is already claimed
        
        @param   files:list<str>    File to claim
        @param   pony:str           The pony
        @param   recursiveness:int  0 for not recursive, 1 for recursive, 2 for recursive at detection
        @param   private:bool       Whether the pony is user private rather the user shared
        @param   force:bool         Whether to override current file claim
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def disclaim(files, pony, recursive = False, private = False):
        '''
        Disclaim one or more files as a part of a pony
        
        @param   files:list<str>    File to disclaim
        @param   pony:str           The pony
        @param   recursive:bool     Whether to disclaim directories recursively
        @param   private:bool       Whether the pony is user private rather the user shared
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def archive(aggregator, archive, scrolls = False):
        '''
        Archive the current system installation state
        
        @param   aggregator:(str,int,int,int,int)→void
                     Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
        
        @param   archive:str   The archive file to create
        @param   scrolls:bool  Whether to only store scroll states and not installed files
        @return  :byte         Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def rollback(aggregator, archive, keep = False, skip = False, gradeness = 0, shred = False):
        '''
        Roll back to an archived state
        
        @param   aggregator:(str,int,int,int,int)→void
                     Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
        
        @param   archive:str    Archive to roll back to
        @param   keep:bool      Keep non-archived installed ponies rather than uninstall them
        @param   skip:bool      Skip rollback of non-installed archived ponies
        @param   gradeness:int  -1 for downgrades only, 1 for upgrades only, 0 for rollback regardless of version
        @param   shred:bool     Whether to preform secure removal when possible
        @return  :byte          Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def proofread(aggregator, scrolls):
        '''
        Look for errors in a scrolls
        
        @param   aggregator:(str,int,[*])→void
                     Feed a scroll, 0, scroll index:int, scroll count:int when a scroll proofreading begins
                     Feed a scroll, 1, error message:str when a error is found
        
        @param   scrolls:list<str>  Scrolls to proofread
        @return  :byte              Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0
    
    
    @staticmethod
    def clean(aggregator, shred = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   aggregator:(str,int,int)→void
                     Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                     this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
        
        @param   shred:bool  Whether to preform secure removal when possible
        @return  :byte       Exit value, see description of `LibSpike`, the possible ones are: 0 (TODO)
        '''
        return 0



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



if not SPIKE_PATH.endswith('/'):
    SPIKE_PATH += '/'

linuxvt = ('TERM' in os.environ) and (os.environ['TERM'] == 'linux')

if __name__ == '__main__': # sic
    spike = Spike()
    spike.mane(sys.argv)

