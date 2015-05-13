#!/usr/bin/env python

""" Script to register irods files with bisque
"""
__author__    = "Center for Bioimage Informatics"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os
import sys
import shlex
import urllib
import urllib2
import urlparse
import base64
import logging
import argparse
import requests
import ConfigParser

############################
# Config for local installation
DEFAULTS  = dict(
    logfile    = '/tmp/bisque_insert.log',
    bisque_host='https://loup.ece.ucsb.edu',
    bisque_admin_pass='admin',
    irods_host='irods://irods.ece.ucsb.edu',
    )
# End Config
############################

log = logging.getLogger('IrodsBisque')

def bisque_delete(session, args):
    """delete a file based on the irods path"""
    url = urlparse.urljoin(args.target, "/blob_service/paths/delete_path?path=%s" % args.srcpath)
    r = session.get (url)
    r.raise_for_status()

def bisque_insert(session, args):
    """insert  a file based on the irods path"""

def bisque_rename(session, args):
    """rename based on paths"""
    url = urlparse.urljoin(args.target, "/blob_service/paths/move_path?path=%s&dst=%s" % (args.srcpath, args.dstpath))
    r = session.get (url)
    if r.status_code == requests.codes.ok:
        print r.text
        return r

def bisque_list(session, args):
    """delete a file based on the irods path"""

    url = urlparse.urljoin(args.target, "/blob_service/paths/list_path?path=%s" % args.srcpath)
    r = session.get (url)
    print r.request.headers
    if r.status_code == requests.codes.ok:
        print r.text
        return r
    print r
    r.raise_for_status()



def main():

    config = ConfigParser.SafeConfigParser()
    config.add_section('bqcommand')
    for k,v in DEFAULTS.items():
        config.set('bqcommand', k,v)

    config.read (['.bqconfig', os.path.expanduser('~/.bqconfig'), '/etc/bisque/bqconfig'])
    defaults =  dict(config.items('bqcommand'))

    parser = argparse.ArgumentParser(description='interface with irods and bisque')
    parser.add_argument('command', help="one of ls, cp, mv, rm" )
    parser.add_argument('srcpath')
    parser.add_argument('dstpath', nargs='?')
    parser.add_argument('--user', '-u')
    parser.add_argument('-d', '--debug', action="store_true", default=False, help="log debugging")
    parser.add_argument('-t', '--target', default="%s/import/insert_inplace" % defaults['bisque_host'], help="bisque host entry url")
    parser.add_argument('-c', '--credentials', default="admin:%s" % defaults["bisque_admin_pass"], help="user credentials")
    parser.add_argument('-r', '--resource', default = None)
    parser.add_argument('-f', '--resource_file', default = None)


    log.debug( "IrodsBisque recevied %s" % (sys.argv) )

    args = parser.parse_args ()
    if args.debug:
        logging.basicConfig(filename=config.get ('bqcommand', 'logfile'), level=logging.INFO)

    OPERATIONS = {
        'ls' : bisque_list,
        'cp' : bisque_insert,
        'mv' : bisque_rename,
        'rm' : bisque_delete,
        }

    if args.command not in OPERATIONS:
        parser.error("command must be one of 'ls', 'cp', 'mv', 'rm'")

    try:
        session = requests.Session()
        session.verify = False
        session.auth = tuple (args.credentials.split(':'))
        session.headers.update ( {'content-type': 'application/xml'} )
        OPERATIONS[args.command] (session, args)
    except requests.exceptions.HTTPError,e:
        log.exception( "exception occurred %s" % e )

    sys.exit(0)

if __name__ == "__main__":
    main()
