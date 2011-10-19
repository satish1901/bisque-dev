import sys
import re
import pkg_resources
import bq
import optparse
from bq.release import __VERSION__

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

    



class servers(object):
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
        self.server_type = 'bisque'
        if len(args) >= 1:
            if args[0] in ('bisque', 'engine'):
                self.server_type = args.pop(0)

        for arg in args:
            if arg not in install_options:
                parser.error('argument must be install option')

        
        self.args = args
        self.options = options


    def run(self):
        ''
        from bq.setup import bisque_setup

        bisque_setup.setup( self.server_type, self.options, self.args )




class sql(object):
    desc = 'Run a sql command '
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog sql <sql>",
                    version="%prog " + version)
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

        engine = config['pylons.app_globals'].sa_engine

        print engine


