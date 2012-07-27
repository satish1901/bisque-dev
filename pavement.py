import os
import sys
import tarfile
import urllib2
from urlparse import urlparse

from paver.easy import *
from paver.setuputils import find_packages, find_package_data
import paver.misctasks

from paver.setuputils import install_distutils_tasks
install_distutils_tasks()

VERSION = '0.5.1'


options(
    setup=dict(
        name='bisque',
        version=VERSION,
        author="Center for BioImage Informatics, UCSB"
        ),

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Framework :: TurboGears :: Applications",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: BSD License",
        ],
    #package_data=find_package_data(),
    #packages=find_packages(exclude=['ez_setup']),
    #packages=["bqcore/bq"],
    
    setup_requires=["PasteScript >= 1.7"],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2'],
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

server_subdirs=['bqdev', 'bqcore', 'bqserver', 'bqengine' ]
engine_subdirs=['bqdev', 'bqcore', 'bqengine' ]


@task
@cmdopts([('engine', 'e', 'install only the engine')])
def setup(options):
    'install local version and setup local packages'

    engine_install = getattr(options, 'engine', False)

    if not engine_install:
        # Hack as numpy fails to install when in setup.py dependencies
        sh('easy_install numpy==1.6.0')
        sh('easy_install numpy==1.6.0')
        # End Hack
        sh('easy_install http://biodev.ece.ucsb.edu/binaries/download/tw.output/tw.output-0.5.0dev-20110906.tar.gz') 
        sh('easy_install http://biodev.ece.ucsb.edu/binaries/depot/tgext.registration2/tgext.registration2-0.5.2.tar.gz')
    sh('easy_install http://biodev.ece.ucsb.edu/binaries/depot/httplib2/httplib2-0.7.1.tar.gz')
    sh('easy_install http://biodev.ece.ucsb.edu/binaries/depot/Paste/Paste-1.7.5.1bisque2.tar.gz')

    top = os.getcwd()
    subdirs = server_subdirs
    if hasattr(options, 'engine'):
        print "INSTALLING ENGINE"
        subdirs = engine_subdirs

    for d in subdirs:
        app_dir = path('.') / d
        if os.path.exists(app_dir):
            os.chdir(app_dir)
            sh('python setup.py develop')
            os.chdir(top)
    sh('easy_install http://biodev.ece.ucsb.edu/binaries/depot/Paste/Paste-1.7.5.1bisque2.tar.gz')


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    sh('tar -czf dist/bisque-modules-%s.tgz --exclude="*.pyc" --exclude="*~" --exclude="*.ctf" --exclude="*pydist" --exclude="UNPORTED" modules' % VERSION)


@task
@needs('setuptools.command.install')
def install():
    setup()

@task
def test():
    os.chdir('bqcore')
    sh('python setup.py test')
    

@task
def distclean():
    'clean out all pyc and backup files'
    sh('find . -name "*.pyc" | xargs rm ')
    sh('find . -name "*~" | xargs rm ')

@task
def package():
    'create distributable packages'
    pass
