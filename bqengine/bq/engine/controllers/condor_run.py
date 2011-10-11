# condor_run.py
#
import os, sys,shutil
import logging
import string
import subprocess
import StringIO
from bq.core.commands.configfile import ConfigFile
from command_run import CommandRunner, strtolist
from condor_templates import CondorTemplates



def check_exec (path, fix = True):
    if os.access (path, os.X_OK):
        return
    print "%s is not executable..fixing" % path
    if fix:
        os.chmod (path, 0744)

class CondorHelper(object):
    """Condor script construction

    Used to construct condor execution scripts based
    on internal or user defined templates.
    """

    
    def __init__(self, **kw):
        class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                dict.__init__(self, *args, **kwargs)
            def __getattr__(self, name):
                return self[name]
            
        self.args = AttrDict (script_exec='',
                              script_args='',
                              requirements='',
                              cmd_extra='',
                              post_exec= '',
                              post_args='',
                              transfers='',
                              staging_path='',
                              staging_id='')
        self.update(**kw)

    def update(self, **kw):
        self.condor_vars = kw.pop('condor_vars', None)
        self.args.update (kw)
        self.staging_path = self.args.staging_path
        self.staging_id   = self.args.staging_id

    def create_file(self, template, name, extra=None):
        
        path  = os.path.join (self.staging_path, name % self.args)
        content = string.Template(template)
        nfile = open(path,'w')
        nfile.write(content.safe_substitute (self.args))
        if extra:
            nfile.write(extra)
        nfile.close()
        return path

    def construct_dag (self, dag_template):
        dag = templateDAG
        if os.path.exists(dag_template):
            dag = open(dag_template).read()
        self.dag_path = self.create_file(dag, '%(staging_id)s.dag')
        self.dag_config = self.create_file(templateDAGCONF, '%(staging_id)s.dag.config')
        
    def construct_submit(self, submit):
        condor_submit = StringIO.StringIO(templateCMD)
        if os.path.exists (submit):
            condor_submit = submit

        cfg = ConfigFile(condor_submit)
        cfg.edit_update (None, self.condor_vars, self.condor_vars)
        cfg.edit_config (None, 'queue', 'queue')
        self.submit_path  = os.path.join(self.staging_path,
                             '%(staging_id)s.cmd'%self.args)
        cfg.write(self.submit_path)
        #self.submit_path = self.create_file (condor_submit, '%(staging_id)s.cmd',
        #extra = "\n".join(['%s=%s' % (k,v)
        #for k,v in self.condor_vars.items()])) 

    def construct_launcher(self):
        return self.create_file(LAUNCHER_SCRIPT, '%(staging_id)s_launch.py')
        
    def prepare_submit(self, dag_template, submit_template, **kw):
        """Create the condor required files"""
        self.update (**kw)
        self.construct_dag(dag_template)
        self.construct_submit(submit_template)

    def submit (self, **kw):
        cmd = ['condor_submit_dag', self.dag_path]
        print "SUBMIT %s in %s " % (cmd, self.staging_path)
        
        message =  subprocess.Popen (cmd, cwd=self.staging_path,
                                     stdout = subprocess.PIPE).communicate()[0]

        # Scan the message for the proper cluster number
        return message

    def status (self, cluster, **kw):
        message =  subprocess.Popen (['condor_q', ],
                          cwd=self.staging_path,
                          stdout = subprocess.PIPE).communicate()[0]
        return message
        
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

        # any listed file will be a transfer
        if not self.transfers:
            self.transfers = self.files
        #transfers = condor_cfg.get('transfers', "")
        #self.cmd_extra = condor_cfg.get('cmd_extra', None)
        #self.requirements = condor_cfg.get('requirements', None)

        self.files.append('runtime-module.cfg')
        self.files.append('runtime-bisque.cfg')
        if self.launcher is not None:
            self.files.append( self.launcher )

    def command_start(self, **kw):
        super(CondorRunner, self).command_start(**kw)

        self.helper = CondorTemplates(self.sections['condor'])
        # Condor requires a real Launcher (executable) in order
        # to post process. If it does not exist we create a small stub

        postargs=[]
        if self.options.verbose:
            postargs.append('-v')
        if self.options.debug:
            postargs.append('-d')
        if self.options.dryrun:
            postargs.append('-n')
        postargs.append ('staging_id=%s' % self.staging_id)
        postargs.append ('staging_path=%s' % self.staging_path)
        postargs.extend ([ '%s=%s' % (k,v) for k,v in self.named_args.items()
                           if k!='staging_id' and k!='staging_path'])
        postargs.append ('finish')

        condor_vars = dict(self.__dict__)
        condor_vars.update(self.sections['condor'])
        condor_vars.update(self.sections['condor_submit'])
        if self.launcher is None:
            self.launcher = self.helper.construct_launcher(condor_vars)
            self.launcher = os.path.basename(self.launcher)
        check_exec (self.launcher) # Esnure this launcher is executable
        self.log("Creating submit file")

        condor_vars.update(
            executable  = self.executable[0],
            arguments   = ' '.join (self.executable[1:]),
            transfers   = ",".join(self.transfers),
            post_exec   = self.launcher,
            post_args   = " ".join (postargs),
            condor_submit= "\n".join(["%s=%s"%(k,v)
                                      for k,v in self.sections['condor_submit'].items()])
            )
        self.helper.prepare_submit(condor_vars)
            
        # Immediately go to execute
        return self.command_execute

    def command_execute(self, **kw):
        cmd = ['condor_submit_dag', self.helper.dag_path]
        self.log( "SUBMIT %s in %s " % (cmd, self.staging_path))
        if not self.options.dryrun:
            submit =  subprocess.Popen (cmd, cwd=self.staging_path,
                                         stdout = subprocess.PIPE)
            out, err = submit.communicate()

            # Scan the message for the proper cluster number
            #return message

        # Don't do anything after execute
        return None

    def command_finish(self, **kw):
        # Cleanup condor stuff and look for error files.
        return super(CondorRunner, self).command_finish(**kw)

    def command_kill(self, **kw):
        """Kill the running module if possible
        """
        return False

    def command_status(self, **kw):
        message =  subprocess.Popen (['condor_q', ],
                          cwd=self.staging_path,
                          stdout = subprocess.PIPE).communicate()[0]
        self.log ("status = %s " % message)
        return None



class CondorMatlabRunner(CondorRunner):
    
   def process_config(self, **kw):
        super(CondorMatlabRunner, self).process_config(**kw)

   

