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
        if len(args) < 1 or args[0] not in ['start', 'stop', 'restart', 'echo', 'list' ]:
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
        self.public_dir = self.args.pop(0) if len(self.args)>0 else 'public'
        self.deploy_public()



    def deploy_public(self):
        ''
        from bq.util.copylink import copy_symlink
        import pkg_resources
        try:
            print "Creating %s" % self.public_dir
            os.makedirs (self.public_dir)
        except OSError, e:
            pass

        rootdir = os.getcwd()
        coredir = os.path.join(rootdir, 'bqcore/bq/core/public/').replace('/', os.sep)

        os.chdir(self.public_dir)
        currdir = os.getcwd()


        for x in pkg_resources.iter_entry_points ("bisque.services"):
            try:
                #print ('found static service: ' + str(x))
                try:
                    service = x.load()
                except Exception, e:
                    print "Problem loading %s: %s" % (x, e)
                    continue
                if not hasattr(service, 'get_static_dirs'):
                    continue
                staticdirs  = service.get_static_dirs()
                for d,r in staticdirs:
                    #print ( "adding static: %s %s" % ( d,r ))
                    static_path =  r[len(d)+1:]
                    #print "path =", os.path.dirname(static_path)
                    basedir = os.path.dirname(static_path)
                    try:
                        #os.makedirs (os.path.join(self.dir, os.path.dirname(static_path)))
                        os.makedirs (os.path.dirname(static_path))

                    except OSError,e:
                        pass
                    #print "link ", (r, os.path.join('public', static_path))
                    dest = os.path.join(currdir, static_path)
                    if os.path.exists (dest):
                        os.unlink (dest)
                    relpath = os.path.relpath(r, os.path.dirname(dest))
                    #print "%s -> %s" % (relpath, dest)

                    copydir = os.getcwd()
                    os.chdir(basedir)
                    copy_symlink (relpath, dest)
                    os.chdir(copydir)
                    print "Deployed ", r
            except Exception, e:
                print "Exception: ", e
                pass
        # Link all core dirs
        import glob
        for l in glob.glob(os.path.join(coredir, '*')):
            dest = os.path.join(currdir, os.path.basename(l))
            if os.path.exists (dest):
                os.unlink (dest)

            relpath = os.path.relpath(l, currdir)
            #print "%s -> %s " % (relpath, dest)
            copy_symlink (relpath, dest)
        os.chdir (rootdir)


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
                    sys.exit (1)

            if os.path.exists(prefs):
                if self.options.force:
                    print ("deleting %s" % prefs)
                    os.remove (prefs)
                else:
                    print ('NO ACTION: %s exists.. cannot init' % prefs)
                    sys.exit(1)

            system = etree.parse('config/preferences.xml.default').getroot()
            for el in system.getiterator(tag=etree.Element):
                el.set ('permission', 'published')
            system = data_service.new_resource(system, view='deep')
        else:
            system = etree.parse(prefs).getroot()
            # Esnure all elements are published
            for el in system.getiterator(tag=etree.Element):
                el.set ('permission', 'published')
            # Read system object
            uri = system.get('uri')
            if self.args[0].startswith('read'):
                system = data_service.get_resource(uri, view='deep')
            elif self.args[0] == 'save':
                logging.debug ('system = %s' % etree.tostring(system))
                system = data_service.update_resource(new_resource=system, resource=uri,  view='deep')
        transaction.commit()
        with open(prefs,'w') as f:
            f.write(etree.tostring(system, pretty_print=True))
            print "Wrote %s" % prefs


class sql(object):
    desc = 'Run a sql command (disabled)'
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


class group(object):
    'do a group command'
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



class stores(object):
    desc = 'Generate stores resource by visiting image/file resouces'

    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog stores  [list|create [name]] ",
                    version="%prog " + version)
        parser.add_option('-c','--config', default="config/site.cfg")
        options, args = parser.parse_args()
        if len(args) < 1 or args[0] not in ('list', 'create'):
            parser.error()
        self.command  = args.pop(0)
        self.args = args
        self.options = options

    def run(self):
        ''
        #engine = config['pylons.app_globals'].sa_engine
        #print engine
        load_config(self.options.config)
        from bq.blob_service.controllers.blobsrv import load_stores

        self.stores = load_stores()

        if self.command == 'list':
            print self.stores.keys()
            return
        store_name = None

        nested = self.create_trees(store_name)
        self.create_store(nested)


    def create_trees(self, name=None):
        """Create a nested dictionary representing all the element
        found in the store

        { 'local' : { 'D1'  : { 'name' : Resource } }}

        """
        from bq.data_service.model.tag_model import Taggable, DBSession
        from bq.util.dotnested import parse_nested
        from sqlalchemy import or_

        stores = self.stores
        toplevel = DBSession.query(Taggable).filter(
            Taggable.resource_parent_id == None,
            or_(Taggable.resource_type == 'image',
                Taggable.resource_type == 'file',))

        def match_store (path):
            best = None
            best_top = 0
            for k,store in stores.items():
                if store.valid (path) and len(store.top) > best_top:
                    best = store
                    best_top = len(store.top)
                    best.name = k
            return best

        stores_resource = {}
        for r in toplevel:
            if  r.value is None:
                print "BADVAL", r.resource_type, r.resource_uniq,  r.name, r.value
                continue
            store = match_store (r.value)
            # If only dealing with  store 'name' then skip others
            if store is None:
                print "NOSTORE", r.resource_type, r.resource_uniq,  r.name, r.value
                continue

            if name is not None and name != store.name:
                continue

            if r.value.startswith (store.top):
                path = r.value[len(store.top):]
            else:
                path = r.value

            # For each store, make a path string for each loaded resource
            el = stores_resource.setdefault (store.name, {})
            el[path] = r
            #print path

        # We parse the paths into a set of nested dicts .
        nested = {}
        for k,p in stores_resource.items():
            nested[k] = parse_nested(p, sep = '/')
        return  nested


    def create_store (self, nested):
        """ Use the dictionary to save/create a store resource"""

        from lxml import etree
        def visit_level(root, d):
            count = 0
            for k,v in d.items():
                if isinstance (v, dict):
                    subroot = etree.SubElement (root, 'dir', name = k, permission='published')
                    visit_level(subroot, v)
                else:
                    xv = etree.SubElement (root, 'link', name=(v.resource_name or 'filename%s' %count), value = str(v.resource_uniq))
                    count += 1

        for store, paths in nested.items():
            root = etree.Element('resource', resource_type='store', name=store, value = self.stores[store].top, permission='published')
            visit_level (root, paths)
            self.save_store(store, root)

    def save_store (self, store, root):
        "Save the store to location"
        from lxml import etree

        with open('tree_%s.xml' % store, 'w') as w:
            w.write(etree.tostring(root, pretty_print=True))



class password(object):
    desc = 'Password utilities'

    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog sql <sql>",
                    version="%prog " + version)
        parser.add_option('-c','--config', default="config/site.cfg")
        parser.add_option('-f','--force', action="store_true", default=False)
        options, args = parser.parse_args()

        if len(args) > 0:
            self.command = args.pop(0)

        self.args = args
        self.options = options
        if self.command not in ('convert', 'set', 'list'):
            parser.print_help()
            return

    def run(self):
        import transaction
        load_config(self.options.config)

        from tg import config
        print config.get ('bisque.login.password', 'freetext')


        if self.command == 'set':
            user_name, password = self.args
            self.set_password (user_name, password)
        elif self.command == 'list':
            from bq.core.model.auth import User, DBSession
            for user in DBSession.query(User):
                print user.user_name, user.password
        elif self.command == 'convert':
            from bq.core.model.auth import User, DBSession
            for user in DBSession.query(User):
                if len(user.password)==80 and not self.options.force:
                    print "Skipping user %s already  converted" % user.user_name
                    continue
                self.set_password (user.user_name, user.password)
        transaction.commit()

    def set_password(self, user_name, password):
            from bq.core.model.auth import User, DBSession
            user = DBSession.query(User).filter_by(user_name = user_name).first()
            if user:
                print "setting %s" % user.user_name
                user.password = password
            else:
                print "cannot find user %s" % user_name

