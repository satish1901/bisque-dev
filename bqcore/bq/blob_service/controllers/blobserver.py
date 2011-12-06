# obsolete
#
#

# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
import tg
from tg import expose, flash, request
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from pylons.controllers.util import abort
from repoze.what.predicates import not_anonymous

from bq.core.service import ServiceMixin
from tg.controllers import RestController
from bq.core.model import DBSession, metadata
from bq import ingest
from bq.util import http

import os
from urlparse import urlparse
import urllib2
from urllib2 import quote
from urllib2 import unquote
from bq.util.http import request

from xml.etree.ElementTree import Element, SubElement, tostring 
from bq.blob_service.model import *

__all__ = ['BlobServerController']

import logging
log = logging.getLogger('bisquik.BS2')

class BlobServerController(RestController, ServiceMixin):
    # The predicate that must be met for all the actions in this controller:
    allow_only = not_anonymous(msg='All actions require login or basic auth')

    service_type = "blob_service"
    def __init__(self, url):
       ServiceMixin.__init__(self, url)

    def __init__(self, url):
        ServiceMixin.__init__(self, url)


    @expose(content_type='text/xml')
    def get_all(self):
        log.info("get_all() called")
        user = tg.request.identity['user']

        blobs = DBSession.query(Blob).filter(Blob.user_id == user.user_id).all()
        root = Element("blobs")
        for i in blobs:
            blob = SubElement(root, "blob")
            blob.attrib['original_uri'] = i.uri 
            blob.attrib['content_hash'] = i.hash 
            blob.attrib['blob_uri'] = self.makeurl("/blob_service/00_" + i.hash + "_" + str(i.id)) 
        log.info(tostring(root))
        return (tostring(root)) 

    @expose(content_type='text/xml')
    def get_one(self, *args):
        log.info("get_one() called")
        for arg in args:
            print("Arg: %s" % (arg))
        narg = args[0].rpartition('_')
        given_id = narg[2]
        given_hash = narg[0].rpartition('_')[2]
        log.info("Given_id: %s given_hash: %s" % (given_id, given_hash))
        root = Element("blobs")
        user = tg.request.identity['user']
        b = DBSession.query(Blob).filter(Blob.id == given_id).filter(Blob.user_id == user.user_id).filter(Blob.hash == given_hash).first()
        if b:
            blob = SubElement(root, "blob")
            blob.attrib['original_uri'] = b.uri 
            blob.attrib['hash'] = b.hash 
        else:
            abort(404)
        return (tostring(root))

    @expose(content_type='text/xml')
    def post(self, **kwargs):
        log.info("post() called %s" % kwargs)
        log.info("post() body %s" % tg.request.body_file.read())
        blobs = []
        for i in kwargs:
                for j in i.split('\n'):
                    if len(j) == 0:
                        continue
                    fields = j.rsplit(None,1)
                    existing = DBSession.query(Blob).filter(Blob.uri == fields[0]).first()
                    if existing:
                        log.info('skipped existing ITEM: %s ', (j))
                        continue
                    blob = Blob()
                    blob.uri = fields[0]
                    blob.hash = fields[1].strip('\"')
                    blob.user = tg.request.identity['user']
                    blob.perms = 0
                    DBSession.add(blob)
                    blobs.append(blob)
                    log.info('added ITEM: %s ', (j))
        DBSession.flush()
        root = Element("blobs")
        for i in blobs:
            DBSession.refresh(i)
            blob = SubElement(root, "blob")
            blob.attrib['original_uri'] = i.uri 
            blob.attrib['content_hash'] = i.hash 
            blob.attrib['blob_uri'] = self.makeurl("/blob_service/00_" + i.hash + "_" + str(i.id)) 
        # Post to ingest url now
        blobs = tostring(root)
        log.info ("SENDING blobs %s" % blobs)
        ingest.new_blobs (body = blobs )
        return blobs

    @expose(content_type='text/xml')
    def put(self, imageuri, **kwargs):
        q = DBSession.query(Blob).filter (files.c.uri==image_uri).first()
        if q:
            for k,v in kwargs.items():
                setattr(q, k, v)
            DBSession.flush()        
            res = True
        else:
            res = False
        return res        

    # Dmitry wanted this function for the image server, but it's not sufficient.  It's not required in our
    # new design, and as far as I know, will be unused.  Probably a good candidate for removal.
    @expose(content_type='text/xml')
    def uri_service(self, uri):
        root = Element("uri")
        root.attrib['uri']=uri

        url = unquote(uri)
        log.info('URI service: [' + url +']' )
        url_filename = quote(url, "")
        ofile = self.getOutFileName( 'url_', url_filename )

        if not os.path.exists(ofile):
            log.info('URI service: Fetching to file - ' + str(ofile) )
            resp, content = request(url)
            log.info ("URI service: result header=" + str(resp))
            if int(resp['status']) >= 400:
                root.attrib['error'] = 'URI service: requested URI could not be fetched...'
            else:
                f = open(ofile, 'wb')
                f.write(content)
                f.flush()
                f.close()

        root.attrib['path'] = ofile
        log.debug('URI service: ' + tostring(root) )
        return tostring(root) 

    @expose()
    def stream(self, *args):
        narg = args[0].rpartition('_')
        given_id = narg[2]
        given_hash = narg[0].rpartition('_')[2]
        log.info("Stream() action called: Given_id: %s given_hash: %s" % (given_id, given_hash))

        user = tg.request.identity['user']
        b = DBSession.query(Blob).filter(Blob.id == given_id).filter(Blob.user_id == user.user_id).filter(Blob.hash == given_hash).first()
        if not b: abort(404)
        action = b.uri.partition('://')[0]
        if action == 'file' or action == 'http' or action == 'https' :
            log.info("Stream() detected a %s url" % (action)) 
            req = urllib2.urlopen(b.uri)
            tg.response.headers['Content-Type'] =  req.info()['Content-Type']
            tg.response.headers['Content-Length'] = req.info()['Content-Length']
            def read_response_chunk(req):
                CHUNK = 16 * 1024
                while True:
                    chunk = req.read(CHUNK)
                    if not chunk: break
                    yield chunk 
            return read_response_chunk(req)



######################## Non-actions below

    imagedir = "/tmp/imagedir"
    workdir = "/tmp/workdir"

    def ensureWorkPath(self, path):
        # change ./imagedir to ./workdir if needed
        path = path.replace( self.imagedir, self.workdir, 1 )
        if path.find( self.workdir ) == -1:
            path = self.workdir + '/' + path

        #make sure that the path directory exists
        print os.path.dirname(path)
        self.mymkdir( os.path.dirname(path) )
        return path

    def getOutFileName(self, infilename, appendix):
        ofile = self.ensureWorkPath(infilename)
        return ofile + appendix

    def mymkdir(self, newdir):
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




    
def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  BlobServerController(uri)
    #directory.register_service ('client_service', service)

    return service

def get_model():
    from bq.blob_service import model
    return model



__controller__ = BlobServerController
#__staticdir__ = get_static_dirs()
__model__ = get_model()


################################################################################
# ProcessToken
################################################################################

class ProcessToken(object):
    'Keep data with correct content type and cache info'
    def __init__(self):
        self.data        = False
        self.contentType = ''
        self.cacheInfo   = ''
        self.outFileName = ''
        self.httpResponseCode = 200
        self.dims        = None
        self.histogram   = None

    def setData (self, data_buf, content_type):
        self.data = data_buf
        self.contentType = content_type
        self.cacheInfo = 'max-age=302400' # one week

    def setHtml (self, text):
        self.data = text
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'

    def setXml (self, xml_str):
        self.data = xml_str
        self.contentType = 'text/xml'
        self.cacheInfo = 'max-age=302400' # one week
        #self.cacheInfo = 'no-cache'

    def setImage (self, fname, format):
        self.data = fname
        self.contentType = 'image/' + format.lower()
        #self.cacheInfo = 'max-age=43200' # one day
        #self.cacheInfo = 'max-age=86400' # two days
        self.cacheInfo = 'max-age=302400' # one week
        #self.cacheInfo = 'no-cache'
        if self.contentType.lower() == 'image/flash':
          self.contentType = 'application/x-shockwave-flash'
        if self.contentType.lower() == 'image/flv':
          self.contentType = 'video/x-flv'
        if self.contentType.lower() == 'image/avi':
          self.contentType = 'video/avi'
        if self.contentType.lower() == 'image/quicktime':
          self.contentType = 'video/quicktime'
        if self.contentType.lower() == 'image/wmv':
          self.contentType = 'video/x-ms-wmv'
        if self.contentType.lower().startswith('image/mpeg'):
          self.contentType = 'video/mp4'
        if self.contentType.lower() == 'image/matroska':
          self.contentType = 'video/x-matroska'


    def setFile (self, fname):
        self.data = fname
        self.contentType = 'application/octet-stream'
        self.cacheInfo = 'max-age=302400' # one week

    def setNone (self):
        self.data = False
        self.contentType = ''
    #Status-Code    = "200"   ; OK
      #| "201"   ; Created
      #| "202"   ; Accepted
      #| "204"   ; No Content
      #| "301"   ; Moved Permanently
      #| "302"   ; Moved Temporarily
      #| "304"   ; Not Modified
      #| "400"   ; Bad Request
      #| "401"   ; Unauthorized
      #| "403"   ; Forbidden
      #| "404"   ; Not Found
      #| "500"   ; Internal Server Error
      #| "501"   ; Not Implemented
      #| "502"   ; Bad Gateway
      #| "503"   ; Service Unavailable

    def setHtmlErrorUnauthorized (self):
        self.data = 'Permission denied...'
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 401

    def setHtmlErrorNotFound (self):
        self.data = 'File not found...'
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 404

    def isValid (self):
        if self.data:
            return True
        else:
            return False

    def isImage (self):
        if self.contentType.startswith('image/'):
            return True
        if self.contentType.startswith('video/'):
            return True
        elif self.contentType.lower() == 'application/x-shockwave-flash':
            return True
        else:
            return False

    def isFile (self):
        if self.contentType.startswith('image/') or self.contentType.startswith('application/') or self.contentType.startswith('video/'):
            return True
        else:
            return False

    def isText (self):
        if self.contentType.startswith('text/'):
            return True
        else:
            return False

    def isHtml (self):
        if self.contentType == 'text/html':
            return True
        else:
            return False

    def isXml (self):
        if self.contentType == 'text/xml':
            return True
        else:
            return False

    def isHttpError (self):

        return (not self.httpResponseCode == 200)

    def hasFileName (self):
        if len(self.outFileName) > 0:
            return True
        else:
            return False

    def testFile (self):
        if self.isFile() and not os.path.exists(self.data):
            self.setHtmlErrorNotFound()

    def getDim (self, key, def_val):
        if self.dims is None:
            return def_val
        if key in self.dims:
            return self.dims[key]
        else:
            return def_val

