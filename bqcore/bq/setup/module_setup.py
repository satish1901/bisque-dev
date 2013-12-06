# Collection of routines to be used during the bisque setup process
#
#
#

import os,sys
from subprocess import call
import shutil
import functools
from bq.util.configfile import ConfigFile
from bq.util.copylink import copy_link
from bq.util.paths import config_path
from mako.template import Template
import bbfreeze

BISQUE_DEPS = map (functools.partial(os.path.join, '../../external'), [ "bisque.jar", "jai_codec.jar", "jai_core.jar", "jai_imageio.jar", "clibwrapper_jiio.jar"])


class SetupError(Exception):
    pass



def ensure_matlab(params):
    'make sure matlab is enabled and in the path'

    require('runtime.matlab_home', params)
    matlab_home = params['runtime.matlab_home']
    if matlab_home not in  os.environ['PATH']:
        os.environ['PATH'] = os.path.join(matlab_home,'bin') + os.pathsep + os.environ['PATH']
        print "ADDING MATLAB TO PATH->", os.environ['PATH']

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

def mex_compile (command_list, where = None, **kw):
    """mex compile a command_list a list of arguments to the matlab mex_compiler

    :param: command_list - a list of command
    :param: where - directory in which mex will be compiled"""

    if where:
        cwd = os.getcwd()
        os.chdir(where)
    mex = ['mex']
    mex.extend (command_list)
    print " ".join (mex)
    try:
        ret = call (mex, shell = (os.name == "nt"))
    except OSError:
        print "Couldn't execute command %s" % (" ".join(mex))
        print "Please check your matlab enviroment. In particular check if mcc is available and callable from the shell"
        return False
    if where:
        os.chdir (cwd)
    return ret == 0

def matlab (command, where = None, params={ }):
    'run matlab with a command'
    if not require('runtime.matlab_home', params):
        return False
    if where:
        cwd = os.getcwd()
        os.chdir(where)
    call (['matlab', '-nodisplay' , '-r', command])
    if where:
        os.chdir (cwd)
    return True


def copy_files (files, dest):
    'copy a list of files to a dest'
    for f in files:
        fname = os.path.basename (f)
        dname = os.path.join (dest, fname)
        if os.path.exists (dname): os.unlink (dname)
        copy_link (f, dest)


def matlab_setup(main_path, files = [], bisque_deps = False, dependency_dir = "mbuild",  params = {}, **kw):
    'prepare a matlab script for execution  by compiling with mcc'

    ensure_matlab(params)
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


    rest = []

    if isinstance(main_path, list):
        mpath = main_path.pop(0)
        rest = main_path
        main_path = mpath

    ext_map = { 'nt' : '.exe' }
    if main_path.endswith (".m"):
        main_path = main_path [0:-2]
    main_name = os.path.basename(main_path)
    if bisque_deps:
        files.extend (BISQUE_DEPS)
    if len(files):
        copy_files (files, '.')
    if not os.path.exists (dependency_dir): os.mkdir (dependency_dir)

    if mcc(main_path + '.m', '-d', dependency_dir, '-m', '-C', '-R', '-nodisplay', '-R', '-nosplash', *rest):
        main = main_name + ext_map.get(os.name, '')
        ctf  = main_name + '.ctf'
        shutil.copyfile(os.path.join(dependency_dir, main), main)
        shutil.copyfile(os.path.join(dependency_dir, ctf), ctf)
        shutil.rmtree (dependency_dir)
        os.chmod (main, 0744)
        return 0
    return 1

def python_setup(scripts,  package_scripts =True, dependency_dir = 'pydist', params = {} ):
    """compile python dependencies into a package

    if package_script is true then a runner scripts will be generated
    for each script
    """
    fr = bbfreeze.Freezer(dependency_dir)
    fr.include_py = False
    if not isinstance(scripts, list):
        scripts = [ scripts ]
    for script in scripts:
        fr.addScript(script)
    fr()
    if not package_scripts:
        return
    data = dict(params)

    for script in scripts:
        script_name = os.path.splitext(script)[0]
        data['script'] = os.path.join('.', dependency_dir, script_name)
        # THIS os.path.join needs to be replaced by pkg_resources or pkg_util
        # when the toplevel is packaged
        try:
            template = Template(filename=os.path.abspath (os.path.join('..','..', 'config','templates','python_launcher.tmpl')))
            with open(script_name, 'wb') as f:
                f.write(template.render(script = data['script']))
                os.chmod (script_name, 0744)
                return 0
        except Exception,e:
            print ("Could not create python launcher script %s" % e)


def ensure_binary(exe):
    'make sure executable is available to the module'
    import distutils.spawn
    p = distutils.spawn.find_executable(exe)
    if p is None:
        raise SetupError("Executable required but not found: %s" % exe)

def require(expression, params, throws = True):
    """Require everying in expression

    Can be in simple variable in params or a callable of
    the form f (params) which returns boolean
    """

    valid = True
    if not isinstance(expression,list):
        expression = [ expression ]

    for e in expression:
        if callable(e):
            if not e(params):
                valid = False
                break
        if isinstance(e, basestring):
            if not bool(params.get(e, False)):
                valid = False
                break

    if not valid and throws:
        raise SetupError("required expression failed %s" % expression)

    return valid

def read_config(filename):
    return ConfigFile(filename).get (None, asdict = True)

