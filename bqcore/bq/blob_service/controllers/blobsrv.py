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
    service_type = "blob_service"
    
    def __init__(self, url ):
        ServiceMixin.__init__(self, url)
        store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ] 
        log.debug ('requested stores = %s' % store_list)
        # Filter out None values for stores that can't be made
        self.stores = list(itertools.ifilter(lambda x:x, (blob_storage.make_driver(st) for st in store_list )))
        log.info ('configured stores %s' % ','.join( str(x) for x in self.stores))


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

    @expose(content_type='text/xml')
    def get_all(self):
        log.info("get_all() called")
        user = identity.get_user_id()




    @expose()
    def get_one(self, *args):
        "Fetch a blob based on uniq ID"
        log.info("get_one() called %s" % args)
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        ident = args[0]
        self.check_access(ident, RESOURCE_READ)
        try:
            localpath = self.localpath(ident)
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
        log.info("post() body %s" % tg.request.body_file.read())
        user = identity.get_user_id()


    # available additional configs:
    # perm
    # tags
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
        if flosrc is not None:
            for store in self.stores:
                try:
                    # blob storage part
                    blob_id, flocal = store.write(flosrc, filename, user_name = user_name)
                    break
                except Exception, e:
                    log.exception('storing blob failed')
            if blob_id is None:
                log.error('Could not store %s on any %s' %(filename, self.stores))
                return None
            fhash = file_hash_SHA1( flocal )
        elif url is not None:
            if filename is None:
                filename  = url.rsplit('/',1)[1]
            blob_id = url
            fhash   = make_uniq_hash(filename)
        else:
            log.error("blobStore without URL or file: nothing to do")
            return None

        # resource creation
        resource_type = guess_type(filename)                  

        if 'perm' in kw:             
            permision = perm2str.get (kw['perm'], 'private')

        resource = etree.Element( resource_type, permision = permission,
                                  resource_uniq = fhash,
                                  resource_name = filename,
                                  resource_value  = blob_id )

        if resource_type == 'image':
            resource.set('src', "/image_service/images/%s" % fhash) # dima: this here is a hack!!!!

        etree.SubElement(resource, 'tag', name="filename", value=filename)
        etree.SubElement(resource, 'tag', name="upload_datetime", value=datetime.now().isoformat(' '), type='datetime' ) 

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
        if resource is not None and resource.resource_value:
            for store in self.stores:
                if store.valid(resource.resource_value):
                    path =  store.localpath(resource.resource_value)
                    break
            log.debug('using localpath=%s' % path)
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

