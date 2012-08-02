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


        

if __name__ == '__main__':
    sys.exit(main())
