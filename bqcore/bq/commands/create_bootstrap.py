#!/usr/bin/env python  

import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess, shutil,glob

def extend_parser(optparse_parser):
    optparse_parser.add_option('--repo', help='Specify a repository to bootstrap from', 
                               default= 'http://biodev.ece.ucsb.edu/hg/bisque-stable')

    optparse_parser.add_option('--tg', help='Specify turbogears repo to bootstrap', 
                                default = 'http://www.turbogears.org/2.1/downloads/current/index',)

def adjust_options(options, args):
    if len(args) == 0:
        print "installing in bqenv"
        args.append( 'bqenv' )


def after_install(options, home_dir):
    if sys.platform == 'win32':
        bindir = 'Scripts'
    else:
       bindir = 'bin'
    
    subprocess.call([os.path.join(home_dir, bindir, 'easy_install'), 'paver'])
    subprocess.call([os.path.join(home_dir, bindir, 'easy_install'),
                     '-i', options.tg, 'tg.devtools'])

    bisque_install(options, home_dir, bindir)

def bisque_install(options, home_dir, bindir):
    try:
       r = subprocess.call(['hg', '--version'])
    except OSError:
       r = 1

    if r !=  0:
         subprocess.call([os.path.join(home_dir, bindir, 'easy_install'), 'mercurial'])
         mercurial = os.path.join(home_dir, bindir, 'hg')
    else:
         mercurial = 'hg'


    print "********************************"
    print "**     Fetching bisque        **"
    print "********************************"
    print "Cloning: ", options.repo
    print 
    subprocess.call([mercurial, 'clone', options.repo, 'tmp'])
    for df in glob.glob('tmp/*') + glob.glob('tmp/.hg*'):
        if not os.path.exists(os.path.basename(df)):
            shutil.move (df, os.path.basename(df))
    print "********************************"
    print "**Dowload and layout completed**"
    print "********************************"
    print 
    print "*********************************"
    print "* Execute the following commands*"
    if sys.platform == 'win32':
        print "bqenv\\\\Scripts\\\\activate.bat"
    else:
        print "source bqenv/bin/activate"
    print "paver setup    [engine]"
    print "bq-admin setup [engine]"

    print "Please visit http://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions and follow instructions there"
"""))

class make_bootstrap():
    desc = "Make a bootstrap script"
    def __init__(self, version):
        pass

    def run(self):
        f = open('bisque-bootstrap.py', 'w').write(output)

#mode: python
