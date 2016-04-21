# condor_run.py
#
import os, sys,shutil
import logging
import string
import subprocess
import StringIO

from bq.util.configfile import ConfigFile
from bqapi import BQSession

from command_run import CommandRunner, strtolist, AttrDict, check_exec
from condor_templates import CondorTemplates

class CondorRunner (CommandRunner):
    """A Runtime to execute a module on a condor enabled system


    """
    name     = "condor"

    transfers= []  # Condor transfers (see condor docs)
    requirements = ""  #  Condor "&& (Memory > 3000) && IsWholeMachineSlot"
    dag_template = ""
    submit_template = ""


    def __init__(self, **kw):
        super(CondorRunner, self).__init__(**kw)

    def read_config(self, **kw):
        super(CondorRunner, self).read_config(**kw)
        self.log("CondorRunner: read_config")
        self.load_section ('condor', self.bisque_cfg)
        self.load_section ('condor', self.module_cfg)
        self.load_section ('condor_submit', self.bisque_cfg)
        self.load_section ('condor_submit', self.module_cfg)

    def process_config(self, **kw):
        super(CondorRunner, self).process_config(**kw)

    def command_start(self, **kw):
        super(CondorRunner, self).command_start(**kw)

        # any listed file will be a transfer
        for mex in self.mexes:
            mex.files = mex.get('files', [])
            mex.transfers = list(mex.files)
            mex.files.append('runtime-module.cfg')
            mex.files.append('runtime-bisque.cfg')
            if mex.executable:
                mex.log_name = os.path.join(mex.rundir, "%s.log" % mex.executable[0])

        self.helper = CondorTemplates(self.sections['condor'])
        # Condor requires a real Launcher (executable) in order
        # to post process. If it does not exist we create a small stub
        topmex = self.mexes[0]
        executable = topmex.executable
        if len(self.mexes)>1:
            # multimex
            executable = self.mexes[1].executable

        postargs=[]
        if self.options.verbose:
            postargs.append('-v')
        if self.options.debug:
            postargs.append('-d')
        if self.options.dryrun:
            postargs.append('-n')
        postargs.append ('staging_id=%s' % topmex.staging_id)
        postargs.append ('staging_path=%s' % topmex.staging_path)
        postargs.extend ([ '%s=%s' % (k,v) for k,v in topmex.named_args.items()
                           if k!='staging_id' and k!='staging_path'])
        postargs.append('mex_url=%s' % topmex.mex_url)
        postargs.append('bisque_token=%s' % topmex.bisque_token)
        #postargs.append('job_return= $RETURN')
        postargs.append('$RETURN')
        postargs.append ('finish')

        for mex in self.mexes:
            mex_vars = dict(mex)
            mex_vars.update(mex.named_args)
            mex_vars.update(self.sections['condor'])
            mex_vars.update(self.sections['condor_submit'])
            if mex.get('launcher') is None:
                mex.launcher = self.helper.construct_launcher(mex_vars)
                check_exec (mex.launcher) # Esnure this launcher is executable
            mex.launcher = os.path.basename(mex.launcher)

        self.log("Creating submit file")

        top_vars = dict(topmex)
        top_vars.update(topmex.named_args)
        top_vars.update(self.sections['condor'])
        top_vars.update(self.sections['condor_submit'])
        top_vars.update(
            executable   = executable[0],
            #arguments   = ' '.join (self.executable[1:]),
            #transfers   = ",".join(self.transfers),
            mexes        = self.mexes,
            post_exec    = topmex.launcher,
            post_args    = " ".join (postargs),
            condor_submit= "\n".join(["%s=%s"%(k,v)
                                      for k,v in self.sections['condor_submit'].items()])
            )
        self.helper.prepare_submit(top_vars)

        # Immediately go to execute
        return self.command_execute

    def command_execute(self, **kw):
        cmd = ['condor_submit_dag', self.helper.dag_path]
        process = dict(command_line = cmd, mex = self.mexes[0])
        self.log( "SUBMIT %s in %s " % (cmd, self.mexes[0].get('staging_path')))
        if not self.options.dryrun:
            submit =  subprocess.Popen (cmd, cwd=self.mexes[0].get('staging_path'),
                                         stdout = subprocess.PIPE)
            out, err = submit.communicate()

            if submit.returncode != 0:
                self.command_failed(process, submit.returncode)

        # Don't do anything after execute
        return None

    def command_finish(self, **kw):
        # Cleanup condor stuff and look for error files.

        topmex = self.mexes[0]
        #job_return = int(self.mexes[0].named_args['job_return'])
        job_return = int(topmex.arguments.pop())
        if job_return != 0:
            if self.session is None:
                mex_url = topmex.named_args['mex_url']
                token   = topmex.named_args['bisque_token']
                self.session = BQSession().init_mex(mex_url, token)
            # Possible look for log files and append to message here
            #if os.path.exists(''):
            #    pass
            self.session.fail_mex(msg = 'job failed with return code %s' % job_return)
            return None

        return super(CondorRunner, self).command_finish(**kw)

    def command_failed(self, process, retcode):
        """Update the bisque server  with a failed command for a mex"""
        mex = process['mex']
        command = " ".join(process['command_line'])
        msg = "%s: returned (non-zero) %s" % (command, retcode)
        self.log(msg, logging.ERROR)
        # update process mex
        if self.session is None:
            self.session = BQSession().init_mex(self.mexes[0].mex_url, self.mexes[0].bisque_token)
        if self.session.mex.value not in ('FAILED', 'FINISHED'):
            self.session.fail_mex (msg)


    def command_kill(self, **kw):
        """Kill the running module if possible
        """
        return False

    def command_status(self, **kw):
        message =  subprocess.Popen (['condor_q', ],
                          cwd=self.mexes[0].get('staging_path'),
                          stdout = subprocess.PIPE).communicate()[0]
        self.log ("status = %s " % message)
        return None



class CondorMatlabRunner(CondorRunner):

   def process_config(self, **kw):
        super(CondorMatlabRunner, self).process_config(**kw)



