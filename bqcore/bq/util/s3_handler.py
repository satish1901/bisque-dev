import os
import logging
import shutil
from boto.s3.key import Key

from bq.util.mkdir import _mkdir
from bq.util.paths import data_path
S3_CACHE = data_path('s3_cache')

class S3Error(Exception):
    pass

log = logging.getLogger('bq.blobs.storage.s3')

if not os.path.exists(S3_CACHE):
    _mkdir (S3_CACHE)

def s3_cache_fetch(bucket, key):
    cache_filename = os.path.join(S3_CACHE, key)
    if not os.path.exists(cache_filename):
        k = Key(bucket)
        k.key = key
        k.get_contents_to_filename(cache_filename)
    return cache_filename

def s3_cache_save(f, bucket, key):
    cache_filename = os.path.join(S3_CACHE, key)
    _mkdir(os.path.dirname(cache_filename))

    #patch for no copy file uploads - check for regular file or file like object
    abs_path_src = os.path.abspath(f.name)
    if os.path.isfile(abs_path_src):
        f.close() #patch to make file move possible on windows
        shutil.move(abs_path_src, cache_filename)
    else:
        with open(cache_filename, 'wb') as fw:
            shutil.copyfileobj(f, fw)

    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(cache_filename)
    return cache_filename

def s3_cache_delete(bucket, key):
    cache_filename = os.path.join(S3_CACHE, key)
    if os.path.exists(cache_filename):
        os.remove (cache_filename)
    k = Key(bucket)
    k.key = key
    k.delete()

def s3_fetch_file(bucket, key):
    localname = s3_cache_fetch(bucket, key)
    return localname

def s3_isfile(bucket, key):
    key = bucket.get_key (key)
    return key is not None

def s3_push_file(fileobj, bucket , key):
    localname = s3_cache_save(fileobj, bucket, key)
    return localname

def s3_delete_file(bucket, key):
    s3_cache_delete(bucket, key)

