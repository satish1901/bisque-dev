#
"""
Use a script specified by the user to run setup, run, and teardown


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
        
    def create_script(self, mex):
        """Runs before the normal command but after read the config"""
        script = string.Template(runner.script).safe_substitute(mex.named_args)
        script = string.Template(script).safe_substitute(mex.__dict__)
        script = shlex.split(script, posix=(os.name != "nt"))
        mex.executable=list(script) + ['start']
        return script
        
    def setup_environment(self, runner):
        for mex in runner.mexes:
            if mex.executable:
                script = self.create_script(mex)
                runner.log ("Execute setup '%s' in %s" % (" ".join (script + ['setup']), os.getcwd()))
                if subprocess.call(script + ['setup'])!=0:
                    raise ModuleEnvironmentError("Error during setup")
        
    def teardown_environment(self, runner):
        for mex in runner.mexes:
            if mex.executable:
                script = self.create_script(mex)
                runner.log ("Execute teardown '%s' in %s" % (" ".join(script+['teardown']), os.getcwd()))
                if subprocess.call(script + ['teardown'])!= 0:
                    raise ModuleEnvironmentError("Error during teardown")
            
