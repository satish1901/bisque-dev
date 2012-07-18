import os, sys, shutil
import logging
import string
import time
import stat
import urllib2
import shlex
import subprocess
import optparse
import pickle
import tempfile
try:
    from lxml import etree as et
except:
    from xml.etree import ElementTree as et
from bq.util.configfile import ConfigFile
from bq.api import BQSession

from module_env import MODULE_ENVS, ModuleEnvironmentError
from mexparser import MexParser

ENV_MAP = dict ([ (env.name, env) for env in MODULE_ENVS ])
logging.basicConfig(level=logging.DEBUG, filename='module.log')
log = logging.getLogger('bq.runtime')

####################
# Helpers
def check_exec (path, fix = True):
    if os.access (path, os.X_OK):
        return
    if fix:
        os.chmod (path, 0744)

def strtobool(x):
    return {"true": True, "false": False}.get(x.lower())

def strtolist(x, sep=','):
    return [ s.strip() for s in x.split(sep)]

def config_path(*names):
    return to_sys_path(os.path.join('.', 'config', *names))

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        p = os.environ["PATH"].split(os.pathsep)
        p.insert(0, '.')
        for path in p:
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
##########################################
# Local exception
class RunnerException(Exception):
    """Exception in the runners"""
    def __init__(self, msg =None, mex= {}):
        super( RunnerException, self).__init__(msg)
        self.mex = mex
    def __str__(self):
        #return "\n".join( [ str (super( RunnerException, self) ) ] +  
        #                  [ "%s: %s" % (k, self.mex[k]) for k in sorted(self.mex.keys() )] )
        return "%s env=%s" % (super( RunnerException, self).__str__(), self.mex ) 



######################################
# dict allowing field access to elements
class AttrDict(dict):
    "dictionary allowing access to elements as field"

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError
    def __setattr__(self, name, value):
        self[name] = value
        return value

    def __getstate__(self):
        return self.items()

    def __setstate__(self, items):
        for key, val in items:
            self[key] = val


###############################
# BaseRunner
class BaseRunner(object):
    """Base runner for ways of running a module in some runtime evironment.

    Runtime environments include the command line, condor and hadoop

    Each runner basically prepares the module environment, runs or stops
    modules, and allows the status of a run to be queried

    Runners interact with module environments (see base_env)

    For each module it is expected that custom  launcher will be written.
    A simple example might be:
       from bisque.util.launcher import Launcher
       class MyModuleLauncher (Launcher):
           execute='myrealmodule'
            ...

       if __name__ == "__main__":
           MyModuleLauncher().main()


    The engine will launch a subprocess with the following template:
        
      launcher arg1 arg2 arg3 mex=http://somehost/ms/mex/1212 start

    The launcher code will strip off the last 2 arguments and
    pass the other arguments to the real module.

    The last argument is command it must be one of the following
       start, stop, status

    """
    name       = "Base"
    env = None # A mapping of environment variables (or Inherit)
    executable = [] # A command line list of the arguments
    environments = []
    launcher   = None  # Use Default launcher
    mexhandled = "true"

    def __init__(self, **kw):
        self.parser =  optparse.OptionParser()
        self.parser.add_option("-n","--dryrun", action="store_true",
                               default=False)
        self.parser.add_option('-v', '--verbose', action="store_true",
                               default=False)
        self.parser.add_option('-d', '--debug', action="store_true",
                               default=False)
        self.session = None

    def log (self, msg):
        #if self.options.verbose:
        log.info( msg )

    ###########################################
    # Config 
    def read_config (self, **kw):
        """Initial state of a runner.  The module-runtime.cfg is read
        and the relevent runner section is applied.  The environment
        list is created and setup in order to construct the
        environments next
        """
        self.config = AttrDict(executable="", environments="")
        self.sections = {}
        self.log("BaseRunner: read_config")
        # Load any bisque related variable into this runner
        if os.path.exists('runtime-bisque.cfg'):
            self.bisque_cfg = ConfigFile('runtime-bisque.cfg')
            self.load_section(None, self.bisque_cfg)

        if not os.path.exists('runtime-module.cfg'):
            self.log ("missing runtime-module.cfg")
            return
        self.module_cfg = ConfigFile('runtime-module.cfg')
        # Process Command section
        self.load_section(None, self.module_cfg)      # Globals

    def load_section (self, name, cfg):
        name = name or "__GLOBAL__"
        section = self.sections.setdefault(name, {})
        section.update  ( cfg.get (name, asdict = True) )
        self.config.update (section)
        #for k,v in section.items():
        #    setattr(self,k,v)

    #########################################################
    # Helpers 
    def create_environments(self,  **kw):
        """Build the set of environments listed by the module config"""
        if isinstance(self.config.environments, basestring):
            self.environments = strtolist(self.config.environments)
        envs = []
        for name in self.environments:
            env = ENV_MAP.get (name, None)
            if env is not None:
                envs.append (env(runner = self))
                continue
            log.debug ('Unknown environment: %s ignoring' % name)
        self.environments = envs
        log.info ('created environments %s' % envs)


    def process_config(self, **kw):
        """Configuration occurs in several passes.
        1.  read config file and associated runtime section 
             create environments
        2.   Process the config values converting types
        """
        self.mexhandled = strtobool(self.mexhandled)

        # Find any configuration parameters in the envs
        # and add them to the class
        for env in self.environments:
            env.process_config (self)

    def setup_environments(self, **kw):
        'Call setup_environment during "start" processing'
        for env in self.environments:
            env.setup_environment (self, **kw)

    # Run during finish
    def teardown_environments(self, **kw):
        'Call teardown_environment during "finish" processing'
        for env in reversed(self.environments):
            env.teardown_environment (self, **kw)

    ##########################################
    # Extract arguments from command line or mex
    def process_args(self,  **kw):
        """Deal with any arguments and prepare the mex and module
        returns a callable for the next actions
        """
        # Args are passed directly from the Engine
        # However condor_dag will enter here with command line arguments
        args  = kw.pop('arguments', None)
        self.mex_tree = kw.pop('mex_tree', None)
        self.module_tree = kw.pop('module_tree', None)
        self.bisque_token = kw.pop('bisque_token', None)
        # list of dict representing each mex : variables and arguments
        self.mexes = []
        self.rundir = os.getcwd()

        # Add remaining arguments to the executable line
        # Ensure the loaded executable is a list
        if isinstance(self.config.executable, str):
            executable = shlex.split(self.config.executable)
        #self.executable.extend (arguments)

        topmex = AttrDict(self.config)
        topmex.update(dict(named_args={}, 
                           executable=list(executable), 
#                           arguments = [],
                           mex_url = self.mex_tree is not None and self.mex_tree.get('uri') or None,
                           bisque_token = self.bisque_token, 
                           rundir = self.rundir))
        self.mexes.append(topmex)

        # Pull out command line arguments 
        self.options, topmex.arguments = self.parser.parse_args(args)
        self.command = topmex.arguments.pop()
        # Scan argument looking for named arguments
        for arg in topmex.arguments:
            tag, sep, val = arg.partition('=')
            if sep == '=':
                topmex.named_args[tag] = val


        # Pull out arguments from mex 
        if self.mex_tree is not None and self.module_tree is not None:
            mexparser = MexParser()
            mex_inputs  = mexparser.prepare_mex_params(self.module_tree, self.mex_tree)
            module_options = mexparser.prepare_options(self.module_tree, self.mex_tree)

            argument_style = module_options.get('argument_style')
            if argument_style == 'named':
                topmex.named_args.update ( [x.split('=') for x in mex_inputs] )
            topmex.executable.extend(mex_inputs)
            topmex.rundir = self.rundir
            topmex.options = module_options
            
            # Create a nested list of  arguments  (in case of submex)
            submexes = self.mex_tree.xpath('/mex/mex')
            for mex in submexes:
                sub_inputs = mexparser.prepare_mex_params(self.module_tree, mex)
                submex = AttrDict(self.config)
                submex.update(dict(named_args=dict(topmex.named_args), 
#                                   arguments =list(topmex.arguments),
                                   executable=list(executable), #+ topmex.arguments,
                                   mex_url = mex.get('uri'), 
                                   bisque_token = self.bisque_token,
                                   rundir = self.rundir))
                #if argument_style == 'named':
                #    submex.named_args.update ( [x.split('=') for x in sub_inputs] )
                submex.executable.extend(sub_inputs)
                self.mexes.append(submex)
            # Submex's imply that we are iterated.
            # We can set up some options here and remove any execution 
            # for the top mex.
            if len(self.mex_tree.xpath('//tag[@name="iterable"]')) or len(self.mexes) > 1:
                topmex.executable = None
                topmex.iterables = mexparser.process_iterables(self.module_tree, self.mex_tree)

        log.info("processing %d mexes -> %s" % (len(self.mexes), self.mexes))

        command = getattr (self, 'command_%s' % self.command, None)
        return command


    ##################################################
    # Command sections
    # A command is launched with last argument on the command line of the launcher
    # Each command must return the either the next fommand to run or None to stop
    # Derived classes should overload these functions

    def command_start(self, **kw):
        self.setup_environments()
        with open('%s/mexes.bq' % self.mexes[0].get('staging_path', tempfile.gettempdir()),'wb') as f:
            pickle.dump(self.mexes, f)

        log.info("starting %d mexes -> %s" % (len(self.mexes), self.mexes))

        if len(self.mexes) > 1:
            if self.session is None:
                self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
            self.session.update_mex('running parallel')
        return self.command_execute

    def command_execute(self, **kw):
        """Execute the internal executable"""
        return self.command_finish

    def command_finish(self, **kw):
        """Cleanup the environment and perform any needed actions
        after the module completion
        """
        with open('%s/mexes.bq' % self.mexes[0].get('staging_path', tempfile.gettempdir()),'rb') as f:
            self.mexes = pickle.load(f)

        log.info("finishing %d mexes -> %s" % (len(self.mexes), self.mexes))

        self.teardown_environments()

        if len(self.mexes) > 1:
            if self.session is None:
                self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
            # outputs 
            #   mex_rul
            #   dataset_url
            tags = None
            if 'iterables' in self.mexes[0] and self.mexes[0].iterables is not None:
                iter_name, iter_val, iter_type = self.mexes[0].iterables
                tags = [ { 'name' : 'outputs',
                           'tag' : [ { 'name': iter_name, 'value': iter_val, 'type': iter_type },
                                     { 'name': 'mex_url', 'value': self.mexes[0].mex_url, 'type' : 'mex' },]}]
            self.session.finish_mex(tags = tags)
        return None

    def command_kill(self, **kw):
        """Kill the running module if possible
        """
        return False

    def command_status(self, **kw):
        return None

    def check(self, module_tree=None, **kw):
        "check whether the module seems to be runnable"
        self.read_config(**kw)
        # check for a disabled module
        enabled = self.config.get('module_enabled', 'true').lower() == "true"
        if not enabled :
            log.info ('Module is disabled')
            return False
        # Add remaining arguments to the executable line
        # Ensure the loaded executable is a list
        if isinstance(self.config.executable, str):
            executable = shlex.split(self.config.executable)
        if os.name == 'nt':
            return True
        return executable and which(executable[0]) is not None

    def main(self, **kw):
        # Find and read a config file for the module
        try:
            self.read_config(**kw)
            command = self.process_args(**kw)
            self.create_environments(**kw)
            self.process_config(**kw)

            while command:
                log.info("COMMAND_RUNNER %s" % command)
                command = command(**kw)
            return 0
        except ModuleEnvironmentError, e:
            log.exception( "Problem occured in module")
            raise RunnerException(str(e), self.mexes)
        except RunnerException, e:
            raise
        except Exception, e:
            log.exception ("Unknown exeception: %s" % e)
            raise RunnerException(str(e), self.mexes)
        return 1


class CommandRunner(BaseRunner):
    """Small extension to BaseRunner to actually execute the script.
    """
    name = "command"

    def read_config (self, **kw):
        super(CommandRunner, self).read_config (**kw)
        self.log("CommandRunner: read_config")
        self.load_section('command', self.module_cfg) # Runner's name
        
    
    def process_config(self, **kw):
        super(CommandRunner, self).process_config(**kw)
        for mex in self.mexes:
            if not mex.executable:
                continue
            mex.log_name = os.path.join(mex.rundir, "%s.log" % mex.executable[0])


    def execone(self, command_line, stdout = None, stderr=None, cwd = None):
        if os.name=='nt':
            exe = which(command_line[0])
            exe = exe or which(command_line[0] + '.exe')
            exe = exe or which(command_line[0] + '.bat')
            if exe is None:
                 raise RunnerException ("Executable was not found: %s" % command_line[0])                
            command_line[0] = exe
        retcode = subprocess.call(command_line,
                                  stdout = stdout,
                                  stderr = stderr,
                                  #stdin  = open("/dev/null"),
                                  shell  = (os.name == "nt"),
                                  cwd    = cwd
                                  )
        if retcode:
            raise RunnerException (
                "Command %s gave non-zero return code %s" %
                (" ".join(command_line), retcode))

    def command_execute(self, **kw):

        for mex in self.mexes:
            if not mex.executable:
                log.info ('skipping mex %s ' % mex)
                continue
            command_line = list(mex.executable)
            #command_line.extend (mex.arguments)
            rundir = mex.get('rundir')
            if  self.options.dryrun:
                self.log( "DryRunning '%s' in %s" % (' '.join(command_line), rundir))
                continue

            self.log( "running '%s' in %s" % (' '.join(command_line), rundir))
            log.info ('mex %s ' % mex)

            self.execone(command_line, 
                         stdout = open(mex.log_name,'a'),
                         stderr = subprocess.STDOUT,
                         cwd = rundir)
        
        return self.command_finish





if __name__ == "__main__":
    CommandRunner().main()
    sys.exit(0)
