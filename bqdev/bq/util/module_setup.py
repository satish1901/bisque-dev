# Collection of routines to be used during the bisque setup process
#
#
#

import os,sys
from subprocess import call
import shutil
import functools
from bq.util.configfile import ConfigFile

BISQUE_DEPS = map (functools.partial(os.path.join, '../../external'), [ "bisque.jar", "jai_codec.jar", "jai_core.jar", "jai_imageio.jar", "clibwrapper_jiio.jar"])

def copy_link (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            print "linking %s to %s"%(f,dest)
            os.link(f, dest)
        except (AttributeError, OSError), e:
            print "Problem in link %s .. trying copy" % e
            shutil.copy (f, dest)



def mcc (command,  *largs, **kw):
    where = kw.pop('where', None)
    if where:
        cwd = os.getcwd()
        os.chdir(where)
    mcc = ['mcc']
    mcc += largs
    mcc.append (command)
    print " ".join (mcc)
    try:
        ret = call (mcc, shell = (os.name == "nt"))
    except OSError:
        print "Couldn't execute command %s" % (" ".join(mcc))
        print "Please check your matlab enviroment. In particular check if mcc is available and callable from the shell"
        return False
    if where:
        os.chdir (cwd)
    return ret == 0

def matlab (command, where = None, params={ }):

    if not require('matlab_home', params):
        return False
    
    if where:
        cwd = os.getcwd()
        os.chdir(where)
    call (['matlab', '-nodisplay' , '-r', command])
    if where:
        os.chdir (cwd)
    return True


def copy_files (files, dest):
    for f in files:
        fname = os.path.basename (f)
        dname = os.path.join (dest, fname)
        if os.path.exists (dname): os.unlink (dname)
        copy_link (f, dest)
    

def matlab_setup(main_path, files = [], bisque_deps = True, params = {}, **kw):

    if not require('matlab_home', params):
        return False

    if main_path.endswith (".m"):
        main_path = main_path [0:-2]

    main_name = os.path.basename(main_path)
    if os.name=='nt': 
      main_ext  = ".exe"
    else: 
      main_ext = ""
    
	#mcc -m -C -R -nodisplay -R -nojvm -nocache maizeG.m
    #m Macro that generates a C stand-alone application. This is
    #equivalent to the options "-W main -T link:exe", which can be
    #found in the file
    #<MATLAB>/toolbox/compiler/bundles/macro_option_m.

    #C For stand-alone applications and shared libraries, generate a
    #separate CTF archive. If this option is not specified, the CTF
    #will be embedded within the stand-alone application or library.

    # -R Specify the run-time options for the MATLAB Common Runtime
    # (MCR) usage: mcc -m -R -nojvm,<args>,-nojit,<args> -v foo.m
    if bisque_deps:
        files.extend (BISQUE_DEPS)

    if len(files):
        copy_files (files, '.')
    if not os.path.exists ('build'): os.mkdir ('build')
    if mcc(main_path + '.m', '-d', 'build', '-m', '-C', '-R', '-nodisplay'):
        shutil.move (os.path.join('build',  main_name + main_ext),'.')
        shutil.move (os.path.join('build', '%s.ctf' % main_name),'.')
        shutil.rmtree ('build')
        
        return 0
    return 1



def require(expression, params):
    """Require everying in expression

    Can be in simple variable in params or a callable of
    the form f (params) which returns boolean
    """

    if not isinstance(expression,list):
        expression = [ expression ]

    for e in expression:
        if callable(e):
            if not e(params):
                return False
        if isinstance(e, basestring):
            if not bool(params.get(e, False)):
                return False
    return True
        
def read_config(filename):
    return ConfigFile(filename).get (None, asdict = True)

