#
"""



"""
import os,sys
from module_env import BaseEnvironment, ModuleEnvironmentError

STAGING_BASE="~/staging"


import shutil
def copy_link (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            print ("linking %s to %s"%(f,dest))
            if os.path.exists(dest):
                print ("Found existing file %s: removing .." % dest)
                os.unlink (dest)
            os.link(f, dest)
        except (OSError, AttributeError), e:
            print ("Problem in link %s .. trying copy" % e)
            if os.path.isdir(f):
                shutil.copytree(f, dest)
            else:
                shutil.copy2(f, dest)
def strtolist(x, sep=','):
    return [ s.strip() for s in x.split(sep)]



class StagedEnvironment(BaseEnvironment):
    """A staged environment creates a temporary staging area
    for a module run.  This is usefull for launcher that need
    local files or simply shouldn't be run in source area
    """
    name       = "Staged"
    config    = {'files':[], 'staging_path':None, 'staging_id':None}

    def __init__(self, runner, **kw):
        super(StagedEnvironment, self).__init__(runner, **kw)
        self.mex = None
        self.initial_dir = None
        
    def process_config(self, runner):
        #super(StagedEnvironment, self).process_config(self, runner)
        runner.files = self.files = strtolist(runner.files)
        staging_base = getattr(runner,'staging_base', STAGING_BASE)

        self.staging_path=runner.named_args.get ('staging_path', None)
        self.staging_id=runner.named_args.get ('staging_id', None) 

        if not self.staging_id:
            if self.staging_path:
                self.staging_id = self.staging_path.rsplit('/',1)[1]
            elif hasattr(runner, 'mex_url'): # Use the MEX_ID as the staging ID
                mexid = runner.mex_url.rsplit('/', 1)[1]
                self.staging_id = mexid

        runner.log ( 'staging_id = %s' % self.staging_id)
        if not self.staging_id:
            raise ModuleEnvironmentError ("No Staging_id given and cannot determine one (missing staging_path or mex)")

        if not self.staging_path:
            self.staging_path = os.path.abspath(os.path.expanduser(
                os.path.join (staging_base, self.staging_id)))
            
        runner.log ( 'staging_path = %s' % self.staging_path)
        runner.staging_path = self.staging_path
        runner.staging_id   = self.staging_id
        self.initial_dir = os.getcwd()
        runner.module_dir = self.initial_dir


    def _staging_setup(self, runner, create=True, **kw):
        runner.log ( 'staging_path = %s' % self.staging_path)
        
        if create and not os.path.exists (self.staging_path) :
            os.makedirs (self.staging_path)


    def setup_environment(self, runner, **kw):
        """Create the staging area and place the executable there
        """
        runner.log ("staged environment setup")
        self._staging_setup(runner)

        if hasattr(runner, 'files'):
            self.files = runner.files 
        if isinstance(self.files, str):
            self.files = [ f.strip() for f in self.files.split(',') ]

        runner.log ("copying %s: %s to %s" % (self.initial_dir, self.files, self.staging_path))
        copy_link(*self.files + [ self.staging_path ])

        os.chdir (self.staging_path)
        

    def teardown_environment(self, runner, **lw):
        """Remove the staging area
        """
        self._staging_setup(runner, False)

        if self.initial_dir:
            os.chdir (self.initial_dir)
        
        if not runner.options.dryrun and not runner.options.debug:
            runner.log( "Cleaning %s " % self.staging_path)
            shutil.rmtree (self.staging_path)

