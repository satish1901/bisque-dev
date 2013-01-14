import sys
import os
import subprocess
import re
import pkg_resources
import bq
import optparse
import errno
import logging

from bq.release import __VERSION__


logging.basicConfig(level=logging.WARN)

def load_config(filename):
    from paste.deploy import appconfig
    from bq.config.environment import load_environment
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

def main():
    """Main entrypoint for bq-admin commands"""
    commands = {}
    for entrypoint in pkg_resources.iter_entry_points("bq.commands"):
        command = entrypoint.load()
        commands[entrypoint.name] = (command.desc, entrypoint)

    def _help():
        "Custom help text for bq-admin."

        print """
Bisque %s command line interface

Usage: %s [options] <command>

options: -d, --debug : print debug

Commands:""" % (__VERSION__, sys.argv[0])

        longest = max([len(key) for key in commands.keys()])
        format = "%" + str(longest) + "s  %s"
        commandlist = commands.keys()
        commandlist.sort()
        for key in commandlist:
            print format % (key, commands[key][0])


    parser = optparse.OptionParser()
    parser.allow_interspersed_args = False
    #parser.add_option("-c", "--config", dest="config")
    #parser.add_option("-e", "--egg", dest="egg")
    parser.add_option("-d", "--debug", action="store_true", default=False)
    parser.print_help = _help
    (options, args) = parser.parse_args(sys.argv[1:])
    if not args or not commands.has_key(args[0]):
        _help()
        sys.exit()

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    commandname = args[0]
        
    # strip command and any global options from the sys.argv
    sys.argv = [sys.argv[0],] + args[1:]
    command = commands[commandname][1]
    command = command.load()
    command = command(__VERSION__)
    command.run()

class server(object):
    desc = "Start or stop a bisque server"
    
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog servers [options] start|stop|restart",
                    version="%prog " + version)
        parser.add_option("--reload", action="store_true", help="autoreload for development" )
        parser.add_option("-n", "--dryrun", action="store_true", help="Dry run and show commands")
        parser.add_option("-v", "--verbose", action="store_true", help="show commands as run" )
        parser.add_option("-w", "--wait", action="store_true", help="wait for children" )
        parser.add_option("-s", "--site", help="specify location of site.cfg" )
        parser.add_option("-f", "--force", action="store_true", default=False, help="try force start or stop: ignore old pid files etc." )

        options, args = parser.parse_args()
        self.command = self.options = None
        if len(args) < 1 or args[0] not in ['start', 'stop', 'restart', 'echo', ]:
            parser.print_help()
            return

        if options.dryrun:
            options.verbose = True
        
        self.options = options
        self.command = args[0]
        self.args = args[1:]

    def run(self):
        #Check for self.command in init..
        import server_ops
        if self.command:
            server_ops.operation(self.command, self.options, *self.args)


class cache(object):
    desc = "delete the cache"

    def run(self):
        #Check for self.command in init..
        from bq.utils.paths import data_path
        for p in (data_path('.server_cache'), data_path('.client_cache')):
            if os.path.exists (p):
                shutil.rmtree (p)
                os.makedirs(p)

class database(object):
    desc = 'Execute a database command'
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog database [admin]",
                    version="%prog " + version)
    

        parser.add_option('-c','--config', default="config/site.cfg")
        parser.add_option('-n','--dryrun', action="store_true", default=False)
        options, args = parser.parse_args()

        self.args = args
        self.options = options
        if len(args) == 0:
            parser.error('argument must be clean')

        options, args = parser.parse_args()
        self.command = args[0]
        self.args = args[1:]


    def run(self):
        load_config(self.options.config)
        import cleandb
        cleandb.clean_images(self.options)
            

        
class setup(object):
    desc = 'Setup or update a bisque server'
    def __init__(self, version):
        from bq.setup.bisque_setup import usage, install_options
        parser = optparse.OptionParser(
                    usage=usage,
                    version="%prog " + version)
        parser.add_option("--inscript", action="store_true", help="we are running under typescript" )
        parser.add_option("-r", "--read", action="store", help="Read answers from given file" )
        parser.add_option("-w", "--write", action="store", help="Write answers from given file" )
        options, args = parser.parse_args()
        for arg in args:
            if arg not in install_options + ['bisque', 'engine']:
                parser.error('argument must be install option')
        
        self.args = args
        self.options = options


    def run(self):
        ''
        from bq.setup import bisque_setup
        r = bisque_setup.setup( self.options, self.args )
        sys.exit(r)

class deploy(object):
    desc = 'Advanced deployment options: public'
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog deploy [public]",
                    version="%prog " + version)
        options, args = parser.parse_args()
        self.args = args
        self.options = options

    def run(self):
        #if 'public' in self.args:
        self.deploy_public()
        
        

    def deploy_public(self):
        ''
        import pkg_resources
        if  os.path.exists('public'):
            print "Warning public exists"
            print "Please remove public before continuing"
            return
        else:
            os.makedirs ('public')
        for x in pkg_resources.iter_entry_points ("bisque.services"):
            try:
                #print ('found static service: ' + str(x))
                service = x.load()
                if not hasattr(service, 'get_static_dirs'):
                    continue
                staticdirs  = service.get_static_dirs()
                for d,r in staticdirs:
                    #print ( "adding static: %s %s" % ( d,r ))
                    static_path =  r[len(d)+1:]
                    #print "path =", os.path.dirname(static_path)
                    os.makedirs (os.path.join('public', os.path.dirname(static_path)))
                    #print "link ", (r, os.path.join('public', static_path))
                    os.symlink (r, os.path.join('public', static_path))
                    print "Deployed ", r
            except Exception, e:
                #print "Exception: ", e
                pass
        # Link all core dirs
        import glob
        for l in glob.glob('bqcore/bq/core/public/*'):
            os.symlink (os.path.join('..', l), os.path.join('public', os.path.basename(l)))
        #check if grunt exists, if so, run it to pack and minify javascript
        try:
            subprocess.call(["grunt"])
        except OSError as e:
            if e.errno == errno.ENOENT:
                print "grunt not found.\n install it by typing 'npm install -g grunt'"
            else:
                print "Unknown error while trying to run grunt. Is it installed correctly?\n install it by typing 'npm install -g grunt'"

class preferences (object):
    desc = "read and/or update preferences"
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog preferences [init (db)|read (from db)|save (to db)]",
                    version="%prog " + version)
        parser.add_option('-c','--config', default="config/site.cfg")
        parser.add_option('-f','--force', action="store_true", help="Force action if able")
        options, args = parser.parse_args()

        self.args = args
        self.options = options
        if len(args) == 0:
            parser.error('argument must be init, read, save')

    def run(self):
        load_config(self.options.config)
        from lxml import etree
        from tg import config, session, request
        from bq import data_service
        from bq.core.identity import set_admin_mode
        import transaction
        from paste.registry import Registry
        from beaker.session import Session, SessionObject
        from pylons.controllers.util import Request

        registry = Registry()
        registry.prepare()
        registry.register(session, SessionObject({}))
        registry.register(request, Request.blank('/bootstrap'))
        request.identity = {}


        root = config.get ('bisque.root')
        #enabled = config.get('bisque.services_enabled', None)
        #disabled = config.get('bisque.services_disabled', None)
        #enabled  = enabled and [ x.strip() for x in enabled.split(',') ] or []
        #disabled = disabled and [ x.strip() for x in disabled.split(',') ] or []
        enabled = [ 'data_service' ]
        disabled= []

        from bq.core.controllers.root import RootController
        RootController.mount_local_services(root, enabled, disabled)
        prefs = 'config/preferences.xml'

        set_admin_mode(True)
        if self.args[0].startswith('init'):
            x = data_service.query('system')
            if len(x):
                if self.options.force:
                    print ("deleting current system object")
                    data_service.del_resource(x[0])
                else:
                    print ("NO ACTION: System object initialized at %s " % etree.tostring(x[0]))
                    return 

            if os.path.exists(prefs):
                if self.options.force:
                    print ("deleting %s" % prefs)
                    os.remove (prefs)
                else:
                    print ('NO ACTION: %s exists.. cannot init' % prefs)
                    return
            
            system = etree.parse('config/preferences.xml.default').getroot()
            for el in system.getiterator(tag=etree.Element):
                el.set ('permission', 'published')
            system = data_service.new_resource(system, view='deep')
        else:
            system = etree.parse(prefs).getroot()
            for el in system.getiterator(tag=etree.Element):
                el.set ('permission', 'published')
            uri = system.get('uri')
            if self.args[0].startswith('read'):
                system = data_service.get_resource(uri, view='deep')
            elif self.args[0] == 'save':
                logging.debug ('system = %s' % etree.tostring(system))
                system = data_service.update_resource(system, view='deep')
        transaction.commit()
        with open(prefs,'w') as f:
            f.write(etree.tostring(system, pretty_print=True))


class sql(object):
    desc = 'Run a sql command '
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog sql <sql>",
                    version="%prog " + version)
        parser.add_option('-c','--config', default="config/site.cfg")
        options, args = parser.parse_args()

        self.args = args
        self.options = options

    def run(self):
        ''

        from tg import config
        import bq
        from sqlalchemy import create_engine
        from sqlalchemy.sql import text
        from ConfigParser import ConfigParser

        load_config(self.options.config)

        engine = config['pylons.app_globals'].sa_engine

        print engine


