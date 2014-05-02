#!/usr/bin/env python
import os
import sys
import subprocess
import argparse
import glob
import shutil


PIP_LIST=["pip", "setuptools"]

def main():
    parser = argparse.ArgumentParser(description='Boostrap bisque')
    parser.add_argument("--repo", default="http://biodev.ece.ucsb.edu/hg/bisque-stable")
    parser.add_argument("bqenv", nargs="?", default="bqenv")

    args = parser.parse_args()

    r = subprocess.call(["virtualenv", args.bqenv])

    activate = os.path.join(args.bqenv, 'bin', 'activate_this.py')
    print "Exec file ", activate

    execfile (activate, dict(__file__=activate))

    os.environ['VIRTUAL_ENV'] = os.path.abspath(args.bqenv)

    for install in PIP_LIST:
        subprocess.call (["pip", "install", "-U", install])

    try:
       r = subprocess.call(['hg', '--version'])
    except OSError:
        subprocess.call (["pip", "install", "-U", 'mercurial'])

    print "********************************"
    print "**     Fetching bisque        **"
    print "********************************"
    print "Cloning: ", args.repo
    print
    subprocess.call(['hg', 'clone', args.repo, 'tmp'])
    for df in glob.glob('tmp/*') + glob.glob('tmp/.hg*'):
        if not os.path.exists(os.path.basename(df)):
            shutil.move (df, os.path.basename(df))

    print "********************************"
    print "**Dowload and layout completed**"
    print "********************************"
    print
    print
    #subprocess.call(['pip', 'install', '-r', 'requirements.txt'])

    print "*********************************"
    print "* Execute the following commands*"
    if sys.platform == 'win32':
        print "bqenv\\\\Scripts\\\\activate.bat"
    else:
        print "source bqenv/bin/activate"
    print "paver setup    [server|engine]"
    print "bq-admin setup [engine]"

    print "Please visit http://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions and follow instructions there"




if __name__=="__main__":
    main()
