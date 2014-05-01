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
import string
import shutil
import datetime

from tg import config
from paste.deploy.converters import asbool

from bq.exceptions import ConfigurationError, ServiceError, IllegalOperation, DuplicateFile

from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_short_uuid
from bq.util.http import get_file
from bq.util.compat import OrderedDict


log = logging.getLogger('bq.blobs.storage')

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



def formatPath(format_path, user, filename, uniq, **params):
    """Create a unique path using a format and hash of filename
    i.e. {user}/{dirhash}/{filehash}-{filename}
    """
    #if uniq is None:
    #    uniq = make_short_uuid(filename)

    #filename = params.get('relpath', None) or os.path.basename(filename)
    log.debug('formatPath: %s', filename)

    filebase,fileext = os.path.splitext(filename)
    dirhash = uniq[2]=='-' and uniq[3] or uniq[0]
    return string.Template(format_path).substitute(
        user=user or '',
        date=datetime.datetime.now().strftime('%Y-%m-%d'),
        dirhash=dirhash,
        filehash=uniq,
        filename=filename,
        filebase=filebase,
        fileext=fileext, **params)

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
        if path[2] == ':' and path[0] == '/':
            path = path[1:]
        return path
else:
    def move_file (fp, newpath):
        oldpath = os.path.abspath(fp.name)
        shutil.move (oldpath, newpath)

    data_url_path = data_path

    def url2localpath(url):
        return urlparse.urlparse(url).path



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
        log.debug("params = %s" % params)
        driver = make_storage_driver(params.pop('path'), **params)
        if driver is None:
            log.error ("failed to configure %s.  Please check log for errors " , str(store))
            continue
        stores[store] = driver
    return stores


###############################################
#  BlobStorage
class BlobStorage(object):
    "base class for blob storage adapters"
    scheme   = "scheme"   # The URL scheme id
    path     = "unassigned format_path"  # Storage path using scheme
    readonly = False      # store is readonly or r/w
    top      = ""         # top path useful to identify URLs as part of a store
    format_path = "<undefined>"

    def __str__(self):
        return "<%s>" % (self.format_path)
    def valid(self, ident):
        'determine whether this store can access the identified file'
    def localpath(self, ident):
        'return the local path of  the identified file'
    def write(self, fp, name, user_name=None, uniq=None):
        'write the file to a local blob returning a short ident and the localpath'
    def walk(self):
        'walk entries on this store .. see os.walk'
    def delete(self, ident):
        'delete an entry on the store'


###############################################
# Local
class LocalStorage(BlobStorage):
    "blobs locally on file system"
    scheme = 'file'

    def __init__(self, path, top = data_url_path('imagedir'), readonly=False, **kw):
        """Create a local storage driver:

        :param path: format_path for how to store files
        :param  top: allow old style (relatave path file paths)
        :param readonly: set repo readonly
        """
        datadir = data_url_path()
        for key, value in kw.items():
            setattr(self, key, string.Template(value).safe_substitute(datadir=datadir))
        self.top = top
        self.top = string.Template(self.top).safe_substitute(datadir=datadir)
        self.top_path = url2localpath(self.top)
        self.options = kw

        self.readonly = asbool(readonly)
        self.format_path = string.Template(path).safe_substitute (datadir=datadir)
        if self.format_path.startswith('file://') and not self.top.startswith('file://'):
            self.top = 'file://' + self.top
        if not self.format_path.startswith(self.top):
            raise ConfigurationError('Check site.cfg:local storage %s does not begin with  %s'
                                     % (self.format_path, self.top))
        log.info("created localstore %s (%s) options %s" , self.format_path, self.top, self.options)

    def valid(self, ident):
        return ((ident.startswith(self.top)  and ident)
                or  (urlparse.urlparse(ident).scheme == '' and os.path.join(self.top, ident).replace('\\', '/')))
                #and os.path.exists(self.localpath(ident)))

    def write(self, fp, filename, user_name=None, uniq=None):
        'store blobs given local path'
        if '$' in self.top_path:
            top_path  = url2localpath(formatPath(self.top_path, user_name, filename, uniq))
        else:
            top_path  = self.top_path
        filepath = formatPath(self.format_path, user_name, filename, uniq)
        origpath = localpath = url2localpath(filepath)
        fpath,ext = os.path.splitext(origpath)
        _mkdir (os.path.dirname(localpath))
        for x in xrange(len(uniq)-7):
            if not os.path.exists (localpath):
                log.debug('local.write: %s -> %s' , filename, localpath)
                #patch for no copy file uploads - check for regular file or file like object
                move_file (fp, localpath)
                ident = localpath[len(top_path):]
                if ident[0] == '/':
                    ident = ident[1:]
                #ident = "file://%s" % localpath

                log.debug('local.blob_id: %s -> %s',  ident, localpath)
                return ident, localpath
            localpath = "%s-%s%s" % (fpath , uniq[3:7+x] , ext)
            log.debug ("local.write: File exists .. trying %s", localpath)

        raise DuplicateFile(localpath)

    def localpath(self, path):
        path = path.replace('\\', '/')
        if not path.startswith('file://'):
            path = os.path.join(self.top, path)
            path = path.replace('\\', '/')
        return url2localpath(path)

    def walk(self):
        'walk store returning all elements'
        for tp in os.walk (self.top[5:]):   # remove file:
            yield tp

    def delete(self, ident):
        fullpath = os.path.join(self.top[5:], ident) # remove file
        log.debug("deleting %s" ,  fullpath)
        os.remove (fullpath)

    def __str__(self):
        return "localstore[%s, %s]" % (self.top, self.format_path)

###############################################
# Irods
class iRodsStorage(BlobStorage):
    """iRods storage driver """
    scheme = 'irods'

    def __init__(self, path, readonly=False, **kw):
        """Create a iRods storage driver:

        :param path: irods:// url format_path for where to store files
        :param  user: the irods users
        :param  password: the irods password
        :param readonly: set repo readonly
        """
        datadir = data_url_path()
        for key, value in kw.items():
            setattr(self, key, string.Template(value).safe_substitute(datadir=datadir))
        self.format_path = path
        self.user = kw.pop('credentials.user',None) or kw.pop('user',None)
        self.password = kw.pop('credentials.password', None) or kw.pop('password', None)
        self.readonly = asbool(readonly)
        self.options = kw

        if self.password:
            self.password = self.password.strip('"\'')
        log.debug('irods.user: %s irods.password: %s' , self.user, self.password)
        # Get the constant portion of the path
        self.top = path.split('$')[0]
        log.info("created irods store %s (%s)" , self.format_path, self.top)

    def valid(self, irods_ident):
        return  irods_ident.startswith(self.top) and irods_ident

    def write(self, fp, filename, user_name=None, uniq=None):
        blob_ident = formatPath(self.format_path, user_name, filename, uniq)
        log.debug('irods.write: %s -> %s' , filename, blob_ident)
        flocal = irods_handler.irods_push_file(fp, blob_ident, user=self.user, password=self.password)
        return blob_ident, flocal

    def localpath(self, irods_ident):
        try:
            path = irods_handler.irods_fetch_file(irods_ident, user=self.user, password=self.password)
            return  path
        except irods_handler.IrodsError, e:
            log.exception ("Error fetching %s ", irods_ident)
        return None

    def delete(self, irods_ident):
        try:
            irods_handler.irods_delete_file(irods_ident, user=self.user, password=self.password)
        except irods_handler.IrodsError, e:
            log.exception ("Error deleteing %s ", irods_ident)
        return None


###############################################
# S3
class S3Storage(BlobStorage):
    'blobs on s3'

    scheme = 's3'

    def __init__(self, path,
                 access_key=None, secret_key=None, bucket_id=None, location=Location.USWest,
                 readonly = False, **kw):
        """Create a iRods storage driver:

        :param path: s3:// url format_path for where to store files
        :param  access_key: the s3 access_key
        :param  secret_key: the s3 secret_key
        :param  bucket_id: A unique bucket ID to store file
        :param location: The S3 location identifier (default is USWest)
        :param readonly: set repo readonly
        """

        self.format_path = path
        self.access_key = access_key #config.get('bisque.blob_service.s3.access_key')
        self.secret_key = secret_key #config.get('bisque.blob_service.s3.secret_key')
        self.bucket_id = bucket_id #config.get('bisque.blob_service.s3.bucket_id')
        self.bucket = None
        self.readonly = asbool(readonly)
        self.top = path.split('$')[0]
        self.options = kw

        if self.access_key is None or self.secret_key is None or self.bucket_id is None:
            raise ConfigurationError('bisque.blob_service.s3 incomplete config')

        self.conn = S3Connection(self.access_key, self.secret_key)

        try:
            self.bucket = self.conn.get_bucket(self.bucket_id)
        except:
            try:
                self.bucket = self.conn.create_bucket(self.bucket_id, location=location)
            except boto.exception.S3CreateError:
                raise ConfigurationError('bisque.blob_service.s3.bucket_id already owned by someone else. Please use a different bucket_id')
            except:
                raise ServiceError('error while creating bucket in s3 blob storage')

        log.info("created S3 store %s (%s)" , self.format_path, self.top)

    def valid(self, s3_ident):
        return s3_ident.startswith(self.top) and s3_ident

    def write(self, fp, filename, user_name=None, uniq=None):
        'write a file to s3'
        blob_ident = formatPath(self.format_path, user_name, filename, uniq)
        log.debug('s3.write: %s -> %s' , filename, blob_ident)
        s3_key = blob_ident.replace("s3://","")
        flocal = s3_handler.s3_push_file(fp, self.bucket , s3_key)
        return blob_ident, flocal

    def localpath(self, s3_ident):
        'return path to local copy of the s3 resource'
        s3_key = s3_ident.replace("s3://","")
        path = s3_handler.s3_fetch_file(self.bucket, s3_key)
        return  path

    def delete(self, s3_ident):
        s3_key = s3_ident.replace("s3://","")
        s3_handler.s3_delete_file(self.bucket, s3_key)



###############################################
# HTTP(S)
class HttpStorage(BlobStorage):
    """HTTP storage driver  """
    scheme = 'http'

    def __init__(self, path, user=None, password=None, readonly=True, **kw):
        """Create a HTTP storage driver:

        :param path: http:// url format_path for where to read/store files
        :param  user: the irods users
        :param  password: the irods password
        :param readonly: set repo readonly
        """
        self.format_path = path
        self.user = user # config.get('bisque.blob_service.irods.user')
        self.password = password # config.get('bisque.blob_service.irods.password')
        self.readonly = asbool(readonly)
        self.options = kw

        if self.password:
            self.password = self.password.strip('"\'')
        log.debug('http.user: %s http.password: %s' , self.user, self.password)
        # Get the constant portion of the path
        self.top = path.split('$')[0]
        log.info("created irods store %s (%s)" , self.format_path, self.top)

    def valid(self, http_ident):
        return  http_ident.startswith(self.top) and http_ident

    def write(self, fp, filename, user_name=None, uniq=None):
        raise IllegalOperation('HTTP(S) write is not implemented')

    def localpath(self, http_ident):
        raise IllegalOperation('HTTP(S) localpath is not implemented')

class HttpsStorage (HttpStorage):
    "HTTPS storage"
    scheme = 'https'



###############################################
# Construct a driver

def make_storage_driver(path, **kw):
    """construct a driver using the URL path

    :param path: URL of storage path
    :param kw:   arguments to passed to storage constructor
    """

    storage_drivers = {
        'file' : LocalStorage,
        ''     : LocalStorage,
        'irods' : iRodsStorage,
        's3'    : S3Storage,
        'http'  : HttpStorage,
        'https' : HttpsStorage,
        }

    scheme = urlparse.urlparse(path).scheme.lower()
    if scheme in supported_storage_schemes:
        store = storage_drivers.get(scheme)
        log.debug ("creating %s with %s " , scheme, path)
        return store(path=path, **kw)
    log.error ('request storage scheme %s unavailable' , scheme)
    return None

