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


log = logging.getLogger('bq.mexrunner')
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
    logging.basicConfig(level=logging.DEBUG)

    opts, args = parse_args()

    if len(args) == 0:
        args = [ 'config/site.cfg' ]
    load_config(args[0])

    root = tg.config.get('bisque.root', None)
    log.info ("using site.cfg for bisque.root=%s" % root)
    if root[-1] != '/':
        root = root + '/'


    from bq.module_service.controllers.mexrunner import MexRunner

    module_service = '%smodule_service/' % root
    log.info("starting with %s" % module_service)
    mexrunner = MexRunner(module_service)


    qwait = int(tg.config.get('bisque.module_service.queue_wait', 5))

    time.sleep(10)
    while True:
        try:
            mexrunner.process_pending()
        except  (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            log.exception("Continuing after exception:")
        time.sleep(qwait)

if __name__ == '__main__':
    sys.exit(main())
