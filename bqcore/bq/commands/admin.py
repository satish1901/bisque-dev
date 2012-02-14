import sys
import os
import re
import pkg_resources
import bq
import optparse
from bq.release import __VERSION__

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
    parser.print_help = _help
    (options, args) = parser.parse_args(sys.argv[1:])
    if not args or not commands.has_key(args[0]):
        _help()
        sys.exit()

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


class engine(server):
    desc = 'Start or stop a bisque engine'

    def run(self):
        #Check for self.command in init..
        import server_ops
        if self.command:
            server_ops.operation(self.command, self.options, 
                                 mexrun=False,  cfg_file = 'engine.cfg',
                                 *self.args)
            

class cache(object):
    desc = "delete the cache"

    def run(self):
        #Check for self.command in init..
        import server_ops
        if self.command:
            server_ops.operation(self.command, self.options, *self.args)

        if os.path.exists ('.cache'):
            shutil.rmtree ('.cache')
        os.mkdir ('.cache')
        if os.path.exists('.server_cache'):
            shutil.rmtree('.server_cache')
        os.mkdir ('.server_cache')
        


class database(object):
    desc = 'Execute a database command'
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog database [admin]",
                    version="%prog " + version)
    
        options, args = parser.parse_args()
        self.command = args[0]
        self.args = args[1:]


    def run(self):
        ''
            
        
class setup(object):
    desc = 'Setup or update a bisque server'
    def __init__(self, version):
        from bq.setup.bisque_setup import usage, install_options
        parser = optparse.OptionParser(
                    usage=usage,
                    version="%prog " + version)
        parser.add_option("--inscript", action="store_true", help="we are running under typescript" )
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



class preferences (object):
    desc = "read and/or update preferences"
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog preferences [init|read|save]",
                    version="%prog " + version)
        parser.add_option('-c','--config', default="config/site.cfg")
        options, args = parser.parse_args()

        self.args = args
        self.options = options
        if len(args) == 0:
            parser.error('argument must be init, read, save')

    def run(self):
        load_config(self.options.config)
        from tg import config
        from lxml import etree
        from bq import data_service
        import transaction

        root = config.get ('bisque.root')
        enabled = config.get('bisque.services_enabled', None)
        disabled = config.get('bisque.services_disabled', None)
        enabled  = enabled and [ x.strip() for x in enabled.split(',') ] or []
        disabled = disabled and [ x.strip() for x in disabled.split(',') ] or []

        from bq.core.controllers.root import RootController
        RootController.mount_local_services(root, enabled, disabled)
        prefs = 'config/preferences.xml'

        if self.args[0].startswith('init'):
            if os.path.exists(prefs):
                print ('%s exists.. cannot init' % prefs)
                return
            
            system = etree.parse('config/preferences.xml.default').getroot()
            system = data_service.new_resource(system, view='deep')
        else:
            system = etree.parse(prefs)
            uri = system.getroot().get('uri')
            if self.args[0].startswith('read'):
                system = data_service.get_resource(uri, view='deep')
            elif self.args[0] == 'save':
                system = data_service.update(system, view='deep')
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


