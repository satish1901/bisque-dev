###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011                                ##
##     by the Regents of the University of California                        ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========

DESCRIPTION
===========

"""
import os
import sys
import urlparse
import urllib
import logging
import itertools
import tempfile
import mimetypes
import warnings
import posixpath


import requests
from requests.auth import HTTPBasicAuth
from requests.auth import AuthBase
from requests import Session
from requests_toolbelt import MultipartEncoder

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

from .types import BQMex, BQNode, BQFactory
from .util import parse_qs, make_qs, xml2d, d2xml, normalize_unicode
from .RequestsMonkeyPatch import requests_patch #allows multipart form to accept unicode
try:
    from .casauth import caslogin
    CAS_SUPPORT=True
except ImportError:
    CAS_SUPPORT = False


log = logging.getLogger('bqapi.comm')

#SERVICES = ['']

class BQException(Exception):
    """
        BQException
    """

class BQApiError(BQException):
    """Exception in API usage"""



class BQCommError(BQException):

    def __init__(self, response):
        """
            @param: status - error code
            @param: headers - dictionary of response headers
            @param: content - body of the response (default: None)

        """
        #print 'Status: %s'%status
        #print 'Headers: %s'%headers
        self.response = response


    def __str__(self):
        content = "%s...%s" % (self.response.content[:64], self.response.content[-64:]) if len (self.response.content) > 64 else self.response.content
        return "BQCommError(%s, status=%s, req headers=%s)%s" % (self.response.url,
                                                                 self.response.status_code,
                                                                 self.response.request.headers,
                                                                 content )


class MexAuth(AuthBase):
    """
        Bisque's Mex Authentication
    """
    def __init__(self, token, user=None):
        """
            Sets a mex authentication for the requests

            @param token: Token for authenticating a mex. The token can contain the user name
            and a user name does not have to be provided.
            @param user: The user the mex is attached. (default: None)
        """
        if user is None:
            self.username = "Mex %s"%(token)
        elif user in token.split(':')[0]: #check if token contains user
            self.username = "Mex %s"%(token)
        else:
            self.username = "Mex %s:%s"%(user, token)

    def __call__(self, r):
        """
            Sets the authorization on the headers of the requests.
            @param r: the requests
        """
        r.headers['Authorization'] = self.username
        return r


class BQServer(Session):
    """ A reference to Bisque server
    Allow communucation with a bisque server

    A wrapper over requests.Session
    """

    def __init__(self):
        super(BQServer, self).__init__()
        # Disable https session authentication..
        #self.verify = False
        self.root = None


    def authenticate_mex(self, token, user=None):
        """
            Sets mex authorization to the requests

            @param token: this can be a combination of both token and user or just the token
            @param user: the user attached to the mex

        """
        self.auth = MexAuth(token, user=user)


    def authenticate_basic(self, user, pwd):
        """
            Sets basic authorization along with the request

            @param user: The user for the requests.
            @param pwd: The password for the user.
        """
        self.auth = HTTPBasicAuth(user, pwd)


    def prepare_headers(self, user_headers):
        """

        """
        headers = {}
        headers.update(self.auth)
        if user_headers:
            headers.update(user_headers)
        return headers


    def prepare_url(self, url, **params):
        """
            Prepares the url

            @param url: if the url is not provided with a root and a root has been provided to the session
            the root will be added to the url
            @param odict: ordered dictionary object, addes to the query in the order provided
            @param params: adds params to query potion of the url

            @return prepared url
        """

        u = urlparse.urlsplit(url)

        #root
        if u.scheme and u.netloc:
            scheme = u.scheme
            netloc = u.netloc
        elif self.root and u.netloc=='':
            #adds root request if no root is provided in the url
            r = urlparse.urlsplit(self.root)
            scheme = r.scheme
            netloc = r.netloc
        else: #no root provided
            raise BQApiError("No root provided")

        #query
        query = ['%s=%s'%(k,v) for k,v in urlparse.parse_qsl(u.query, True)]
        unordered_query = []
        ordered_query = []

        if 'odict' in params:
            odict = params['odict']
            del params['odict']
            if odict and isinstance(odict,OrderedDict):
                while len(odict)>0:
                    ordered_query.append('%s=%s'%odict.popitem(False))

        if params:
            unordered_query = ['%s=%s'%(k,v) for k,v in params.items()]

        query = query + unordered_query + ordered_query
        query = '&'.join(query)

        return urlparse.urlunsplit([scheme,netloc,u.path,query,u.fragment])




    def webreq(self, method, url, headers = None, path=None, **params):
        """
            Makes a http GET to the url given

            @param url: the url that is fetched
            @param headers: headers provided for this specific fetch (default: None)
            @param path: the location to where the contents will be stored on the file system (default:None)
            if no path is provided the contents of the response will be returned
            @param timeout: (optional) How long to wait for the server to send data before giving up, as a float, or a (connect timeout, read timeout) tuple

            @return returns either the contents of the rests or the file name if a path is provided

            @exception: BQCommError if the requests returns an error code and message
        """
        log.debug("%s: %s req  header=%s" , method, url, headers)
        timeout = params.get('timeout', None)
        r = self.request(method=method, url=url, headers=headers, stream = (path is not None), timeout=timeout)

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            log.exception ("issue with %s", r)
            raise BQCommError(r)

        if path:
            with open(path, 'wb') as f:
                f.write(r.content)
#                for line in r.iter_content(): #really slow
#                    f.write(line)
            return f.name
        else:
            return r.content

    def fetch(self, url, headers = None, path=None):
        return self.webreq(method='get', url=url, headers=headers, path=path)

    def push(self, url, content=None, files=None, headers=None, path=None, method="POST", boundary=None):
        """
            Makes a http request

            @param url: the url the request is made with
            @param content: an xml document that will be sent along with the url
            @param files: a dictonary with the format {filename: file handle or string}, sends as a multipart form
            @param headers: headers provided for this specific request (default: None)
            @param path: the location to where the contents will be stored on the file system (default:None)
            if no path is provided the contents of the response will be returned
            @param method: the method of the http request (HEAD,GET,POST,PUT,DELETE,...) (default: POST)

            @return returns either the contents of the rests or the file name if a path is provided

            @exception: BQCommError if the requests returns an error code and message
        """
        log.debug("POST %s req %s" % (url, headers))

        try: #error checking
            r = self.request(method, url, data=content, headers=headers, files=files)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            log.exception("In push request: %s %s %s" % (method, url, r.content))
            raise BQCommError(r)

        if path:
            with open(path, 'wb') as f:
                f.write(r.content)
            return f.name
        else:
            return r.content


class BQSession(object):
    """
        Top level Bisque communication object
    """
    def __init__(self):
        self.c = BQServer()
        self.mex = None
        self.services  = {}
        self.new = set()
        self.dirty = set()
        self.deleted = set()
        self.bisque_root = None
        self.factory = BQFactory(self)
        self.dryrun = False


    ############################
    # Establish a bisque session
    ############################
    def _create_mex (self, user, moduleuri):
        mex = BQMex()
        mex.name = moduleuri or 'script:%s' % " ".join (sys.argv)
        mex.status = 'RUNNING'
        self.mex = self.save(mex, url=self.service_url('module_service', 'mex'))
        if self.mex:
            mextoken = self.mex.resource_uniq
            self.c.authenticate_mex(mextoken, user)
            # May not be needed
            for c in range (100):
                try:
                    self.load(url = self.service_url('module_service', path = "/".join (['mex', mextoken])))
                    return True
                except BQCommError:
                    pass
        return False
    def _check_session(self):
        """Used to check that session is actuall active"""
        r = self.fetchxml (self.service_url("auth_service", 'session'))
        users = r.findall('./tag[@name="user"]')
        return  len(users) > 0


    def init_local(self, user, pwd, moduleuri=None, bisque_root=None, create_mex=True):
        """
            Initalizes a local session

            @param: user - a bisque user
            @param: pwd - the bisque user's password
            @param: moduleuri - module uri to be set to the mex (Only matter if create mex is set to true) (moduleuri: None)
            @param: bisque_root - the root of the bisque system the user is trying to access (bisque_root: None)
            @param: create_mex - creates a mex session under the user (default: True)

            @return: self
        """

        if bisque_root != None:
            self.bisque_root = bisque_root
            self.c.root = bisque_root

        self.c.authenticate_basic(user, pwd)
        self._load_services()
        if not self._check_session():
            log.error("Session failed to be created.. please check credentials")
            return None

        self.mex = None

        if create_mex:
            self._create_mex(user, moduleuri)

        return self


    def init_mex(self, mex_url, token, user=None, bisque_root=None):
        """
            Initalizing a local session from a mex

            @param: mex_url - the mex url to initalize the session from
            @param: token - the mex token to access the mex
            @param: user - the owner of the mex (Does not have to be provided if already
            provided in the token) (default: None)
            @param: bisque_root - the root of the bisque system the user is trying to access (bisque_root: None)

            @return self
        """
        if bisque_root is None:
            # This assumes that bisque_root is http://host.org:port/
            mex_tuple = list(urlparse.urlparse(mex_url))
            mex_tuple[2:5] = '','',''
            bisque_root = urlparse.urlunparse(mex_tuple)

        self.bisque_root = bisque_root
        self.c.root = bisque_root
        self.c.authenticate_mex(token, user=user)
        self._load_services()
        self.mex = self.load(mex_url, view='deep')
        return self


    def init_cas(self, user, pwd, moduleuri=None, bisque_root=None, create_mex=False):
        """Initalizes a cas session

        @param: user - a bisque user
        @param: pwd - the bisque user's password
        @param: moduleuri - module uri to be set to the mex (Only matter if create mex is set to true) (moduleuri: None)
        @param: bisque_root - the root of the bisque system the user is trying to access (bisque_root: None)
        @param: create_mex - creates a mex session under the user (default: True)
        @return: self

        Example
        >>>from bqapi import BQSession
        >>>s = BQSession()
        >>>s.init_cas (CASNAME, CASPASS, bisque_root='http://bisque.iplantcollaborative.org', create_mex=False)
        >>>s.fetchxml('/data_serice/image', limit=10)
        """
        if not CAS_SUPPORT:
            raise BQApiError ("CAS not support.. please check installation")

        if bisque_root == None:
            raise BQApiError ("cas login requires bisque_root")

        self.bisque_root = bisque_root
        self.c.root = bisque_root

        caslogin (self.c, bisque_root + "/auth_service/login", user, pwd)
        self._load_services()
        if not self._check_session():
            log.error("Session failed to be created.. please check credentials")
            return None
        self.mex = None

        if create_mex:
            self._create_mex(user, moduleuri)
        return self


    def close(self):
        pass

    def parameter(self, name):
        if self.mex is None:
            return None
        return self.mex.xmltree.find('tag[@name="inputs"]//tag[@name="%s"]'%name)

    def get_value_safe(self, v, t):
        try:
            if t == 'boolean':
                return v.lower() == 'true'
            elif t == 'number':
                return float(v)
            return v
        except AttributeError:
            return None

    def parameter_value(self, name=None, p=None):
        if p is None:
            p = self.parameter(name)
        else:
            name = p.get('name')

        if p is None: return None
        values = p.xpath('value')
        if len(values)<1:
            v = p.get('value')
            t = p.get('type', '').lower()
            return self.get_value_safe(v, t)

        r = []
        for vv in values:
            v = vv.text
            t = vv.get('type', '').lower()
            r.append(self.get_value_safe(v, t))
        return r

    def parameters(self):
        p = {}
        if self.mex is None:
            return p
        inputs = self.mex.xmltree.iterfind('tag[@name="inputs"]//tag')
        for i in inputs:
            p[i.get('name')] = self.parameter_value(p=i)
        return p

    def fetchxml(self, url, path=None, **params):
        """
            Fetch an xml object from the url

            @param: url - A url to fetch from
            @param: path - a location on the file system were one wishes the response to be stored (default: None)
            @param: odict - ordered dictionary of params will be added to url for when the order matters
            @param: params - params will be added to url

            @return xml etree
        """
        url = self.c.prepare_url(url, **params)
        log.debug('fetchxml %s ' % url)
        if path:
            return self.c.fetch(url, headers={'Content-Type':'text/xml', 'Accept':'text/xml'}, path=path)
        else:
            r = self.c.fetch(url, headers = {'Content-Type':'text/xml', 'Accept':'text/xml'})
            return self.factory.string2etree(r)


    def postxml(self, url, xml, path=None, method="POST", **params):
        """
            Post xml allowed with files to bisque

            @param: url - the url to make to the request
            @param: xml - an xml document that is post at the url location (excepts either string or etree._Element)
            @param: path - a location on the file system were one wishes the response to be stored (default: None)
            @param method - the method of the http request (HEAD,GET,POST,PUT,DELETE,...) (default: POST)
            @param: odict - ordered dictionary of params will be added to url for when the order matters
            @param: params - params will be added to url

            @return: xml etree or path to the file were the response was stored
        """

        if not isinstance(xml, basestring):
            xml = self.factory.to_string (xml)

        log.debug('postxml %s  content %s ' % (url, xml))

        url = self.c.prepare_url(url, **params)

        try:
            r = None
            if not self.dryrun:
                r = self.c.push(url, content=xml, method=method, path=path, headers={'Content-Type':'text/xml', 'Accept': 'text/xml' })
            if path is not None:
                return r
            return r and self.factory.string2etree(r)
        except etree.ParseError, e:
            log.exception("Problem with post response %s", e)
            return r

    def deletexml(self, url):
        "Delete a resource"
        url = self.c.prepare_url(url)
        r = self.c.webreq (method='delete', url=url)
        return r


    def fetchblob(self, url, path=None, **params):
        """
            Requests for a blob

            @param: url - filename of the blob
            @param: path - a location on the file system were one wishes the response to be stored (default: None)
            @param: params -  params will be added to url query

            @return: contents or filename
        """
        url = self.c.prepare_url(url, **params)
        return self.c.fetch(url, path=path )


    def postblob(self, filename, xml=None, path=None, method="POST", **params):
        """
            Create Multipart Post with blob to blob service

            @param filename: filename of the blob
            @param xml: xml to be posted along with the file
            @param params: params will be added to url query
            @return: a <resource type="uploaded" <image> uri="URI to BLOB" > </image>
        """
        import_service_url = self.service_url('import', path='transfer')
        if import_service_url is None:
            raise BQApiError('Could not find import service to post blob.')

        url = self.c.prepare_url(import_service_url, **params)

        if xml!=None:
            if not isinstance(xml, basestring):
                xml = self.factory.to_string(xml)

        fields = {}
        if filename is not None:
            filename = normalize_unicode(filename)
            fields['file'] = (filename, open(filename, 'rb'), 'application/octet-stream')
        if xml is not None:
            fields['file_resource'] = xml
        if fields:
            m = MultipartEncoder(fields = fields )
            return self.c.push(url,
                               content=m,
                               headers={'Accept': 'text/xml', 'Content-Type':m.content_type},
                               path=path, method=method)
        raise BQApiError("improper parameters for postblob: must use paramater xml or filename or both ")


    def service_url(self, service_type, path = "" , query=None):
        """
            @param service_type:
            @param path:
            @param query:

            @return
        """
        root = self.service_map.get(service_type, None)
        if root is None:
            raise BQApiError('Not a service type')
        if query:
            path = "%s?%s" % (path, urllib.urlencode(query))
        return urlparse.urljoin(root, path)


    def _load_services(self):
        """
            @return
        """
        services = self.load (posixpath.join(self.bisque_root , "services"))
        smap = {}
        for service in services.tags:
            smap [service.type] = service.value
        self.service_map = smap


    #############################
    # Classes and Type
    #############################
    def element(self, ty, **attrib):
        elem = etree.Element(ty, **attrib)


    def append(self, mex, tags=[], gobjects=[], children=[]):
        def append_mex (mex, type_tup):
            type_, elems = type_tup
            for  tg in elems:
                if isinstance(tg, dict):
                    tg = d2xml({ type_ : tg})
                elif isinstance(tg, BQNode):
                    tg = BQFactory.to_etree(tg)
                elif isinstance(tg, etree._Element):
                    pass
                else:
                    raise BQApiError('bad values in tag/gobject list %s' % tg)
                mex.append(tg)

        append_mex(mex, ('tag', tags))
        append_mex(mex, ('gobject', gobjects))
        for elem in children:
            append_mex(mex, elem)


    ##############################
    # Mex
    ##############################
    def update_mex(self, status, tags = [], gobjects = [], children=[], reload=False, merge=False):
        """save an updated mex with the addition

        @param status:  The current status of the mex
        @param tags: list of etree.Element|BQTags|dict objects of form { 'name': 'x', 'value':'z' }
        @param gobjects: same as etree.Element|BQGobject|dict objects of form { 'name': 'x', 'value':'z' }
        @param children: list of tuple (type, obj array) i.e ('mex', dict.. )
        @param reload:
        @param merge: merge "outputs"/"inputs" section if needed
        @return
        """
        if merge:
            mex = self.fetchxml(self.mex.uri, view='deep')  # get old version of MEX, so it can be merged if needed
            mex.set('value', status)
        else:
            mex = etree.Element('mex', value = status, uri = self.mex.uri)
        #self.mex.value = status
        def append_mex (mex, type_tup):
            type_, elems = type_tup
            for  tg in elems:
                if isinstance(tg, dict):
                    tg = d2xml({ type_ : tg})
                elif isinstance(tg, BQNode):
                    tg = self.factory.to_etree(tg)
                elif isinstance(tg, etree._Element):
                    pass
                else:
                    raise BQApiError('bad values in tag/gobject list %s' % tg)
                was_merged = False
                if merge and tg.tag == 'tag' and tg.get('name', '') in ['inputs', 'outputs']:
                    hits = mex.xpath('./tag[@name="%s"]' % tg.get('name', ''))
                    if hits:
                        assert len(hits) == 1
                        hits[0].extend(list(tg))
                        was_merged = True
                        log.debug("merged '%s' section in MEX", tg.get('name', ''))
                if not was_merged:
                    mex.append(tg)

        append_mex(mex, ('tag', tags))
        append_mex(mex, ('gobject', gobjects))
        for elem in children:
            append_mex(mex, elem)

        #mex = { 'mex' : { 'uri' : self.mex.uri,
        #                  'status' : status,
        #                  'tag' : tags,
        #                  'gobject': gobjects }}
        content = self.postxml(self.mex.uri, mex, view='deep' if reload else 'short')
        if reload and content is not None:
            self.mex = self.factory.from_string(content)
            return self.mex
        return None


    def finish_mex(self, status="FINISHED", tags=[], gobjects=[], children=[], msg=None ):
        """
            @param status:
            @param tags:
            @param gobject:
            @param children:
            @param msg:

            @return
        """
        if msg is not None:
            tags.append( { 'name':'message', 'value': msg })
        try:
            return self.update_mex(status, tags=tags, gobjects=gobjects, children=children, reload=False, merge=True)
        except BQCommError, ce:
            log.error ("Problem during finish mex %s" % ce.response.request.headers)
            try:
                return self.update_mex( status='FAILED',tags= [  { 'name':'error_message', 'value':  "Error during saving (status %s)" % ce.response.status_code } ] )
            except:
                log.exception ("Cannot finish/fail Mex ")

    def fail_mex(self, msg):
        """
            @param msg:
        """
        if msg is not None:
            tags = [  { 'name':'error_message', 'value': msg } ]
        self.finish_mex( status='FAILED', tags=tags)

    def _begin_mex(self, moduleuri):
        """create a mex on the server for this run"""
        pass



    ##############################
    # Module control
    ##############################
    def run_modules(self, module_list, pre_run=None, post_run=None, callback_fct=None):
        """Run one or more modules in parallel.

        :param module_list: List of modules to run
        :type  module_list: [ { moduleuri: ..., inputs: { param1:val1, param2:val2, ...}, parent_mex: ... }, {...}, ... ]
        :param pre_run: module entrypoint to call before run (or None if no prerun)
        :type pre_run: str
        :param post_run: module entrypoint to call after run (or None if no postrun)
        :type post_run: str
        :param callback_fct: function to call on completion (None: block until completion)
        :type  callback_fct: fct(mex_list=list(str))
        :returns: list of mex URIs, one for each module
        :rtype: list(str)
        """
        # TODO: create MEX according to params and POST it to module_service
        pass

    ##############################
    # Resources
    ##############################
    def query(self, resource_type, **kw):
        """Query for a resource
        tag_query=None, tag_order=None, offset=None, limit=None
        """
        results = []
        queryurl = self.service_url ('data_service', path=resource_type, query=kw)
        items = self.fetchxml (queryurl)
        for item in items:
            results.append (self.factory.from_etree(item))
        return results


    def load(self, url,  **params):
        """Load a bisque object

        @param url:
        @param params:

        @return
        """
        #if view not in url:
        #    url = url + "?view=%s" % view
        try:
            xml = self.fetchxml(url, **params)
            if xml.tag == "response":
                xml = xml[0]
            bqo = self.factory.from_etree(xml)
            return bqo
        except BQCommError, ce:
            log.exception('communication issue while loading %s' % ce)
            return None

    def delete(self, bqo, url=None, **kw):
        "Delete an object and all children"
        url = bqo.uri or url
        if url is not None:
            return self.deletexml(url)


    def save(self, bqo, url=None, **kw):
        """
            @param bqo:
            @param url:
            @param kw:

            @return
        """
        try:
            original = bqo

            # Find an object (or parent with a valild uri)
            url = url or bqo.uri
            if url is None:
                while url is None and bqo.parent:
                    bqo = bqo.parent
                    url=  bqo.parent.uri
            if url is None:
                url = self.service_url ('data_service')

            xml =  self.factory.to_etree(bqo)
            xml = self.postxml(url, xml, **kw)
            return xml is not None and self.factory.from_etree(xml)
        except BQCommError, ce:
            log.exception('communication issue while saving %s' , ce)
            return None

    def saveblob(self, bqo, filename):
        """Save a blob to the server and return metadata structure
        """

        try:
            xml =  self.factory.to_etree(bqo)
            xmlstr = self.postblob (filename=filename, xml= xml)
            xmlet  = self.factory.string2etree (xmlstr)
            if xmlet.tag == 'resource' and xmlet.get ('type') == 'uploaded':
                # return inside
                bqo =  self.factory.from_etree(xmlet[0])
                return bqo
            return None
        except BQCommError, ce:
            log.exception('communication issue while saving %s' , filename)
            return None
