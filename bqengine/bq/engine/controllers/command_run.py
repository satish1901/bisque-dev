import os, sys, shutil
import logging
import string
import time
import stat
import urllib2
import shlex
import subprocess
import optparse
try:
    from lxml import etree as et
except:
    from xml.etree import ElementTree as et

logging.basicConfig(level=logging.DEBUG, filename='module.log')

from bq.core.commands.configfile import ConfigFile

from module_env import MODULE_ENVS, ModuleEnvironmentError

ENV_MAP = dict ([ (env.name, env) for env in MODULE_ENVS ])

def check_exec (path, fix = True):
    if os.access (path, os.X_OK):
        return
    print "%s is not executable"
    if fix:
        os.chmod (path, 0744)


log = logging.getLogger('bq.runtime')

def strtobool(x):
    return {"true": True, "false": False}.get(x.lower())

def strtolist(x, sep=','):
    return [ s.strip() for s in x.split(sep)]


class RunnerException(Exception):
    """Exception in the runners"""
    pass

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
    environments =""
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

    def log (self, msg):
        #if self.options.verbose:
        log.info( msg )

    def read_config (self, **kw):
        """Initial state of a runner.  The module-runtime.cfg is read
        and the relevent runner section is applied.  The environment
        list is created and setup in order to construct the
        environments next
        """
        self.config = {}
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
        for k,v in section.items():
            setattr(self,k,v)

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


    def create_environments(self,  **kw):
        """Build the set of environment managers from the config
        """
        if isinstance(self.environments,basestring):
            self.environments = strtolist(self.environments)
        envs = []
        for name in self.environments:
            env = ENV_MAP.get (name, None)
            if env is not None:
                envs.append (env(self))
        self.environments = envs


    def setup_environments(self, **kw):
        for env in self.environments:
            env.setup_environment (self, **kw)

    def teardown_environments(self, **kw):
        for env in reversed(self.environments):
            env.teardown_environment (self, **kw)


    def process_args(self,  **kw):
        """Deal with any arguments and prepare the mex and module
        returns a callable for the next actions
        """

        self.options, arguments = self.parser.parse_args()
        self.named_args = {}
        
        command = arguments.pop()
        self.command = command
        # Scan argument looking for named arguments
        for arg in reversed(arguments):
            tag, sep, val = arg.partition('=')
            if sep != '=':
                break
            self.named_args[tag] = val
            arguments.remove(arg)

        # Add remaining arguments to the executable line
        # Ensure the loaded executable is a list
        if isinstance(self.executable, str):
            self.executable = shlex.split(self.executable)
        self.executable.extend (arguments)

        mexurl  = self.named_args.get ('mex_url', None)
        modurl  = self.named_args.get ('module_url', None)
        if mexurl:
            self.mex_url = mexurl
        #    handle = urllib2.urlopen(mex)
        #    self.mex = et.parse(handle).getroot()
        #    handle.close()
        if modurl:
            self.module_url = modurl
        #    handle = urllib2.urlopen(mod)
        #    self.module = et.parse(handle).getroot()
        #    handle.close()

        command = getattr (self, 'command_%s' % command, None)
        return command


    ##################################################
    # Command sections
    # A command is launched with last argument on the command line of the launcher
    # Each command must return the either the next fommand to run or None to stop
    # Derived classes should overload these functions

    def command_start(self, **kw):
        #if self.mexhandled is False:
        self.setup_environments()
        return self.command_execute

    def command_execute(self, **kw):
        """Execute the internal executable"""
        return self.command_finish

    def command_finish(self, **kw):
        """Cleanup the environment and perform any needed actions
        after the module completion
        """
        self.teardown_environments()
        return None
    def command_kill(self, **kw):
        """Kill the running module if possible
        """
        return False

    def command_status(self, **kw):
        return None

    def main(self, **kw):
        # Find and read a config file for the module
        try:
            self.read_config(**kw)
            self.create_environments(**kw)
            command = self.process_args(**kw)
            self.process_config(**kw)

            while command:
                log.info("COMMAND_RUNNER %s" % command)
                command = command(**kw)
            return 0
        except ModuleEnvironmentError, e:
            log.exception( "Problem occured in module")
        except RunnerException, e:
            log.exception("during the command %s:" % (command))
        except:
            log.exception ("Unknown exeception")

        return 1

class CommandRunner(BaseRunner):
    """Small extension to BaseRunner to actually execute the script.
    """
    name = "command"

    def read_config (self, **kw):
        super(CommandRunner, self).read_config (**kw)
        self.log("CommandRunner: read_config")
        self.load_section('command', self.module_cfg) # Runner's name
        
    
    def command_execute(self, **kw):
        if not self.options.dryrun:
            print "Running '%s' in %s" % (' '.join(self.executable), os.getcwd())
            # Check 
            if len(self.executable) > 1:
                #check_exec (self.executable[0])
                retcode = subprocess.call (self.executable,
                                  stdout = open("%s.log" % self.executable[0],'w'),
                                  stderr = open("%s.err" % self.executable[0],'w'),
                                  #stdin  = open("/dev/null"),
                                  shell  = (os.name == "nt")
                                  )
                if retcode:
                    raise RunnerException (
                        "Command %s gave non-zero return code %s" %
                        (" ".join(self.executable), retcode))
        else:
            self.log ("Dryrun of '%s'" % ' '.join(self.executable))
        
        return self.command_finish





if __name__ == "__main__":
    CommandRunner().main()
    sys.exit(0)
