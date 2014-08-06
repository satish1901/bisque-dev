import os
import sys
import tarfile
import urllib2
from urlparse import urlparse

from paver.easy import *
import paver.misctasks

options(
    virtualenv=Bunch(
        packages_to_install=['pip'],
        paver_command_line="required"
    ),
    sphinx = Bunch (
        builddir = "build",
        sourcedir = "docs/source"
        ),
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
)

feature_subdirs=['bqfeature' ]
server_subdirs=['bqapi', 'bqcore', 'bqserver', 'bqengine' ]
engine_subdirs=['bqapi', 'bqcore', 'bqengine' ]

PREINSTALLS = {'features' : ['numpexpr', 'cython'] }

all_packages = set (feature_subdirs + server_subdirs + engine_subdirs)

#################################################################


def getanswer(question, default, help=None):
    import textwrap
    if "\n" in question:
        question = textwrap.dedent (question)
    while 1:
        a =  raw_input ("%s [%s]? " % (question, default))

        if a=='?':
            if help is not None:
                print textwrap.dedent(help)
            else:
                print "Sorry no help available currently."
            continue
        y_n = ['Y', 'y', 'N', 'n']
        if default in y_n and a in y_n:
            a = a.upper()

        if a == '': a = default
        break
    return a

########################################################
import urllib2
import shutil
import urlparse
import os


def process_options(options):
    if hasattr(options, 'installing'):
        return
    installing = None
    if len(options.args) :
        installing = options.args[0]

    if installing not in ('engine', 'server', 'features'):
        installing =  getanswer("install [server, engine or features", "engine",
"""server installs component to run a basic bisque server
engine will provide just enough components to run a module engine,
all will install everything including the feature service""")

    if installing not in ('engine', 'server', 'features'):
        print "Must choose 'engine', 'server', or 'features'"
        sys.exit(1)


    preinstalls = PREINSTALLS.get (installing, [])

    for package in preinstalls:
        sh ("pip install %s" % package)

    subdirs  = dict (engine=engine_subdirs,
                     server = server_subdirs,
                     features = feature_subdirs) [ installing]
    print "installing all components from  %s" % subdirs
    options.subdirs = subdirs
    options.installing = installing




def install_prereqs (options):
    "Ensure required packages are installed"
    pass

def install_postreqs (options):
    "Install or Modify any packages post installation"
    pass


#############################################################
#@cmdopts([('engine', 'e', 'install only the engine')])
@task
@consume_args
def setup(options):
    'install local version and setup local packages'
    process_options(options)
    install_prereqs(options)
    setup_developer(options)
    #install_postreqs(options)

    print  'now run bq-admin setup %s' % ( 'engine' if options.installing =='engine' else '' )


@task
@consume_args
def setup_developer(options):
    process_options(options)
    top = os.getcwd()
    for d in options.subdirs:
        app_dir = path('.') / d
        if os.path.exists(app_dir):
	    sh('pip install -e %s' % app_dir)
            #os.chdir(app_dir)
            #sh('python setup.py develop')
            #os.chdir(top)

#@task
#@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
#def sdist():
#    """Overrides sdist to make sure that our setup.py is generated."""
#    sh('tar -czf dist/bisque-modules-%s.tgz --exclude="*.pyc" --exclude="*~" --exclude="*.ctf" --exclude="*pydist" --exclude="UNPORTED" modules' % VERSION)


@task
@needs('setuptools.command.install')
def install():
    setup()


@task
@consume_args
def package_wheels(options):
    if not os.path.exists('./dist'):
        os.makedirs ('./dist')
    top = os.getcwd()
    for app_dir in all_packages:
        os.chdir(app_dir)
        sh('python setup.py bdist_wheel --dist-dir=../dist')
        os.chdir(top)
    sh('python setup.py bdist_wheel --dist-dir=./dist')

@task
@consume_args
def upload(options):
    top = os.getcwd()
    for app_dir in all_packages:
        os.chdir(app_dir)
        sh('devpi upload  --no-vcs --format=bdist_wheel')
        os.chdir(top)
    sh('devpi upload  --no-vcs --format=bdist_wheel')




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

@task
@needs('paver.doctools.html')
def html(options):
    """Build docs"""
    destdir = path('docs/html')
    if destdir.exists():
        destdir.rmtree()
    builtdocs = path("docs") / options.builddir / "html"
    builtdocs.move(destdir)

@task
def pastershell():
    'setup env for paster shell config/shell.ini'
    bisque_info = path('bisque.egg-info')
    if not bisque_info.exists():
        sh ('paver egg_info')
    path ('bqcore/bqcore.egg-info/paster_plugins.txt').copy (bisque_info)


@task
@consume_args
def pylint(options):
    args = 'bqcore/bq bqserver/bq bqengine/bq bqfeature/bq'
    if options.args:
        args = " ".join(options.args)
    if os.name != 'nt':
        sh('PYTHONPATH=bqcore/bq:bqserver/bq:bqengine/bq:bqfeature/bq pylint %s --rcfile=bqcore/pylint.rc' % args)
    else:
        sh('set PYTHONPATH=bqcore\\bq;bqserver\\bq;bqengine\\bq;bqfeature\\bq & pylint %s --rcfile=bqcore\\pylint.rc' % args)



@task
@consume_args
def pylint_modules(options):
    args = 'modules/*/*.py'
    if options.args:
        args = " ".join(options.args)
    if os.name != 'nt':
        sh('PYTHONPATH=bqcore/bq:bqserver/bq:bqengine/bq:bqfeature/bq pylint %s --rcfile=bqcore/pylint.rc' % args)
    else:
        sh('set PYTHONPATH=bqcore\\bq;bqserver\\bq;bqengine\\bq;bqfeature\\bq & pylint %s --rcfile=bqcore\\pylint.rc' % args)


@task
@consume_args
def pyfind(options):
    args = 'bqcore/bq bqserver/bq bqengine/bq bqfeature/bq'
    sh ("find %s -name '*.py' | xargs fgrep %s" % (args, " ".join(options.args)))
