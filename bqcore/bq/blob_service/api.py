from bq.core.service import service_registry

from controllers.blobsrv import  guess_type
from controllers.blob_storage import make_uniq_hash

def find_server():
    return service_registry.find_service ('blobs')

def store_blob(flosrc=None, filename=None, url=None, permission='private', **kw):
    server = find_server()
    return server.storeBlob(flosrc=flosrc, filename=filename,url=url, permission=permission, **kw)

def localpath(ident):
    server = find_server()
    return server.localpath(ident)

def file_exists(ident):
    server = find_server()
    return server.fileExists(ident)

def original_name(ident):
    server = find_server()
    return server.originalFileName(ident)

def files_exist(hashes):
    server = find_server()
    return server.blobsExist(hashes)



#def fetch(url):
#    server = find_server(url)
#    return server.get_one(url)

#def stream(url):
#    server = find_server(url)

#    blob_path = url.rsplit('/',1)[1]
#    return server.stream(blob_path)
