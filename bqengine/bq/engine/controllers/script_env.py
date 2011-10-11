#
"""
Allow remapping of arguments to the Module


"""
import os,sys
import shlex
import string
import subprocess
from module_env import BaseEnvironment, ModuleEnvironmentError

class ScriptEnvironment(BaseEnvironment):
    """Run an external script for environment prep
    """
    name       = "Script"
    config    = {'script':""}

    def __init__(self, runner, **kw):
        super(ScriptEnvironment, self).__init__(runner, **kw)
        
    def process_config(self, runner):
        """Runs before the normal command but after read the config"""

        script = string.Template(runner.script).safe_substitute(runner.named_args)
        script = string.Template(script).safe_substitute(runner.__dict__)
        self.script = shlex.split(script, posix=(os.name != "nt"))
        runner.executable=list(self.script) + ['start']
        
    def setup_environment(self, runner):
        runner.log ("Execute setup '%s' in %s" % (" ".join (self.script + ['setup']), os.getcwd()))
        if subprocess.call(self.script + ['setup'])!=0:
            raise ModuleEnvironmentError("Error during setup")
        
    def teardown_environment(self, runner):
        runner.log ("Execute teardown '%s' in %s" % (" ".join(self.script+['teardown']), os.getcwd()))
        if subprocess.call(self.script + ['teardown'])!= 0:
            raise ModuleEnvironmentError("Error during teardown")
            
