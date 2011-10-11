from bq.core.service import service_registry

def find_server(url):
    return service_registry.find_service ('blob_service')


def fetch(url):
    server = find_server(url)

    
    return server.get_one(url)

def stream(url):
    server = find_server(url)

    blob_path = url.rsplit('/',1)[1]
    return server.stream(blob_path)
