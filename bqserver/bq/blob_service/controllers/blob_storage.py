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
import cgi

from tg import config
from paste.deploy.converters import asbool

from bq.exceptions import ConfigurationError, ServiceError
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_uniq_hash


log = logging.getLogger('bq.blobs.storage')

__all__ = [ 'make_storage_driver' ]

supported_storage_schemes = [ '', 'file' ] 

try:
    from bq.util import irods_handler
    supported_storage_schemes.append('irods')
except ImportError:
    log.warn ("Can't import irods: irods storage not supported")

try:
    import boto
    from bq.util import s3_handler
    from boto.s3.connection import S3Connection, Location
    supported_storage_schemes.append('s3')
except ImportError:
    log.warn ("Can't import boto:  S3  Storage not supported")



def randomPath (format_path, user, filename, **params):
    """Create a unique path using a format and hash of filename
    i.e. {user}/{dirhash}/{filehash}-{filename}
    """
    rand_hash = make_uniq_hash(filename)
    #return "%s/%s/%s/%s-%s" % (top, user, rand_hash[0], rand_hash, os.path.basename(filename))
    return string.Template(format_path).substitute(
        user=user,
        dirhash=rand_hash[0],
        filehash=rand_hash,
        filename=os.path.basename(filename), **params)

#patch to allow no copy file uploads (direct to destination directory)
import tempfile
tmp_upload_dir = config.get('bisque.blob_service.tmp_upload_dir', string.Template("$datadir/tmp_upload_dir").safe_substitute(datadir=data_path()))
_mkdir(tmp_upload_dir)
def import_transfer_handler(filename):
    return tempfile.NamedTemporaryFile('w+b', suffix = filename, dir=tmp_upload_dir, delete = False)

#register callables here
#cgi.file_upload_handler['/import/transfer'] = import_transfer_handler

###############################################
#  BlobStorage
class BlobStorage(object):
    "base class for blob storage adapters"
    scheme   = "scheme"   # The URL scheme id
    path     = "unassigned format_path"  # Storage path using scheme
    readonly = False      # store is readonly or r/w
    top      = ""         # top path useful to identify URLs as part of a store

    def __str__(self):
        return "<%s>" % (self.format_path)

    def valid(self, ident):
        'determine whether this store can access the identified file'
    def localpath(self, ident):
        'return the local path of  the identified file'
    def write(self, fp, name, user_name=''):
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

    def __init__(self, path, top = data_path('imagedir'), readonly=False):
        """Create a local storage driver:

        :param path: format_path for how to store files
        :param  top: allow old style (relatave path file paths)
        :param readonly: set repo readonly
        """
        self.top = top
        self.top = string.Template(self.top).safe_substitute(datadir=data_path())
        self.readonly = asbool(readonly)
        self.format_path = string.Template(path).safe_substitute (datadir=data_path())
        if self.format_path.startswith('file:') and not self.top.startswith('file:'):
            self.top = 'file:' + self.top
        if not self.format_path.startswith(self.top):
            raise ConfigurationError('local storage %s does not begin with blob_service.local.dir %s' 
                                     % (self.format_path, self.top))

        log.info("created localstore %s (%s)" % (self.format_path, self.top))


    def valid(self, ident):
        return os.path.exists(self.localpath(ident))

    def write(self, fp, name, user_name=''):
        'store blobs given local path'
        opened = False
        if not fp and name:
            src = open(name, 'rb')
            opened = True
        else:
            src = fp
            src.seek(0)

        filepath = self.nextEmptyBlob(user_name, name)
        localpath = urlparse.urlparse(filepath).path 
        log.debug('local.write: %s -> %s' % (name, localpath))
        
        #patch for no copy file uploads - check for regular file or file like object
        abs_path_src = os.path.abspath(src.name)
        if os.path.isfile(abs_path_src):
            shutil.move(abs_path_src,localpath)
        else:
            with open(localpath, 'wb') as trg:
                shutil.copyfileobj(src, trg)
        ident = filepath[len(self.top) + 1:]
        if opened:
            src.close()
        return ident, localpath

    def localpath(self, path):
        return  urlparse.urlparse(os.path.join(self.top, path)).path

    def nextEmptyBlob(self, user, filename):
        "Return a file object to the next empty blob"
        while 1:
            fn = randomPath(self.format_path, user, filename)
            fp = urlparse.urlparse(fn).path
            _mkdir (os.path.dirname(fp))
            if os.path.exists (fp):
                log.warning('%s already exists' % fn)
            else:
                break
        return fn

    def walk(self):
        'walk store returning all elements'
        for tp in os.walk (self.top[5:]):   # remove file: 
            yield tp
    def delete(self, ident):
        fullpath = os.path.join(self.top[5:], ident) # remove file
        log.debug("deleting %s" %  fullpath)
        os.remove (fullpath) 
            

###############################################
# Irods
class iRodsStorage(BlobStorage):
    """iRods storage driver """
    scheme = 'irods'

    def __init__(self, path, user=None, password=None, readonly=False):
        """Create a iRods storage driver:

        :param path: irods:// url format_path for where to store files
        :param  user: the irods users 
        :param  password: the irods password 
        :param readonly: set repo readonly
        """
        self.format_path = path
        self.user = user # config.get('bisque.blob_service.irods.user')
        self.password = password # config.get('bisque.blob_service.irods.password')
        self.readonly = asbool(readonly)

        if self.password:
            self.password = self.password.strip('"\'')
        log.debug('irods.user: %s irods.password: %s' % (self.user, self.password))
        # Get the constant portion of the path
        self.top = path.split('$')[0]
        log.info("created irods store %s (%s)" % (self.format_path, self.top))
            
    def valid(self, irods_ident):
        return irods_ident and irods_ident.startswith(self.top)

    def write(self, fp, filename, user_name=None):
        blob_ident = randomPath(self.format_path, user_name, filename)
        log.debug('irods.write: %s -> %s' % (filename, blob_ident))
        flocal = irods_handler.irods_push_file(fp, blob_ident, user=self.user, password=self.password)
        return blob_ident, flocal

    def localpath(self, irods_ident):
        path = irods_handler.irods_fetch_file(irods_ident, user=self.user, password=self.password)
        return  path

###############################################
# S3
class S3Storage(BlobStorage):
    'blobs on s3' 

    scheme = 's3'

    def __init__(self, path, 
                 access_key=None, secret_key=None, bucket_id=None, location=Location.USWest, 
                 readonly = False):
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
        
        log.info("created S3 store %s (%s)" % (self.format_path, self.top))

        
    def valid(self, s3_ident):
        return s3_ident and s3_ident.startswith(self.top)

    def write(self, fp, filename, user_name=None):
        'write a file to s3'
        blob_ident = randomPath(self.format_path, user_name, filename)
        log.debug('s3.write: %s -> %s' % (filename, blob_ident))
        s3_key = blob_ident.replace("s3://","")
        flocal = s3_handler.s3_push_file(fp, self.bucket , s3_key)
        return blob_ident, flocal

    def localpath(self, s3_ident):
        'return path to local copy of the s3 resource'
        s3_key = s3_ident.replace("s3://","")
        path = s3_handler.s3_fetch_file(self.bucket, s3_key)
        return  path
        

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
        }

    scheme = urlparse.urlparse(path).scheme.lower()
    if scheme in supported_storage_schemes:
        store = storage_drivers.get(scheme)
        log.debug ("creating %s with %s " % (scheme, path))
        return store(path=path, **kw)
    log.error ('request storage scheme %s unavailable' % scheme)
    return None
 
