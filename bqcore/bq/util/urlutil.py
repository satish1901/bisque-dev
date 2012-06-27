import urlparse
import posixpath
import urllib
import urlparse

def urljoin(base, partialpath, **kw):
    url = urlparse.urlparse(base)
    path = posixpath.normpath(posixpath.join(url[2], partialpath))
    #query = urlparse.parse_qs(url[4])
    if url[4]:
        query = dict ([ q.split('=')  for q in url[4].split('&')])
    else:
        query = {}
    query.update ( urllib.urlencode(kw) )
    return urlparse.urlunparse(
        (url.scheme,url.netloc,path,url.params,query,url.fragment)
        )

def update_url(url, params = {}):
    'construct a url with new params'

    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    
    url_parts[4] = urllib.urlencode(query)
    return  urlparse.urlunparse(url_parts)
