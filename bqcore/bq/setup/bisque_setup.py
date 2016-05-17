#!/usr/bin/env python
from __future__ import with_statement
import traceback
#import package_resources
import os,sys,stat,platform, datetime
import socket
import shutil
import fnmatch
import subprocess
import zipfile
import tarfile
import StringIO
import textwrap
import getpass
import string
import re
import logging
import time
import pprint
import six
import uuid
import posixpath

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



if os.name == 'nt':
    EXEC_EXTS = ['.com', '.exe', '.bat' ]
    SCRIPT_EXT = '.exe'
    ARCHIVE_EXT = '.zip'
else:
    SCRIPT_EXT = ''
    ARCHIVE_EXT = '.tar.gz'
    EXEC_EXTS = ['']

## ENSURE setup.py has been run before..
capture = None
answer_file = None
save_answers = False
use_defaults = False

try:
    import sqlalchemy as sa
    from bq.util.configfile import ConfigFile
    #from bq.model import db_version
except ImportError, e:
    log.exception( "There was a problem with the bisque environment\n"
                   "Have you run %s setup.py yet?" , sys.executable)

    sys.exit(0)

try:
    #pylint:disable=W0611
    import readline
    #readline.parse_and_bind('tab: complete')
    #readline.parse_and_bind('set editing-mode emacs')
except ImportError, e:
    log.info( "No readline available" )

try:
    import pty
    has_script=True
except ImportError:
    has_script=False


class SetupError(Exception):
    'error in setup'

class InstallError(Exception):
    pass


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

def contrib_path(*names):
    return to_sys_path(os.path.join(BQDIR, 'contrib', *names))

def bisque_path(*names):
    return to_sys_path(os.path.join(BQDIR, *names))

QUOTED_CHARS="#"
def quoted(value):
    'quote a value if has special chars'
    return '\"%s\"' % value if any(c in value for c in QUOTED_CHARS ) else value



def which(command):
    """Emulate the Shell command which returning the path of the command
    base on the shell PATH variable
    """
    for d in [ os.path.expanduser (x) for x in os.environ['PATH'].split (os.pathsep)]:
        for ext in EXEC_EXTS:
            path  = os.path.join(d, "%s%s" % (command, ext) )
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
            log.info( "linking %s to %s", f, dest )
            if os.path.exists (dest):
                os.unlink(dest)
            os.link(f, dest)
        except Exception:
            if os.name is not 'nt':
                log.exception( "Problem in link %s .. trying copy" , f)
            shutil.copyfile (f, dest)

def getanswer(question, default, help=None):
    global capture
    if "\n" in question:
        question = textwrap.dedent (question)
    while 1:
        if not save_answers and answer_file:
            a = answer_file.readline().strip()
            if question.strip() != a:
                raise SetupError( "Mismatch '%s' !=  '%s' " % (question, a) )
            a = answer_file.readline().strip()
            answer_file.readline()

        elif capture is not None:
            a =  capture.logged_input ("%s [%s]? " % (question, default))
        else:
            if not use_defaults:
                a =  raw_input ("%s [%s]? " % (question, default))
            else:
                a = default

        if a=='?':
            if help is not None:
                six.print_ (textwrap.dedent(help))
            else:
                six.print_ ("Sorry no help available currently.")
            continue
        y_n = ['Y', 'y', 'N', 'n']
        if default in y_n and a in y_n:
            a = a.upper()

        if a == '': a = default
        if save_answers and answer_file:
            answer_file.write(question)
            answer_file.write ('\n')
            answer_file.write (a)
            answer_file.write ('\n\n')
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
    except Exception:
        if verbose:
            log.exception('in sql %s' % statement)
        return 1, ''


    six.print_ ( "SQL: NOT IMPLEMEMENT %s" % statement )
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


def call(cmd, echo=False, capture=False, **kw):
    """Special version subprocess.call that write output
    """
    lines = []
    if echo:
        six.print_( "Executing '%s'" % ' '.join (cmd))
    if not kw.has_key ('stdout'):
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, **kw)
        while True:
            l = p.stdout.readline()
            if not l: break
            six.print_ (l, end='')
            lines .append(l)
            #p.wait()
    else:
        p = subprocess.Popen(cmd, **kw)

    p.wait()

    if capture:
        return p.returncode, "".join(lines)
    else:
        return p.returncode




def unpack_zip (zfile, dest, strip_root=None):
    z = zipfile.ZipFile (zfile, 'r')
    if strip_root is None:
        z.extractall(dest)
        names = z.namelist()
    else:
        top_dir = z.infolist()[0].filename.split('/',1)[0]+'/'
        names = []
        for info in z.infolist():
            new_path = info.filename.replace(top_dir, '')
            filename = os.path.join(dest, new_path)
            names.append(filename)
            if os.name == 'nt':
                filename = filename.replace('/', '\\')
            mypath = os.path.dirname(filename)
            if not os.path.exists(mypath):
                os.makedirs(mypath)
            # write the file, .extract would force the subpath and can't be used
            try:
                f = open(filename, 'wb')
                f.write(z.read(info))
                f.close()
            except IOError:
                pass
    z.close()
    return names

def newer_file (f1, f2):
    "check if f1 is newer than f2"
    if not os.path.exists(f1) or not os.path.exists(f2):
        return True
    return   os.path.getmtime(f1) > os.path.getmtime(f2)

def touch(fname, times=None):
    "emulate unix touch"
    # http://stackoverflow.com/questions/1158076/implement-touch-using-python
    fhandle = open(fname, 'a')
    try:
        os.utime(fname, times)
    finally:
        fhandle.close()



#############################################
#  Setup some local constants

PYTHON=sys.executable
EXT_SERVER = "http://biodev.ece.ucsb.edu/binaries/depot/" # EXTERNAL host server BQDEPOT
BQDIR = os.path.abspath ('.')  # Our top installation path
BQDEPOT  = os.path.join(BQDIR, "external") # Local directory for externals

BQENV = None
BQBIN = None
SITE_PACKAGES = None

ALEMBIC_CFG  = config_path('alembic.ini')
SITE_CFG     = config_path('site.cfg')
SITE_DEFAULT = config_path('site.cfg.default')
RUNTIME_CFG  = config_path('runtime-bisque.cfg')
UWSGI_DEFAULT = config_path('uwsgi.cfg.default')
PASTER_DEFAULT = config_path('server.ini.default')

#HOSTNAME = socket.getfqdn()
HOSTNAME = "localhost"




#################################################
## Initial values
SITE_VARS = {
    'bisque.server' : 'http://%s:8080' % HOSTNAME,
    'bisque.organization': 'Your Organization',
    'bisque.title': 'Image Repository',
    'bisque.admin_email' : 'YourEmail@YourOrganization',
    'bisque.admin_id' : 'admin',
    'bisque.paths.root' : os.getcwd(),
    }

ENGINE_VARS  ={
#    'bisque.engine': 'http://%s:27000'  % HOSTNAME,
    'bisque.paths.root' : os.getcwd(),
    # 'bisque.admin_email' : 'YourEmail@YourOrganization',
    }

# Add any variables to read from the site.cfg each time
# you run bisque-setup
initial_vars = {
    'bisque.paths.root' : os.getcwd(),
    'bisque.root' : 'http://localhost:8080',
    'bisque.organization': 'Your Organization',
    'bisque.title': 'Image Repository',
    'bisque.admin_email' : 'YourEmail@YourOrganization',
    'bisque.admin_id'    : 'admin',
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
    'h1.url' : '${bisque.server}',
    'bisque.root' : '${bisque.server}',
    'smtp_server' : '${mail.smtp.server}',
    'registration.site_name' : '${bisque.title} (${bisque.server})',
    'registration.host' : '${bisque.server}',
    'registration.mail.smtp_server' : '${mail.smtp.server}',
    'registration.mail.admin_email' : '${bisque.admin_email}',
    'beaker.session.sa.url' : '${sqlalchemy.url}',
}


SITE_QUESTIONS = [
('bisque.server' , 'Enter the root URL of the server ',
                   """A complete URL where your application will be mounted i.e. http://someserver:8080/
#If you server will be mounted behind a proxy, please enter
#the proxy address and see AdvancedInstalls"""),
                  ('bisque.admin_displayname', 'Your real name  administrator account', None),
                  ('bisque.admin_id', 'A login ID for the administrator account', None),
                  ('bisque.admin_email' , 'An email for the administrator', None),
                  ('bisque.organization', 'A small organization title for the main page',
                   "This will show up in the upper left of every page display"),
                  ('bisque.title', 'The main title for the web page header',
                   "The title of your collection, group or project" ),
                  ('bisque.paths.root', 'Installation Directory',
                   'Location of bisque installation.. used for find configuration and data')]


ENGINE_QUESTIONS=[
    #    ('bisque.root' , 'Enter the root URL of the BISQUE server ',
    #     "A URL of Bisque site where this engine will register modules"),
#    ('bisque.engine', "Enter the URL of this bisque module engine",
#     "A module engine offers services over an open URL like a web-server. Please make sure any firewall software allows access to the selected port"),
    ('bisque.paths.root', 'Installation Directory',
     'Location of bisque installation.. used for find configuration and data'),]



DB_QUESTIONS = [('sqlalchemy.url', 'A database URI', """
                  A SQLAlchemy DBURI (see http://www.sqlalchemy.org/).
                  Examples of typical DB URI:
                      sqlite:///bisque.db
                      postgresql://localhost:5432/bisque
                      mysql://user:pass@localhost/bisque
                      mysql://user:pass@localhost/bisque?unix_socket=/bisque-data/mysql-db/mysql-socket.sock
                  """),
               ]

MATLAB_QUESTIONS=[
    ('runtime.matlab_home', "Enter toplevel matlab directory (under which is bin)",
     "matlab home is used by modules to setup the correct environment variables"),

    ]
RUNTIME_QUESTIONS=[
    ('runtime.platforms', "Enter a list (comma,seperated) of module platforms",
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

#####################################################
# Installer routines
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
# config editing
BQ_SECTION="app:main"

def install_cfg (site_cfg, section, default_cfg):
    if not os.path.exists (site_cfg):
        shutil.copyfile(default_cfg, site_cfg)
    params = read_site_cfg(cfg=site_cfg, section=section)
    return params

def read_site_cfg(cfg , section):
    "Read the config and return a dict with elements found"
    bisque_vars = {}

    # first pull initial values from config files
    #iv = initial
    tc = ConfigFile()
    if os.path.exists (cfg):
        tc.read(open(cfg))
        bisque_vars.update(tc.get(section, asdict=True))

    return bisque_vars


def visible(k,v):
    return not k.startswith('__')

def update_site_cfg (bisque_vars, section = BQ_SECTION, append=True, cfg=SITE_CFG, filterby = visible ):
    """Read the config file and update the variables in a section
    @param bisque_vars: dict of variables
    @param section: name of section to modify
    @param append:  bool append new variables
    @param cfg : the file to modify
    """

    c = ConfigFile()
    if os.path.exists (cfg):
        c.read(open(cfg))

    for k,v in bisque_vars.items():
        if filterby is None or filterby(k, v):
            c.edit_config (section, k, '%s = %s' % (k,quoted(str(v))), {}, append)
        #print "edit %s %s" % (k,v)
    c.write (open (cfg, 'w'))
    return bisque_vars


def modify_site_cfg(qs, bisque_vars, section = BQ_SECTION, append=True, cfg=SITE_CFG):
    """Ask questions and modify a config file
    see update_site_cfg
    """

    if not os.path.exists (cfg):
        raise InstallError('missing %s' % cfg)

    bisque_vars =  update_variables(qs, bisque_vars )
    for k,v in linked_vars.items():
        if k in bisque_vars:
            bisque_vars [k] = v
    bisque_vars =  update_variables([], bisque_vars )

    c = ConfigFile()
    c.read(open(cfg))
    for k,v in bisque_vars.items():
        c.edit_config (section, k, '%s = %s' % (k,quoted(str(v))), {}, append)
        #print "edit %s %s" % (k,v)
    c.write (open (cfg, 'w'))
    return bisque_vars



############################################
# Database

DB_CREATE_ERROR = """
*** Database creation failed ***
Please check your db url to ensure that it is in the correct format.
Also please ensure that the user specified can actually create/access a database.
"""

def create_postgres_sa (dburl):
    "Check existance of database base and create new if needed"
    dbstr = str (dburl)
    template1 = posixpath.join (posixpath.dirname (dbstr), "template1")
    dbname    = posixpath.basename (dbstr)

    engine = sa.create_engine(template1)
    conn   = engine.connect()
    # End automatic Postgres  transaction with commit
    conn.execute("commit")
    # create new database
    conn.execute("create database %s" % dbname)
    conn.close()
    log.info ("Created postgresql database %s", dbname)
    return True


def create_postgres_psql (dburl):
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
        six.print_ ("Database exists, not creating")
        return False
    # http://www.faqs.org/docs/ppbook/x17149.htm
    # psql needs a database to connect to even when creating.. use template1
    if dburl.password:
        stdin = StringIO.StringIO(dburl.password)
    if call (command + ['-c', 'create database %s' % dburl.database, 'template1'], echo=True,
             stdin = stdin) != 0:
        six.print_( DB_CREATE_ERROR)
        return False

    return True



###############
#

def create_mysql_sa(dburl):
    "Create a new mysql database "
    dbstr = str(dburl)
    connecturl = posixpath.dirname (dbstr)
    dbname     = posixpath.basename (dbstr)

    engine = sa.create_engine (connecturl)
    engine.execute ("CREATE DATABASE %s" % dbname)
    log.info ("Created mysql database %s", dbname)
    return True

def create_mysql_cmd(dburl):
    command = [ 'mysql' ]
    if dburl.query.has_key('unix_socket'):
        command.append ( '--socket=%s' % dburl.query['unix_socket'] )
    if dburl.username:
        command.append ('-u%s' % dburl.username)
    if dburl.password:
        command.append ('-p%s' % dburl.password)

    six.print_( "PLEASE ignore 'ERROR (...)Unknown database ..' ")
    if call (command+[dburl.database, '-e', 'quit'], echo=True) == 0:
        print "Database exists, not creating"
        return False

    if call (command+['-e', 'create database %s' % dburl.database], echo=True) != 0:
        six.print_( DB_CREATE_ERROR )
        return False
    return True


###############
#
def create_sqlite (dburl):
    return True


known_db_types = {
    'sqlite'     : ('sqlite3', '',   create_sqlite ),
    'postgres'   : ('psycopg2',  'psycopg2', create_postgres_sa   ),
    'postgresql' : ('psycopg2',  'psycopg2',  create_postgres_sa  ),
    'mysql'      : ('_mysql',    'mysql-python', create_mysql_sa ),
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
            except Exception:
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
    except Exception:
        log.warn("Could not contact database %s. It may not exist yet", str(DBURL))
        return False

def get_dburi(params):

    if os.getenv('BISQUE_DBURL'):
        params['sqlalchemy.url'] = os.getenv('BISQUE_DBURL')
    params = modify_site_cfg(DB_QUESTIONS, params)
    dburi = os.getenv('BISQUE_DBURL') or params.get('sqlalchemy.url', None)
    DBURL = sa.engine.url.make_url (dburi)
    return params, DBURL


def test_db_alembic (DBURL):
    r, out = sql(DBURL, 'select * from alembic_version')
    return r == 0

def test_db_sqlmigrate(DBURL):
    r, out = sql(DBURL, 'select * from migrate_version')
    return r == 0

def test_db_initialized(DBURL):
    r, out = sql(DBURL, 'select * from taggable limit 1')
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
        params, DBURL = get_dburi(params)
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
        print("""Database   driver was bit installed.  Missing packages?
Please resolve the problem(s) and re-run 'bisque-setup --database'.""")
        return params

    if getanswer("Create and initialize database", "Y", "Create, initialize or upgrade database") == "Y":
        params = setup_database (params)
    return params


def setup_database (params):
    try:
        params, DBURL = get_dburi(params)
    except sa.exc.ArgumentError:
        log.exception( "Unable to understand DB url. Please see SqlAlchemy" )
        return params
    # Step 2: check whether the database exists and is accessible
    if not create_database(DBURL):
        print "database not created"
        return params
    # Step 3: find out whether the database needs initialization
    params = initialize_database(params, DBURL)
    # Step 4: migrate database (and project to latest version)"
    if not params['new_database']:
        migrate_database(DBURL)
    return params

def create_database(DBURL):
    "Create a database based on the DB URL"

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
                except Exception:
                    log.exception('Could not create database')

    if not db_exists:
        print( """
        Database was NOT prepared -- either server has no database '%s'
        or user "%s" has no rights to access this database.
        Please fix the problem(s) and re-run 'bq-admin setup createdb'
        """ % (DBURL.database,DBURL.username) )
        return False
    return True


def initialize_database(params, DBURL=None):
    "Initialize the database with tables"

    if DBURL:
        db_initialized = test_db_initialized(DBURL)
    else:
        db_initialized = True

    params['new_database'] = False
    install_cfg(ALEMBIC_CFG, section="alembic", default_cfg=config_path('alembic.ini.default'))
    update_site_cfg(params, section='alembic', cfg = ALEMBIC_CFG, append=False)
    if not db_initialized and getanswer(
        "Intialize the new database",  "Y",
        """
        The database is freshly created and doesn't seem to have
        any tables yet.  Allow the system to create them..
        """) == "Y":
        if call (['paster','setup-app', config_path('site.cfg')]) != 0:
            raise SetupError("There was a problem initializing the Database")
        params['new_database'] = True
    return params


def migrate_database(DBURL=None):
    "Attempt to migrate existing database to latest version"

    #if DBURL and test_db_sqlmigrate(DBURL):
    #    print "Upgrading database version (sqlmigrate)"
    #    call ([PYTHON, to_sys_path ('bqcore/migration/manage.py'), 'upgrade'])

    #if not params['new_database'] : #and test_db_alembic(DBURL):
    print "Upgrading database version (alembic)"
    if call (["alembic", '-c', config_path('alembic.ini'), 'upgrade', 'head']) != 0:
        raise SetupError("There was a problem initializing the Database")




#######################################################
# Matlab
def install_matlab(params, cfg = RUNTIME_CFG):
    #print params
    matlab_home = which('matlab')
    if matlab_home:
        params['runtime.matlab_home'] = os.path.abspath(os.path.join (matlab_home, '../..'))
    if params['runtime.matlab_launcher'] == 'config/templates/matlab_launcher_SYS.tmpl':
        if os.name == 'nt':
            params['runtime.matlab_launcher'] = 'config/templates/matlab_launcher_win.tmpl'
        else:
            params['runtime.matlab_launcher'] = 'config/templates/matlab_launcher.tmpl'
    for f in ['runtime.matlab_launcher' ] :
        if os.path.exists(params[f]):
            params[f] = os.path.abspath(params[f])

    while True:
        params = modify_site_cfg(MATLAB_QUESTIONS, params, section=None, cfg=cfg)
        if  os.path.exists(params['runtime.matlab_home']):
            break
        if  getanswer("Matlab not found: Try again", 'N',
                      "Matlab (and compile) is needed for many modules") == 'Y':
            continue
        print "Matlab must be provided to install modules"
        params['matlab_installed'] = False
        break


    #install_matlabwrap(params)
    return params


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
# Modules

def install_modules(params):
    # Check each module for an install script and run it.
    ans =  getanswer( "Try to setup modules", 'N',
                  "Run the installation scripts on the modules. Some of these require local compilations and have outside dependencies. Please monitor carefullly")
    if ans != 'Y':
        return params
    if not os.path.exists(bisque_path('modules')):
        os.makedirs (bisque_path('modules'))
        print "No modules were found on the system. Please install sample modules from http://biodev.ece.ucsb.edu/binaries/depot/bisque-modules.tgz"
        return params

    environ = dict(os.environ)
    environ.pop ('DISPLAY', None) # Makes matlab hiccup
    environ['BISQUE_ROOT'] = os.getcwd()
    for bm in os.listdir (bisque_path('modules')):
        modpath = bisque_path('modules', bm)
        # if os.path.isdir(modpath) and os.path.exists(os.path.join(modpath, "runtime-module.cfg")):
        #     cfg_path = os.path.join(modpath, 'runtime-bisque.cfg')
        #     copy_link(RUNTIME_CFG, cfg_path)
        if os.path.exists(os.path.join(modpath, 'setup.py')):
            cwd = os.getcwd()
            os.chdir (modpath)
            print "################################"
            print "Running setup.py in %s" % modpath
            try:
                r = call ([PYTHON, '-u', 'setup.py'], env=environ)
                if r != 0:
                    print "setup in %s returned error " % modpath
            except Exception, e:
                log.exception ("An exception occured during the module setup: %s" % str(e))
            os.chdir (cwd)
    return params




#######################################################
# initial configuration files

def install_server_defaults(params):
    "Install initial configuration for a bisque server"
    print "Server config"
    new_install = False

    if not os.path.exists(config_path('server.ini')):
        shutil.copyfile(config_path('server.ini.default'), config_path('server.ini'))

    if not os.path.exists(config_path('shell.ini')):
        shutil.copyfile(config_path('shell.ini.default'), config_path('shell.ini'))

    if not os.path.exists(config_path('who.ini')):
        shutil.copy(config_path('who.ini.default'), config_path('who.ini'))


    if not os.path.exists(config_path('registration.cfg')):
        shutil.copyfile(config_path('registration.cfg.default'), config_path('registration.cfg'))

    if not os.path.exists(SITE_CFG):
        params = install_cfg(SITE_CFG, section=BQ_SECTION, default_cfg=config_path('site.cfg.default') )
        params.update(SITE_VARS)
        new_install = True

    print "Top level site variables are:"
    for k in sorted(SITE_VARS.keys()):
        if k not in params:
            params[k] = SITE_VARS[k]
        print "  %s=%s" % (k,params[k])

    if getanswer("Change a site variable", 'N')=='Y':
        params = modify_site_cfg(SITE_QUESTIONS, params)

        path = urlparse.urlparse(params['bisque.server']).path
        params['bisque.root'] = path

    if new_install:
        server_params = {  'h1.url' : params['bisque.server']}
        server_params = update_site_cfg(server_params, 'servers', append=False)

    if getanswer ('Do you want to create new server configuations', 'Y',
                  "Use an editor to edit the server section (see http://biodev.ece.ucsb.edu/projects/bisquik/wiki/Installation/ParsingSiteCfg )") == 'Y':
        setup_server_cfg(params)

    return params


def setup_server_cfg (params):
    'Edit the server section of the site.cfg'

    server_params = read_site_cfg (SITE_CFG, 'servers')
    pprint.pprint (server_params)
    previous_backend = server_params['backend']

    status = 0
    if getanswer ('Edit servers in site.cfg ', 'N',
                  "Please edit only the server section ") != 'N':
        editor = os.environ.get ('EDITOR', which ('vi'))
        if editor is not None:
            status = subprocess.call ([editor, SITE_CFG])
        else:
            print "No editor found. Please set EDITOR"
            return

    if status != 0:
        print "GOT status", status
        return params

    server_params = read_site_cfg (SITE_CFG, 'servers')
    if server_params['backend'] == 'uwsgi':
        params = setup_uwsgi(params, server_params)
    if server_params['backend'] == 'paster':
        params = setup_paster(params, server_params)
    return params



def install_engine_defaults(params):
    "Install initial configuration for a bisque engine"
    print "Engine config"
    new_install = False

    if not os.path.exists(config_path('server.ini')):
        shutil.copyfile(config_path('server.ini.default'), config_path('server.ini'))

    if not os.path.exists(config_path('shell.ini')):
        shutil.copyfile(config_path('shell.ini.default'), config_path('shell.ini'))

    if not os.path.exists(config_path('who.ini')):
        shutil.copy(config_path('who.engine.ini'), config_path('who.ini'))

    if not os.path.exists(SITE_CFG):
        params = install_cfg(SITE_CFG, section=BQ_SECTION, default_cfg=config_path('engine.cfg.default'))
        params.update(ENGINE_VARS)
        new_install = True

    print "Top level site variables are:"
    for k in sorted(ENGINE_VARS.keys()):
        if k not in params:
            params[k] = ENGINE_VARS[k]
        print "  %s=%s" % (k,params[k])

    if getanswer("Change a site variable", 'Y')=='Y':
        params = modify_site_cfg(SITE_QUESTIONS, params)

    if getanswer("Update servers", 'Y' if new_install else 'N', 'Modify [server] section of site.cfg') == 'Y':
        server_params = { 'e1.proxyroot' : params['bisque.root'], 'e1.url' : params['bisque.engine'], }
        server_params = update_site_cfg(server_params, 'servers', append=False )
        params.update(server_params)
    else:
        print "Warning: Please review the [server] section of site.cfg after modifying site variables"
    return params



def install_proxy(params):
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
def check_condor (params, cfg  = RUNTIME_CFG):
    try:

        if os.path.exists('/dev/null'):
            devnull = open ('/dev/null')
        else:
            import tempfile
            devnull = tempfile.TemporaryFile(mode='w')

        retcode = call ([ 'condor_status' ], stdout=devnull, stderr=devnull )
    except OSError:
        print "No condor was found. See bisque website for details on using condor"
        return params
    print "Condor job management software has been found on your system"
    print "Bisque can use condor facilities for some module execution"

    if getanswer("Configure modules for condor", 'Y',
                 "Configure condor shared directories for better performance")=="Y":
        if 'condor' not in params['runtime.platforms']:
            params['runtime.platforms'] = ','.join (['condor', params['runtime.platforms']])

        print """
        NOTE: condor configuration is complex and must be tuned to
        every instance.  Bisque will try to use the condor facilities
        but please check that this is operating correctly for your
        installation

        Please check the wiki at biodev.ece.ucsb.edu/projects/bisquik/wiki/AdvancedInstalls#CondorConfiguration
        """

        params = read_site_cfg(cfg=cfg, section='condor', )
        params['condor.enabled'] = "True"
        #print params
        if getanswer("Advanced Bisque-Condor configuration", "N",
                     "Change the condor templates used for submitting jobs")!='Y':
            for f in ['condor.dag_template', 'condor.submit_template', 'condor.dag_config_template']:
                if os.path.exists(params[f]):
                    params[f] = os.path.abspath(params[f])

            update_site_cfg(params, section="condor", cfg=cfg)
            return params

        params = modify_site_cfg(CONDOR_QUESTIONS, params, section='condor', cfg=cfg)
        for v, d, h in CONDOR_QUESTIONS:
            if params[v]:
                params[v] = os.path.abspath(os.path.expanduser(params[v]))
                print "CONDOR", v, params[v]
        update_site_cfg(params, section="condor", cfg=cfg)

    return params



def install_runtime(params, cfg = RUNTIME_CFG):
    """Check and install runtime control files"""

    params['runtime.platforms'] = "command"
    check_condor(params, cfg=cfg)

    params = modify_site_cfg(RUNTIME_QUESTIONS, params, section=None, cfg=cfg)
    staging=params['runtime.staging_base'] = os.path.abspath(os.path.expanduser(params['runtime.staging_base']))

    update_site_cfg(params, section=None, cfg=cfg)

    # for bm in os.listdir (bisque_path('modules')):
    #     modpath = bisque_path('modules', bm)
    #     if os.path.isdir(modpath) and os.path.exists(os.path.join(modpath, "runtime-module.cfg")):
    #         cfg_path = os.path.join(modpath, 'runtime-bisque.cfg')
    #         copy_link(RUNTIME_CFG, cfg_path)
    try:
        if not os.path.exists(staging):
            os.makedirs(staging)
    except OSError,e:
        print "%s does not exist and cannot create: %s" % (staging, e)

    return params




#######################################################
#

def install_mail(params):
    MAIL_QUESTIONS = [
        ('mail.smtp.server', "Enter your smtp mail server",
         "The mail server that delivers mail.. often localhost"),
    ]

    params['mail.smtp.server'] = os.getenv('MAIL_SERVER', params['mail.smtp.server'])


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

def install_preferences(params):
    if params.get('new_database'): #already initialized
        return params
    if getanswer ("Initialize Preferences ","N",
                  """Initialize system preferences.. new systems will
requires this while, upgraded system may depending on chnages""")!="Y":
        return params
    cmd = ['bq-admin', 'preferences', 'init', ]
    if getanswer("Force initialization ", "Y", "Replace any existing preferences with new ones") == "Y":
        cmd.append ('-f')
    r  = subprocess.call (cmd, stderr = None)
    if r!=0:
        print "Problem initializing preferences.. please use bq-admin preferences"
    return params


#######################################################

def install_public_static(params):
    "Setup up public JS area with all static resources"

    if getanswer("Deploy all static resources to public directory", "Y",
                 "Usefull for integrating with frontend webserverv") == 'Y':
        cmd = ['bq-admin', 'deploy', 'public' ]
        r  = subprocess.call (cmd, stderr = None)
        if r!=0:
            print 'Problem deploying static resources... run "bq-admin deploy public" manually'

    return params

#######################################################

def install_secrets(params):
    "Ensure cookies are unique across sites"

    secrets = os.getenv ("BISQUE_SECRET", None) or "secrets"
    secrets = getanswer("Encrypt cookies with secret phrase", secrets,
                        "Login informations if encoded with this secret")
    who_cfg = config_path ("who.ini")

    update_site_cfg(cfg=who_cfg, section='plugin:auth_tkt', bisque_vars= { 'secret' : secrets })
    # Update the beaker session secret also
    update_site_cfg(bisque_vars= { 'beaker.session.secret' : secrets }, append=False)
    params ['beaker.session.secret'] = secrets
    return params


#######################################################
#
def setup_uwsgi(params, server_params):
    if getanswer("Install uwsgi (application server and configs)", 'Y',
                 "Uwsgi can act as backend server when utilized with web-front end (Nginx)") != 'Y':
        return params
    if which ('uwsgi') is None:
        easy_install.main(['-U','uwsgi'])

    from bq.util.dotnested import parse_nested, unparse_nested
    servers = [ x.strip() for x in server_params['servers'].split(',') ]
    servers =  parse_nested (server_params, servers)
    print servers
    for server, sv in servers.items():
        cfg = config_path ("%s_uwsgi.cfg" % server)

        if os.path.exists (cfg) and os.path.exists(SITE_CFG):
            cfg_time  = os.stat(cfg).st_mtime
            site_time = os.stat (SITE_CFG).st_mtime
            if cfg_time - site_time > 60:
                if getanswer ("%s looks newer than %s.. modify" % (cfg, SITE_CFG), "N",
                              "%s may have special modifications" %cfg) == "N":
                    continue
        install_cfg (cfg, section="*", default_cfg=UWSGI_DEFAULT)

        uwsgi_vars = sv.get ('uwsgi', {})
        bisque_vars = sv.get ('bisque', {})

        if 'socket' in uwsgi_vars:
            uwsgi_vars['socket'] =  uwsgi_vars['socket'].replace('unix://','').strip()

        svars = { #'bisque.root' : sv['url'],
                  'bisque.server' : sv['url'],
                  'bisque.services_disabled' : sv.get ('services_disabled', ''),
                  'bisque.services_enabled'  : sv.get ('services_enabled', ''),
                }
        for k,v in unparse_nested (bisque_vars):
            svars["bisque.%s" % k] = v

        uwsgi_vars ['virtualenv'] = BQENV
        uwsgi_vars ['procname-prefix'] = "bisque_%s_" % server
        update_site_cfg(cfg=cfg, bisque_vars=svars)
        update_site_cfg(cfg=cfg, section='uwsgi',bisque_vars = uwsgi_vars )
        update_site_cfg(cfg=cfg, section='sa_auth',
                        bisque_vars = { 'cookie_secret' : uuid.uuid4()} )
    return params

#######################################################
#
def setup_paster(params, server_params):
    if getanswer("Install paster (application server and configs)", 'Y',
                 "Paster is the default backend server") != 'Y':
        return params

    from bq.util.dotnested import parse_nested, unparse_nested
    servers = [ x.strip() for x in server_params['servers'].split(',') ]
    servers =  parse_nested (server_params, servers)
    print servers

    for server, sv in servers.items():
        cfg = config_path ("%s_paster.cfg" % server)
        if os.path.exists (cfg) and os.path.exists(SITE_CFG):
            cfg_time  = os.stat(cfg).st_mtime
            site_time = os.stat (SITE_CFG).st_mtime
            if cfg_time - site_time > 60:
                if getanswer ("%s looks newer than %s.. modify" % (cfg, SITE_CFG), "N",
                              "%s may have special modifications" %cfg) == "N":
                    continue
        install_cfg (cfg, section="*", default_cfg=PASTER_DEFAULT)

        paster_vars = sv.get ('paster', {})
        bisque_vars = sv.get ('bisque', {})

        svars = { #'bisque.root' : sv['url'],
                  'bisque.server' : sv['url'],
                  'bisque.services_disabled' : sv.get ('services_disabled', ''),
                  'bisque.services_enabled'  : sv.get ('services_enabled', ''),
                }

        for k,v in unparse_nested (bisque_vars):
            svars["bisque.%s" % k] = str(v)

        #svars.update (bisque_vars)

        fullurl = urlparse.urlparse (sv['url'])
        if 'host' not in paster_vars:
            paster_vars['host'] = fullurl[1].split(':')[0]
        if 'port' not in paster_vars:
            paster_vars['port'] = str(fullurl.port)

        update_site_cfg(cfg=cfg, bisque_vars=svars)
        update_site_cfg(cfg=cfg, section='server:main',bisque_vars = paster_vars )
        update_site_cfg(cfg=cfg, section='sa_auth',
                        bisque_vars = { 'cookie_secret' : uuid.uuid4()} )


    return params



#######################################################
#

import urllib2
import urlparse
import hashlib
def _sha1hash(data):
    return hashlib.sha1(data).hexdigest().upper()

def fetch_external_binaries (params):
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
            with  open(dest, 'rb') as f:
                shash = _sha1hash (f.read())
            if sha1 == shash:
                print "%s found locally" % name
                return

        fetch_url = urlparse.urljoin(EXT_SERVER,  hash_name)
        print "Fetching %s" % fetch_url
        handle = urllib2.urlopen (fetch_url)
        data   = handle.read()
        info   = handle.info()
        handle.close()

        if sha1 != _sha1hash(data):
            raise Exception('hash mismatch in %s' % name)
        handle = open(dest, 'wb')
        handle.write(data)
        print "Wrote %s in %s" % (name, where)
        handle.close()

        # Set the time to Server File  time.
        from dateutil.parser import parse
        from dateutil import tz
        try:
            mtime = parse (info['Last-Modified']).astimezone(tz.tzlocal())
            srvLastModified = time.mktime(mtime.timetuple())
            touch (dest, (srvLastModified, srvLastModified))
        except (ValueError):
            pass

    if getanswer ("Fetch external binary files from Bisque development server",
                  "Y",
                  "This action is required only on first download") != 'Y':
        return params

    if not os.path.exists(BQDEPOT):
        os.makedirs (BQDEPOT)
    conf = ConfigFile(config_path('EXTERNAL_FILES'))
    external_files = conf.get ('common')
    #local_platform = platform.platform()
    local_platform = platform.platform().replace('-', '-%s-'%platform.architecture()[0], 1) # dima: added 64bit
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
                log.exception ("Problem in fetch")
                print "Failed to fetch '%s' with %s" % (fname,e)

    return params

#######################################################
#
def uncompress_dependencies (archive, filename_dest, filename_check, strip_root=None):
    """Install dependencies that aren't handled by setup.py"""

    if os.path.exists(filename_check) and os.path.getmtime(archive) < os.path.getmtime(filename_check):
        return

    print "Unpacking %s into %s"  % (archive, filename_dest)
    if tarfile.is_tarfile(archive):
        return tarfile.open(archive).extractall (filename_dest)
    else:
        return unpack_zip(archive, filename_dest, strip_root)

def uncompress_extjs (extzip, public, extjs):
    """Install extjs"""

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

def install_dependencies (params):
    """Install dependencies that aren't handled by setup.py"""

    # install ExtJS
    extzip = os.path.join(BQDEPOT, 'extjs.zip')
    public = to_sys_path('bqcore/bq/core/public')
    extjs =  os.path.join (public, "extjs")
    uncompress_extjs (extzip, public, extjs)

    install_imgcnv()
    install_imarisconvert()
    install_openslide()
    install_bioformats()

    return params


#######################################################
# Image Converters

def install_imgcnv ():
    """Install dependencies that aren't handled by setup.py"""

    filename_zip = os.path.join(BQDEPOT, 'imgcnv.zip')
    imgcnv = which('imgcnv')
    if imgcnv :
        r, version = call ([ imgcnv, '-v'], capture = True)
        if r == 0:
            print "Found imgcnv version %s" % version
        if  not os.path.exists(filename_zip):
            print "Imgcnv is installed and no-precompiled version exists. Using installed version"
            return

    if not os.path.exists(filename_zip):
        print "No pre-compiled version of imgcnv exists for your system"
        print "Please visit biodev.ece.ucsb.edu/projects/imgcnv"
        print "or visit our mailing list https://groups.google.com/forum/#!forum/bisque-bioimage"
        print "for help"
        return


    if getanswer ("Install Bio-Image Convert", "Y",
                  "imgcnv will allow image server to read pixel data") == "Y":

        filename_check = os.path.join(BQBIN, 'imgcnv%s'% SCRIPT_EXT)
        uncompress_dependencies (filename_zip, BQBIN, filename_check)

def install_openslide ():
    """Install dependencies that aren't handled by setup.py"""

    archive = os.path.join(BQDEPOT, 'openslide-bisque%s' % ARCHIVE_EXT)
    if not os.path.exists(archive):
        print "No pre-compiled version of openslide exists for your system"
        print "Please visit our mailing list https://groups.google.com/forum/#!forum/bisque-bioimage for help"
        return
    if getanswer ("Install OpenSlide converter", "Y",
                  "OpenSlide will allow image server to read full slide pixel data") == "Y":
        uncompress_dependencies (archive, BQBIN, '')


def install_bioformats():

    archive = os.path.join(BQDEPOT, 'bioformats-pack.zip')
    filename_check = os.path.join(BQBIN, 'bioformats_package.jar')

    if not newer_file(archive, filename_check):
        print "Bioformats is up to date"
        return

    if getanswer ("Install bioformats", "Y",
                  "Bioformats can be used as a backup to read many image file types") == "Y":

        old_bf_files = [
            'bfconvert', 'bfconvert.bat', 'bfview', 'bfview.bat', 'bio-formats.jar',
            'domainlist', 'domainlist.bat', 'editor', 'editor.bat', 'formatlist',
            'formatlist.bat', 'ijview', 'ijview.bat', 'jai_imageio.jar', 'list.txt',
            'loci_plugins.jar', 'loci_tools.jar', 'loci-common.jar', 'loci-testing-framework.jar',
            'log4j.properties', 'lwf-stubs.jar', 'mdbtools-java.jar', 'metakit.jar', 'notes',
            'notes.bat', 'ome_plugins.jar', 'ome_tools.jar', 'ome-editor.jar', 'ome-io.jar',
            'omeul', 'omeul.bat', 'ome-xml.jar', 'poi-loci.jar', 'scifio.jar', 'showinf',
            'showinf.bat', 'tiffcomment', 'tiffcomment.bat', 'xmlindent', 'xmlindent.bat', 'xmlvalid', 'xmlvalid.bat'
        ]

        # first remove old files
        for f in old_bf_files:
            p = os.path.join(BQBIN ,f)
            if os.path.exists(p):
                os.remove(p)

        biozip = zipfile.ZipFile (archive)
        for fname in  biozip.namelist():
            if fname[-1] == '/':  # skip dirs
                continue
            dest = os.path.join(BQBIN, os.path.basename(fname))

            data = biozip.read(fname)
            fd = open(dest, 'wb')
            fd.write(data)
            if not fname.endswith ('jar'):
                os.chmod (dest, os.fstat(fd.fileno()).st_mode | stat.S_IXUSR)  # User exec
            fd.close()

        # python >2.6
        #biozip.extractall(os.path.join(BQENV, "bin"))
        biozip.close()

def install_imarisconvert ():
    """Install dependencies that aren't handled by setup.py"""

    archive = os.path.join(BQDEPOT, 'ImarisConvert%s' % ARCHIVE_EXT)
    if not os.path.exists(archive):
        print "No pre-compiled version of ImarisConvert exists for your system"
        print "Please visit our mailing list https://groups.google.com/forum/#!forum/bisque-bioimage for help"
        return
    filename_check = which ("ImarisConvert")
    filename_check = filename_check or os.path.join (BQBIN, 'ImarisConvert%s' % SCRIPT_EXT)
    if not newer_file(archive, filename_check) :
        print "ImarisConvert is up to date"
        return
    if  getanswer ("Install ImarisConvert", "Y",
                      "ImarisConvert will allow image server to read many image formats") == "Y":
        uncompress_dependencies (archive, BQBIN, filename_check)
        touch (filename_check)

############################
# Features server deps


def install_features (params):
    """Install dependencies that aren't handled by setup.py"""

    if getanswer ("Install feature extractors (Feature Server)", "Y",
                  "Feature extractors will enable many descriptors in the Feature Server that require binary code") == "Y":

        filename_zip = os.path.join(BQDEPOT, 'feature_extractors.zip')
        filename_dest = to_sys_path('bqfeature/bq')
        filename_check = ''
        uncompress_dependencies (filename_zip, filename_dest, filename_check)

        install_features_source()
        install_libtiff()
        install_opencv()

    return params


def install_features_source ():
    """Install dependencies that aren't handled by setup.py"""

    if getanswer ("Install source code for feature extractors", "N",
                  "Feature descriptors source code will allow recompiling external feature extractors on unsupported platforms") == "Y":

        filename_zip = os.path.join(BQDEPOT, 'feature_extractors_source.zip')
        import urllib
        urllib.urlretrieve ('https://bitbucket.org/bisque/featureextractors/get/default.zip', filename_zip)
        filename_dest = to_sys_path('bqfeature/bq/src')
        filename_check = ''
        uncompress_dependencies (filename_zip, filename_dest, filename_check, strip_root=True)

        print """Now you can recompile feature extractors. Follow instructions located in:
          bqserver/bq/features/src/extractors/build/Readme.txt
        """

def install_libtiff():
    """
        Install dependencies that aren't handled by setup.py

        Downloads and installs libtiff-4.0.3 in sitepackages in bqenv/Scripts

        Only for Windows, for debian linux use apt-get
    """
    import urllib
    src = 'https://bitbucket.org/bisque/pylibtiff/downloads/LibTiff-4.0.3-Windows-64bit.zip'
    filename_zip = os.path.join(BQDEPOT, 'LibTiff-4.0.3-Windows-64bit.zip')
    filename_dest = bisque_path(os.path.join('bqenv','Scripts'))
    filename_check = ''

    if sys.platform == 'win32':
        if getanswer ("Install libtiff-4.0.3", "Y",
                      "Enables reading OME-bigtiff for feature extraction") == "Y":
            print 'Fetching from %s'%src

            urllib.urlretrieve ( src, filename_zip)
            uncompress_dependencies ( filename_zip, filename_dest, filename_check, strip_root=True)
            print 'Installed libtiff-4.0.3 in %s'%filename_dest
    else:
        print """To enable the feature service to read OME-bigtiff for feature extraction install
        libtiff4
        For Debian use the command apt-get install libtiff5-dev
        """

def install_opencv():
    """
        Install dependencies that aren't handled by setup.py

        Downloads and installs opencv in sitepackages in bqenv
    """

    def extract_archive_dir(zip_file,zip_dir,destination,verbose = True):
        """
            unzips files in dir in the zipfile
            warning: can not extract a dir in that dir
            @zip_file - name of the zip file
            @zip_dir - path to the dir in the zip file from the root file in the zip
            @destination - dir were the extracted files will be placed
            @verbose

            @output - none
        """

        #with zipfile.ZipFile(zip_file, 'r') as z:  # KGK Not available in 2.6
        z =  zipfile.ZipFile(zip_file, 'r')
        for f in z.namelist():
            if os.path.normpath(f).startswith(zip_dir) and not os.path.normpath(f) == zip_dir:
                with open(os.path.join(destination,os.path.relpath(f, zip_dir)), 'wb') as fout:
                    fout.write(z.read(f))
                    if verbose:
                        print 'Extracted %s -> %s'%(f,os.path.join(destination,os.path.relpath(f, zip_dir)))


    if getanswer ("Install OpenCV-2.4.6", "Y",
                  "Enables descriptors in the Feature Server that use OpenCV-2.4.6") == "Y":

        filename_check = ''
        python_version = sys.version_info[:2]
        if not (python_version==(2,6) or python_version==(2,7)):
            print 'Failed to install opencv. Requires python 2.6 or 2.7.'
            return
        filename_zip = os.path.join(BQDEPOT, 'opencv-2.4.6.zip')
        if sys.platform.startswith ('win'): #windows
            extract_archive_dir(filename_zip,os.path.join('opencv-2.4.6','static_libs',''), SITE_PACKAGES)
        elif sys.platform.startswith('linux'):
            pass
        else:
            print 'Failed to install opencv. System type is neither linux or windows'
            return

        #unpackes opencv cv2.so/.dll and cv.py in to bqenv site-packages
        extract_archive_dir(filename_zip,os.path.join('opencv-2.4.6','python%s.%s'%python_version,''), SITE_PACKAGES)


#######################################################
#
def setup_admin(params):
    try:
        params, DBURL = get_dburi(params)
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


############################################
# Upgrade scripts
def kill_server(params):
    "Attempt to kill the server"

    if getanswer ("Stop server for upgrade", "Y",
                  "Server must be restarted during an upgrade operation") == "Y":
        r = call(['bq-admin', 'server', 'stop'])
        print "Server is *not* automatically restarted"
    else:
        print "Proceeding with upgrade with (possibly) running server (dangerous)"

    return params



def fetch_stable (params):
    r = call (['hg', 'pull', '-u'])
    if r!= 0:
        print("There was a problem fetching new version")
        return
    return params

def migrate(params):
    "migrate db, site.cfg, and preferences "

    # Step 1: migrate db
    migrate_database()

    #Step 2: migrate site.cfg
    print "NO automatic way to upgrade site.cfg.. please check site.cfg.default"

    #Step 3: migrate preferences
    print "No Automatic way to migrate system preferences.. please check config/preferences.xml.default"

    return params


def cleanup(params):
    "clean up caches and prepare for restart"

    from bq.util.paths import data_path

    # support function: check and remove data tree
    def cleandata (path):
        rpath = os.path.realpath(data_path (path))
        if os.path.exists (rpath):
            shutil.rmtree(rpath)

    if getanswer("Purge cache", "Y", "cleaning cache is recommended on upgrades") == "Y":
        cleandata ('server_cache')

    if getanswer("Purge image workdir", "N", "cleaning workdir not is recommended unless noted in release") == "Y":
        cleandata ('workdir')

    # Kill the bisque.js minified file
    b_js = os.path.realpath('public/js/b.js')
    if os.path.exists (b_js):
          os.remove (b_js)

    return params




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
              #platform = platform.platform(),
              platform = platform.platform().replace('-', '-%s-'%platform.architecture()[0], 1), # dima: added 64bit
              python_version = platform.python_version(),
              installtime = params['install_started'],
              duration = params['duration'],
                                                  )
    parts.append(text)
    parts.append(str(params))
    if os.path.exists('bisque-install.log'):
        parts.append (remove_control_chars (open('bisque-install.log','r').read()))

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
Initialize your database with:
   $$ bq-admin setup createdb

You can start bisque with:
   $$ bq-admin server start
then point your browser to:
    ${bisque.server}
If you need to shutdown the servers, then use:
   $$ bq-admin server stop
You can login as admin and change the default password.
"""

engine_msg="""
You can start a bisque module engine with
   $$ bq-admin server start
which will register any module with
    ${bisque.engine}
"""


########################################################
# User visible command line packages to be run in order i.e. during a
# server install

install_options= [
    'site',
    # 'mercurial',
    'binaries',
    'database',
    'matlab',
    'modules',
    'runtime',
    'features',
    'server',
    'mail',
    'preferences',
    'production',
    ]

# engine install packages
engine_options= [
    # 'binaries',
    'matlab',
    'modules',
    'runtime',
    'engine',
    ]

# other unrelated packages
other_options = [
    "upgrade",
    'admin',
    'configuration',
    'createdb',
]

all_options = list (set (install_options + engine_options + other_options))


######################################################################
# List of user visible commands and their corresponding internal actions
SETUP_COMMANDS = {
    'site' : [ install_server_defaults],
    'engine' : [install_engine_defaults],
    'binaries': [ fetch_external_binaries, install_dependencies ],
    'features' : [ install_features ],
    'database' : [ install_database ],
    'mail' : [ install_mail ],
    'preferences' : [ install_preferences ],
    'production' : [ install_public_static, install_secrets ],
    'upgrade' : [ kill_server, fetch_stable, fetch_external_binaries, install_dependencies, migrate, cleanup ],
    "configuration" : [ setup_server_cfg ],
    "createdb" : [ setup_database ],
    }

# Special procedures that modify runtime-bisque.cfg (for the engine)
RUNTIME_COMMANDS = {
    'matlab' : [ install_matlab ],
    'runtime' : [ install_runtime ],
    'modules' : [ install_modules ],
    }



usage = " usage: bq-admin setup [%s] " % ' '.join(all_options)


def bisque_installer(options, args):
    #cwd = to_posix_path(os.getcwd())
    #if not os.path.exists ('bqcore'):
    #    print "ERROR: This script must be bisque installation directory"
    #    sys.exit()

    if not os.path.exists('config'):
        print "Cannot find config.. please run bq-admin setup from bisque install"
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
    system_type = 'bisque'
    if len(args) == 0 or args[0] == 'bisque':
        installer = install_options[:]
    elif args[0] == 'engine':
        installer = engine_options[:]
        system_type = 'engine'
    elif args[0] == 'server':
        installer = install_options[:]
        system_type = 'bisque'
    else:
        installer = args

    if 'help' in installer:
        print usage
        return

    print "Beginning install of %s" % (system_type)

    params = {}
    if  os.path.exists (SITE_CFG):
        params = read_site_cfg(cfg = SITE_CFG, section=BQ_SECTION)
        #print params

    if not os.path.exists(RUNTIME_CFG):
        runtime_params = install_cfg(RUNTIME_CFG, section=None, default_cfg=config_path('runtime-bisque.default'))
    else:
        runtime_params = read_site_cfg(cfg=RUNTIME_CFG, section = None)

    params['bisque.installed'] = "inprogress"

    for step in installer:
        # Normal commands that modify site.cfg
        flist  =  SETUP_COMMANDS.get(step, [])
        for step_f in flist:
            params = step_f(params)
        # Special commands that modify runtime-bisque.cfg
        flist  =  RUNTIME_COMMANDS.get(step, [])
        for step_f in flist:
            runtime_params = step_f(runtime_params)

    params['bisque.installed'] = "finished"
    params = modify_site_cfg([], params,)

    if installer == install_options:
        print STemplate(start_msg).substitute(params)
        return 0

    if installer == engine_options:
        print STemplate(engine_msg).substitute(params)
        return 0


    return -1


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
#    import sys, os, time
#    import pty
    mode = 'wb'
    script = open(filename, mode)
    def read(fd):
        data = os.read(fd, 1024)
        script.write(data)
        return data

    script.write(('Script started on %s\n' % time.asctime()).encode())
    pty.spawn(command, read)
    script.write(('Script done on %s\n' % time.asctime()).encode())
    script.close()
    with open(filename) as install:
        if 'Cancel' in install.read():
            return 128
    return 0

def setup(options, args):
    virtenv = os.environ.get ('VIRTUAL_ENV', None)
    if virtenv is None:
        print "Cannot determine your python virtual environment"
        print "This make installation much simpler.  Please activate or prepare the environment given by the web instructions"
        if getanswer ("Continue without virtualenv", "N", "Try installation without python virtualenv") == 'N':
            sys.exit(0)

    cancelled = False
    global answer_file, save_answers
    global use_defaults
    global BQENV
    global BQBIN
    global SITE_PACKAGES

    python_version = sys.version_info[:2]

    BQENV = virtenv
    if os.name == "nt":
        BQBIN = os.path.join(BQENV, 'Scripts') # windows local
        SITE_PACKAGES = os.path.join(BQENV, 'Lib', 'site-packages')
    else:
        BQBIN = os.path.join(BQENV, 'bin') # Our local bin
        SITE_PACKAGES = os.path.join(BQENV, 'lib','python%s.%s'%python_version,'site-packages')

    begin_install = datetime.datetime.now()
    if options.read:
        print "Reading answers from %s" % options.read
        answer_file = open (options.read)
    elif options.write:
        print "Saving answers to %s" % options.write
        answer_file = open (options.write, "wb")
        save_answers = True
    elif options.yes:
        use_defaults = True
    elif has_script and not options.inscript:
        script = ['bq-admin', 'setup', '--inscript']
        script.extend (args)
        r = typescript(script, 'bisque-install.log')
        #print "RETURN is ", r
        if not cancelled and r != 128:
            end_install = datetime.datetime.now()
            params = read_site_cfg(cfg= SITE_CFG, section=BQ_SECTION)
            params['install_started'] = begin_install
            params['duration'] = str(end_install-begin_install)
            try:
                send_installation_report(params)
            except KeyboardInterrupt:
                print "Cancelled"
        sys.exit(r)


    try:
        r  = bisque_installer(options, args)
        return r
    except InstallError, e:
        cancelled = True
    except KeyboardInterrupt:
        print "Interupted"
        print "Cancelling Installation"
        sys.exit (128)
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
