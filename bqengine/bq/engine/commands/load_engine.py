#!/usr/bin/env python
""" Print all the usernames to the console. """


import os
import time
import sys
#import tgscheduler
import logging
#from argparse import ArgumentParser
from optparse import OptionParser

import tg
from paste.script import command
from paste.deploy import appconfig
from bq.config.environment import load_environment
from bq.core import model
from bq.util.paths import config_path



def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

def parse_args():
#    parser = ArgumentParser(description=__doc__)
#    parser.add_argument("conf_file", help="configuration to use")
    parser = OptionParser(description=__doc__)
    #parser.add_option("config", help="configuration to use", default="development.ini")
    
    return parser.parse_args()



def main():
    print("using {0}".format(sys.argv[1]))
    load_config (sys.argv[1])
    from bq.engine.controllers.engine_service import execone

    print "DUMMY LOAD"


class LoadEngine(command.Command):
    """Load the engine without starting"""

    usage = "load_engine config_file"
    summary = "load the engine code without running engine"
    group_name = "Bisque"
    name = None
    auth = None
    geo = False
    package = None
    sqlalchemy = True

    dry_run = False



    parser = command.Command.standard_parser(verbose=True)
    def command(self):
        config = self.args[0]
        print("using {0}".format(config))
        load_config (config)
        from bq.engine.controllers.engine_service import execone
        print "DUMMY LOAD"
        
        

if __name__ == '__main__':
    sys.exit(main())
