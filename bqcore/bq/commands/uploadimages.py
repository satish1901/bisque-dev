#!/usr/bin/python
import os, sys

import urlparse
from optparse import OptionParser
from bq.util import http 


try:
    from lxml import etree as et
except:
    from xml.etree import ElementTree as et

try:
    import magic
    ms = magic.open(magic.MAGIC_NONE)
    ms.load()
    def isimagefile(fname):
        ftype = ms.file(fname)
        return ftype.lower().find ('image') >= 0
except:
    def isimagefile(fname):
        return True

DESTINATION = "/import/transfer"

def upload(dest, filename, userpass, tags=None):
    files = {  "file" : open(filename, "rb") }
    if tags:
        files['file_resource'] = tags
        
    headers, content = http.post_files (dest, files, userpass = userpass)
    if headers['status'] != '200':
        print "error while copying %s: Server response %s" % (filename, headers['status'])
        open(filename + "-transfer.err",'wb').write(content)
    

def main():
    usage="usage %prog [options] f1 [f2 f2 d1 ] bisque-url"
    parser = OptionParser(usage)
    parser.add_option('-u','--user', dest="user", help="Credentials in  user:pass form" )
    parser.add_option('-r','--recursive', action="store_true", default=False)
    parser.add_option('-v','--verbose',  action="store_true", default=False)
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
                upload(dest, path, userpass, tags)
            
            


if __name__=="__main__":
    main()
