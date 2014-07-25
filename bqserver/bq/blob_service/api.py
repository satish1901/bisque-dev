from bq.core.service import service_registry

from controllers.blobsrv import guess_type
from controllers.blob_storage import make_short_uuid, localpath2url, url2localpath

def find_server():
    return service_registry.find_service ('blob_service')

def store_blob(resource, fileobj=None):
    "create and store a resource blob"
    server = find_server()
    return server.store_blob(resource=resource, fileobj=fileobj)

def store_multi_blob(resource, unpack_dir):
    "create and store a resource multi-blob"
    server = find_server()
    return server.store_multi_blob(resource=resource, unpack_dir=unpack_dir)

def create_resource(resource):
    "create a resource blob"
    server = find_server()
    return server.create_resource(resource=resource)

def localpath(uniq_ident):
    "return localpath of resource by ident (uniq)"
    server = find_server()
    return server.localpath(uniq_ident)

def original_name(ident):
    "create  localpath if possible of resource by ident (uniq)"
    server = find_server()
    return server.originalFileName(ident)

def url2local(path):
    "decode url into a local path"
    return url2localpath(path)

def local2url(path):
    "decode local path as a url"
    return localpath2url(path)