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
import sys

from dragonsuite import *
from scrollmagick import *

SOFTWARE_SHAREABLE = 1
SOFTWARE_COMMERCIAL = 2
SOFTWARE_DERIVATIVE = 4
MEDIA_SHAREABLE = 8
MEDIA_COMMERCIAL = 16
MEDIA_DERIVATIVE = 32
TRADEMARKED = 64
PATENTED = 128
MEDIA = MEDIA_SHAREABLE | MEDIA_COMMERCIAL | MEDIA_DERIVATIVE
SOFTWARE = SOFTWARE_SHAREABLE | SOFTWARE_COMMERCIAL | SOFTWARE_DERIVATIVE

UNSUPPORTED = 0
SUPPORTED = 1
MANDITORY = 2


class Spikeless():
    '''
    Spike but without the package managing, it just installs scrolls
    
    @author  Mattias Andrée (maandree@member.fsf.org)
    '''
    
    @staticmethod
    def install(scroll, startdir, pinpal = '', private = False, freshinstallation = True, buildpatch = None, checkpatch = None, packagepatch = None, inspection = None):
        '''
        Installs a scroll, but does not do any package managing
        
        @param   scroll:str                                                     Scroll to install, by filename
        @param   startdir:str                                                   Scroll base working directory
        @param   pinpal:str                                                     Installation root
        @param   private:bool                                                   Whether to install privately
        @param   freshinstallation:bool                                         Whether it is a fresh installation
        @param   buildpatch:(srcdir:str, pkgdir:str)?→void                      Scroll build patch function
        @param   checkpatch:(srcdir:str, pkgdir:str)?→void                      Scroll check patch function
        @param   packagepatch:(srcdir:str, pkgdir:str)?→void                    Scroll package patch function
        @param   inspection:(pkgdir:str)?→bool                                  Function that checks that the package can be installed
        @return  (pre, pkgdir, post):((list<str>)→void, str, (list<str>)→void)  Preinstall functor, director with files to install, postinstall functor.
                                                                                The functors takes the files installed by the scrolls, before and after the installation, respectively.
                                                                                Between calling the functor you just install file files in the returned directory
        '''
        global _dragonsuite_output
        _dragonsuite_output = sys.stdout.buffer
        
        ScrollMagick.init_methods()
        ScrollMagick.init_fields()
        
        scrolldir = os.path.abspath(dirname(scroll))
        cwd = os.getcwd()
        
        ScrollMagick.export_environment()
        
        environ = {}
        for var in os.environ:
            environ[var] = os.environ[var]
        def resetEnviron(reset_to):
            delete = []
            s = set(reset_to.keys())
            for var in os.environ:
                if var not in s:
                    delete.append(var)
                else:
                    os.putenv(var, reset_to[var])
                    os.environ[var] = reset_to[var]
            for var in delete:
                os.unsetenv(var)
                del os.environ[var]
        
        cd(startdir)
        startdir = os.getcwd()
        cd(cwd)
        srcdir = startdir + os.sep + 'src'
        pkgdir = startdir + os.sep + 'pkg'
        if not os.path.exists(srcdir):
            os.makedirs(srcdir)
        if not os.path.exists(pkgdir):
            os.mkdir(pkgdir)
        
        ScrollMagick.execute_scroll(scroll)
        
        def sources(scrolldir):
            global noextract, source, sha3sums
            noextract = set([] if noextract is None else noextract)
            extract = []
            
            pushd(scrolldir)
            for i in range(len(source)):
                src = source[i]
                extras = None
                if not isinstance(src, str):
                    extras = list(src[1:])
                    src = src[0]
                _src = src
                if src.startswith('file:'):
                    src = src[5:]
                    if src.startswith('//'):
                        src = src[2:]
                elif ':' in src:
                    if extras is not None:
                        src = [src] + extras
                    source[i] = (src, _src not in noextract)
                    continue
                src = os.path.abspath(src)
                src = 'file://' + src
                if extras is not None:
                    src = [src] + extras
                source[i] = (src, _src not in noextract)
            popd()
            
            def inetget(params, dest, sha3sum):
                if os.path.exists(dest):
                    if sha3sum is not None:
                        if sha3sum(dest) != sha3sum.upper():
                            wget(params)
                else:
                    wget(params)
            
            i = 0
            for (src, extractsrc) in source:
                dest = None
                d = None
                if isinstance(src, str):
                    dest = src[src.rfind('/'):]
                    if dest == '':
                        dest = 'index.html'
                    d = dest
                    dest = startdir + os.sep + dest
                    if ':' not in src:
                        cp(src.replace('/', os.sep), dest)
                    elif src.startswith('file:'):
                        src = src[5:]
                        if src.startswith('//'):
                            src = src[2:]
                        cp(src.replace('/', os.sep), dest)
                    else:
                        inetget(src, dest, sha3sums[i])
                else:
                    extras = src[2:]
                    (src, dest) = src[:2]
                    if dest is None:
                        dest = src[src.rfind('/'):]
                        if dest == '':
                            dest = 'index.html'
                    d = dest
                    dest = startdir + os.sep + dest
                    if ':' not in src:
                        cp(src.replace('/', os.sep), dest)
                    elif src.startswith('file:'):
                        src = src[5:]
                        if src.startswith('//'):
                            src = src[2:]
                        cp(src.replace('/', os.sep), dest)
                    else:
                        inetget([src, '-O', dest] + extras, dest, sha3sums[i])
                if sha3sums[i] is not None:
                    sha3 = sha3sum(sumdests)
                    if sha3 == sha3sums[i].upper():
                        pass ## TODO sha3sums
                if extractsrc:
                    extract.append(os.path.abspath(dest))
                i += 1
            
            cd('src')
            decompress(extract)
            cd('..')
        
        cd(startdir)
        msg('Fetching sources')
        sources(scrolldir)
        
        if build is not None:
            if buildpatch is not None:
                msg('Patching build process')
                resetEnviron(environ)
                os.chdir(startdir)
                os.umask(0o022)
                buildpatch(srcdir, pkgdir)
            msg('Building')
            resetEnviron(environ)
            os.chdir(startdir)
            os.umask(0o022)
            build(startdir, srcdir, pkgdir, private)
        if check is not None:
            if checkpatch is not None:
                msg('Patching check process')
                resetEnviron(environ)
                os.chdir(startdir)
                os.umask(0o022)
                checkpatch(srcdir, pkgdir)
            msg('Checking')
            resetEnviron(environ)
            os.chdir(startdir)
            os.umask(0o022)
            check(startdir, srcdir, pkgdir, private)
        if package is not None:
            if packagepatch is not None:
                msg('Patching package process')
                resetEnviron(environ)
                os.chdir(startdir)
                os.umask(0o022)
                packagepatch(srcdir, pkgdir)
            msg('Packaging')
            resetEnviron(environ)
            os.chdir(startdir)
            os.umask(0o022)
            package(startdir, srcdir, pkgdir, private)
        
        os.chdir(cwd)
        resetEnviron(environ)
        
        global useopts, compresses ## TODO defualt options should be load
        if useopts is None:
            useopts = set(['strip', 'docs', 'info', 'man', 'licenses' 'changelogs', 'libtool', 'upx'])
        if compresses is None:
            compresses = {'docs' : 'gz', 'info' : 'gz', 'man' : 'gz'}
        if options != None:
            for opt in options:
                if opt.startswith('!'):
                    if opt[1:] in useopts:
                        del useopts[opt[1:]]
                elif '=' in opts:
                    compresses[opts.split('=')[0]] = opts.split('=')[1]
                else:
                    if opt not in useopts:
                        useopts.add(opt)
        
        ## TODO apply options
        
        if inspection is not None:
            inspection(pkgdir)
        if not os.path.exists(pinpal):
            os.makedirs(pinpal + os.sep + 'src')
        
        class preFunctor():
            def __init__(self, fresh, start, root, priv, env):
                self.fresh = fresh
                self.start = start
                self.root = root
                self.env = env
            def __call__(self, installedfiles = []):
                global pre_install, pre_upgrade
                cwd = os.getcwd()
                os.chdir(self.root)
                os.umask(0o022)
                if self.fresh:
                    if pre_install is not None:
                        msg('Preinstall processing')
                        tmpdir = self.start + os.sep + 'pretmp'
                        if not os.path.exists(tmpdir):
                            os.mkdir(tmpdir)
                        pre_install(tmpdir, self.root, self.priv)
                else:
                    if pre_upgrade is not None:
                        msg('Preupgrade processing')
                        tmpdir = self.start + os.sep + 'pretmp'
                        if not os.path.exists(tmpdir):
                            os.mkdir(tmpdir)
                        pre_install(tmpdir, self.root, installedfiles, self.priv)
                resetEnviron(self.env)
                os.chdir(cwd)
        
        class postFunctor():
            def __init__(self, fresh, start, root, priv, env):
                self.fresh = fresh
                self.start = start
                self.root = root
                self.env = env
            def __call__(self, installedfiles = []):
                global post_install, post_upgrade
                cwd = os.getcwd()
                os.chdir(self.root)
                os.umask(0o022)
                if self.fresh:
                    if post_install is not None:
                        msg('Postinstall processing')
                        tmpdir = self.start + os.sep + 'posttmp'
                        if not os.path.exists(tmpdir):
                            os.mkdir(tmpdir)
                        post_install(tmpdir, self.root, installedfiles, self.priv)
                else:
                    if post_upgrade is not None:
                        msg('Postupgrade processing')
                        tmpdir = self.start + os.sep + 'posttmp'
                        if not os.path.exists(tmpdir):
                            os.mkdir(tmpdir)
                        post_install(tmpdir, self.root, installedfiles, self.priv)
                resetEnviron(self.env)
                os.chdir(cwd)
        
        pre = preFunctor(freshinstallation, startdir, pinpal, private, environ)
        post = postFunctor(freshinstallation, startdir, pinpal, private, environ)
        return (pre, pkgdir, post)


if __name__ == '__main__': # sic
    if len(sys.argv) < 3:
        print('USAGE: spikeless SCROLL STARTDIR PINPAL [private]')
        sys.exit(1)
    global useopts, compresses
    (useopts, compresses) = (None, None)
    def installdir(src, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)
        files = [src + os.sep + f for f in os.listdir(src)]
        cp_r(files, dest)
    scroll = os.path.abspath(sys.argv[1])
    startdir = os.path.abspath(sys.argv[2])
    pinpal = os.path.abspath(sys.argv[3])
    (_a, pkgdir, _b) = Spikeless.install(scroll, startdir, pinpal, 'private' in sys.argv[4:])
    msg('Installing packaged files')
    installdir(pkgdir, pinpal)

