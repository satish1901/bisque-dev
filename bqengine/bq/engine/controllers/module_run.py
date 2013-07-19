#!/usr/bin/env python
#
import os,sys
import subprocess 
import logging

from bq.util.configfile import ConfigFile
from module_env import ModuleEnvironmentError
from command_run import CommandRunner
from condor_run import CondorRunner

MODULE_RUNNERS = [CommandRunner, CondorRunner]
RUNNER_MAP     = dict([(r.name, r) for r in MODULE_RUNNERS ])

log = logging.getLogger('bq.engine_service.modulerunner')

class ModuleRunner(object):
    """Top Level runner and entry point for the Runners and Environments

    The module runner is responsible for reading the module-runtime.cfg
    and choosing the proper runner based on system and module
    preferences.
    i.e.
      runtime-module.cfg:
        runner = condor, command

      site.cfg:
        engine_runner = command
    """
    system_runners = ["command"]
    
    def __init__(self, **kw):
        self.module_runners = []

    def choose_runner (self, **kw):
        # Choose a runner
        if os.path.exists('runtime-module.cfg'):
            cfg = ConfigFile('runtime-module.cfg')
            launcher = cfg.get (None, 'launcher')
            if launcher and os.path.abspath(sys.argv[0]) != os.path.abspath(launcher):
                if os.path.exists (launcher):
                    # Given launcher
                    cmd = launcher.split(' ')
                    cmd.extend (sys.argv[1:])
                    log.debug( "Calling %s" % cmd )
                    subprocess.call (cmd)
                    return None
                log.warn( "Missing launcher: %s" % launcher)
                return None
        else:
            log.error( "Missing runtime-module.cfg" )
            return None            
            
        log.debug('Path: %s'%os.getcwd())         
            
        runners = cfg.get(None, 'runtime.platforms')
        if runners is None:
            raise ModuleEnvironmentError("Must define legal platforms:  runtime.platforms in module config")
        log.debug('Module runners: %s'%runners)
        self.module_runners = [r.strip() for r in runners.split(',')]

        if os.path.exists('runtime-bisque.cfg'):
            cfg = ConfigFile('runtime-bisque.cfg')
            runners = cfg.get(None, 'runtime.platforms')
            log.debug('System runners: %s'%runners)
            self.system_runners = [r.strip() for r in runners.split(',')]

        # Determine best platform for module by comparing system platforms 
        # and module platforms.  The platforms are listed in order
        # of preference based on the system preferences
        for run_platform in self.system_runners:
            if run_platform in self.module_runners:
                log.info( "Choosing Runtime Platform: %s" % run_platform)
                return RUNNER_MAP[run_platform]
        return None

    def check(self, **kw):
        runner_class = self.choose_runner()
        if runner_class:
            runner = runner_class(**kw)
            return runner.check(**kw)
        return False

    def main(self, **kw):
        """Called when module is launched.
        """
        runner_class = self.choose_runner()
        if runner_class is not None:
            runner = runner_class(**kw)
            log.debug( "ModuleRunner.Main")
            return runner.main(**kw)

if __name__ == "__main__":
    log.info( "ModuleRunner: main %s" % " ".join(sys.argv) )
    ModuleRunner().main()
    sys.exit(0)
