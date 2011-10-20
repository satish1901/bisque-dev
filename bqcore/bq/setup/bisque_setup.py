#!/usr/bin/env python
from __future__ import with_statement
import traceback
import optparse
#import package_resources
import os,sys,stat,platform, datetime
import shutil
import fnmatch
import subprocess 
import zipfile
import StringIO
import textwrap
import getpass
import string
import re
import logging

import pkg_resources
from setuptools.command import easy_install

#logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('bisque-setup')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
# add formatter to ch
ch.setFormatter(formatter)
log.addHandler(ch)

## ENSURE setup.py has been run before..

capture = None

try:
    import bq
    import sqlalchemy as sa
    from bq.core.commands.configfile import ConfigFile
    #from bq.model import db_version
except ImportError, e:
    log.exception( "There was a problem with the bisque environment\n"
                   "Have you run %s setup.py yet?" % sys.executable)
    
    sys.exit(0)

try:
    import readline
    #readline.parse_and_bind('tab: complete')
    #readline.parse_and_bind('set editing-mode emacs')
except ImportError, e:
    log.info( "No readline available" )
    pass

try:
    import pty
    has_script=True
except ImportError:
    has_script=False


class SetupError(Exception):
    'error in setup'


#############################################
#  Setup some local constants

PYTHON=sys.executable
EXT_SERVER = "http://biodev.ece.ucsb.edu/binaries/depot/" # EXTERNAL host server BQDEPOT
BQDIR = os.path.abspath ('.')  # Our top installation path
BQDEPOT  = os.path.join(BQDIR, "external") # Local directory for externals

BQENV = None
BQBIN = None


#################################################
## Initial values
site = {
    'bisque.root' : 'http://localhost:8080',
    'bisque.organization': 'Your Organization',
    'bisque.title': 'Image Repository',
    'bisque.admin_email' : 'YourEmail@YourOrganization',
    'bisque.paths.root' : os.getcwd(),
    }
# Add any variables to read from the site.cfg each time
# you run bisque-setup
initial_vars = {
    'bisque.paths.root' : os.getcwd(),
    'bisque.root' : 'http://localhost:8080',
    'bisque.organization': 'Your Organization',
    'bisque.title': 'Image Repository',
    'bisque.admin_email' : 'YourEmail@YourOrganization',
    'sqlalchemy.url': 'sqlite:///bisque.db',
    'mail.on' : 'False',
    'mail.manager' : "immediate",
    'mail.transport' : "smtp",
    'mail.smtp.server' : 'localhost',
    'runtime.matlab_home' : '',
    'runtime.mode' : 'command',
    'runtime.staging_base' : '',
    'condor.submit_template': '',
    'condor.dag_template' : '',
    'condor.dag_config_template': '',
    }

linked_vars = {
    'h1.url' : '${bisque.root}',
    'smtp_server' : '${mail.smtp.server}',        
    'registration.host' : '${bisque.root}',
    'registration.mail.smtp_server' : '${mail.smtp.server}',
    'registration.mail.admin_email' : '${bisque.admin_email}',
}


SITE_QUESTIONS = [('bisque.root' , 'Enter the root URL of the server ',
"""A complete URL where your application will be mounted i.e. http://someserver:8080/
If you server will be mounted behind a proxy, please enter
the proxy address and see AdvancedInstalls"""),
             ('bisque.admin_email' , 'An email for the administrator', None),
             ('bisque.organization', 'A small organization title for the main page',
              "This will show up in the upper left of every page display"),
             ('bisque.title', 'The main title for the web page header',
              "The title of your collection, group or project" ),
             ('bisque.paths.root', 'Installation Directory', 
              'Location of bisque installation.. used for find configuration and data')
             ]



DB_QUESTIONS = [
                 ('sqlalchemy.url', 'A database URI', """
                  A SQLAlchemy DBURI (see http://www.sqlalchemy.org/).
                  Examples of typical DB URI:
                      sqlite:///bisque.db
                      postgres://localhost:5432/bisque
                      mysql://user:pass@localhost/bisque
                      mysql://user:pass@localhost/bisque?unix_socket=/bisque-data/mysql-db/mysql-socket.sock
                  """),
    ]

MATLAB_QUESTIONS=[
    ('runtime.matlab_home', "Enter toplevel matlab directory (under which is bin)",
     "matlab home is used by modules to setup the correct environment variables"),

    ]
RUNTIME_QUESTIONS=[
    ('runtime.mode', "Enter a list (comma,seperated) of module runtimes",
     'controls how  module are run locally or condor'),

    ('runtime.staging_base', "An temproary area that can be used to stage execution of modules",
    """
    Some modules are copied to a temporary directory with data so that they may run
    cleanly.  Condor often requires a staging area that is seen by all nodes that
    it can dispatch jobs to.  This area can be a local or condor shared filesystem
    """)
    ]


CONDOR_QUESTIONS =[
    ('condor.submit_template', "Path to condor submit script",
     """A script used to submit jobs to Condor"""),
    ('condor.dag_template', "A DAGMAN script", None),
    ('condor.dag_config_template', "A DAGMan Config", None)
    ]




###
### Unfinished 
# SERVER_QUESTIONS = [
#     ('bisque.root.port_range',
#      'Enter port range for root servers',
#      """
#      Multple bisque servers can help performance and machine
#      utilization.  Each bisque server needs it's own TCP/IP port.
#      Please enter a free range i.e. 5000,5004
#      """),
#     ('bisquik.engine_service.port_range',
#      'Port range for engine servers'
#      """
#      Mutliple engine servers can be run on a single machine but each needs
#      a single TCP port to operate on. Please give a suitable free range i.e.
#      10000,10004
#      """)
#     ]

############################################
# HELPER FUNCTIONS
def to_sys_path( p ):
    ''' Converts POSIX style path into the system style path '''
    return p.replace('/', os.sep)

def to_posix_path( p ):
    ''' Converts system style path into POSIX style path '''
    return p.replace(os.sep, '/')


def config_path(*names):
    return to_sys_path(os.path.join(BQDIR, 'config', *names))

def bisque_path(*names):
    return to_sys_path(os.path.join(BQDIR, *names))


def which(command):
    """Emulate the Shell command which returning the path of the command
    base on the shell PATH variable
    """
    for d in [ os.path.expanduser (x) for x in os.environ['PATH'].split (os.pathsep)]:
        path  = os.path.join(d, command)
        if os.path.isfile (path):
            mode =  os.stat (path).st_mode
            if stat.S_IXUSR & mode:
                return path
    return None

def check_exec(command):
    return which (command) != None


def copy_link (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            log.info( "linking %s to %s"%(f,dest) )
            if os.path.exists (dest):
                os.unlink(dest)
            os.link(f, dest)
        except:
            if os.name is not 'nt':
                log.exception( "Problem in link %s .. trying copy" )
            shutil.copyfile (f, dest)

def getanswer(question, default, help=None):
    global capture
    if "\n" in question:
        question = textwrap.dedent (question)
    while 1:
        if capture is not None:
            a =  capture.logged_input ("%s [%s]? " % (question, default))
        else:
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


def patch_file (path, mapping, destination=None, **kw):
    """Replace the file at path replacing the elements found in kw
    Keyword are signaled with '$' i.e.  $KEY is reaplced with 'something'
    if mapping has {'KEY' : 'something' }
    """
    with open(path) as f:
        contents = f.read()
    template = string.Template(contents).substitute(mapping, **kw)
    if destination is None:
        destination = path
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(path))
    with open(destination,'w') as f:
        f.write (template)
    
   
def sql(DBURI, statement, verbose = False):

    from sqlalchemy import create_engine, sql
    try:
        engine = create_engine(DBURI, echo= verbose)
        result = engine.execute(sql.text(statement))
        return 0, result.fetchall()
    except:
        if verbose:
            log.exception('in sql %s' % statement)
        return 1, ''
    

    print "SQL: NOT IMPLEMEMENT %s" % statement
    return 0, ''

    command = ["psql"]
    if DBURI.username:
        command.extend (['-U', DBURI.username])
    if DBURI.host:
        command.extend (['-h', DBURI.host])
    if DBURI.port:
        command.extend (['-p', str(DBURI.port)])
    stdin = None
    if DBURI.password:
        stdin = StringIO.StringIO(DBURI.password)

    p =subprocess.Popen(command + ['-d',str(DBURI.database), '-c', statement],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
    out, err = p.communicate()
    return p.returncode, out


class STemplate (string.Template):
    """ Like the standard template but allows '.' in names
    """
    idpattern = r'[_a-z][._a-z0-9]*'


def call(cmd, **kw):
    if not kw.has_key ('stdout'):
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, **kw)
        while True:
            l = p.stdout.readline()
            if not l: break
            print l,
            #p.wait()
    else:
        p = subprocess.Popen(cmd, **kw)
        
    p.wait()
        
    return p.returncode
    



def unpack_zip (zfile, dest):
    z = zipfile.ZipFile (zfile, 'r')
    #for info in z.infolist():
    #    filename = os.path.join (dest, info.filename)
    #    if filename.endswith('/'):
    #        if not os.path.exists(filename):
    #            os.makedirs (filename)
    #        continue
    #    f = open(filename, 'wb')
    #    f.write (z.read (info.filename))
    #    f.close()
    z.extractall(dest)
    # Return top dirname
    names = z.namelist()
    z.close()
    return names

class InstallError(Exception):
    pass
    

#####################################################
# Installer routines

def install_site (params):
    if not os.path.exists (config_path('site.cfg')):
        shutil.copyfile(config_path('site.cfg.default'), config_path('site.cfg'))
        params = read_site_cfg()
        params.update(initial_vars)

    print "Top level site variables are:"
    for k in sorted(params.keys()):
        if k in site:
            print "  %s=%s" % (k,params[k])

    if getanswer("Change a site variable", 'Y')!='Y':
        return params
        
    params = modify_site_cfg(SITE_QUESTIONS, params)
    return params




# install binary hooks into local .hgrc file
def install_mercurial_hooks():
  
    if getanswer ("May I reconfigure your mercurial?", "Y",
                  "This will change your mercurial setup adding hooks for binary file handling") != 'Y':
        return  

    external = to_sys_path('external/*')+'.{zip,jar,gz,bz2,gem,dll,a,egg}'
    elements = { 'extensions' :  [ ('external', None)],
      'hooks' :[ ('pretxncommit.crlf', 'pretxncommit.crlf = python:hgext.win32text.forbidcrlf')],
      'encode':[ (external, None)],
#      'decode':[external, '#' + external + '= download: http://biodev.ece.ucsb.edu/binaries/'],
      'decode':[ (external, None)],
    }
    

#    env = { 'path' : package_resources.resource_filename('Bisquik', 'tools') }
    env = { 'path' : os.getcwd() }


    log.info( "Adding mercurial hooks" )
    c = ConfigFile ()
    #hgrc = os.path.expanduser(to_sys_path("~/.hgrc"))
    hgrc = bisque_path(".hg/hgrc")
    c.read (open(hgrc))
    for section, lines in elements.items():
        for key,val in lines:
            c.edit_config (section, key, val, env)
    if getanswer ('May I reconfigure your ' + hgrc, 'Y',
                  "This will change your mercurial setup adding hooks for binary file handling") == 'Y':
        c.write (open(hgrc, 'w'))
    
    



##################################################
#


def update_variables (qs, store):
    """Ask questions to update any global  variables"""
    values = {}
    values.update (store)

    for key, q, h in qs:
        values.setdefault (key, '')

    # Ask the question in qs after substituting vars
    for key, question, help in qs:
        values[key] = STemplate (values[key]).safe_substitute(values)
        values[key] = getanswer (question, values[key], help)

    # Based on the given answers, update the again values  (for mutual references)
    for key in values.keys():
        if isinstance (values[key], basestring):
            values[key] = STemplate (values[key]).safe_substitute(values)
        
    return values


#######################################################
#
BQ_SECTION="app:main"
SITE_CFG = config_path('site.cfg')
SITE_DEFAULT = config_path('site.cfg.default')

def read_site_cfg(section = BQ_SECTION ):
    bisque_vars = {}
    
    # first pull initial values from config files
    #iv = initial
    tc = ConfigFile()      
    if os.path.exists (SITE_CFG): 
        tc.read(open(SITE_CFG))
        bisque_vars.update(tc.get(section, asdict=True))

    return bisque_vars


def update_site_cfg (bisque_vars, section = BQ_SECTION, append=True):
    c = ConfigFile()
    if os.path.exists (SITE_CFG):
        c.read(open(SITE_CFG))

    for k,v in bisque_vars.items():
        c.edit_config (section, k, '%s = %s' % (k,v), {}, append)
    c.write (open (SITE_CFG, 'w'))


def modify_site_cfg(qs, bisque_vars, section = BQ_SECTION, append=True):

    bisque_vars =  update_variables(qs, bisque_vars )
    for k,v in linked_vars.items():
        if k in bisque_vars:
            bisque_vars [k] = v
    bisque_vars =  update_variables([], bisque_vars )

    c = ConfigFile()
    if os.path.exists (SITE_CFG):
        c.read(open(SITE_CFG))
    else:
        c.read (open(SITE_DEFAULT))
        
    for k,v in bisque_vars.items():
        c.edit_config (section, k, '%s = %s' % (k,v), {}, append)

    c.write (open (SITE_CFG, 'w'))

    return bisque_vars



############################################
#

def create_postgres (dburl):
    "Check existance of database base and create new if needed"

    command = ["psql"]
    if dburl.username:
        command.extend (['-U', dburl.username])
    if dburl.host:
        command.extend (['-h', dburl.host])
    if dburl.port:
        command.extend (['-p', str(dburl.port)])

    stdin = None
    if dburl.password:
        stdin = StringIO.StringIO(dburl.password)
    if call (command + [ '-d', str(dburl.database), '-c', r'\q'], stdin = stdin ) == 0:
        print "Database exists, not creating"
        return False
    # http://www.faqs.org/docs/ppbook/x17149.htm
    # psql needs a database to connect to even when creating.. use template1
    if dburl.password:
        stdin = StringIO.StringIO(dburl.password)
    if call (command + ['-c', 'create database %s' % dburl.database, 'template1'],
             stdin = stdin) != 0:

        print "Database creation failed.. Please check your permissions"
        return False
    
    return True
    
    
        
###############
#

def create_mysql(dburl):
    command = [ 'mysql' ]
    if dburl.query.has_key('unix_socket'):
        command.append ( '--socket=%s' % dburl.query['unix_socket'] )
    if dburl.username:
        command.append ('-u%s' % dburl.username)
    if dburl.password:
        command.append ('-p%s' % dburl.password)
    
    print "please ignore 'Unknown database ..' "
    if call (command+[dburl.database, '-e', 'quit']) == 0:
        print "Database exists, not creating"
        return False

    if call (command+['-e', 'create database %s' % dburl.database]) != 0:
        print "Database creation failed."
        return False
    return True
          
            
###############
#
def create_sqlite (dburl):
    return True


known_db_types = {
    'sqlite'     : ('sqlite3', '',   create_sqlite ),
    'postgres'   : ('psycopg2',  'psycopg2', create_postgres   ),
    'postgresql' : ('psycopg2',  'psycopg2',  create_postgres  ),
    'mysql'      : ('_mysql',    'mysql-python', create_mysql ),
    }

def install_driver(DBURL):
    """For known database types: check whether required driver is installed;
    install it if not installed.
    
    Argument: sqlalchemy.engine.url.URL object.
    
    Returns True if driver is available (so it makes sense to continue),
    False otherwise (database configuration should be cancelled).
    """
    py_drname, ei_drname, create = known_db_types.get(DBURL.drivername,
                                                      (None,None,None))
    if py_drname is None:
        return 'Y' == getanswer(
            """
            This database type is not known to Bisque.
            Make sure that you have installed appropriate driver
            so SQLAlchemy can use it to access your database.
            Continue?
            """, 
            'N',
            """
            Bisque knows what driver is required for SQLite, PostreSQL, and MySQL
            and automatically installs it if needed.
            For other databases, you have to install driver manually.
            It is also recommended that you create empty database manually,
            as some databases may use proprietary syntax for database creation.
            """)
            
    else:
        try:
            print 'Trying to import driver %s...' % py_drname,
            __import__(py_drname)
            print 'Driver successfully imported.'
            return True
        except ImportError:
            print
            print 'Import failed, trying to install package %s...' % ei_drname
            try:
                easy_install.main(['-U',ei_drname])
                # The following line is needed to make installed module importable
                pkg_resources.require(ei_drname)
                print 'Package %s successfully installed.' % ei_drname
                return True
            except:
                print "ERROR: Could not easy install package"
                print "Usually this occurs if the development headers for a partcular driver"
                print "are not available. Please check the Bisque Wiki"
                print "http://biodev.ece.ucsb.edu/projects/bisquik/wiki/AdvancedInstalls"

                log.exception( 'Failed to install package %s.' % ei_drname )
                return False



def test_db_existance(DBURL):
    """Test whether Bisque database exists and is accessible.
    Note that database may exist, but the user specified in DBURL has no
    rights to access it, etc.
    This function is able to catch only basic configuration errors
    (like Bisque database user was created, but no rigts were granted to it).
    Even if this function succeeds, later steps may fail due to misconfigured
    access rights.
    
    Argument: sqlalchemy.engine.url.URL object.
    
    Returns True if database exists and is accessible, False otherwise.
    """
    try:
        print 'Checking whether database "%s" already exists...' % DBURL.database,
        d = sa.create_engine(DBURL)
        try:
            c = d.connect()
            c.close()
        finally:
            d.dispose()
        print 'Yes, it exists.'
        return True
    except:
        log.warn("Could not contact database")
        return False

def get_dburi(params):

    params = modify_site_cfg(DB_QUESTIONS, params)
    dburi = params.get('sqlalchemy.url', None)
    DBURL = sa.engine.url.make_url (dburi)
    return DBURL


def test_db_initialized(DBURL):
    r, out = sql(DBURL, 'select * from migrate_version')
    return r == 0
    

def install_database(params):
    """Main database configuration routine.
    To succeed, database server should run, be accessible using the specified
    dburi, and have the specified database.
    
    Note: this always is true for SQLite.
    
    Note: for all other database types, database should be created manually
    before running Bisque setup.
    """
    try:
        DBURL = get_dburi(params) 
    except sa.exc.ArgumentError:
        log.exception( "Unable to understand DB url. Please see SqlAlchemy" )
        return params
    
    # 'dburi' is a string entered by the user
    # 'DBURL' is an object with attributes:
    #   drivername  -- string like 'sqlite', 'postgres', 'mysql'
    #   username    -- string
    #   password    -- string
    #   host        -- string
    #   port        -- string
    #   database    -- string
    #   query       -- map from query's names to values
    
    # Step 1: check whether database driver is available (install it if needed)
    if not install_driver(DBURL):
        print(
            """Database was NOT prepared due to absence of database driver
Please resolve the problem(s) and re-run 'bisque-setup --database'.""")
        return params
        
        
    # Step 2: check whether the database exists and is accessible
    db_exists = test_db_existance(DBURL)
    if not db_exists:
        if getanswer ("Would you like to create the database",
                      "Y",
                      """
      Try to create the database using system level command.  This
      really is outside of the scope of the installer due to the complexity
      of user and rights management in database systems.   This command
      may succeed if you been able to create database previously at the
      command line
      """) == 'Y':
            py_drname, ei_drname, create_db = \
                       known_db_types.get(DBURL.drivername, (None,None,None))
            if callable(create_db):
                try:
                    db_exists = create_db (DBURL)
                except:
                    log.warn('Could not create database')

    if not db_exists:
        print( """
        Database was NOT prepared -- either server has no database '%s'
        or user "%s" has no rights to access this database.
        Please fix the problem(s) and re-run 'bisque-setup --database'
        """ % (DBURL.database,DBURL.username) )
        return params
               
    # Step 3: find out whether the database needs initialization
    db_initialized = test_db_initialized(DBURL)
    if not db_initialized and getanswer(
        "Intialize the new database",  "Y",
        """
        The database is freshly created and doesn't seem to have
        any tables yet.  Allow the system to create them..
        """) == "Y":
        r = call (['paster','setup-app', config_path('site.cfg')])
        if r != 0:
            raise SetupError("There was a problem initializing the Database")
        db_version = call ([PYTHON, to_sys_path('bqcore/migration/manage.py'),
                            'version_control'])
        sql(DBURL, "update migrate_version set version=%s" % db_version)
        
    # Step 4: Always upgrade the database to newest version
    print "Upgrading database version"
    call ([PYTHON, to_sys_path ('bqcore/migration/manage.py'), 'upgrade'])
    return params
        
        


#######################################################
#
def install_matlab(params):
    if getanswer ('Install matlab helpers', 'Y',
"""Matlab is needed to compile and run several default modules in bisque.
These modules are not required, but do show the capabilities.  The installer
will look for matlab and use that to perform the the rest of the install""") != 'Y':
        return

    matlab_home = which('matlab')
    if matlab_home:
        params['runtime.matlab_home'] = os.path.abspath(os.path.join (matlab_home, '../..'))
    else:
        if getanswer("No Matlab was found.. please add matlab to the path (cancel now)", "Y",
                     "Matlab needs to be in the shell path, then rerun setup") == 'Y':
            #raise InstallError ("need matlab for modules")
            return
    #params['matlab_installed'] = str(check_exec('matlab'))
    params = modify_site_cfg(MATLAB_QUESTIONS, params)

    #install_matlabwrap(params)


def install_matlabwrap(params):
    if  not params['runtime.matlab_home']:
        return

    if getanswer( "Install mlabwrap (need for some analysis)", 'Y',
                  "Install a compiled helper to run matlab scripts.  Matlab must be installed and visible!") != 'Y':
        return

    # Already installed for stats server
    #print "Installing mlabwrap dependencies"
    #retcode = call(['easy_install', 'numpy'])

    print """untar'ing  mlabwrap from the external directory
    and running python setup.py.. Please watch for errors

    Please visit for more information:
    
    http://biodev.ece.ucsb.edu/projects/bisquik/wiki/RequiredAndSuggestedSoftware
    
    """
    import tarfile

    BUILD = to_sys_path("../build")
    if not os.path.exists (BUILD):
        os.mkdir (BUILD)

    tf = tarfile.open (to_sys_path("../external/mlabwrap-1.0.tar.gz"))
    tf.extractall(path = BUILD)
    cwd = os.getcwd()
    os.chdir(os.path.join(BUILD,"mlabwrap-1.0-bisquik"))
    call ([PYTHON, 'setup.py', 'install'])
    os.chdir (cwd)




#######################################################
#

def install_modules(params):
    # Check each module for an install script and run it.
    if getanswer( "Try to setup modules", 'Y',
                  "Run the installation scripts on the modules. Some of these require local compilations and have outside dependencies. Please monitor carefullly") != 'Y':
        return

    for bm in os.listdir (bisque_path('modules')):
        modpath = bisque_path('modules', bm)
        environ = dict(os.environ)
        environ.pop ('DISPLAY', None) # Makes matlab hiccup
        if os.path.exists(os.path.join(modpath, 'setup.py')):
            cwd = os.getcwd()
            os.chdir (modpath)
            print ("Running setup.py in %s" % modpath)
            try:
                r = call ([PYTHON, '-u', 'setup.py'], env=environ)
                if r != 0:
                    print "setup in %s returned error " % modpath 
            except Exception, e:
                log.exception ("An exception occured during the module setup: %s" % str(e))
            os.chdir (cwd)

#######################################################
#

#######################################################
#

def install_scripts ():
    scripts = [ 'bq-start-servers', 'bq-kill-servers' ]
    mapping = { 'BQENV' : BQENV,
                'BQDIR' : BQDIR,
                'BQBIN' : BQBIN,
#                '$PIDDIR' : '/var/run',
#                '$LOGDIR' : '/var/log'
                'BQPID' : '.',
                'BQLOG' : '.',
                }
    for script  in scripts:
        patch_file (os.path.join ('scripts', script), mapping, destination=BQBIN)

#######################################################
#
def install_bioformats(params):
    
    if getanswer ("Install bioformats", "Y",
                  "Bioformats can be used as a backup to read many image file types") == "Y":


        bio_files = [ 'bio-formats.jar', 'loci-common.jar', 'mdbtools-java.jar', 'ome-io.jar',
                      'poi-loci.jar', 'jai_imageio.jar', 'loci_tools.jar', 'metakit.jar', 'ome-xml.jar' ]

        for bf in bio_files:
            copy_link (os.path.join(BQDEPOT, bf), BQBIN)
             
        biozip = zipfile.ZipFile (os.path.join(BQDEPOT, 'bftools.zip'))
        for fname in  biozip.namelist():
            if fname[-1] == '/':  # skip dirs
                continue
            
            dest = os.path.join(BQBIN, os.path.basename(fname))
            #destdir = os.path.dirname(dest)
            #if not os.path.isdir(destdir):
            #    os.makedirs(destdir)
            data = biozip.read(fname)
            f = open(dest, 'w')
            f.write(data)
            #os.fchmod (f, os.fstat(f) | stat.S_IXUSR)  # User exec
            os.chmod (dest, os.fstat(f.fileno()).st_mode | stat.S_IXUSR)  # User exec
            f.close()
                
        # python >2.6
        #biozip.extractall(os.path.join(BQENV, "bin"))

        biozip.close()
                           



#######################################################
#

def install_servers(params):

    #if getanswer("Configure bisque to run behind apache",
    #             "Apache provides some benifits for large sites", "N") == "N":
    #    return

    print "Server config"


    if not os.path.exists(config_path('server.ini')):
        shutil.copyfile(config_path('server.ini.default'), config_path('server.ini'))
        server_params = { 'bisque.root' : params['bisque.root'], 'h1.url' : params['bisque.root']}
        params = modify_site_cfg([], server_params, 'servers', append=False)

    if not os.path.exists(config_path('shell.ini')):
        shutil.copyfile(config_path('shell.ini.default'), config_path('shell.ini'))

    if not os.path.exists(config_path('who.ini')):
        shutil.copy(config_path('who.ini.default'), config_path('who.ini'))

    if not os.path.exists(config_path('registration.cfg')):
        shutil.copyfile(config_path('registration.cfg.default'), config_path('registration.cfg'))
    if getanswer('Configure bisque with proxy', 'N',
                 ("Multiple bisque servers can be configure behind a proxy "
                  "providing enhanced performance.  As this an advanced "
                  "configuration it is only suggested for experienced "
                  "system administrators")) == 'Y':
        print ("See site.cfg comments and contrib/apache/proxy-{http,ssl} "
               "for details. Also see the website "
               "http://biodev.ece.ucsb.edu/projects/bisquik/wiki/AdvancedInstalls")


#######################################################
#
def check_condor (params):
    params['condor.enabled'] = ""
    try:
        if os.path.exists('/dev/null'):
          devnull = open ('/dev/null') 
        else:
          devnull = open('junk.txt', 'w')
        retcode = call ([ 'condor_status' ], stdout=devnull, stderr=devnull )
    except OSError:
        print "No condor was found. See bisque website for details on using condor"
        return params
    print "Condor job management software has been found on your system"
    print "Bisque can use condor facilities for some module execution"

    if getanswer("Condigure modules for condor", 'Y',
                 "Configure condor shared directories for better performance")=="Y":
        params['condor.enabled'] = "true"
        params['runtime.mode'] = ','.join ([params['runtime.mode'], 'condor'])
        print """
        NOTE: condor configuration is complex and must be tuned to
        every instance.  Bisque will try to use the condor facilities
        but please check that this is operating correctly for your
        installation

        Please check the wiki at biodev.ece.ucsb.edu/projects/bisquik/wiki/AdvancedInstalls#CondorConfiguration
        """

        if getanswer("Advanced Bisque-Condor configuration", "N",
                     "Change the condor templates used for submitting jobs")!='Y':
            return params
        
        params = modify_site_cfg(CONDOR_QUESTIONS, params)
        for v, d, h in CONDOR_QUESTIONS:
            if params[v]:
                params[v] = os.path.abspath(os.path.expanduser(params[v]))
                print "CONDOR", v, params[v]
        update_site_cfg(params)

    return params



def install_runtime(params):
    """Check and install runtime control files"""
    params['runtime.mode'] = "command"
    params = check_condor(params)

    params = modify_site_cfg(RUNTIME_QUESTIONS, params)
    staging=params['runtime.staging_base'] = os.path.abspath(os.path.expanduser(params['runtime.staging_base']))

    try:
        if not os.path.exists(staging):
            os.makedirs(staging)
    except OSError,e:
        print "%s does not exist and cannot create: %s" % (staging, e)

    print params
    for bm in os.listdir (bisque_path('modules')):
        modpath = bisque_path('modules', bm)
        if os.path.isdir(modpath) and os.path.exists(os.path.join(modpath, "%s.xml" % bm )):
            cfg_path = os.path.join(modpath, 'runtime-bisque.cfg')
            #if  os.path.exists(cfg_path):
            #    shutil.copyfile(cfg_path, "%s.old" %cfg_path)

            cfg = ConfigFile (cfg_path)
            if not os.path.exists(cfg_path):
                cfg.edit_config(None, None,
                   '# runtime-bisque.cfg created by bisque-setup')
                cfg.edit_config(None, 'module_enabled',
                                'module_enabled=True'  )
            cfg.edit_config(None, 'runtime', 'runtime=%s' % params['runtime.mode'])
            cfg.edit_config(None, 'staging_base', 'staging_base=%s' % params['runtime.staging_base'])
            if params['runtime.matlab_home']:
                cfg.edit_config(None, 'matlab_home', 'matlab_home=%s'%params['runtime.matlab_home'])
            for v, d, h in CONDOR_QUESTIONS:
                if params.get(v, None):
                    cfg.edit_config("condor", v, "%s=%s" % (v, params[v]))
                    print "CONDIR EDIT", v
            cfg.write (open(cfg_path, 'w'))
    return params
    



#######################################################
#

def install_mail(params):
    MAIL_QUESTIONS = [
        ('mail.smtp.server', "Enter your smtp mail server",
         "The mail server that delivers mail.. often localhost"),
    ]


    if getanswer ("Enable mail delivery","Y",
                  """
                  The system requires mail delivery for a variety of operations
                  including user registration and sharing notifications.
                  This section allows you to configure the mail system""" )!="Y":
        params['mail.on'] =  'False'
        return params
    params['mail.on'] = 'True'
    params = modify_site_cfg (MAIL_QUESTIONS, params)
    print "Please review/edit the mail.* settings in site.cfg for you site"""
    return params


#######################################################
#

import urllib2
import urlparse
import hashlib
def _sha1hash(data):
    return hashlib.sha1(data).hexdigest().upper()

def fetch_external_binaries ():
    """Read EXTERNAL_FILES for binary file names (with prepended hash)
    and download from external site.  Allows binary files to be distributed
    with source code

    Syntax
    """

    def fetch_file (hash_name, where, localname=None):
        sha1, name = hash_name.split ('-', 1)

        if localname is not None:
            name = localname
        
        if os.path.isdir (where):
            dest = os.path.join(where,name)
        else:
            dest = where
        if os.path.exists(dest):
            f = open(dest)
            shash = _sha1hash (f.read())
            f.close()
            if sha1 == shash:
                print "%s found locally" % name
                return
            
        fetch_url = urlparse.urljoin(EXT_SERVER,  hash_name)
        print "Fetching %s" % fetch_url
        handle = urllib2.urlopen (fetch_url)
        data   = handle.read()
        handle.close()
        
        if sha1 != _sha1hash(data):
            raise Exception('hash mismatch in %s' % filename) 
        handle = open(dest, 'wb')
        handle.write(data)
        print "Wrote %s in %s" % (name, where)
        handle.close()
    
    if getanswer ("Fetch external binary files from Bisque development server",
                  "Y",
                  "This action is required only on first download") != 'Y':
        return

    if not os.path.exists(BQDEPOT):
        os.makedirs (BQDEPOT)
    conf = ConfigFile(config_path('EXTERNAL_FILES'))
    external_files = conf.get ('common')
    local_platform = platform.platform()
    for section in conf.section_names():
        if fnmatch.fnmatch(local_platform, section):
            print "Matched section %s" % section
            external_files.extend (conf.get (section))
    for  line in [ f.strip().split('=') for f in external_files]:
        lname = None
        fname = line.pop(0)
        if len(line):
            lname =line.pop(0)
        if fname:
            try:
                fetch_file (fname, BQDEPOT, lname)
            except Exception, e:
                print "Failed to fetch '%s' with %s" % (fname,e)



#######################################################
#
def install_dependencies ():
    """Install dependencies that aren't handled by setup.py"""

    extzip = os.path.join(BQDEPOT, 'extjs.zip')
    public = to_sys_path('bqcore/bq/core/public') 
    extjs =  os.path.join (public, "extjs")

    if os.path.exists(extjs) and os.path.getmtime(extzip) < os.path.getmtime(extjs):
        return

    print "Unpacking %s into %s"  % (extzip, public)

    names = unpack_zip(extzip, public)
    if os.path.exists(extjs):
        shutil.rmtree(extjs)
    # Move whatever dir name you found in the names to "public/extjs"
    topdir = names and names[0].split('/',1)[0] or "extjs-4.0.0"
    unpackdir = to_sys_path('%s/%s' % (public, topdir))
    while not os.path.exists(unpackdir):
        print "Couldn't find top level dir of %s" % extzip
        unpackdir = getanswer("Dirname in %s " % public,
                              unpackdir,
                              "Will rename whater top level dir to extjs")
    shutil.move (unpackdir, extjs)


#######################################################
#
def setup_admin(params):
    try:
        DBURL = get_dburi(params) 
    except sa.exc.ArgumentError:
        log.exception( "Unable to understand DB url. Please see SqlAlchemy" )
        return 

    # Not sure why, but needs to separate script
    r = call ([PYTHON, 'scripts/create_admin.py'])
    #r, admin_pass = sql("select password from tg_user where user_name='admin';")
    # Returns "[(pass, )]"
    if r!= 0:
        print("There was a problem fetching the initial admin password")
        return
    
    #admin_pass = eval(admin_pass)[0][0]
    new_pass = getpass.getpass ("Please set the bisque admin password >")
    
    #sql(DBURL, "update tg_user set password='%s' where user_name='admin';" % (new_pass))
    print "Set new admin password"
        

    
    
            
#######################################################
#  Send the installation report 
# http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
import re
unprintable = "".join(set(unichr(x) for x in range(0,255)) - set(string.printable))
control_char_re = re.compile('[%s]' % re.escape(unprintable))
def remove_control_chars(s):
    return control_char_re.sub('', s)

def send_installation_report(params):
    if getanswer("Send Installation/Registration report", "Y",
                  """This helps the developers understand what issues
                  come up with installation.  This information is never
                  shared with others.""") != "Y":
        return
    import socket
    import turbomail
    import platform
    import textwrap
    
    BISQUE_REPORT="""
    Host: %(host)s
    Platform : %(platform)s
    Python : %(python_version)s
    Admin: %(admin)s
    Time: %(installtime)s
    Duration: %(duration)s
    
    """
    sender_email = params.get ('bisque.admin_email', 'YOUR EMAIL')

    sender_email  = getanswer ("Enter the site administrator's email",
                               sender_email,
                               """This will us to contact you (very rarely) with updates""")
    
    turbomail.control.interface.start ({'mail.on':True,
                                        'mail.transport': 'smtp',
#                                        'mail.transport': 'debug',
                                        'mail.smtp.server' : 'localhost'})

    parts = []
    text = textwrap.dedent(BISQUE_REPORT) % dict (host = socket.getfqdn(),
              admin = sender_email,
              platform = platform.platform(),
              python_version = platform.python_version(),
              installtime = params['install_started'],
              duration = params['duration'],
                                                  )
    parts.append(text)
    parts.append(str(params))
    if os.path.exists('bisque-install.log'):
        parts.append (remove_control_chars (open ('bisque-install.log','r').read()))

    try:
        msg = turbomail.Message(sender_email, "bisque-install@biodev.ece.ucsb.edu", "Installation report")
    
        msg.plain = "\n-----------\n".join (parts)
        msg.send()
    except Exception,e:
        print "Mail not sent.. problem sending the email %s" % str(e)
        print "----------------------------------------"
        print text
        print "----------------------------------------"
        print "Please send your installation log to the bisque-help@biodev.ece.ucsb.edu"


    print """Please join the bisque mailing list at:
    User Group:    http://groups.google.com/group/bisque-bioimage
    Developer :    http://biodev.ece.ucsb.edu/cgi-bin/mailman/listinfo/bisque-dev
    """




#######################################################
#

start_msg = """
You can start bisque with

   bq-admin servers start

then point your browser to

    ${bisque.root}

If you need to shutdown the servers, then use

   bq-admin servers stop

You can login as admin and change the default password.

"""

install_options= [
           'site',
#           'mercurial',
           'binaries',
           'database',
           'matlab',
           'modules',
           'runtime',
           'bioformats',
           'servers',
           'mail',
           'admin']


usage = " usage: bq-admin setup [%s] " % ' '.join(install_options)


def bisque_installer(options, args):
    cwd = to_posix_path(os.getcwd())
    if not os.path.exists ('bqcore'):
        print "ERROR: This script must be bisque installation directory"
        sys.exit()

    print """This is the main installer for Bisque

    The system will initialize and be ready for use after a succesfull
    setup has completed.

    Several questions must be answered to complete the install.  Each
    question is presented with default in brackets [].  Pressing
    <enter> means that you are accepting the default value. You may
    request more information by responding with single '?' and then <enter>.

    For example:
    What is postal abbreviation of Alaska [AK]?

    The default answer is AK and is chosen by simply entering <enter>

    """
    if len(args) == 0:
        installer = install_options[:]
    else:
        installer = args

    if 'help' in installer:
        print usage
        return

        
    #call ([PYTHON, "setup.py", "develop"])
    
    #install_scripts()
    params = {}
    if os.path.exists (SITE_CFG): 
        params = read_site_cfg()
    
    params['bisque.installed'] = "inprogress"
    if 'site' in installer:
        params = install_site(params)
#    if 'mercurial' in installer:
#        install_mercurial_hooks()
    if 'binaries'  in installer:
        fetch_external_binaries()
        install_dependencies()
    if 'database'  in installer:
        params = install_database(params)
    if 'bioformats'  in installer:
        install_bioformats(params)
    if 'matlab'  in installer:
        install_matlab(params)
    if 'runtime'  in installer:
        params = install_runtime(params)
    if 'modules'  in installer:
        install_modules(params)
    if 'servers'  in installer:
        install_servers(params)
    if 'mail'  in installer:
        params = install_mail(params)
    #if options.admin:
    #    setup_admin(params)


    params['bisque.installed'] = "finished"
    params = modify_site_cfg([], params,)

    print STemplate(start_msg).substitute(params)


class CaptureIO(object):
    def __init__(self, logfile):
        self.o = sys.stdout
        self.f = open(logfile,'w')

    def close(self):
        self.f.close()
        sys.stdout = self.o
        
    def __del__(self):
        if 'CaptureIO' in locals() and isinstance(sys.stdout, CaptureIO):
            self.close()
        
    def write(self,s):
        self.o.write(s)
        self.f.write(s); self.f.flush()
    def logged_input(self,prompt):
        response = raw_input(prompt)
        self.f.write (response)
        self.f.write ('\n')
        return response

#capture = CaptureIO('bisque-install.log')
#sys.stdout = capture


def typescript(command, filename="typescript"):
    import sys, os, time
    import pty
    mode = 'wb'
    script = open(filename, mode)
    def read(fd):
        data = os.read(fd, 1024)
        script.write(data)
        return data

    script.write(('Script started on %s\n' % time.asctime()).encode())
    r = pty.spawn(command, read)
    script.write(('Script done on %s\n' % time.asctime()).encode())
    return r

def setup(server_type, options, args):
    virtenv = os.environ.get ('VIRTUAL_ENV', None)
    if virtenv is None:
        print "Cannot determine your python virtual environment"
        print "This make installation much simpler.  Please activate or prepare the environment given by the web instructions"
        if getanswer ("Continue without virtualenv", "N", "Try installation without python virtualenv") == 'N':
            sys.exit(0)

    cancelled = False
    global BQENV
    global BQBIN
    BQENV = virtenv
    BQBIN = os.path.join(BQENV, 'bin') # Our local bin
    if os.name == "nt":
        BQBIN = os.path.join(BQENV, 'Scripts') # windows local bin 
        
    begin_install = datetime.datetime.now()
    if has_script and not options.inscript:
        script = ['bq-admin', 'setup', '--inscript']
        script.extend (args)
        r = typescript(script, 'bisque-install.log')
        #print "RETURN is ", r
        if not cancelled:
            end_install = datetime.datetime.now()
            params = read_site_cfg()
            params['install_started'] = begin_install 
            params['duration'] = str(end_install-begin_install)
            send_installation_report(params)
        sys.exit(0)
        
    
    try:
        params  = bisque_installer(options, args)
    except InstallError, e:
        cancelled = True
    except KeyboardInterrupt:
        print "Interuppted"
        print "Cancelling Installation"
        cancelled = True
    except Exception,e :
        print "An Unknown exception occured %s" % e
        excType, excVal, excTrace  = sys.exc_info()
        msg = ["During setup:", "Exception:"]
        msg.extend (traceback.format_exception(excType,excVal, excTrace))
        msg = "\n".join(msg)

        print msg

#    finally:
#        capture.close();
#        capture = None
#        
#        if not cancelled:
#            end_install = datetime.datetime.now()
#            send_installation_report(params)

if __name__ == "__main__":
    setup('bisque')
