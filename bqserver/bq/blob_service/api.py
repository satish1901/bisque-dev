from bq.core.service import service_registry

from controllers.blobsrv import  guess_type
from controllers.blob_storage import make_uniq_hash

def find_server():
    return service_registry.find_service ('blob_service')

def store_blob(filesrc=None, filename=None, url=None, permission='private', **kw):
    "create and store a resource blob"

    server = find_server()
    return server.storeBlob(flosrc=filesrc, filename=filename,url=url, permission=permission, **kw)

def fetch_blob(ident):
    "return resource identified by ident (uniq)"
    server = find_server()
    return server.getBlobInfo(ident)
    
def localpath(ident):
    "return localpath of resource by ident (uniq)"
    server = find_server()
    return server.localpath(ident)

def original_name(ident):
    "create  localpath if possible of resource by ident (uniq)"
    server = find_server()
    return server.originalFileName(ident)

def file_exists(ident):
    "determine if resource exists by ident (uniq)"
    server = find_server()
    return server.fileExists(ident)

def files_exist(hashes):
    "check content hashes of files"
    server = find_server()
    return server.blobsExist(hashes)



#def fetch(url):
#    server = find_server(url)
#    return server.get_one(url)

#def stream(url):
#    server = find_server(url)

#    blob_path = url.rsplit('/',1)[1]
#    return server.stream(blob_path)
