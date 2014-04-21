from bq.core.service import service_registry

from controllers.blobsrv import  guess_type
from controllers.blob_storage import make_short_uuid

def find_server():
    return service_registry.find_service ('blob_service')

def store_blob(resource, fileobj=None):
    "create and store a resource blob"
    server = find_server()
    return server.store_blob(resource=resource, fileobj=fileobj)

def localpath(uniq_ident):
    "return localpath of resource by ident (uniq)"
    server = find_server()
    return server.localpath(uniq_ident)

def original_name(ident):
    "create  localpath if possible of resource by ident (uniq)"
    server = find_server()
    return server.originalFileName(ident)

