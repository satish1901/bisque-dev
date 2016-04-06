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
except Exception:
    from xml.etree import ElementTree as et
from bq.util.configfile import ConfigFile
from bqapi import BQSession

from module_env import MODULE_ENVS, ModuleEnvironmentError
from mexparser import MexParser

ENV_MAP = dict ([ (env.name, env) for env in MODULE_ENVS ])
logging.basicConfig(level=logging.DEBUG, filename='module.log')
log = logging.getLogger('bq.engine_service.runtime')

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
    prerun = None      # entrypoint for prerun
    postrun = None     # entrypoint for postrun

    def __init__(self, **kw):
        self.parser =  optparse.OptionParser()
        self.parser.add_option("-n","--dryrun", action="store_true",
                               default=False)
        self.parser.add_option('-v', '--verbose', action="store_true",
                               default=False)
        self.parser.add_option('-d', '--debug', action="store_true",
                               default=False)
        self.session = None

    def log (self, msg, level = logging.INFO):
        #if self.options.verbose:
        log.log( level, msg )

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
            log.warn ('Unknown environment: %s ignoring' % name)
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
        self.pool = kw.pop('pool', None)
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
                           rundir = self.rundir,
                           prerun=None,
                           postrun=None))
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
            mex_inputs  = mexparser.prepare_inputs(self.module_tree, self.mex_tree, self.bisque_token)
            module_options = mexparser.prepare_options(self.module_tree, self.mex_tree)
            
            argument_style = module_options.get('argument_style', 'positional')            
            # see if we have pre/postrun option            
            self.prerun = module_options.get('prerun_entrypoint', None)
            self.postrun = module_options.get('postrun_entrypoint', None)
            
            topmex.named_args.update ( mexparser.prepare_mex_params( mex_inputs ) )
            topmex.executable.extend(mexparser.prepare_mex_params (mex_inputs, argument_style))
            topmex.rundir = self.rundir
            #topmex.options = module_options
            # remember topmex executable for pre/post runs
            self.executable = topmex.executable

            # Create a nested list of  arguments  (in case of submex)
            submexes = self.mex_tree.xpath('/mex/mex')
            for mex in submexes:
                sub_inputs = mexparser.prepare_inputs(self.module_tree, mex)
                submex = AttrDict(self.config)
                submex.update(dict(named_args=dict(topmex.named_args),
#                                   arguments =list(topmex.arguments),
                                   executable=list(executable), #+ topmex.arguments,
                                   mex_url = mex.get('uri'),
                                   bisque_token = self.bisque_token,
                                   rundir = self.rundir))
                #if argument_style == 'named':
                #    submex.named_args.update ( [x.split('=') for x in sub_inputs] )
                submex.named_args.update(mexparser.prepare_mex_params(sub_inputs))
                submex.executable.extend(mexparser.prepare_mex_params(sub_inputs, argument_style))
                self.mexes.append(submex)
            # Submex's imply that we are iterated.
            # We can set up some options here and remove any execution
            # for the top mex.
            topmex.iterables = len(self.mexes) > 1 and mexparser.process_iterables(self.module_tree, self.mex_tree)
            if topmex.iterables:
                topmex.executable = None

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

        # add empty "outputs" section in topmex
        if self.session is None:
            self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
        self.session.update_mex(status='starting', tags=[{'name':'outputs'}])

        if self.mexes[0].iterables:
            if self.session is None:
                self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
            self.session.update_mex('running parallel')
            
        # if there is a prerun, run it now
        if self.prerun:
            log.info("prerun starting")
            self.command_single_entrypoint(self.prerun, **kw)
            log.info("prerun completed")
            
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

        # if there is a postrun (aka "reduce phase"), run it now
        if self.postrun:
            log.info("postrun starting")
            self.command_single_entrypoint(self.postrun, **kw)
            log.info("postrun completed")

        self.teardown_environments()

        if self.mexes[0].iterables:
            if self.session is None:
                self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
            # outputs
            #   mex_rul
            #   dataset_url
            tags = None
            itrs = []
            for iter_name, iter_val, iter_type in self.mexes[0].iterables:
                itrs.append( { 'name': iter_name, 'value': iter_val, 'type': iter_type } )
            itrs.append ( { 'name': 'mex_url', 'value': self.mexes[0].mex_url, 'type' : 'mex' })
            tags = [ { 'name' : 'outputs',
                       'tag' : itrs } ]


            self.session.finish_mex(tags = tags)
        return None

    def command_single_entrypoint(self, entrypoint, **kw):
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
        canrun = executable and which(executable[0]) is not None
        if not canrun:
           log.error ("Executable cannot be run %s" % executable)
        return canrun

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

#import multiprocessing
#log = multiprocessing.log_to_stderr()
#log.setLevel(multiprocessing.SUBDEBUG)


class CommandRunner(BaseRunner):
    """Small extension to BaseRunner to actually execute the script.
    """
    name = "command"

    def __init__(self, **kw):
        super(CommandRunner, self).__init__(**kw)

    def read_config (self, **kw):
        super(CommandRunner, self).read_config (**kw)
        self.log("CommandRunner: read_config")
        self.load_section('command', self.module_cfg) # Runner's name


    def process_config(self, **kw):
        super(CommandRunner, self).process_config(**kw)
        for mex in self.mexes:
            if not mex.executable:
                mex.log_name = os.path.join(mex.rundir, "topmex.log")
            else:
                mex.log_name = os.path.join(mex.rundir, "%s.log" % mex.executable[0])

    def command_single_entrypoint(self, entrypoint, **kw):
        "Execute specific entrypoint"
        mex = self.mexes[0]   # topmex
        command_line = list(self.executable)
        # add entrypoint to command_line
        command_line += [ '--entrypoint', entrypoint ]
        # enclose options that start with '-' in quotes to handle numbers properly (e.g., '-3.3')
        command_line = [ tok if tok.startswith('--') or not tok.startswith('-') else '"%s"'%tok for tok in command_line ]
        rundir = mex.get('rundir')
        if self.options.dryrun:
            self.log( "DryRunning '%s' in %s" % (' '.join(command_line), rundir))
        else:
            self.log( "running '%s' in %s" % (' '.join(command_line), rundir))            
            proc = dict(command_line = command_line, logfile = mex.log_name, rundir = rundir, mex=mex)
            
            from bq.engine.controllers.execone import execone            
            retcode = execone (proc)
            if retcode:
                self.command_failed(proc, retcode)
        return None

    def command_execute(self, **kw):
        "Execute the commands locally specified the mex list"
        self.execute_kw = kw
        self.processes = []
        for mex in self.mexes:
            if not mex.executable:
                log.info ('skipping mex %s ' % mex)
                continue
            command_line = list(mex.executable)
            #command_line.extend (mex.arguments)
            # enclose options that start with '-' in quotes to handle numbers properly (e.g., '-3.3')
            command_line = [ tok if tok.startswith('--') or not tok.startswith('-') else '"%s"'%tok for tok in command_line ]
            rundir = mex.get('rundir')
            if  self.options.dryrun:
                self.log( "DryRunning '%s' in %s" % (' '.join(command_line), rundir))
                continue

            self.log( "running '%s' in %s" % (' '.join(command_line), rundir))
            log.info ('mex %s ' % mex)

            self.processes.append(dict( command_line = command_line, logfile = mex.log_name, rundir = rundir, mex=mex))

        # ****NOTE***
        # execone must be in engine_service as otherwise multiprocessing is unable to find it
        # I have no idea why not.
        from bq.engine.controllers.execone import execone

        if self.pool:
            log.debug ('Using async ppool %s with %s ' % (self.pool, self.processes))
            #self.pool.map_async(fun, [1,2], callback = self.command_return)
            self.pool.map_async(execone, self.processes, callback = self.command_return)
        else:
            for p in self.processes:
                retcode = execone (p)
                if retcode:
                    self.command_failed(p, retcode)
            return self.command_finish

        return None
    def command_return(self, returns):
        "collect return values when mex was executed asynchronously "
        log.info ("Command_return with %s" % returns)
        for item, retcode in enumerate(returns):
            command = self.processes[item]['command_line']
            if retcode:
                self.command_failed(self.processes[item], retcode)
        self.command_finish(**self.execute_kw)

    def command_failed(self, process, retcode):
        """Update the bisque server  with a failed command for a mex"""
        mex = process['mex']
        command = " ".join(process['command_line'])
        msg = "%s: returned (non-zero) %s" % (command, retcode)
        log.error(msg)
        # update process mex
        if self.session is None:
            self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
        if self.session.mex.value not in ('FAILED', 'FINISHED'):
            self.session.fail_mex (msg)




#if __name__ == "__main__":
#    CommandRunner().main()
#    sys.exit(0)
