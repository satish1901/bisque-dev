import os
import logging
import shutil
import math
from boto.s3.key import Key
from filechunkio import FileChunkIO

from bq.util.mkdir import _mkdir
from bq.util.paths import data_path
from bq.util.copylink import copy_link
S3_CACHE = data_path('s3_cache')

class S3Error(Exception):
    pass

log = logging.getLogger('bq.blobs.storage.s3')

def s3_parse_url(url):
    "Read an s3 url, return a bucket and key"



def s3_cache_fetch(bucket, key):
    if not os.path.exists(S3_CACHE):
        _mkdir (S3_CACHE)

    cache_filename = os.path.join(S3_CACHE, key)
    if not os.path.exists(cache_filename):
        k = Key(bucket)
        k.key = key
        _mkdir(os.path.dirname(cache_filename))
        k.get_contents_to_filename(cache_filename)
    return cache_filename

def s3_cache_save(f, bucket, key):
    if not os.path.exists(S3_CACHE):
        _mkdir (S3_CACHE)
    cache_filename = os.path.join(S3_CACHE, key)
    _mkdir(os.path.dirname(cache_filename))

    #patch for no copy file uploads - check for regular file or file like object
    abs_path_src = os.path.abspath(f.name)
    if os.path.isfile(abs_path_src):
        #f.close() #patch to make file move possible on windows
        #shutil.move(abs_path_src, cache_filename)
        copy_link (abs_path_src, cache_filename)
    else:
        with open(cache_filename, 'wb') as fw:
            shutil.copyfileobj(f, fw)

    file_size = os.path.getsize(cache_filename)
    if file_size < 60 * 1e6:
        log.debug ("PUSH normal")
        k = Key(bucket)
        k.key = key
        k.set_contents_from_filename(cache_filename)
    else:
        log.debug ("PUSH multi")
        chunk_size = 52428800 #50MB
        chunk_count = int(math.ceil(file_size / float(chunk_size)))
        mp = bucket.initiate_multipart_upload(key)
        for i in range(chunk_count):
            offset = chunk_size * i
            bytes = min(chunk_size, file_size - offset)
            with FileChunkIO(cache_filename, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)
        mp.complete_upload()

    return cache_filename

def s3_cache_delete(bucket, key):
    if not os.path.exists(S3_CACHE):
        _mkdir (S3_CACHE)
    cache_filename = os.path.join(S3_CACHE, key)
    if os.path.exists(cache_filename):
        os.remove (cache_filename)
    k = Key(bucket)
    k.key = key
    k.delete()

def s3_fetch_file(bucket, key):
    if not os.path.exists(S3_CACHE):
        _mkdir (S3_CACHE)
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

def s3_list(bucket, key):
    return bucket.list(prefix=key, delimiter='/')
