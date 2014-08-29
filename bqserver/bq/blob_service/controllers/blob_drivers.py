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


DESCRIPTION
===========

"""
import os
import logging
import urlparse
import urllib
import string
import shutil
import collections
import posixpath

from tg import config
from paste.deploy.converters import asbool

from bq.exceptions import ConfigurationError, IllegalOperation, DuplicateFile

from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.compat import OrderedDict

from bq.image_service.controllers.misc import blocked_alpha_num_sort

log = logging.getLogger('bq.blobs.drivers')

__all__ = [ 'make_storage_driver' ]

supported_storage_schemes = [ '', 'file' ]

try:
    from bq.util import irods_handler
    supported_storage_schemes.append('irods')
except ImportError:
    #log.warn ("Can't import irods: irods storage not supported")
    pass

try:
    import boto
    from bq.util import s3_handler
    from boto.s3.connection import S3Connection, Location
    supported_storage_schemes.append('s3')
except ImportError:
    #log.warn ("Can't import boto:  S3  Storage not supported")
    pass


#################################################
#  misc
#################################################
# Blobs class
class Blobs(collections.namedtuple("Blobs", ["path", "sub", "files"])):
    "A tuple of main file, , suburl , and list of files associated with a blobid(storeurl)"


def split_subpath(path):
    """Splits sub path that follows # sign if present
    """
    spot = path.rfind ('#')
    if spot < 0:
        return path,''
    return path[:spot], path[spot+1:]

def join_subpath(path, sub):
    return "%s#%s" % (path, sub) if sub else path


def walk_deep(path):
    """Splits sub path that follows # sign if present
    """
    for root, _, filenames in os.walk(path):
        for f in filenames:
            yield os.path.join(root, f).replace('\\', '/')

#################################################
#  Define helper functions for NT vs Unix/Mac
#
if os.name == 'nt':
    def move_file (fp, newpath):
        with open(newpath, 'wb') as trg:
            shutil.copyfileobj(fp, trg)

    def data_url_path (*names):
        path = data_path(*names)
        if len(path)>1 and path[1]==':': #file:// url requires / for drive lettered path like c: -> file:///c:/path
            path = '/%s'%path
        return path

    def url2localpath(url):
        path = urlparse.urlparse(url).path
        if len(path)>0 and path[0] == '/':
            path = path[1:]
        try:
            return urllib.unquote(path).decode('utf-8')
        except UnicodeEncodeError:
            # dima: safeguard measure for old non-encoded unicode paths
            return urllib.unquote(path)

    def localpath2url(path):
        path = path.replace('\\', '/')
        url = urllib.quote(path.encode('utf-8'))
        if len(path)>3 and path[0] != '/' and path[1] == ':':
            # path starts with a drive letter: c:/
            url = 'file:///%s'%url
        else:
            # path is a relative path
            url = 'file://%s'%url
        return url

else:
    def move_file (fp, newpath):
        log.debug ("moving file %s", fp.name)
        if os.path.exists(fp.name):
            oldpath = os.path.abspath(fp.name)
            shutil.move (oldpath, newpath)
        else:
            with open(newpath, 'wb') as trg:
                shutil.copyfileobj(fp, trg)

    data_url_path = data_path

    def url2localpath(url):
        url = url.encode('utf-8') # safegurd against un-encoded values in the DB
        path = urlparse.urlparse(url).path
        return urllib.unquote(path)

    def localpath2url(path):
        url = urllib.quote(path.encode('utf-8'))
        #if len(url)>1 and url[0] == '/':
        url = 'file://%s'%url
        return url


##############################################
#  Load store parameters
def load_storage_drivers():
    stores = OrderedDict()
    store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ]
    log.debug ('requested stores = %s' , store_list)
    for store in store_list:
        # pull out store related params from config
        params = dict ( (x[0].replace('bisque.stores.%s.' % store, ''), x[1])
                        for x in  config.items() if x[0].startswith('bisque.stores.%s.' % store))
        if 'path' not in params:
            log.error ('cannot configure %s without the path parameter' , store)
            continue
        log.debug("params = %s" ,  str(params))
        driver = make_storage_driver(params.pop('path'), **params)
        if driver is None:
            log.error ("failed to configure %s.  Please check log for errors " , str(store))
            continue
        stores[store] = driver
    return stores



class StorageDriver(object):
    scheme   = "scheme"   # The URL scheme id
    readonly = False      # store is readonly or r/w

#     def __init__(self, mount_url=None, **kw):
#         """ initializae a storage driver
#         @param mount_url: optional full storeurl to mount
#         """

    # New interface
    def mount(self, mount_url, **kw):
        """Mount the driver"""
    def unmount (self):
        """Unmount the driver """

    def mount_status(self):
        """return the status of the mount: mounted, error, unmounted
        """

    # File interface
    def valid (self, storurl):
        "Return validity of storeurl"
    def push(self, fp, storeurl):
        "Push a local file (file pointer)  to the store"
    def pull (self, storeurl, localpath=None):
        "Pull a store file to a local location"
    def chmod(self, storeurl, permission):
        """Change permission of """
    def delete(self, ident):
        'delete an entry on the store'
    def isdir (self, storeurl):
        "Check if a url is a container/directory"
    def status(self, storeurl):
        "return status of url: dir/file, readable, etc"
    def list(self, storeurl):
        "list contents of store url"




    # dima: possible additions ???, should modify walk to take ident ???
#     def is_directory(self, ident):
#         'check if the ident points to a directory'
#     def walk(self, ident):
#         'walk a specific directory in the store'



class LocalDriver (StorageDriver):
    """Local filesystem driver"""

    def __init__(self, mount_url=None, top = None,  readonly=False, **kw):
        """Create a local storage driver:

        :param path: format_path for how to store files
        :param  top: allow old style (relatave path file paths)
        :param readonly: set repo readonly
        """
        self.mount_url = posixpath.join(mount_url,'')
        datadir = data_url_path()
        for key, value in kw.items():
            setattr(self, key, string.Template(value).safe_substitute(datadir=datadir))
        self.top = posixpath.join(top, '')
        self.readonly = asbool(readonly)
        if top:
            self.top = string.Template(self.top).safe_substitute(datadir=datadir)
            self.top_path = url2localpath(self.top)
        self.options = kw


    def valid(self, storeurl):
        # dima: there's only one local storage in the system, file:// should all be redirected to it

        #log.debug('valid ident %s top %s', ident, self.top)
        #log.debug('valid local ident %s local top %s', url2localpath(ident), url2localpath(self.top))
        if storeurl.startswith (self.mount_url):
            return storeurl
        # It might be a shorted
        storeurl,_ = split_subpath(storeurl)
        scheme = urlparse.urlparse(storeurl).scheme

        if not scheme:
            storeurl = urlparse.urljoin (self.top, storeurl)
        elif storeurl.startswith('file:///'):
            pass
        elif storeurl.startswith('file://'):
            storeurl = urlparse.urljoin(self.top, storeurl[7:])
        else:
            return None
        localpath = url2localpath (storeurl)
        log.debug ("checking %s", localpath)
        return os.path.exists(localpath) and localpath2url(localpath)

    # New interface
    def push(self, storeurl, fp):
        "Push a local file (file pointer)  to the store"

        log.debug('local.push: %s' , storeurl)
        origpath = localpath = url2localpath(storeurl)
        fpath,ext = os.path.splitext(origpath)
        _mkdir (os.path.dirname(localpath))
        for x in range(100):
            if not os.path.exists (localpath):
                log.debug('local.write: %s -> %s' , storeurl, localpath)
                #patch for no copy file uploads - check for regular file or file like object
                move_file (fp, localpath)
                ident = localpath #[len(top_path):]
                #if ident[0] == '/':
                #    ident = ident[1:]
                #ident = "file://%s" % localpath
                ident = localpath2url(ident)
                log.debug('local.blob_id: %s -> %s',  storeurl,  localpath)
                return ident, localpath
            localpath = "%s-%04d%s" % (fpath , x , ext)
            log.debug ("local.write: File exists... trying %s", localpath)
        raise DuplicateFile(localpath)

    def pull (self, storeurl, localpath=None):
        "Pull a store file to a local location"
        #log.debug('local_store localpath: %s', path)
        path,sub = split_subpath(storeurl)
        if not path.startswith('file:///'):
            if path.startswith('file://'):
                path = os.path.join(self.top, path.replace('file://', ''))
            else:
                path = os.path.join(self.top, path)

        path = url2localpath(path.replace('\\', '/'))

        #log.debug('local_store localpath path: %s', path)

        # if path is a directory, list contents
        files = None
        if os.path.isdir(path):
            files = walk_deep(path)
            files = sorted(files, key=blocked_alpha_num_sort) # use alpha-numeric block sort
        elif not os.path.exists(path):
            # No file at location .. fail
            return None
        # local storage can't extract sub paths, pass it along
        return Blobs(path=path, sub=sub, files=files)


    def list(self, storeurl):
        "list contents of store url"
        raise NotImplementedError("list")

    def delete(self, ident):
        #ident,_ = split_subpath(ident) # reference counting required?
        fullpath = os.path.join(self.top[5:], ident) # remove file
        log.debug("deleting %s", fullpath)
        os.remove (fullpath)

    def __str__(self):
        return "localstore[%s, %s]" % (self.mount_url, self.top)

###############################################
# Irods

class IrodsDriver(StorageDriver):
    """New Irods driver :

    MAYBE TO BE REDONE to reuse connection.
    """

    def __init__(self, mount_url, readonly=False, credentials=None, **kw):
        """Create a iRods storage driver:

        :param path: irods:// url format_path for where to store files
        :param  user: the irods users
        :param  password: the irods password
        :param readonly: set repo readonly
        """
        self.mount_url = mount_url
        datadir = data_url_path()
        for key, value in kw.items():
            setattr(self, key, string.Template(value).safe_substitute(datadir=datadir))
        if credentials:
            try:
                self.user, self.password = [ x.strip('"\'') for x in credentials.split(':') ]
            except ValueError:
                log.exception ('bad credentials for irods %s', credentials)

        #self.user = kw.pop('credentials.user',None) or kw.pop('user',None)
        #self.password = kw.pop('credentials.password', None) or kw.pop('password', None)
        self.readonly = asbool(readonly)
        self.options = kw
        log.debug('irods.user: %s irods.password: %s' , self.user, self.password)
        # Get the constant portion of the path
        log.info("created irods store %s " , self.mount_url)

    def valid(self, storeurl):
        return storeurl.startswith(self.mount_url) and storeurl

    # New interface
    def push(self, fp, storeurl):
        "Push a local file (file pointer)  to the store"
        log.debug('irods.push: %s' , storeurl)
        flocal = irods_handler.irods_push_file(fp, storeurl, user=self.user, password=self.password)
        return storeurl, flocal

    def pull (self, storeurl, localpath=None):
        "Pull a store file to a local location"
        # dima: path can be a directory, needs listing and fetching all enclosed files
        try:
            # if irods will provide extraction of sub files from compressed (zip, tar, ...) ask for it and return sub as None
            irods_ident,sub = split_subpath(storeurl)
            path = irods_handler.irods_fetch_file(storeurl, user=self.user, password=self.password)
            # dima: if path is a directory, list contents
            return Blobs(path=path, sub=sub, files=None)
        except irods_handler.IrodsError:
            log.exception ("Error fetching %s ", irods_ident)
        return None

    def list(self, storeurl):
        "list contents of store url"

    def delete(self, irods_ident):
        try:
            irods_handler.irods_delete_file(irods_ident, user=self.user, password=self.password)
        except irods_handler.IrodsError, e:
            log.exception ("Error deleteing %s ", irods_ident)
        return None

###############################################
# S3
class S3Driver(StorageDriver):
    'blobs on s3'

    scheme = 's3'

    def __init__(self, mount_url=None, credentials = None,
                 bucket_id=None, location=Location.USWest,
                 readonly = False, **kw):
        """Create a iRods storage driver:

        :param path: s3:// url format_path for where to store files
        :param  credentials : access_key, secret_key
        :param  bucket_id: A unique bucket ID to store file
        :param location: The S3 location identifier (default is USWest)
        :param readonly: set repo readonly
        """

        self.mount_url = mount_url
        if credentials:
            self.access_key,  self.secret_key = credentials.split(':')
        else:
            log.error ('need credentials for S3 store')

        self.location = location
        self.bucket_id = bucket_id #config.get('bisque.blob_service.s3.bucket_id')
        self.bucket = None
        self.conn = None
        self.readonly = asbool(readonly)
        self.top = mount_url.split('$')[0]
        self.options = kw
        self.mount (mount_url, **kw)


    def mount(self, mount_url, **kw):
        self.mount_url = mount_url

        if self.access_key is None or self.secret_key is None or self.bucket_id is None:
            raise ConfigurationError('bisque.blob_service.s3 incomplete config')

        self.conn = S3Connection(self.access_key, self.secret_key)

        try:
            self.bucket = self.conn.get_bucket(self.bucket_id)
        except boto.exception:
            try:
                self.bucket = self.conn.create_bucket(self.bucket_id, location=self.location)
            except boto.exception.S3CreateError:
                raise ConfigurationError('bisque.blob_service.s3.bucket_id already owned by someone else. Please use a different bucket_id')

        log.info("mounted S3 store %s (%s)" , self.mount_url, self.top)

    def unmount (self):
        self.conn.close()

    def valid(self, storeurl):
        return storeurl.startswith(self.mount_url) and storeurl

    def push(self, fp, storeurl):
        'write a file to s3'
        s3_ident,sub = split_subpath(storeurl)
        log.debug('s3.write: %s -> %s' , storeurl, s3_ident)
        s3_key = s3_ident.replace("s3://","")
        flocal = s3_handler.s3_push_file(fp, self.bucket , s3_key)
        return s3_ident, flocal

    def pull(self, storeurl, locapath=None):
        'return path to local copy of the s3 resource'
        # dima: path can be a directory, needs listing and fetching all enclosed files

        # if s3 will provide extraction of sub files from compressed (zip, tar, ...) ask for it and return sub as None
        storeurl,sub = split_subpath(storeurl)
        s3_key = storeurl.replace("s3://","")
        path = s3_handler.s3_fetch_file(self.bucket, s3_key)
        # dima: if path is a directory, list contents
        return Blobs(path=path, sub=sub, files=None)

    def delete(self, storeurl):
        s3_key = storeurl.replace("s3://","")
        s3_handler.s3_delete_file(self.bucket, s3_key)



###############################################
# HTTP(S)
class HttpDriver(StorageDriver):
    """HTTP storage driver  """
    scheme = 'http'

    def __init__(self, mount_url=None, credentials=None, readonly=True, **kw):
        """Create a HTTP storage driver:

        :param path: http:// url format_path for where to read/store files
        :param  user: the irods users
        :param  password: the irods password
        :param readonly: set repo readonly
        """
        self.mount_url = mount_url
        # DECODE Credential string
        if credentials:
            self.auth_scheme = credentials.split(':', 1)
            if self.auth_scheme.lower() == 'basic':
                _, self.user, self.password = [ x.strip('"\'') for x in credentials.split(':')]
        # basic auth
        log.debug('http.user: %s http.password: %s' , self.user, self.password)
        self.readonly = asbool(readonly)
        self.options = kw
        self.top = mount_url.split('$')[0]
        if mount_url:
            self.mount(mount_url, **kw)

    def mount(self, mount_url,  **kw):
        self.mount_url = mount_url
        # Get the constant portion of the path
        log.info("created http store %s " , self.mount_url)

    def valid(self, http_ident):
        return  http_ident.startswith(self.mount_url) and http_ident

    def push(self, fp, filename):
        raise IllegalOperation('HTTP(S) write is not implemented')

    def pull(self, http_ident,  localpath=None):
        # dima: path can be a directory, needs listing and fetching all enclosed files
        raise IllegalOperation('HTTP(S) localpath is not implemented')

class HttpsDriver (HttpDriver):
    "HTTPS storage"
    scheme = 'https'



###############################################
# Construct a driver

def make_storage_driver(mount_url, **kw):
    """construct a driver using the URL path

    :param path: URL of storage path
    :param kw:   arguments to passed to storage constructor
    """

    storage_drivers = {
        #'file' : LocalStorage,
        #''     : LocalStorage,
        'file' : LocalDriver,
        ''     : LocalDriver,
        'irods' : IrodsDriver,
        's3'    : S3Driver,
        'http'  : HttpDriver,
        'https' : HttpsDriver,
        }

    scheme = urlparse.urlparse(mount_url).scheme.lower()
    if scheme in supported_storage_schemes:
        store = storage_drivers.get(scheme)
        log.debug ("creating %s with %s " , scheme, mount_url)
        return store(mount_url=mount_url, **kw)
    log.error ('request storage scheme %s unavailable' , scheme)
    return None

