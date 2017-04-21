#!/usr/bin/env python

""" Script to register irods files with bisque
"""
__author__    = "Center for Bioimage Informatics"
__version__   = "1.0"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import argparse
import os
import sys
import logging
import six
from six.moves.configparser import SafeConfigParser, ConfigParser
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

import requests

############################
# Config for local installation
# These values can be stored in a file ~/.bisque or /etc/bisque/bisque_config
# i.e
#  [bqpath]
#  bisque_admin_pass = gobblygook

DEFAULTS  = dict(
    logfile    = '/tmp/bisque_insert.log',
    bisque_host='https://loup.ece.ucsb.edu',
    bisque_admin_user='admin',
    bisque_admin_pass='admin',
    irods_host='irods://mokie.iplantcollaborative.org',
    )
# End Config
############################


def bisque_delete(session, args):
    """delete a file based on the irods path"""
    session.log.info ("delete %s", args)
    url = args.host +  "/blob_service/paths/remove"
    params = dict(path = args.srcpath)
    if args.alias:
        params['user'] =  args.alias
    r = session.get (url, params =params)
    if r.status_code == requests.codes.ok:
        six.print_ (  r.text )
    r.raise_for_status()

def bisque_link(session, args):
    """insert  a file based on the irods path"""
    session.log.info ("link %s", args)

    url = args.host +  "/blob_service/paths/insert"
    payload = None
    params = {}

    if args.srcpath:
        el_args = {}
        for fld in ('permission', 'hidden'):
            if getattr(args, fld) is not None:
                el_args [fld] = getattr (args, fld)
        resource = ET.Element (args.resource or 'resource', value=args.srcpath[0], **el_args)
        if args.tag_file:
            # Load file into resource
            try:
                resource_tags = ET.parse (args.tag_file).getroot()
                resource.extend (resource_tags)
            except ParseError as pe:
                six.print_('Parse failure: aborting: ', pe)
                return

        payload = ET.tostring (resource)
    if args.alias:
        params['user'] =  args.alias
    r  =  session.post (url, data=payload, params=params)
    if r.status_code == requests.codes.ok:
        if args.compatible:
            response = ET.fromstring(r.text)
            uniq = response.get('resource_uniq')
            uri  = response.get('uri')
            six.print_ (uniq, uri)
        else:
            six.print_(r.text)

    r.raise_for_status()

def bisque_copy(session, args):
    """COPY  a file based on the irods path"""
    session.log.info ("insert %s", args)


    #url = urlparse.urljoin(args.host, "/blob_service/paths/insert_path?path=%s" % args.srcpath)
    url = args.host +  "/import_service/transfer"
    #payload = None
    params = {}

    if args.srcpath:
        resource = ET.Element ('resource', value=args.srcpath[0], permission=args.permission)
        #resource = "<resource  value='%s' />" % (os.path.basename(args.srcpath[0]), args.srcpath[0])
        if args.tag_file:
            # Load file into resource
            try:
                resource_tags = ET.parse (args.tag_file).getroot()
                resource.extend (resource_tags)
            except ParseError as pe:
                six.print_('Parse failure: aborting: ', pe)
                return

        files  = { 'file': ( os.path.basename(args.srcpath[0]), open(args.srcpath[0], 'rb')),
                   'file_resource' : ( None, ET.tostring (resource), 'text/xml'),
        }
    if args.alias:
        params['user'] =  args.alias
    r  =  session.post (url, files=files, params=params)
    if r.status_code == requests.codes.ok:
        six.print_(r.text)
    r.raise_for_status()


def bisque_rename(session, args):
    """rename based on paths"""
    session.log.info ("rename %s", args)

    url = args.host +  "/blob_service/paths/move"
    params={'path': args.srcpath[0], 'destination': args.dstpath}
    if args.alias:
        params['user'] =  args.alias

    r = session.get (url,params=params)
    if r.status_code == requests.codes.ok:
        six.print_ (  r.text )
    r.raise_for_status()


def bisque_list(session, args):
    """delete a file based on the irods path"""

    session.log.info ("list %s", args)

    url = args.host +  "/blob_service/paths/list"
    if len(args.srcpath)>0:
        params = { 'path' : args.srcpath[0] }
    if args.alias:
        params['user'] =  args.alias
    r = session.get(url,params=params)
    #six.print_( r.request.headers )
    if r.status_code == requests.codes.ok:
        if args.compatible :
            for resource  in ET.fromstring (r.text):
                six.print_( resource.get ('resource_uniq') )
            return
        else:
            if args.unique:
                for resource  in ET.fromstring (r.text):
                    six.print_( resource.get ('resource_uniq'), resource.get ('resource_value' ))
                return
        six.print_(r.text)
        #six.print_( r.text )
    r.raise_for_status()



OPERATIONS = {
    'ls' : bisque_list,
    'ln' : bisque_link,
    'cp' : bisque_copy,
    'mv' : bisque_rename,
    'rm' : bisque_delete,
}

DESCRIPTION="""'Manipulate bisque resource with paths

Insert, link, move and remove resource by their path.
"""

class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("Subparser '{}'".format(choice))
                print(subparser.format_help())

        parser.exit()


def main():

    config = SafeConfigParser()
    config.add_section('bqpath')
    for k,v in DEFAULTS.items():
        config.set('bqpath', k,v)

    config.read (['.bisque', os.path.expanduser('~/.bisque'), '/etc/bisque/bisque_config'])
    defaults =  dict(config.items('bqpath'))

    parser = argparse.ArgumentParser(description=DESCRIPTION,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    #parser.add_argument('--help', action=_HelpAction, help='help for help if you need some help')  # add custom help
    parser.add_argument('--alias', help="do action on behalf of user specified")
    parser.add_argument('-d', '--debug', action="store_true", default=False, help="log debugging")
    parser.add_argument('-H', '--host', default=defaults['bisque_host'], help="bisque host")
    parser.add_argument('-c', '--credentials', default="%s:%s" % (defaults['bisque_admin_user'], defaults["bisque_admin_pass"]), help="user credentials")
    parser.add_argument('-C', '--compatible',  action="store_true", help="Make compatible with old script")
    parser.add_argument('-V', '--verbose', action='store_true', help='print stuff')
    #parser.add_argument('-P', '--permission',   default="private", help="Set resource permission (compatibility)")
    #parser.add_argument('--hidden',   default=None, help="Set resource visibility (hidden)")
    #parser.add_argument('command', help="one of ls, cp, mv, rm, ln" )
    #parser.add_argument('paths',  nargs='+')

    sp = parser.add_subparsers()
    lsp = sp.add_parser ('ls')
    lsp.add_argument('-u', '--unique', default=None, action="store_true", help="return unique codes")
    lsp.add_argument('paths',  nargs='+')
    lsp.set_defaults (func=bisque_list)
    lnp = sp.add_parser ('ln')
    lnp.add_argument('-T', '--tag_file', default = None, help="tag document for insert")
    lnp.add_argument('-P', '--permission',   default="private", help="Set resource permission (compatibility)")
    lnp.add_argument('-R', '--resource', default=None, help='force resource type')
    lnp.add_argument('--hidden',   default=None, help="Set resource visibility (hidden)")
    lnp.add_argument('paths',  nargs='+')
    lnp.set_defaults(func=bisque_link)
    cpp = sp.add_parser ('cp')
    cpp.add_argument('paths',  nargs='+')
    cpp.add_argument('-T', '--tag_file', default = None, help="tag document for insert")
    cpp.add_argument('-P', '--permission',   default="private", help="Set resource permission (compatibility)")
    cpp.add_argument('--hidden',   default=None, help="Set resource visibility (hidden)")
    cpp.set_defaults(func=bisque_copy)
    mvp = sp.add_parser ('mv')
    mvp.add_argument('paths',  nargs='+')
    mvp.set_defaults(func=bisque_rename)
    rmp = sp.add_parser ('rm')
    rmp.add_argument('paths',  nargs='+')
    rmp.set_defaults(func=bisque_delete)



    logging.basicConfig(filename=config.get ('bqpath', 'logfile'),
                        level=logging.INFO,
                        format = "%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s")

    log = logging.getLogger('rods2bq')

    args = parser.parse_args ()
    if args.debug:
        logging.getLogger().setLevel (logging.DEBUG)

    #if args.command not in OPERATIONS:
    #    parser.error("command %s must be one of 'ln', 'ls', 'cp', 'mv', 'rm'" % args.command)

    if len(args.paths) > 1:
        args.dstpath = args.paths.pop()
        args.srcpath = args.paths
    else:
        args.srcpath = args.paths

    if args.compatible:
        paths =[]
        irods_host = defaults.get ('irods_host')
        for el in args.srcpath:
            if not el.startswith ('irods://'):
                paths.append (irods_host + el)
            else:
                paths.append (el)
        args.srcpath = paths
        if args.dstpath and not args.dstpath.startswith('irods://'):
            args.dstpath = irods_host + args.dstpath

    if args.debug:
        six.print_(args, file=sys.stderr)

    try:
        session = requests.Session()
        requests.packages.urllib3.disable_warnings()
        session.log = logging.getLogger('rods2bq')
        #session.verify = False
        session.auth = tuple (args.credentials.split(':'))
        session.headers.update ( {'content-type': 'application/xml'} )
        #OPERATIONS[args.command] (session, args)
        args.func (session, args)
    except requests.exceptions.HTTPError as e:
        log.exception( "exception occurred %s : %s", e, e.response.text )
        six.print_("ERROR:",  e.response and e.response.status_code)

    sys.exit(0)

if __name__ == "__main__":
    main()
