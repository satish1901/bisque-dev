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
from datetime import timedelta

#import smokesignal

import tg
from tg import expose, config, require, abort
from tg.controllers import RestController, TGController
#from paste.fileapp import FileApp
from bq.util.fileapp import BQFileApp
from pylons.controllers.util import forward
from paste.deploy.converters import asbool
from repoze.what import predicates

from bq.core import  identity
#from bq.core.identity import set_admin_mode
from bq.core.service import ServiceMixin
from bq.core.service import ServiceController
from bq.exceptions import IllegalOperation, DuplicateFile, ServiceError
from bq.util.timer import Timer
from bq.util.sizeoffmt import sizeof_fmt


from bq import data_service
from bq.data_service.model import Taggable, DBSession
#from bq import image_service

SIG_NEWBLOB  = "new_blob"

from . import blob_storage
from . import store_resource

log = logging.getLogger('bq.blobs')



#########################################################
# Utility functions
########################################################

def guess_type(filename):
    from bq import image_service
    filename = filename.strip()
    if image_service.is_image_type (filename):
        return 'image'
    return 'file'


def transfer_msg(flocal, transfer_t):
    'return a human string for transfer time and size'
    if flocal is None or not os.path.exists(flocal):
        return "NO FILE to measure %s" % flocal
    fsize = os.path.getsize (flocal)
    name  = os.path.basename(flocal)
    if isinstance(name, unicode):
        name  = name.encode('utf-8')
    if transfer_t == 0:
        return "transferred %s in 0 sec!" % fsize
    return "{name} transferred {size} in {time} ({speed}/sec)".format(
        name=name, size=sizeof_fmt(fsize),
        time=timedelta(seconds=transfer_t),
        speed = sizeof_fmt(fsize/transfer_t))


class TransferTimer(Timer):
    def __init__(self, path=''):
        super(TransferTimer, self).__init__()
        self.path = path
    def __exit__(self, *args):
        Timer.__exit__(self, *args)
        if self.path and log.isEnabledFor(logging.INFO):
            log.info (transfer_msg (self.path, self.interval))



######################################################
# Store manageer


class DriverManager(object):
    'Manage multiple stores'

    def __init__(self):
        self.drivers = blob_storage.load_storage_drivers()
        log.info ('configured stores %s' ,  ','.join( str(x) for x in self.drivers.keys()))

    def valid_blob(self, blob_id):
        "Determin if uripath is supported by configured blob_storage (without fetching)"
        for driver in self.drivers.values():
            if driver.valid(blob_id):
                return True
        return False

    def fetch_blob(self, blob_id):
        """Find a driver matching the prefix of blob_id
        """
        for driver in self.drivers.values():
            if driver.valid(blob_id):
                with TransferTimer() as t:
                    b = t.path,_,_ = driver.localpath(blob_id)
                if b.path is not None:
                    # if sub path could not be serviced by the storage system and the file is a package (zip, tar, ...)
                    # extract the sub element here and return the extracted path with sub as None                    
                    return b
        log.warn ("Failed to fetch blob: %s", blob_id)
        return blob_storage.Blobs(path=None, sub=None, files=None)

    def save_blob(self, fileobj, filename, user_name, uniq):
        #filename_safe = filename.encode('ascii', 'xmlcharrefreplace')
        filename_safe = filename
        if filename_safe[0]=='/':
            return self.save_2store(fileobj, filename_safe, user_name, uniq)
        else:
            return self.save_relative(fileobj, filename_safe, user_name, uniq)

    def save_2store (self, fileobj, filename, user_name, uniq):
        empty, store_name, path = filename.split('/', 2)
        driver = self.drivers[store_name]
        try:
            if driver.readonly:
                raise IllegalOperation("Write to readonly store")
            driveruri, localpath =  driver.write(fileobj, path, user_name = user_name, uniq=uniq)
            return driveruri, localpath
        except DuplicateFile, e:
            raise e
        except Exception, e:
            log.exception('storing blob failed')
        return (None,None)


    def save_relative(self, fileobj, filename, user_name, uniq):
        for driver_id, driver in self.drivers.items():
            try:
                # blob storage part
                if driver.readonly:
                    log.debug("skipping %s: is readonly" , driver_id)
                    continue
                driveruri, localpath =  driver.write(fileobj, filename, user_name = user_name, uniq=uniq)
                return driveruri, localpath
            except DuplicateFile, e:
                raise e
            except Exception, e:
                log.exception('storing blob failed')
        return (None,None)

    def __str__(self):
        return "drivers%s" % [ "(%s, %s)" % (k,v) for k,v in self.drivers.items() ]

###########################################################################
# BlobServer
###########################################################################

class PathService (TGController):
    """Manipulate paths in the database

    Service to be used by filesystem agents to move references to files
    """
    def __init__(self, blobsrv):
        super (PathService, self).__init__()
        self.blobsrv = blobsrv

    @expose(content_type='text/xml')
    def index(self):
        "Path service initial page"
        return "<resource resource_type='Path service'/>"

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def list_path(self, path, *args,  **kwargs):
        'Find a resource identified by a path'
        log.info("move() called %s" ,  path)
        resource = data_service.query(None, resource_value = path)
        return etree.tostring(resource)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def insert_path(self, path, resource_type = 'file', *args,  **kwargs):
        ' Move a resource identified by path  '
        log.info("insert_path() called %s %s" , path, args)
        resource = etree.Element(resource_type, value = path)
        resource = self.blobsrv.store_blob(resource)
        return etree.tostring(resource)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def move_path(self, path, dst, *args,  **kwargs):
        ' Move a resource identified by path  '
        log.info("move() called %s" , args)
        resource = data_service.query(None, resource_value = path)
        for child in resource:
            child.set('resource_value',  dst)
            resource = data_service.update(child)
        return etree.tostring(resource)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def delete_path(self, path,  **kwargs):
        ' Delete a resource identified by path  '
        log.info("delete() called %s" , path)
        resource = data_service.query(None, resource_value = path)
        for child in resource:
            data_service.del_resource(child)
        return ""




###########################################################################
# BlobServer
###########################################################################

class BlobServer(RestController, ServiceMixin):
    '''Manage a set of blob files'''
    service_type = "blob_service"

    # do this on init
    #store = store_resource.StoreServer ()

    def __init__(self, url ):
        ServiceMixin.__init__(self, url)
        self.drive_man = DriverManager()
        self.__class__.store = store_resource.StoreServer(self.drive_man.drivers)
        self.__class__.paths  = PathService(self)

#################################
# service  functions
################################
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

    #@expose()
    #def store(self, *path, **kw):
    #    log.debug ("STORE: Got %s and %s" ,  path, kw)





    @expose()
    def get_all(self):
        return "Method Not supported"

    @expose()
    def get_one(self, ident,  **kw):
        "Fetch a blob based on uniq ID"
        log.info("get_one(%s) %s" , ident, kw)
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        #ident = args[0]
        self.check_access(ident, RESOURCE_READ)
        try:
            b = os.path.normpath(self.localpath(ident))
            localpath = b.path
            filename = self.originalFileName(ident)
            if 'localpath' in kw:
                tg.response.headers['Content-Type']  = 'text/xml'
                resource = etree.Element ('resource', name=filename, value = localpath)
                return etree.tostring (resource)
            try:
                disposition = 'attachment; filename="%s"'%filename.encode('ascii')
            except UnicodeEncodeError:
                disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8'))

            return forward(BQFileApp(localpath,
                                   content_disposition=disposition,
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks
        except IllegalOperation:
            abort(404)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def post(self, **transfers):
        "Create a blob based on unique ID"
        log.info("post() called %s" , kwargs)
        #log.info("post() body %s" % tg.request.body_file.read())

        def find_upload_resource(transfers, pname):
            log.debug ("transfers %s " , transfers)

            resource = transfers.pop(pname+'_resource', None) #or transfers.pop(pname+'_tags', None)
            log.debug ("found %s _resource/_tags %s " , pname, resource)
            if resource is not None:
                if hasattr(resource, 'file'):
                    log.warn("XML Resource has file tag")
                    resource = resource.file.read()
                if isinstance(resource, basestring):
                    log.debug ("reading XML %s" , resource)
                    try:
                        resource = etree.fromstring(resource)
                    except etree.XMLSyntaxError:
                        log.exception ("while parsing %s" %resource)
                        resource = None
            return resource

        for k,f in dict(transfers).items():
            if k.endswith ('_resource') or k.endswith('_tags'): continue
            if hasattr(f, 'file'):
                resource = find_upload_resource(transfers, k)
                resource = self.store_blob(resource = resource, fileobj = f.file)

        return resource


    @expose()
    @require(predicates.not_anonymous())
    def delete(self, ident, **kwargs):
        ' Delete the resource  '
        log.info("delete() called %s" , ident)
        from bq.data_service.controllers.resource_query import resource_delete
        from bq.data_service.controllers.resource_query import resource_permission
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        query = DBSession.query(Taggable).filter_by (resource_uniq=ident,resource_parent=None)
        resource = resource_permission(query, RESOURCE_EDIT).first()
        if resource:
            resource_delete(resource)
        return ""






########################################
# API functions
#######################################
    def create_resource(self, resource ):
        'create a resource from a blob and return new resource'
        # hashed filename + stuff

        perm     = resource.get('permission', 'private')
        filename = resource.get('name')
        if resource.tag == 'resource': # requires type guessing
            resource.set('resource_type', resource.get('resource_type') or guess_type(filename))
        if resource.get('resource_uniq') is None:
            resource.set('resource_uniq', data_service.resource_uniq() )
        # KGK
        # These are redundant (filename is the attribute name name upload is the ts
        # dima: today needed for organizer to work
        resource.insert(0, etree.Element('tag', name="filename", value=filename, permission=perm))
        resource.insert(1, etree.Element('tag',
                                         name="upload_datetime",
                                         value=datetime.now().isoformat(' '),
                                         type='datetime',
                                         permission=perm),
                        )

        log.info ("NEW RESOURCE <= %s" , etree.tostring(resource))
        return data_service.new_resource(resource = resource)


    def store_blob(self, resource, fileobj = None):
        'Store a resource in the DB must be a valid resource'
        log.debug('store_blob: %s', etree.tostring(resource))
        for x in range(3):
            try:
                uniq = resource.get ('resource_uniq')
                if uniq is None:
                    resource.set('resource_uniq', data_service.resource_uniq() )
                if fileobj is not None:
                    resource = self._store_fileobj(resource, fileobj)
                else:
                    resource = self._store_reference(resource, resource.get('value') )
                #smokesignal.emit(SIG_NEWBLOB, self.store, path=resource.get('value'), resource_uniq=resource.get ('resource_uniq'))

                if asbool(config.get ('bisque.blob_service.store_paths', True)):
                    self.store.insert_blob_path( path=resource.get('value'),
                                                 resource_name = resource.get('name'),
                                                 resource_uniq = resource.get ('resource_uniq'))
                return resource
            except DuplicateFile, e:
                log.warn("Duplicate file. renaming")
                #resource.set('resource_uniq', data_service.resource_uniq())
                resource.set('name', '%s-%s' % (resource.get('name'), resource.get('resource_uniq')[3:7+x]))
        raise ServiceError("Unable to store blob")

    # dima: store resource with multiple values - pointers to many files
    # right now it's assumed multi-blob came from a packaged file and thus values are local
    # the storage driver should be able to move files over to the desired location
    # it would be best to know where that location is and extract files directly there
    # although that will only work in the local case, if storing to irods or s3 that would
    # have to follow the driver protocol
    def store_multi_blob(self, resource, unpack_dir):
        'Store blobs for a multi-file resource'
        log.debug('store_multi_blob: %s', etree.tostring(resource))
        for x in range(3):
            try:
                uniq = resource.get ('resource_uniq')
                if uniq is None:
                    uniq = data_service.resource_uniq()
                    resource.set('resource_uniq', uniq )

                user_name = identity.current.user_name
                for value in resource.xpath('value'):
                    urlref = value.text
                    if not self.drive_man.valid_blob(urlref):
                        # We have a URLref that is not part of the sanctioned stores:
                        # We will move it
                        localpath = self._make_url_local(urlref)
                        _,sub = blob_storage.split_subpath(urlref)

                        # compute a filename for a sub-file
                        basename,_ = blob_storage.split_subpath(resource.get('name'))
                        basename = '%s.unpacked'%basename
                        subname = blob_storage.url2localpath(urlref).replace(unpack_dir, '')
                        filename = os.path.join(basename, subname).replace('\\', '/')
                        log.debug("Storing new local sub-blob [%s] with [%s]", localpath, filename)
                        if os.path.isdir(localpath):
                            # dima: we should probably list and store all files but there might be overlaps with individual refs
                            value.text = blob_storage.localpath2url(filename)
                            #continue
                        elif localpath:
                            with open(localpath, 'rb') as f:
                                with TransferTimer() as t:
                                    urlref, t.path = self.drive_man.save_blob(f, filename, user_name = user_name, uniq=uniq)
                                    # update the file reference in the resource
                                    value.text = urlref if sub is None else '%s#%s'%(urlref, sub)
                
                resource.set('name', os.path.basename(resource.get('name')))
                resource = self.create_resource(resource)
                
                if asbool(config.get ('bisque.blob_service.store_paths', True)):
                    # dima: insert_blob_path should probably be renamed to insert_blob
                    # it should probably receive a resource and make decisions on what and how to store in the file tree
                    self.store.insert_blob_path( path=resource.xpath('value')[0].text,
                                                 resource_name = resource.get('name'),
                                                 resource_uniq = resource.get ('resource_uniq'))
                return resource
            except DuplicateFile, e:
                log.warn("Duplicate file. renaming")
                resource.set('name', '%s-%s' % (resource.get('name'), resource.get('resource_uniq')[3:7+x]))
        raise ServiceError("Unable to store multi-blob")
    
    def _store_fileobj(self, resource, fileobj ):
        'Create a blob from a file .. used by store_blob'
        user_name = identity.current.user_name
        # dima: make sure local file name will be ascii, should be fixed later
        # dima: unix without LANG or LC_CTYPE will through error due to ascii while using sys.getfilesystemencoding()
        #filename_safe = filename.encode(sys.getfilesystemencoding())
        #filename_safe = filename.encode('ascii', 'xmlcharrefreplace')
        #filename_safe = filename.encode('ascii', 'replace')
        filename = resource.get('name') or  getattr(fileobj, 'name') or ''
        uniq     = resource.get('resource_uniq')

        with TransferTimer() as t:
            blob_id, t.path = self.drive_man.save_blob(fileobj, filename, user_name = user_name, uniq=uniq)

        log.debug ("_store_fileobj %s %s", blob_id, t.path)
        #dima: probably need to update the resource name ???
        #resource.set('name', os.path.basename(filename))
        resource.set('name', os.path.basename(t.path))
        resource.set('value', blob_id)
        #resource.set('resource_uniq', uniq)
        return self.create_resource(resource)

    def _make_url_local(self, urlref):
        'return a local file to the specified urlref'
        #if urlref.startswith ('file:///'):
        #    return urlref.replace('file:///', '')
        #elif urlref.startswith ('file://'):
        #    return urlref [5:]
        if urlref.startswith ('file://'):
            return blob_storage.url2localpath(urlref)
        return None

    def _store_reference(self, resource, urlref ):
        """create a reference to a blob based on its URL

        @param resource: resource an etree resource
        @param urlref:   An URL to configured store or a local file url (which may be moved to a valid store
        @return      : The created resource
        """
        if not self.drive_man.valid_blob(urlref):
            # We have a URLref that is not part of the sanctioned stores:
            # We will move it
            log.debug("Can't match %s in stores : %s", urlref, self.drive_man)
            localpath = self._make_url_local(urlref)
            if localpath:
                with open(localpath) as f:
                    return self._store_fileobj(resource, f)
            else:
                log.error("Can't put %s into stores : %s", urlref, self.drive_man)
                raise IllegalOperation("%s could not be moved to a valid store" % urlref)
        filename  = resource.get ('name') or urlref.rsplit('/',1)[1]
        resource.set ('name' ,os.path.basename(filename))
        resource.set ('value', urlref)

        return self.create_resource(resource)

    def localpath (self, uniq_ident):
        "Find  local path for the identified blob, using workdir for local copy if needed"
        resource = DBSession.query(Taggable).filter_by (resource_uniq = uniq_ident).first()
        if resource is not None and resource.resource_value:
            blob_id = resource.resource_value
            b = self.drive_man.fetch_blob(blob_id)
            log.debug('using %s full=%s localpath=%s sub=%s' , uniq_ident, blob_id, b.path, b.sub)
            return b
        elif resource is not None and resource.resource_value is None:
            #in case of a multi-file resource
            response = data_service.query(resource_uniq=uniq_ident, view='full')
            values = response.xpath('//value')
            if values is not None and len(values)>0:
                files = []
                # fetch all files referenced by the resource and return the first one
                for v in reversed(values):
                    blob_id = v.text
                    b = self.drive_man.fetch_blob(blob_id)
                    if b.files is not None:
                        files.extend(b.files)
                    else:
                        files.append(b.path)
                log.debug('using %s full=%s localpath=%s sub=%s' , uniq_ident, blob_id, b.path, b.sub)
                return blob_storage.Blobs(path=b.path, sub=b.sub, files=files)
        return None

    def originalFileName(self, ident):
        log.debug ('originalFileName: deprecated %s', ident)
        fname  = str (ident)
        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        if resource:
            if resource.resource_name != None:
                fname =  resource.resource_name
        log.debug('Blobsrv - original name %s->%s ' , ident, fname)
        return fname

    def move_resource_store(self, srcstore, dststore):
        """Find all resource on srcstore and move to dststore

        @param srcstore: Source store  ID
        @param dststore: Destination store ID
        """
        src_store = self.drive_man.get(srcstore)
        dst_store = self.drive_man.get(dststore)
        if src_store is None or dst_store is None:
            raise IllegalOperation("cannot access store %s, %s" % (srcstore, dststore))
        if src_store == dst_store:
            raise IllegalOperation("cannot move onto same store %s, %s" % (srcstore, dststore))

        for resource in DBSession.query(Taggable).filter_by(Taggable.resource_value.like (src_store.top)):
            localpath = self.localpath(resource.resource_uniq)

            filename = resource.resource_name
            user_name = resource.owner.resource_name
            try:
                with open(localpath) as f:
                    blob_id, flocal = dst_store.write(f, filename, user_name = user_name)
            except:
                log.error("move failed for resource_uniq %s" , resource.resource_uniq)
                continue
            old_blob_id = resource.resource_value
            resource.resource_value = blob_id

    def geturi(self, id):
        return self.url + '/' + str(id)


def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize %s" , uri)
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

