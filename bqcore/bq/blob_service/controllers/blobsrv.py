import os
import shutil
import logging
from lxml import etree

import random
import datetime  
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
   

def make_uniq_hash(filename):
    rand_str = str(random.randint(1, 1000000))
    rand_str = filename + rand_str + str(datetime.datetime.now().isoformat()) 
    rand_hash = hashlib.sha1(rand_str).hexdigest()
    return rand_hash


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
        imgdir = config.get('bisque.image_service.local_dir', data_path('imagedir'))
        self.top = imgdir


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
        filepath = self.nextEmptyBlob(user_name, name)
            
        log.debug('storeBlob: ' +str(name) +' '+ str(filepath) )               
            
        if not src and name:
            src = open(name,'rb')
        src.seek(0)
        with  open(filepath, 'wb') as trg:
            shutil.copyfileobj(src, trg)

        fhash = file_hash_SHA1( filepath )
        flocal = filepath[len(self.top)+1:]

        #blobdb.updateFile (dbid=id, uri = self.geturi(id), original = name, owner = ownerId, perm = permission, fhash=fhash, ftype=ftype, flocal=flocal )
        #self.loginfo (name, id, **kw)
        return fhash, flocal

    def localpath (self, ident, workdir=None):
        "Find  local path for the identified blob, using workdir for local copy if needed"

        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        if resource is not None:
            # Determine type of resource_ url and fetch to localpath
            if resource.resource_val.startswith('irods://'):
                path = irods_handler.irods_fetch_file(resource.resource_val)
            else:
                path = "%s/%s" % (self.top, resource.resource_val)
            log.debug('using localpath=%s' % path)
            return path

        raise IllegalOperation("bad resource value %s" % ident)


    def getBlobInfo(self, ident): 
        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        return resource

    def setBlobInfo(self, image_uri, **kw): 
        blobdb.set_image_info( image_uri, kw )
        
    def setBlobCredentials(self, image_uri, owner_name, permission ): 
        blobdb.set_image_credentials( image_uri, owner_name, permission )        

    def set_file_acl(self, image_uri, owner_name, permission ): 
        blobdb.set_file_acl( image_uri, owner_name, permission )        

    def getBlobFileName(self, id): 
        fobj = self.getBlobInfo(id)
        fname = str(id)
        if fobj != None and fobj.resource_name != None:
            fname =  fobj.resource_name 
        log.debug('Blobsrv - original name for id: ' +str(id) +' '+ fname )    
        return fname   

    def getBlobOwner(self, id): 
        fobj = self.getBlobInfo(id)
        fown = None
        if fobj != None and fobj.owner != None:        
            fown = str( fobj.owner )
        log.debug('Blobsrv - original owner for id: ' +str(id) +' '+ fown )    
        return fown       

    def getBlobPerm(self, id): 
        fobj = self.getBlobInfo(id)
        fown = None
        if fobj != None and fobj.perm != None:            
            fown = str( fobj.perm )
        log.debug('Blobsrv - original perm for id: ' +str(id) +' '+ fown )    
        return fown    

    def getBlobHash(self, id): 
        fobj = self.getBlobInfo(id)
        fhash = None
        if fobj != None and fobj.sha1 != None:          
            fhash = fobj.sha1
        if fhash == None:
            fhash = file_hash_SHA1( self.originalFileName(id) )
            fobj.sha1 = fhash
            blobdb.set_image_info (fobj.uri, fobj)
            
        log.debug('Blobsrv - hash for id: ' +str(id) +' '+ str(fhash) )    
        return fhash   
        
    def blobExists(self, fhash):
        return blobdb.find_image_id(fhash)

    def blobsExist(self, fhashes):
        blobsfound = []
        for fhash in fhashes:
           if blobdb.find_image_id(fhash) != None:
               blobsfound.append(fhash)
        return blobsfound

    def blobUris(self, fhash):
        return blobdb.find_uris(fhash)

    def originalFileName(self, id): 
        return self.getBlobFileName(id) 
        

    def fileExists(self, id):
        if id==None: return False      
        fileName = self.localpath(id)    
        return os.path.exists(fileName)
        
    def geturi(self, id):
        return self.url + '/' + str(id)


    def reserveFile (self, user, filename):
        rand_str = str(random.randint(1, 1000000))
        rand_str = rand_str + str(datetime.datetime.now().isoformat()) 
        rand_hash = hashlib.sha1(rand_str).hexdigest()
        # imagedir/user/[A-Z0-9]/hash-filename
        return "%s/%s/%s/%s-%s" % (self.top, user, rand_hash[0], rand_hash, filename)

    def nextEmptyBlob(self, user, filename):
        "Return a file object to the next empty blob"
        while 1:
            fn = self.reserveFile(user, filename)
            _mkdir (os.path.dirname(fn))
            if os.path.exists (fn):
                log.warning('%s already exists' % fn)
            else:
                break
        return fn
            



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





#web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
    #web.run(urls, globals())

    srv = BlobServer()
    srv.resetFilenames()
    for i in range(10):
        p = open ('/etc/passwd')
        srv.addBlob(p)
