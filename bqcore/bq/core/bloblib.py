###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c)  2011                                                   ##
##      by the Regents of the University of California                       ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

"""

import os
import logging
import posixpath
import urllib2
import base64
import hashlib
import re
import socket
from urlparse import urlparse
from xml.etree.ElementTree import XMLParser

log = logging.getLogger('bisquik.bloblib')

class BlobLib() :
    def __init__(self, local_cache_dir, basic_auth_user, basic_auth_password):
        self.local_cache_dir = local_cache_dir
        self.basic_auth_user = basic_auth_user
        self.basic_auth_password = basic_auth_password
        self._mymkdir(local_cache_dir)

    def localfile(self, bloburl):
        # First check to see if bloburl is in our local cache.  Hash the bloburl and check for a file with that name in local_cache_dir.
        # If it's there, return it.
        # If it's not there:
        # Query the blob server.  IF we get a URL and it's a local file URL, return that path.
        # If we get a URL and it's not a local file URL, fetch it and cache it locally, then return that path.
        myhash = self._hashurl(bloburl)
        localpath = self.local_cache_dir + "/" + myhash
        if os.path.exists(localpath):
            print("returning from cache")
            return "file://%s/%s" % (socket.getfqdn(), localpath)
        else:
            # Query the blob server on this bloburl...pull out the original url
            # Original URL local?  Then return the path...
            # Not-local?  Stream the thing to a local file, then return that path.
            req = urllib2.Request(bloburl)
            authstring = base64.b64encode(self.basic_auth_user + ":" + self.basic_auth_password)
            req.add_header('Authorization', "Basic " + authstring)
            try:
                resp = urllib2.urlopen(req)
            except URLError, e:
                log.info("localfile(): error fetching url - %s" % e)
                return
            target = BlobLibParser()
            parser = XMLParser(target=target)
            while True:
                buf = resp.read(1024)
                if not buf: break
                parser.feed(buf)
            url = parser.close()
            log.info("Queried and got url %s " % url)

            # Is it a local URL?
            comps = urlparse(url)
            if comps.scheme == 'file' and comps.hostname == socket.getfqdn():
                return url
            else:
                f = open(localpath, 'wb')
                for b in self.localstream(bloburl):
                    f.write(b)
                f.flush()
                f.close()
                return "file://%s/%s" % (socket.getfqdn(), localpath)


    # Generator....use like 'for b in localstream("http://example.com"):'
    def localstream(self, bloburl):
        CHUNK = 16 * 1024
        authstring = base64.b64encode(self.basic_auth_user + ":" + self.basic_auth_password)
        req = urllib2.Request(self._streamurl(bloburl))
        req.add_header('Authorization', "Basic " + authstring)
        try:
            resp = urllib2.urlopen(req)
        except URLError, e:
            return
        while True:
            chunk = resp.read(CHUNK)
            if not chunk: break
            yield chunk

    def _hashurl(self, bloburl):
        h = hashlib.sha1()
        h.update(bloburl)
        return h.hexdigest()


    def _mymkdir(self, newdir):
        """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
        """
        if os.path.isdir(newdir):
            pass
        elif os.path.isfile(newdir):
            raise OSError("a file with the same name as the desired " \
                              "dir, '%s', already exists." % newdir)
        else:
            head, tail = os.path.split(newdir)
            if head and not os.path.isdir(head):
                self.mymkdir(head)
            if tail:
                try:
                    os.mkdir(newdir)
                except OSError, e:
                    log.error ('MKDIR: '+ str(e))

    def _streamurl(self, bloburl):
        a = re.sub('/blob_service/', '/blob_service/stream/', bloburl)
        return a


class BlobLibParser:
    url = ''
    def start(self, tag, attrib):
        if tag == 'blob':
           self.url = attrib['original_uri']
    def end(self, tag):
        pass
    def data(self, data):
        pass
    def close(self):
        return self.url
