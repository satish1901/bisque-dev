###############################################################################
##  Bisque                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011,2012                           ##
##     by the Regents of the University of California                        ##
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
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY         ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE         ##
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR        ##
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR           ##
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,     ##
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,       ##
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR        ##
## PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF    ##
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING      ##
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS        ##
## SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.              ##
##                                                                           ##
## The views and conclusions contained in the software and documentation     ##
## are those of the authors and should not be interpreted as representing    ##
## official policies, either expressed or implied, of <copyright holder>.    ##
###############################################################################
"""
SYNOPSIS
========
blob_service 
  

DESCRIPTION
===========
Micro webservice to store and retrieve blobs(untyped binary storage) on a variety 
of storage platforms: local, irods, s3
"""
import os
import logging
import hashlib
import urlparse
import itertools


from lxml import etree
from datetime import datetime


import tg
from tg import expose, flash, config, require, abort
from tg.controllers import RestController
from paste.fileapp import FileApp
from pylons.controllers.util import forward
from repoze.what import predicates 

from bq.core.service import ServiceMixin
from bq.core.service import ServiceController
from bq.core import  identity
from bq.core.permission import perm2str
from bq.exceptions import IllegalOperation
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_uniq_hash
from bq import data_service
from bq.data_service.model import Taggable, DBSession



import blob_storage

log = logging.getLogger('bq.blobs')

try:
    # python 2.6 import
    from ordereddict import OrderedDict
except ImportError:
    try:
        # python 2.7 import
        from collections import OrderedDict
    except ImportError:
        log.error("can't import OrderedDict")


###########################################################################
# Hashing Utils
###########################################################################

import sys
import hashlib

def file_hash_SHA1( filename ):
    '''Takes a file path and returns a SHA-1 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.sha1()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()

def file_hash_MD5( filename ):
    '''Takes a file path and returns a MD5 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.md5()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()	  
   


def guess_type(filename):
    from bq import image_service 
    filetype = image_service.guess_image_type (filename)
    if filetype:
        return 'image'
    return 'file'

def load_stores():
    stores = OrderedDict()
    store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ] 
    log.debug ('requested stores = %s' % store_list)
    for store in store_list:
        params = dict ( (x[0].replace('bisque.stores.%s.' % store, ''), x[1]) 
                        for x in  config.items() if x[0].startswith('bisque.stores.%s' % store))
        if 'path' not in params:
            log.error ('cannot configure %s with out path parameter' % store)
            continue
        log.debug("params = %s" % params)
        driver = blob_storage.make_storage_driver(params.pop('path'), **params)
        if driver is None: 
            log.error ("failed to configure %s.  Please check log for errors " % store)
            continue
        stores[store] = driver
    return stores


###########################################################################
# BlobServer
###########################################################################

class BlobServer(RestController, ServiceMixin):
    '''Manage a set of blob files'''
    service_type = "blob_service"
    
    def __init__(self, url ):
        ServiceMixin.__init__(self, url)
        self.stores = load_stores()
        log.info ('configured stores %s' % ','.join( str(x) for x in self.stores.keys()))


    def check_access(self, ident, action):
        from bq.data_service.controllers.resource_query import resource_permission
        query = DBSession.query(Taggable).filter_by (resource_uniq = ident)
        resource = resource_permission (query, action=action).first()
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    @expose()
    def get_one(self, *args):
        "Fetch a blob based on uniq ID"
        log.info("get_one() called %s" % args)
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        ident = args[0]
        self.check_access(ident, RESOURCE_READ)
        try:
            localpath = os.path.normpath(self.localpath(ident))
            disposition = 'filename="%s"'% self.getBlobFileName(ident)

            return forward(FileApp(localpath,
                                   content_disposition=disposition,                                   
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks
        except IllegalOperation:
            abort(404)



    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def post(self, **kwargs):
        "Create a blob based on unique ID"
        log.info("post() called %s" % kwargs)
        #log.info("post() body %s" % tg.request.body_file.read())
        resource =  self.storeBlob(flosrc = tg.request.body_file)
        tg.request.body_file.close()
        return resource

    
    @expose()
    @require(predicates.not_anonymous())
    def delete(self, *args, **kwargs):
        ' Delete the resource  '
        ident = args[0]
        log.info("get_one() called %s" % args)
        from bq.data_service.controllers.resource_query import resource_delete
        resource = self.getBlobInfo(ident)
        resource_delete(resource)

    @expose()
    @require(predicates.not_anonymous())
    def move(self, src, dst, *args,  **kwargs):
        ' Move a resource identified by path  '
        log.info("get_one() called %s" % args)
        from bq.data_service.controllers.resource_query import resource_permission
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        query = DBSession.query(Taggable).filter_by (resource_value=src,resource_parent=None)
        resource = resource_permission(query, RESOURCE_EDIT).first()
        if resource:
            resource.resource_value = dst
        return resource


    def storeBlob(self, flosrc=None, filename=None, url=None,  permission="private", **kw):
        """Store the file object in the next blob and return the resource.

        @param flosrc: a local file object
        @param filename: the original filename
        @param url: a url if a remote object
        @param perrmision: the permission for the resource
        @return: a resource or None on failure
        """
        user_name = identity.current.user_name
        blob_id = None
        flocal = None
        if flosrc is not None:
            for store_id, store in self.stores.items():
                try:
                    # blob storage part
                    if store.readonly:
                        log.debug("skipping %s: is readonly" % store_id)
                        continue
                    # dima: make sure local file name will be ascii, should be fixed later
                    # dima: unix without LANG or LC_CTYPE will through error due to ascii while using sys.getfilesystemencoding()
                    #filename_safe = filename.encode(sys.getfilesystemencoding()) 
                    #filename_safe = filename.encode('ascii', 'xmlcharrefreplace')
                    filename_safe = filename.encode('idna')
                    blob_id, flocal = store.write(flosrc, filename_safe, user_name = user_name)
                    break
                except Exception, e:
                    log.exception('storing blob failed')
        elif url is not None:
            if filename is None:
                filename  = url.rsplit('/',1)[1]
            blob_id = url
        else:
            log.error("blobStore without URL or file: nothing to do")
            return None

        if blob_id is None:
            log.error('Could not store %s on any store: %s' %(filename, self.stores.keys()))
            return None

        # hashed filename + stuff
        fhash = make_uniq_hash (filename)
        # resource creation
        resource_type = guess_type(filename)                  

        resource = etree.Element( resource_type, permission = permission,
                                  resource_uniq = fhash,
                                  resource_name = filename,
                                  resource_value = blob_id )

        etree.SubElement(resource, 'tag', name="filename", value=filename)
        etree.SubElement(resource, 'tag', name="upload_datetime", value=datetime.now().isoformat(' '), type='datetime' ) 

        if resource_type == 'image':
            #resource.set('src', "/image_service/images/%s" % fhash) # dima: this here is a hack!!!!
            pass
        #if flocal is not None:
        #    etree.SubElement(resource, 'tag', name='sha1', value=file_hash_SHA1(flocal))


        # ingest extra tags
        if 'tags' in kw and kw['tags'] is not None:
            tags = kw['tags']
            if hasattr(tags, 'tag') and tags.tag == 'resource':
                #resource.extend(copy.deepcopy(list(tags)))
                resource.extend(list(tags))

        log.info ("NEW RESOURCE <= %s" % (etree.tostring(resource)))
        return data_service.new_resource(resource = resource)


    def localpath (self, ident):
        "Find  local path for the identified blob, using workdir for local copy if needed"

        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        path = None
        fullpath = None
        if resource is not None and resource.resource_value:
            for store in self.stores.values():
                if store.valid(resource.resource_value):
                    fullpath = resource.resource_value
                    path =  store.localpath(fullpath)
                    break
            log.debug('using %s full=%s localpath=%s' % (ident, fullpath, path))
            return path
        raise IllegalOperation("bad resource value %s" % ident)


    def getBlobInfo(self, ident): 
        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        return resource

    def getBlobFileName(self, ident): 
        fobj = self.getBlobInfo(ident)
        fname = str(id)
        if fobj != None and fobj.resource_name != None:
            fname =  fobj.resource_name 
        log.debug('Blobsrv - original name %s->%s ' % (ident, fname ))
        return fname   

    def blobsExist(self, fhashes):
        'search for files by content hash'
        blobsfound = []
        #for fhash in fhashes:
        #   if blobdb.find_image_id(fhash) != None:
        #       blobsfound.append(fhash)

        for fhash in fhashes:
            resource = DBSession.query(Taggable).filter_by (resource_uniq = fhash).first()
            if resource:
                blobsfound.append(fhash)
        log.warn("blobsExist not implemented")
        return blobsfound

    def originalFileName(self, id): 
        return self.getBlobFileName(id) 
        
    def fileExists(self, id):
        if id==None: return False      
        try:
            fileName = self.localpath(id)    
            return fileName and os.path.exists(fileName)
        except IllegalOperation,e:
            return False
        except Exception, e:
            log.exception('cannot load resource_uniq %s' % id)
            return False

    def geturi(self, id):
        return self.url + '/' + str(id)



    def move_resource_store(self, srcstore, dststore):
        """Find all resource on srcstore and move to dststore

        :param srcstore: Source store  ID
        :param dststore: Destination store ID
        """
        src_store = self.stores.get(srcstore)
        dst_store = self.stores.get(dststore)

        if src_store is None or dst_store is None:
            raise IllegalOperation("cannot access store %s, %s" % (srcstore, dststore))
        if src_store == dst_store:
            raise IllegalOperation("cannot move onto same store %s, %s" % (srcstore, dststore))

        for resource in DBSession.query(Taggable).filter_by(Taggable.resource_value.like (src_store.top)):
            localpath = self.localpath(resource.resource_uniq)

            filename = resource.resource_name
            user_name = resource.owner.resource_name
            try:
                blob_id, flocal = store.write(flosrc, filename, user_name = user_name)
            except:
                log.error("move failed for resource_uniq %s" % resource.resource_uniq)
                continue

            old_blob_id = resource.resource_value 
            resource.resource_value = blob_id
            



def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  BlobServer(uri)
    #directory.register_service ('image_service', service)

    return service

#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("bqserver")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'image_service', 'public'))]

#def get_model():
#    from bq.image_service import model
#    return model

__controller__ =  BlobServer

