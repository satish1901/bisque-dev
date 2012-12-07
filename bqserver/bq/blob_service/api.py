from bq.core.service import service_registry

from controllers.blobsrv import  guess_type
from controllers.blob_storage import make_uniq_hash

def find_server():
    return service_registry.find_service ('blob_service')

def store_blobOLD(filesrc=None, filename=None, url=None, permission='private', **kw):
    "create and store a resource blob"
    server = find_server()
    return server.storeBlob(flosrc=filesrc, filename=filename,url=url, permission=permission, **kw)

def store_blob(resource, fileobj=None):
    "create and store a resource blob"
    server = find_server()
    return server.store_blob(resource=resource, fileobj=fileobj)

def store_fileobj(resource, fileobj  ):
    "create and store a resource blob"
    server = find_server()
    return server.store_fileobj(resource=resource, fileobj=fileobj )

def store_reference(resource, urlref ):
    "create and store a resource blob"
    server = find_server()
    return server.store_reference( resource=resource, urlref=urlref)

def fetch_blob(blob_id):
    "return localpath of blobid "
    server = find_server()
    return server.fetch_blob(blob_id)
    
def localpath(uniq_ident):
    "return localpath of resource by ident (uniq)"
    server = find_server()
    return server.localpath(uniq_ident)

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
