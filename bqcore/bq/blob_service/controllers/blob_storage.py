import os
import logging

from tg import config

from bq.exceptions import ConfigurationError, ServiceError
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_uniq_hash
import shutil

log = logging.getLogger('bq.blobs.storage')


supported_storage_types = [ 'local' ] 

try:
    from bq.util import irods_handler
    supported_storage_types.append('irods')
except ImportError:
    log.warn ("Can't import irods: irods storage not supported")

try:
    import boto
    supported_storage_types.append('S3')
except ImportError:
    log.warn ("Can't import boto:  S3  Storage not supported")



def randomPath (top, user, filename):
    rand_hash = make_uniq_hash(filename)
    return "%s/%s/%s/%s-%s" % (top, user, rand_hash[0], rand_hash, os.path.basename(filename))

class LocalStorage(object):
    'blobs locally on file system'

    def __init__(self):
        top = config.get('bisque.blob_service.local.dir', data_path('imagedir'))
        self.top = top

    def valid(self, ident):
        return os.path.exists(self.localpath(ident))

    def write(self, fp,  name, user_name = ''):
        'store blobs given local path'
        filepath = self.nextEmptyBlob(user_name, name)
        log.debug('local.write: %s -> %s' % (name,filepath))
        if not fp and name:
            src = open(name,'rb')
        else:
            src=fp
        src.seek(0)
        with  open(filepath, 'wb') as trg:
            shutil.copyfileobj(src, trg)

        ident  = filepath[len(self.top)+1:]
        return ident, filepath

    def localpath(self, ident):
        return  os.path.join(self.top, ident)

    def nextEmptyBlob(self, user, filename):
        "Return a file object to the next empty blob"
        while 1:
            fn = randomPath(self.top, user, filename)
            _mkdir (os.path.dirname(fn))
            if os.path.exists (fn):
                log.warning('%s already exists' % fn)
            else:
                break
        return fn

    def __str__(self):
        return "<local_store: %s>" %self.top
        
        

class iRodsStorage(object):
    'blobs on irods'
    
    def __init__(self):
        self.top = config.get('bisque.blob_service.irods.url', None)
        self.password = config.get('bisque.blob_service.irods.password', None)
        log.debug('irods.password: %s' % (self.password))

    def valid(self, irods_ident):
        return irods_ident and irods_ident.startswith('irods://')

    def write(self, fp, filename, user_name=None):
        if self.top is None:
            raise ConfigurationError('config:bisque.blob_service.irods.url must be set')
            
        blob_ident = randomPath(self.top, user_name, filename)
        log.debug('irods.write: %s -> %s' % (filename,blob_ident))
        flocal = irods_handler.irods_push_file(fp, blob_ident, password = self.password)
        return blob_ident, flocal

    def localpath(self, irods_ident):
        path = irods_handler.irods_fetch_file(irods_ident, password = self.password)
        return  path
    def __str__(self):
        return "<irods_store: %s>" %self.top


class S3Storage(object):
    'blobs on s3' 

    def __init__(self):
        s3_top = config.get('bisque.blob_service.s3')
        raise ConfigurationError('bisque.blob_service.s3 not implemented')
        self.top = s3_top

    def valid(self, irods_ident):
        return False

    def write(self, fp,  filename, user_name=None):
        'write a file to s3'

    def localpath(self, s3_ident):
        'return path to  local copy of the s3'
    def __str__(self):
        return "<s3_store: %s>" %self.top


   
def make(storage):
    storage_drivers = {
        'local' : LocalStorage,
        'irods' : iRodsStorage,
        'S3'    : S3Storage,
        }
    if storage in supported_storage_types:
        store = storage_drivers.get(storage)
        return store()
    return None
 
