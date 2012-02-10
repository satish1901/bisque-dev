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
        script = string.Template(mex.script).safe_substitute(mex.named_args)
        script = string.Template(script).safe_substitute(mex)
        script = shlex.split(script, posix=(os.name != "nt"))
        mex.executable=list(script) + ['start']
        return script
        
    def setup_environment(self, runner):
        for mex in runner.mexes:
            if mex.executable:
                script = self.create_script(mex)
                rundir = mex.get('rundir')
                runner.log ("Execute setup '%s' in %s" % (" ".join (script + ['setup']), rundir))
                runner.log ("logging to  %s " % mex.log_name)
                r =  subprocess.call(script + ['setup'], 
                                     stdout=open(mex.log_name, 'a'),
                                     stderr = subprocess.STDOUT,
                                     cwd = rundir)
                if r != 0:
                    raise ModuleEnvironmentError("setup returned %s"  % r)
        
    def teardown_environment(self, runner):
        for mex in runner.mexes:
            if mex.executable:
                script = self.create_script(mex)
                rundir = mex.get('rundir')
                runner.log ("Execute teardown '%s' in %s" % (" ".join(script+['teardown']), rundir))
                r = subprocess.call(script + ['teardown'],
                                    stdout=open(mex.log_name, 'a'),
                                    stderr = subprocess.STDOUT,
                                    cwd = rundir)
                if r != 0:
                    raise ModuleEnvironmentError("teardown returned %s"  % r)
            
