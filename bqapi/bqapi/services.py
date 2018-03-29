import os
import urllib
import urlparse
import random
import string


from lxml import etree
from requests_toolbelt import MultipartEncoder
from .util import  normalize_unicode
from .exception import BQCommError


#DEFAULT_TIMEOUT=None
DEFAULT_TIMEOUT=60*60 # 1 hour

####
#### KGK
#### Still working on filling this out
#### would be cool to have service definition language to make these.
#### TODO more service, renders etc.

class BaseServiceProxy(object):

    def __init__(self, session, service_name, timeout=DEFAULT_TIMEOUT):
        self.session = session
        self.service_url = session.service_map [service_name]
        self.service_name = service_name
        self.timeout = timeout

    def construct(self, path, params):
        url = self.service_url
        if params:
            path = "%s?%s" % (path, urllib.urlencode(params))
        if path:
            url = urlparse.urljoin (url, path)
        return url

    def request (self, path=None, params=None, method='get', render=None, **kw):
        """
        @param path: a path on the service
        @param params: a diction of value to encode as params
        @return a reuqest.response
        """
        if path and path[0] == "/":
            path = path[1:]
        if path:
            path = urlparse.urljoin (self.service_url, path)
        else:
            path = self.service_url

        # no longer in session https://github.com/requests/requests/issues/3341
        timeout = kw.pop('timeout', self.timeout)
        headers = kw.pop('headers', self.session.c.headers)
        if render=="xml":
            headers.update ({'Content-Type':'text/xml', 'Accept': 'text/xml'})

        try:
            response = self.session.c.request (url=path, params=params, method=method, timeout=timeout, headers=headers, **kw)
            if render =="xml":
                return etree.fromstring (response.content)
            return response
        except etree.ParseError:
            #self.session.log.error ("xml parse error in %s", response.content)
            raise BQCommError(response)

    def fetch(self, path=None, params=None, render=None, **kw):
        return self.request(path=path, params=params, render=render, **kw)
    def get(self, path=None, params=None, render=None, **kw):
        return self.request(path=path, params=params, render=render, **kw)
    def post(self, path=None, params=None, render=None, **kw):
        return self.request(path=path, params=params, render=render, method='post', **kw)
    def put(self, path=None, params=None, render=None, **kw):
        return self.request(path=path, params=params, render=render, method='put', **kw)
    def delete(self, path=None, params=None, render=None, **kw):
        return self.request(path=path, params=params, render=render, method='delete', **kw)


class AdminProxy (BaseServiceProxy):
    def login_as (self, user_name):
        data = self.session.service ('data_service')
        userxml = data.fetch ("user", params = { 'wpublic' :'1', 'resource_name':  user_name}, render="xml")
        user_uniq = userxml.find ("user").get ('resource_uniq')
        self.fetch ('/user/{}/login'.format(user_uniq))


class BlobProxy (BaseServiceProxy): #TODO
    def register_file(self, store_path):
        pass

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class ImportProxy(BaseServiceProxy):
    def transfer (self, filename, xml=None):
        fields = {}
        if filename is not None:
            filename = normalize_unicode(filename)
            fields['file'] = (os.path.basename(filename), open(filename, 'rb'), 'application/octet-stream')
        if xml is not None:
            fields['file_resource'] = xml
        if fields:
            # https://github.com/requests/toolbelt/issues/75
            m = MultipartEncoder(fields = fields )
            m._read = m.read #pylint: disable=protected-member
            m.read = lambda size: m._read (8129*1024) # 8MB
            response = self.post("transfer_"+id_generator(),
                                 data=m,
                                 headers={'Accept': 'text/xml', 'Content-Type':m.content_type})
            return response

class DatasetProxy (BaseServiceProxy):

    def delete (self, dataset_uniq,  members=False, **kw):
        if members:
            params = kw.pop('params', {})
            params['duri'] = dataset_uniq
            return self.fetch("delete", params=params, **kw)
        data = self.session.service('data')
        return data.delete (dataset_uniq)



class ModuleProxy (BaseServiceProxy):
    def execute (self, module_name, **module_parms):
        pass


SERVICE_PROXIES = {
    'admin' : AdminProxy,
    'import' : ImportProxy,
    'blob_serice': BlobProxy,
    'dataset_service': DatasetProxy,
}

class ServiceFactory (object):
    @classmethod
    def make (cls, session, service_name):
        svc = SERVICE_PROXIES.get (service_name, BaseServiceProxy)
        if service_name in session.service_map:
            return svc (session, service_name )
        return None


def test_module():
    from bqapi import BQSession
    session = BQSession ().init_local ('admin', 'admin', 'http://localhost:8080')
    admin = session.service('admin')
    data = session.service('data_service')
    #admin.user(uniq).login().fetch ()
    xml = data.get ("user", params = {'wpublic':'1', 'resource_name' : 'admin'}, render='xml')
    user_uniq = xml.find ("user").get ('resource_uniq')
    admin.fetch ('/user/{}/login'.format( user_uniq))

if __name__ == "__main__":
    test_module()
