import os
import logging
import urlparse
import string

from tg import config

from bq.exceptions import ConfigurationError, ServiceError
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_uniq_hash
import shutil

log = logging.getLogger('bq.blobs.storage')


supported_storage_schemes = [ '', 'file' ] 

try:
    from bq.util import irods_handler
    supported_storage_schemes.append('irods')
except ImportError:
    log.warn ("Can't import irods: irods storage not supported")

try:
    import boto
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


class BlobStorage(object):
    "base class for blob storage adapters"
    scheme = "scheme"
    format_path = "unassigned format_path"
    def __str__(self):
        return "<%s>" %(self.format_path)

    def valid(self, ident):
        'determine whether this store can access the identified file'
    def localpath(self, ident):
        'return the local path of  the identified file'

    def write(self, fp, name, user_name=''):
        'write the file to a local blob returning a short ident and the localpath'



class LocalStorage(BlobStorage):
    'blobs locally on file system'
    scheme = 'file'

    def __init__(self, format_path):
        self.top = config.get('bisque.blob_service.file.dir',  data_path('imagedir'))
        self.format_path = string.Template(format_path).safe_substitute ( datadir = data_path() )
        if self.format_path.startswith('file:') and not self.top.startswith('file:'):
            self.top = 'file:' + self.top
        if not self.format_path.startswith(self.top):
            raise ConfigurationError('local storage %s does not begin with blob_service.local.dir %s' 
                                     % (self.format_path, self.top))


    def valid(self, ident):
        return os.path.exists(self.localpath(ident))

    def write(self, fp,  name, user_name = ''):
        'store blobs given local path'
        if not fp and name:
            src = open(name,'rb')
        else:
            src=fp
            src.seek(0)

        filepath = self.nextEmptyBlob(user_name, name)
        localpath =urlparse.urlparse(filepath).path 
        log.debug('local.write: %s -> %s' % (name,localpath))
        with  open(localpath, 'wb') as trg:
            shutil.copyfileobj(src, trg)
        ident  = filepath[len(self.top)+1:]
        return ident, localpath

    def localpath(self, ident):
        return  urlparse.urlparse(os.path.join(self.top, ident)).path

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

class iRodsStorage(BlobStorage):
    """blobs on irods
    """
    scheme = 'irods'
    
    def __init__(self, format_path):
        self.format_path = format_path
        self.user = config.get('bisque.blob_service.irods.user')
        self.password = config.get('bisque.blob_service.irods.password')
        if self.password:
            self.password = self.password.strip('"\'')
        log.debug('irods.user: %s irods.password: %s' % (self.user, self.password))
            
    def valid(self, irods_ident):
        return irods_ident and irods_ident.startswith('irods://')

    def write(self, fp, filename, user_name=None):
        blob_ident = randomPath(self.format_path, user_name, filename)
        log.debug('irods.write: %s -> %s' % (filename,blob_ident))
        flocal = irods_handler.irods_push_file(fp, blob_ident, user=self.user, password = self.password)
        return blob_ident, flocal

    def localpath(self, irods_ident):
        path = irods_handler.irods_fetch_file(irods_ident, user=self.user, password = self.password)
        return  path


class S3Storage(BlobStorage):
    'blobs on s3' 

    scheme = 's3'

    def __init__(self, format_path):
        self.format_path = format_path
        self.top = config.get('bisque.blob_service.s3')
        raise ConfigurationError('bisque.blob_service.s3 not implemented')

    def valid(self, irods_ident):
        return False

    def write(self, fp,  filename, user_name=None):
        'write a file to s3'

    def localpath(self, s3_ident):
        'return path to  local copy of the s3'


   
def make_driver(storage_url):
    storage_drivers = {
        'file' : LocalStorage,
        ''     : LocalStorage,
        'irods' : iRodsStorage,
        's3'    : S3Storage,
        }

    scheme = urlparse.urlparse(storage_url).scheme.lower()
    if scheme in supported_storage_schemes:
        store = storage_drivers.get(scheme)
        log.debug ("creating %s with %s " % (scheme, storage_url))
        return store(storage_url)
    log.error ('request storage scheme %s unavailable' % scheme)
    return None
 
