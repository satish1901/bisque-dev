#!/usr/bin/env python  

import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess, shutil,glob

def extend_parser(optparse_parser):
    optparse_parser.add_option('--repo', help='Specify a repository to bootstrap from', 
                               default= 'http://biodev.ece.ucsb.edu/hg/bisque-stable')
    optparse_parser.add_option('--engine', action="store_true",
                               help='Specify a repository to bootstrap from', 
                               default= False)

def adjust_options(options, args):
    options.no_site_packages=True

def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
       bin = 'bin'
    
    subprocess.call([os.path.join(home_dir, bin, 'easy_install'),
                     '-i', 'http://www.turbogears.org/2.1/downloads/current/index',
                     'tg.devtools'])
    subprocess.call([os.path.join(home_dir, bin, 'easy_install'),
                     'paver'])

    if options.engine:
       engine_install(options, home_dir)
    else:
       bisque_install(options, home_dir)
      

def engine_install(options, home_dir):
    subprocess.call([os.path.join(home_dir, bin, 'pip'),
                     '-i', 'http://biodev.ece.ucsb.edu/binaries/depot',
                     'bqengine'])
    print "*********************************"
    print "* Execute the following commands*"
    print "source bqenv/bin/activate"
    print "bq-admin setup engine"

def bisque_install(options, home_dir):
    subprocess.call([os.path.join(home_dir, bin, 'easy_install'),
                     'mercurial'])

    print "********************************"
    print "**     Fetching bisque        **"
    print "********************************"
    print 
    subprocess.call([os.path.join(home_dir, bin, 'hg'),
                     'clone', options.repo, 'tmp'])
    for df in glob.glob('tmp/*') + glob.glob('tmp/.hg*'):
        if not os.path.exists(os.path.basename(df)):
            shutil.move (df, os.path.basename(df))
    print "********************************"
    print "**Dowload and layout completed**"
    print "********************************"
    print 
    print "*********************************"
    print "* Execute the following commands*"
    print "source bqenv/bin/activate"
    print "paver setup"
    print "bq-admin setup"

    #subprocess.call([os.path.join(home_dir, bin, 'paver'), 'setup'])
    print "Please visit http://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions and follow instructions there"
"""))

class make_bootstrap():
    desc = "Make a bootstrap script"
    def __init__(self, version):
        pass

    def run(self):
        f = open('bisque-bootstrap.py', 'w').write(output)

#mode: python
