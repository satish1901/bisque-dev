#!/usr/bin/env python
import os
import sys
import subprocess
import argparse
import glob
import shutil
import urllib

PIP_LIST=[
    ('pip', None), 
    ('setuptools', None)
]
if os.name == 'nt':
    PIP_LIST=[
        ('numpy-1.10.4+mkl-cp27-none-win_amd64.whl', 'http://flour.ece.ucsb.edu:8080/~bisque/wheels/numpy-1.10.4+mkl-cp27-none-win_amd64.whl'), 
    ]

shell = False
if os.name == 'nt':
    shell = True

# installs pip wheels from a URL or pypy
def install_package(filename, URL, command):
    print 'Installing %s\n'%filename
    if URL is not None:
        urllib.urlretrieve (URL, filename)
    subprocess.call (command, shell=shell)
    if URL is not None:
        try:
            os.remove(filename)
        except OSError:
            print 'Warning: could not remove %s\n'%filename

# installs package using python setup file
def install_setup(filename, URL=None):
    return install_package(filename, URL, ['python', filename])

# installs package using easy_install
def install_easy(filename, URL=None):
    return install_package(filename, URL, ['easy_install', filename])

# installs package using pip wheels from a URL or pypy
def install_pip(filename, URL=None):
    return install_package(filename, URL, ["pip", "install", "-U", filename])


def main():
    parser = argparse.ArgumentParser(description='Boostrap bisque')
    parser.add_argument("--repo", default="http://biodev.ece.ucsb.edu/hg/bisque-stable")
    parser.add_argument("bqenv", nargs="?", default="bqenv")
    parser.add_argument('install', nargs="?", default='server', choices=['server', 'engine'])
    args = parser.parse_args()
    
    
    # check python version
    if not sys.version_info[:2] == (2, 7):
        print "BisQue requires python 2.7.X but found %s"%(sys.version)
        return 1

    print "\n----------------------------------------------------------"
    print 'Creating virtual environment for BisQue installation'
    print "----------------------------------------------------------\n"
    if os.name != 'nt':
        r = subprocess.call(["virtualenv", args.bqenv])
        activate = os.path.join(args.bqenv, 'bin', 'activate_this.py')
    else:
        # due to a bug in the windows python (~2.7.8) virtual env can't install pip and setuptools
        # so we have to first create a virtualenv without setuptools and pip and then
        # install them into the virtualenv
        r = subprocess.call(["virtualenv", args.bqenv, '--no-setuptools'])
        activate = os.path.join(args.bqenv, 'Scripts', 'activate_this.py')

    print 'Activating virtual environment using: %s\n'%activate
    execfile (activate, dict(__file__=activate))

    os.environ['VIRTUAL_ENV'] = os.path.abspath(args.bqenv)

    # install pip and setuptools if under windows, due to a bug
    if os.name == 'nt':
        print "\n----------------------------------------------------------"
        print 'Re-Installing pip and setuptools to fix virtualenv error under windows'
        print "----------------------------------------------------------\n"
        install_setup("get-pip.py", "https://bootstrap.pypa.io/get-pip.py")
        install_easy('pywin32-220.win-amd64-py2.7.exe', "http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20220/pywin32-220.win-amd64-py2.7.exe?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fpywin32%2Ffiles%2Fpywin32%2FBuild%2520220%2F&ts=1454466819&use_mirror=iweb")
        
    print "\n----------------------------------------------------------"
    print 'Installing additional packages'
    print "----------------------------------------------------------\n"
    for pkg,URL in PIP_LIST:
        install_pip(pkg, URL)
    
    # ensure mercurial is available  
    try:
       r = subprocess.call(['hg', '--version'], shell=shell)
    except OSError:
        install_pip('mercurial')

    print "********************************"
    print "**     Fetching BisQue        **"
    print "********************************"
    print "Cloning: ", args.repo
    print
    subprocess.call(['hg', 'clone', args.repo, 'tmp'], shell=shell)
    for df in glob.glob('tmp/*') + glob.glob('tmp/.hg*'):
        if not os.path.exists(os.path.basename(df)):
            shutil.move (df, os.path.basename(df))

    print "********************************"
    print "**  Installing requirements   **"
    print "********************************"
    print
    print
    #subprocess.call(['pip', 'install', '--trusted-host', 'biodev.ece.ucsb.edu', '-i', 'http://biodev.ece.ucsb.edu/py/bisque/dev/+simple', 'Paste==1.7.5.1+bisque2'], shell=shell)
    #subprocess.call(['pip', 'install', '--trusted-host', 'biodev.ece.ucsb.edu', '-r', 'requirements.txt'], shell=shell)
    subprocess.call(['pip', 'install',  '-r', 'requirements.txt'], shell=shell)

    print "**************************************************************"
    print "To finish installation, please, execute the following commands"
    print "Use 'server' for a full BisQue server"
    print "Use 'engine' to run a module serving a remote BisQue"
    print "Please visit:"
    print "  http://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions"
    print "for more information"
    print "*************************************************************\n"
    if os.name == 'nt':
        print "bqenv\\Scripts\\activate.bat"
    else:
        print "source bqenv/bin/activate"

    print "paver setup    [server|engine]"
    print "bq-admin setup [server|engine]"
    print "bq-admin deploy public"


    # dima: we should run all the above mentioned commands right here
    #args.install




if __name__=="__main__":
    main()
