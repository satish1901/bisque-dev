#
"""



"""
import os,sys
from module_env import BaseEnvironment, ModuleEnvironmentError
from bq.util.copylink import copy_link

STAGING_BASE="~/staging"


import shutil
# def copy_link (*largs):
#     largs = list (largs)
#     d = largs.pop()

#     for f in largs:
#         try:
#             dest = d
#             if os.path.isdir (d):
#                 dest = os.path.join (d, os.path.basename(f))
#             print ("linking %s to %s"%(f,dest))
#             if os.path.exists(dest):
#                 print ("Found existing file %s: removing .." % dest)
#                 os.unlink (dest)
#             os.link(f, dest)
#         except (OSError, AttributeError), e:
#             print ("Problem in link %s .. trying copy" % e)
#             if os.path.isdir(f):
#                 shutil.copytree(f, dest)
#             else:
#                 shutil.copy2(f, dest)

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

        setup_dir = os.getcwd()
        for mex in runner.mexes:
            mex.initial_dir = mex.module_dir = setup_dir
            mex.files = mex.get('files', [])
            if isinstance(mex.files, basestring):
                mex.files =  strtolist(mex.files)


            staging_base = mex.get('runtime.staging_base', STAGING_BASE)
            mex.staging_path=mex.named_args.get ('staging_path')
            mex.staging_id=mex.named_args.get ('staging_id')

            if not mex.staging_id:
                if mex.staging_path:
                    mex.staging_id = mex.staging_path.rsplit('/',1)[1]
                elif mex.get('mex_url'): # Use the MEX_ID as the staging ID
                    mexid = mex.mex_url.rsplit('/', 1)[1]
                    mex.staging_id = mexid

            runner.log ( 'staging_id = %s' % mex.staging_id)
            if not mex.staging_id:
                raise ModuleEnvironmentError ("No Staging_id given and cannot determine one (missing staging_path or mex)")

            if not mex.staging_path:
                mex.staging_path = os.path.abspath(os.path.expanduser(
                    os.path.join (staging_base, mex.staging_id)))

            mex.rundir = mex.staging_path
            runner.log ( 'staging_path = %s' % mex.staging_path)

    def _staging_setup(self, runner, mex, create=True, **kw):

        runner.log ( 'staging_path = %s' % mex.staging_path)
        if create and not os.path.exists (mex.staging_path) :
            os.makedirs (mex.staging_path)

    def _filelist(self, files, **kw):
        if os.name != 'nt':
            return files
        fs = []
        for f in files:
            if not os.path.exists(f) and os.path.exists(f + '.exe'):
                fs.append(f+'.exe')
                continue
            if not os.path.exists(f) and os.path.exists(f + '.bat'):
                fs.append(f+'.bat')
                continue
            fs.append(f)
        return fs

    def setup_environment(self, runner, **kw):
        """Create the staging area and place the executable there
        """
        runner.log ("staged environment setup")
        for mex in runner.mexes:
            self._staging_setup(runner, mex)
            if mex.get('files'):
                files = self._filelist(mex.files)
                runner.log ("copying %s: %s to %s" % (mex.initial_dir, files, mex.staging_path))
                copy_link(*(files + [ mex.staging_path ]))
        return {'HOME': mex.staging_path}

    def teardown_environment(self, runner, **lw):
        """Remove the staging area
        """
        for mex in runner.mexes:
            self._staging_setup(runner, mex, False)

            if mex.initial_dir:
                os.chdir (mex.initial_dir)

            if not runner.options.dryrun and not runner.options.debug:
                runner.log( "Cleaning %s " % mex.staging_path)
                shutil.rmtree (mex.staging_path)
            else:
                runner.log('not removing %s for debug or dryrun' % mex.staging_path)
