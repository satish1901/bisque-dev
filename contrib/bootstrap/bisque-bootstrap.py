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
    
    shell = False
    print 'Creating virtual environment for BisQue installation\n'
    if os.name != 'nt':
        r = subprocess.call(["virtualenv", args.bqenv])
        activate = os.path.join(args.bqenv, 'bin', 'activate_this.py')
    else:
        # due to a bug in the windows python (~2.7.8) virtual env can't install pip and setuptools
        # so we have to first create a virtualenv without setuptools and pip and then
        # install them into the virtualenv
        r = subprocess.call(["virtualenv", args.bqenv, '--no-setuptools'])
        activate = os.path.join(args.bqenv, 'Scripts', 'activate_this.py')        
        shell = True        


    print 'Activating virtual environment using: %s\n'%activate
    execfile (activate, dict(__file__=activate))

    os.environ['VIRTUAL_ENV'] = os.path.abspath(args.bqenv)

    # install pip and setuptools if under windows, due to a bug
    if os.name == 'nt':
        print 'Installing pip and setuptools to fix virtualenv error under windows\n'
        import urllib
        urllib.urlretrieve ("http://raw.github.com/pypa/pip/master/contrib/get-pip.py", "get-pip.py")
        subprocess.call (['python', 'get-pip.py'], shell=shell)        

    # dima, maybe we don't need this given previous lines?
    for install in PIP_LIST:
        subprocess.call (["pip", "install", "-U", install], shell=shell)

    try:
       r = subprocess.call(['hg', '--version'], shell=shell)
    except OSError:
        subprocess.call (["pip", "install", "-U", 'mercurial'], shell=shell)

    print "********************************"
    print "**     Fetching bisque        **"
    print "********************************"
    print "Cloning: ", args.repo
    print
    subprocess.call(['hg', 'clone', args.repo, 'tmp'], shell=shell)
    for df in glob.glob('tmp/*') + glob.glob('tmp/.hg*'):
        if not os.path.exists(os.path.basename(df)):
            shutil.move (df, os.path.basename(df))

    print "********************************"
    print "**Dowload and layout completed**"
    print "********************************"
    print
    print
    subprocess.call(['pip', 'install', '-r', 'requirements.txt'], shell=shell)

    print "********************************************************"
    print "* To finish installation execute the following commands*"
    if os.name == 'nt':
        print "bqenv\\Scripts\\activate.bat"
    else:
        print "source bqenv/bin/activate"
    print "paver setup    [server|engine]"
    print "bq-admin setup [server|engine]"

    print "Please visit http://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions and follow instructions there"




if __name__=="__main__":
    main()
