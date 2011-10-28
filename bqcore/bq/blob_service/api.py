from bq.core.service import service_registry

from controllers.blobsrv import make_uniq_hash, guess_type

def find_server():
    return service_registry.find_service ('blobs')

def store_blob(src, name):
    server = find_server()
    return server.storeBlob(src, name)

def localpath(ident, localdir):
    server = find_server()
    return server.localpath(ident, localdir)

def file_exists(ident):
    server = find_server()
    return server.fileExists(ident)

def original_name(ident):
    server = find_server()
    return server.originalFileName(ident)

def files_exists(hashes):
    server = find_server()
    return server.blobsExist(hashes)



#def fetch(url):
#    server = find_server(url)
#    return server.get_one(url)

#def stream(url):
#    server = find_server(url)

#    blob_path = url.rsplit('/',1)[1]
#    return server.stream(blob_path)
