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
import urlparse
import logging
import ConfigParser
import xml.etree.ElementTree as ET

import argparse
import requests
import six

############################
# Config for local installation
DEFAULTS  = dict(
    logfile    = '/tmp/bisque_insert.log',
    bisque_host='https://loup.ece.ucsb.edu',
    bisque_admin_user='admin',
    bisque_admin_pass='admin',
    irods_host='irods://irods.ece.ucsb.edu',
    )
# End Config
############################

log = logging.getLogger('bqpath')

def bisque_delete(session, args):
    """delete a file based on the irods path"""
    url = urlparse.urljoin(args.host, "/blob_service/paths/delete_path?path=%s" % args.srcpath)
    r = session.get (url)
    r.raise_for_status()

def bisque_link(session, args):
    """insert  a file based on the irods path"""
    #url = urlparse.urljoin(args.host, "/blob_service/paths/insert_path?path=%s" % args.srcpath)
    url = urlparse.urljoin(args.host, "/import_service/insert_inplace")
    payload = None
    params = None

    #if args.srcpath:
    #    resource = "<resource name='%s' value='%s' />" % (os.path.basename(args.srcpath), args.srcpath )
    #    payload = { 'path_resource': resource }
    params = { 'path' : args.srcpath }
    if args.alias:
        params[ 'user' ] = args.alias

    r  =  session.post (url,  params=params)
    if r.status_code == requests.codes.ok:
        six.print_(r.text)
    r.raise_for_status()

def bisque_insert(session, args):
    """insert  a file based on the irods path"""
    #url = urlparse.urljoin(args.host, "/blob_service/paths/insert_path?path=%s" % args.srcpath)
    url = urlparse.urljoin(args.host, "/import_service/transfer")
    payload = None
    params = None

    if not os.path.exists (args.srcpath):
        six.print_()
        return
        resource = ET.Element ('resource', name=os.path.basename(args.srcpath))
        if args.alias:
            resource.attrib['owner'] = args.alias
        xml = ET.tostring(resource)
        #resource = "<resource name='%s' value='%s' />" % (os.path.basename(args.srcpath), args.srcpath )
        files  = { 'file': ( os.path.basename(args.srcpath), open(args.srcpath, 'rb')),
                   'file_resource' : ( None, xml, 'text/xml'),}
    r  =  session.post (url, files=files)
    if r.status_code == requests.codes.ok:
        six.print_(r.text)
    r.raise_for_status()


def bisque_rename(session, args):
    """rename based on paths"""
    url = urlparse.urljoin(args.host, "/blob_service/paths/move_path?path=%s&dst=%s" % (args.srcpath, args.dstpath))
    r = session.get (url)
    if r.status_code == requests.codes.ok:
        six.print_ (  r.text )
        return r

def bisque_list(session, args):
    """delete a file based on the irods path"""

    url = urlparse.urljoin(args.host, "/blob_service/paths/list_path?path=%s" % args.srcpath)
    r = session.get (url)
    #six.print_( r.request.headers )
    if r.status_code == requests.codes.ok:
        #six.print_( r.text )
        for resource  in ET.fromstring (r.text):
            six.print_( resource.get ('resource_uniq') )
    r.raise_for_status()



def main():

    config = ConfigParser.SafeConfigParser()
    config.add_section('bqpath')
    for k,v in DEFAULTS.items():
        config.set('bqpath', k,v)

    config.read (['.bqconfig', os.path.expanduser('~/.bqconfig'), '/etc/bisque/bqconfig'])
    defaults =  dict(config.items('bqpath'))

    parser = argparse.ArgumentParser(description='interface with irods and bisque')
    parser.add_argument('command', help="one of ls, cp, mv, rm, ln" )
    parser.add_argument('srcpath', default = '/', nargs='?')
    parser.add_argument('dstpath', nargs='?')
    parser.add_argument('--alias', help="do action on behalf of user specified")
    parser.add_argument('-d', '--debug', action="store_true", default=False, help="log debugging")
    parser.add_argument('-H', '--host', default=defaults['bisque_host'], help="bisque host")
    parser.add_argument('-c', '--credentials', default="%s:%s" % (defaults['bisque_admin_user'], defaults["bisque_admin_pass"]), help="user credentials (default %s) " %defaults['bisque_admin_user'] )
    parser.add_argument('-r', '--resource', default = None)
    parser.add_argument('-f', '--resource_file', default = None, help="tag document for insert")


    log.debug( "IrodsBisque recevied %s" % (sys.argv) )

    args = parser.parse_args ()
    if args.debug:
        logging.basicConfig(filename=config.get ('bqpath', 'logfile'), level=logging.INFO)

    OPERATIONS = {
        'ls' : bisque_list,
        'ln' : bisque_link,
        'cp' : bisque_insert,
        'mv' : bisque_rename,
        'rm' : bisque_delete,
        }

    if args.command not in OPERATIONS:
        parser.error("command must be one of 'ls', 'cp', 'mv', 'rm'")

    if args.debug:
        six.print_(args, file=sys.stderr)

    try:
        session = requests.Session()
        requests.packages.urllib3.disable_warnings()

        session.verify = False
        session.auth = tuple (args.credentials.split(':'))
        session.headers.update ( {'content-type': 'application/xml'} )
        OPERATIONS[args.command] (session, args)
    except requests.exceptions.HTTPError,e:
        log.exception( "exception occurred %s" % e )

    sys.exit(0)

if __name__ == "__main__":
    main()
