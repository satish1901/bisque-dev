import urlparse
import posixpath
from urllib import urlencode

def urljoin(base, partialpath, **kw):
    url = urlparse.urlparse(base)
    path = posixpath.normpath(posixpath.join(url[2], partialpath))
    #query = urlparse.parse_qs(url[4])
    if url[4]:
        query = dict ([ q.split('=')  for q in url[4].split('&')])
    else:
        query = {}
    query.update ( urlencode(kw) )
    return urlparse.urlunparse(
        (url.scheme,url.netloc,path,url.params,query,url.fragment)
        )
