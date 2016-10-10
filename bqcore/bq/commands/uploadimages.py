#!/usr/bin/python
import os, sys
import urlparse
from optparse import OptionParser
import requests

import logging

logging.basicConfig(level = logging.WARN)



try:
    from lxml import etree as et
except Exception:
    from xml.etree import ElementTree as et

try:
    import magic # pylint: disable=import-error
    ms = magic.open(magic.MAGIC_NONE)
    ms.load()
    def isimagefile(fname):
        ftype = ms.file(fname)
        return ftype.lower().find ('image') >= 0
except Exception:
    def isimagefile(fname):
        return True

DESTINATION = "/import/transfer"

def upload(dest, filename, userpass, tags=None):
    files = []
    if tags:
        files.append( ('file_resource', (None, tags, "text/xml")  ) )
    files.append( ("file",  open(filename, "rb")) )

    response = requests.post (dest, files=files, auth = requests.auth.HTTPBasicAuth(*userpass),verify=False)
    if response.status_code != 200:
        print "error while copying %s: Server response %s" % (filename, response.headers)
        print "saving error information to ", filename , "-transfer.err"
        open(filename + "-transfer.err",'wb').write(response.content)
        return
    return response.content


def walk_deep(path):
    """Splits sub path that follows # sign if present
    """
    for root, _, filenames in os.walk(path):
        for f in filenames:
            yield os.path.join(root, f).replace('\\', '/')



def main():
    usage="usage %prog [options] f1 [f2 f2 d1 ] bisque-url"
    parser = OptionParser(usage)
    parser.add_option('-u','--user', dest="user", help="Credentials in  user:pass form" )
    parser.add_option('-r','--recursive', action="store_true", default=False, help='recurse into dirs')
    parser.add_option('-v','--verbose',  action="store_true", default=False, help="print actions")
    parser.add_option('-d','--debug',  action="store_true", default=False, help='print debug log')
    parser.add_option('-t','--tag', action="append", dest="tags", help="-t name:value")
    parser.add_option('--resource', action="store", default=None, help="XML resource record for the file")

    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error ("Need at least one file or directory and destination")
    dest = args.pop()

    if not dest.endswith(DESTINATION):
        dest += DESTINATION

    if not dest.startswith('http'):
        dest = "http://%s" % dest

    dest_tuple = list(urlparse.urlsplit(dest))
    dest =  urlparse.urlunsplit(dest_tuple)
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)


    # Prepare username
    if options.user is None:
        parser.error ("Need username:password")
    userpass = tuple(options.user.split (':'))

    # Prepare tags
    tags = None
    if options.resource or options.tags:
        from StringIO import StringIO
        resource = None
        if options.resource:
            if options.resource == '-':
                fresource = sys.stdin
            else:
                fresource = open(options.resource, 'r')
            resource = et.parse (fresource).getroot()
        if options.tags:
            if resource is None:
                resource = et.Element('resource', uri = "/tags")
            for t,v in [ x.split(':') for x in options.tags]:
                et.SubElement (resource, 'tag', name=t, value=v)
        if resource is not None:
            #tags = StringIO(et.tostring(resource))
            #tags.name = "stringio"
            tags = et.tostring(resource)


    #Upload copied files
    for p in args:
        path = os.path.abspath(os.path.expanduser(p))
        if os.path.isdir (path):
            for root, dirs, files in os.walk(path):
                for name in files:
                    filename = os.path.join(root, name)
                    if isimagefile (filename):
                        if options.verbose:
                            print ("transfering %s" % (filename))
                        upload(dest, filename, userpass, tags)
        elif os.path.isfile(path):
            if isimagefile (path):
                response = upload(dest, path, userpass, tags)
                if options.verbose:
                    print response




if __name__=="__main__":
    main()
