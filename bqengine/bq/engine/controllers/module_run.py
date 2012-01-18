#!/usr/bin/env python
#
import os,sys
import subprocess 
import logging

from bq.util.configfile import ConfigFile
from command_run import CommandRunner
from condor_run import CondorRunner

MODULE_RUNNERS = [CommandRunner, CondorRunner]
RUNNER_MAP     = dict([(r.name, r) for r in MODULE_RUNNERS ])

log = logging.getLogger('bq.engine.modulerunner')

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
                    print "Calling %s" % cmd
                    subprocess.call (cmd)
                    return None
                print "Missing launcher: %s" % launcher
                return None
        else:
            print "Missing runtime-module.cfg"
            return None            
            
        log.debug('Path: %s'%os.getcwd())         
            
        runners = cfg.get(None, 'runtime.platforms')
        log.debug('Module runners: %s'%runners)
        self.module_runners = [r.strip() for r in runners.split(',')]

        if os.path.exists('runtime-bisque.cfg'):
            cfg = ConfigFile('runtime-bisque.cfg')
            runners = cfg.get(None, 'runtime.platforms')
            log.debug('System runners: %s'%runners)
            self.system_runners = [r.strip() for r in runners.split(',')]

        for sys_runner in self.system_runners:
            if sys_runner in self.module_runners:
                print "Choosing %s" % sys_runner
                return RUNNER_MAP[sys_runner]
        return None

    def main(self, **kw):
        """Called when module is launched.
        """
        runner_class = self.choose_runner()
        if runner_class is not None:
            runner = runner_class(**kw)
            print "ModuleRunner.Main"
            return runner.main(**kw)

if __name__ == "__main__":
    log.info( "ModuleRunner: main %s" % " ".join(sys.argv) )
    ModuleRunner().main()
    sys.exit(0)
