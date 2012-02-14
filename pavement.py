import os
import sys
import tarfile
import urllib2
from urlparse import urlparse

from paver.easy import *
from paver.setuputils import find_packages, find_package_data
import paver.misctasks
import paver.virtual

from paver.setuputils import install_distutils_tasks
install_distutils_tasks()

VERSION = '0.5.0'


options(
    setup=dict(
        name='bisque',
        version=VERSION,
        author="Center for BioImage Informatics, UCSB"
        ),

    package_data=find_package_data(),
    packages=find_packages(exclude=['ez_setup']),
    build_top=path("build"),
    build_dir=lambda: options.build_top / "bisque05",
    license=Bunch(
        extensions = set([
            ("py", "#"), ("js", "//")
        ]),
        exclude=set([
            './ez_setup',
            './data',
            './tg2env',
            './docs',
            # Things we don't want to add our license tag to
        ])
    ),
    virtualenv=Bunch(
        packages_to_install=['pip'],
        paver_command_line="required"
    ),
)

subdirs=['bqcore', 'bqserver', 'bqengine' ]

@task
def setup():
    # Hack as numpy fails to install when in setup.py dependencies
    sh('easy_install numpy==1.6.0')
    sh('easy_install numpy==1.6.0')
    # End Hack
    sh('pip install http://biodev.ece.ucsb.edu/binaries/download/tw.output/tw.output-0.5.0dev-20110906.tar.gz') 
    sh('pip install -i http://biodev.ece.ucsb.edu/binaries/depot tgext.registration2')
    sh('pip install -i http://biodev.ece.ucsb.edu/binaries/depot httplib2')
    sh('pip install --upgrade -i   http://biodev.ece.ucsb.edu/binaries/depot  Paste')

    top = os.getcwd()
    for d in subdirs:
        app_dir = path('.') / d
        os.chdir(app_dir)
        sh('python setup.py develop')
        os.chdir(top)

@task
def test():
    os.chdir('bqcore')
    sh('python setup.py test')
    
