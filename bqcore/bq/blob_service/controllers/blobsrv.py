import os
import logging
import hashlib

import tg
from tg import expose, flash, config
from tg.controllers import RestController

from repoze.what import predicates 

from bq.core.service import ServiceMixin
from bq.core.service import ServiceController
from bq.core import permission, identity
from bq.core.exceptions import IllegalOperation
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util import irods_handler
from bq import data_service
from bq.data_service.model import Taggable, DBSession

import blob_storage

log = logging.getLogger('bq.blobs')

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



###########################################################################
# BlobServer
###########################################################################

class BlobServer(RestController, ServiceMixin):
    '''Manage a set of blob files'''
    service_type = "blobs"
    
    def __init__(self, url ):
        ServiceMixin.__init__(self, url)
        default_store = config.get('bisque.blob_service.default_store', 'local')
        store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','irods,local').split(',') ] 
        self.stores = []
        for st in store_list:
            self.stores.append( (st,  blob_storage.make(st)) )
        self.default_store = dict(self.stores) [default_store]
        log.info ('configured stores %s' % ','.join([ str(x[1]) for x in self.stores]))
        log.info ('Using %s for default storage' % self.default_store)


    @expose(content_type='text/xml')
    def get_all(self):
        log.info("get_all() called")
        user = identity.get_user_id()

    @expose()
    def get_one(self, *args):
        log.info("get_all() called")
        user = identity.get_user_id()

    @expose(content_type='text/xml')
    def post(self, **kwargs):
        log.info("post() called %s" % kwargs)
        log.info("post() body %s" % tg.request.body_file.read())
        user = identity.get_user_id()

    def storeBlob(self, src, name):
        """Store the file object in the next blob and return the
        descriptor"""
        user_name = identity.current.user_name
        blob_ident, flocal = self.default_store.write(src, name, user_name = user_name)
        fhash = file_hash_SHA1( flocal )
        return blob_ident, fhash

    def localpath (self, ident, workdir=None):
        "Find  local path for the identified blob, using workdir for local copy if needed"

        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        path = None
        if resource is not None:
            for nm,store in self.stores:
                if store.valid(resource.resource_value):
                    path =  store.localpath(resource.resource_value)
                    break
            log.debug('using localpath=%s' % path)
            return path
        raise IllegalOperation("bad resource value %s" % ident)


    def getBlobInfo(self, ident): 
        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        return resource

    def getBlobFileName(self, id): 
        fobj = self.getBlobInfo(id)
        fname = str(id)
        if fobj != None and fobj.resource_name != None:
            fname =  fobj.resource_name 
        log.debug('Blobsrv - original name for id: ' +str(id) +' '+ fname )    
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
        fileName = self.localpath(id)    
        return fileName and os.path.exists(fileName)
        



    def geturi(self, id):
        return self.url + '/' + str(id)



def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  BlobServer(uri)
    #directory.register_service ('image_service', service)

    return service

#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("bqcore")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'image_service', 'public'))]

#def get_model():
#    from bq.image_service import model
#    return model

__controller__ =  BlobServer

