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
try:
    import tables #requires pytables
except ImportError:
    tables = None
    warnings.warn('Warning: tables is not installed, not all function will work')
    
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import requests
from RequestsMonkeyPatch import requests_patch #allows multipart form to accept unicode
from requests.auth import HTTPBasicAuth
from requests.auth import AuthBase
from requests import Session

from lxml import etree


USENODE = False
if USENODE:
    from bqapi.bqnode import fromXml, toXml, BQMex, BQNode, BQFactory
else:
    from bqapi.bqclass import fromXml, toXml, BQMex, BQNode

from bqapi.util import parse_qs, make_qs, xml2d, d2xml, normalize_unicode


log = logging.getLogger('bqapi.comm')


#SERVICES = ['']

class BQException(Exception):
    """
        BQException
    """

class BQCommError(BQException):
    
    def __init__(self, status, headers, content=None):
        """
            @param status:
            @param headers:
            @param content:
            
        """
        print 'Status: %s'%status
        print 'Headers: %s'%headers
        self.status = status
        self.headers = headers
        if content is not None:
            self.content = content
            print 'Content: [%s]'%content

    def __str__(self):
        return "CommError(status=%s, %s)" % (self.status, self.headers)

class MexAuth(AuthBase):
    """
        Bisque's Mex Authentication
    """
    def __init__(self, user, token):
        """
            @param user:
            @param token:
        """
        if user in token.split(':')[0]:
            self.username = "Mex %s"%( token)
        else:
            self.username = "Mex %s:%s"%( user, token)
        
    def __call__(self, r):
        """
            @param r:
        """
        r.headers['Authorization'] = self.username
        return r

class BQServer(Session):
    """ A reference to Bisque server
    Allow communucation with a bisque server
    
    A wrapper over requests.Session
    """

    def __init__(self):
        self.root = None
        super(BQServer, self).__init__()
        

    def authenticate_mex(self, user, token):
        """
            @param user:
            @param token:
        """
        self.auth = MexAuth(user, token)


    def authenticate_basic(self, user, pwd):
        """
            @param user:
            @param pwd:
        """
        self.auth = HTTPBasicAuth(user, pwd)


    def prepare_headers(self, user_headers):
        """
            
        """
        headers = {}
        headers.update (self.auth)
        if user_headers:
            headers.update(user_headers)
        return headers
    
    
    def prepare_url(self, url, **params):
        """
            params need to be an ordered dictionary
            
            @param url:
            @param odict:
            @param params:
            
            @return prepared url
        """
        
        u = urlparse.urlsplit(url)

        #root
        if self.root and u.netloc=='':
            #adds root request if no root is provided in the url
            r = urlparse.urlsplit(self.root)
            scheme = r.scheme
            netloc = r.netloc
        
        elif u.scheme and u.netloc:
            scheme = u.scheme
            netloc = u.netloc
        else: #no root provided
            raise BQException()
        
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

    def fetch(self, url, headers = None, path=None):
        """
            @param url:
            @param headers:
            @param path:
            
            @return 
        """
        log.debug("GET: %s req  header=%s" %  (url, headers))
        
#        if headers:
#            self.headers.update(headers)
        
        r = self.get(url, headers=headers)
        
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise BQCommError( r.status_code, r.headers) #need to finish
        
        if path:
            with open(path, 'wb') as f:
                f.write(r.content)
                return f.name
        else:
            return r.content
        

    def post(self, url, content=None, files=None, headers=None, path=None, method="POST", boundary=None):
        """
            @param url:
            @param content:
            @param files:
            @param headers:
            @param path:
            @param method:
            
            @return 
        """
        log.debug("POST %s req %s" % (url, headers))
        
        r = self.request(method, url, data=content, headers=headers, files=files) #maintain name space
        try: #error checking
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise BQCommError(r.status_code, r.headers) #need to finish
        
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
        self.parser = etree.XMLParser()
        self.bisque_root = None
        if USENODE:
            self.parser.set_element_class_lookup(BQFactory())
            

    ############################
    # Establish a bisque session
    ############################
    def init_local(self, user, pwd, moduleuri=None, bisque_root=None, create_mex=True):
        """
            Create a session mex 
            @param user
            @param pwd
            @param module
            @param bisque_root
            @param create_mex
            
            @return self 
        """
        
        if bisque_root != None:
            self.bisque_root = bisque_root
            self.c.root = bisque_root
            
        self.c.authenticate_basic(user, pwd)
        self._load_services()
        self.mex = None
        
        if create_mex:
            mex = BQMex()
            mex.module = moduleuri
            mex.status = 'RUNNING'
            self.mex = self.save(mex, url=self.service_url('module_service', 'mex'))
            if self.mex:
                mextoken = self.mex.resource_uniq
                self.c.authenticate_mex(user, mextoken) 
                #warning: the mex can take a bit of time to appear in the database 
                #so it is probably best to poll the data_service for the mex before
                #performing more authentication limited operations
        return self


    def init_mex(self, mex_url, user, token, bisque_root=None):
        """
            Initalizing a session from a mex
            
            @param mex_url
            @param user
            @token
            @bisque_root
            
            @return self
        """
        if bisque_root is None:
            # This assumes that bisque_root is http://host.org:port/
            mex_tuple = list(urlparse.urlparse (mex_url))
            mex_tuple[2:5] = '','',''
            bisque_root = urlparse.urlunparse(mex_tuple)

        self.bisque_root = bisque_root
        self.c.root = bisque_root
        self.c.authenticate_mex(user, token)
        self._load_services()
        self.mex = self.load (mex_url, view='deep')
        return self


    def close(self):
        pass


    def fetchxml(self, url, path=None, **params):
        """
            Fetch an xml object from the url

            @param url: A url to fetch from
            @param odict: ordered dictionary of params will be added to url for when the order matters
            @param params: params will be added to url
            
            @return xml etree
        """
        url = self.c.prepare_url (url, **params)
        log.debug('fetchxml %s ' % url)
        if path:
            return self.c.fetch(url, headers={'Content-Type':'text/xml', 'Accept':'text/xml'}, path=path)
        else:
            r = self.c.fetch(url, headers = {'Content-Type':'text/xml', 'Accept':'text/xml'})
            return etree.XML(r, self.parser)


    def postxml(self, url, xml, path=None, method="POST", **params):
        """
            Post xml allow with files to bisque
            
            @param url:
            @param xml:
            @param path:
            @param odict:
            @param params:
            
            @return 
        """
        log.debug('postxml %s  content %s ' % (url, xml))
        
        if isinstance(xml, etree._Element):
            xml = etree.tostring(xml, pretty_print=True)

        url = self.c.prepare_url(url, **params)
           
        if path:
            return self.c.post(url, content=xml, path=path, method=method, headers={'Content-Type':'text/xml', 'Accept': 'text/xml' })            
        else:
            r = self.c.post(url, content=xml, method=method, headers={'Content-Type':'text/xml', 'Accept': 'text/xml' })
            return etree.XML(r, self.parser)
        
    if tables: #check if tables is installed before adding functions
        def fetchhdf(self, url, path=None, **params):
            """
                Fetch HDF from bisque
                If path is provided the hdf5 file is stored there else if 
                no path is provided a temporary file is created and an pytables
                object is returned.
                
                @param url:
                @param xml:
                @param path:
                @param method:
                @param param:
                
                @return
            """
            url = self.c.prepare_url (url, **params)
            log.debug('fetchxml %s ' % url)
            if path: #returns path of the file
                return self.c.fetch(url, headers={'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=path)
            else:
                with tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir() ) as f: 
                    path = f.name
                path = self.c.fetch(url, headers = {'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=path)
                return tables.open_file(path, 'r')
            
            
        def posthdf(self, url, xml=None, path=None, method="POST", **params):
            """
                Post xml to retrieve HDF from bisque
                If path is provided the hdf5 file is stored there else if 
                no path is provided a temporary file is created and an pytables
                object is returned.
                
                @param url:
                @param xml:
                @param path:
                @param method:
                @param param:
                
                @return
            """
            url = self.c.prepare_url (url, **params)
            log.debug('fetchxml %s ' % url)
    
            if isinstance(xml, etree._Element):
                xml = etree.tostring(xml, pretty_print=True)
    
            if path: #returns path of the file
                return self.c.post(url, content=xml, headers={'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=path)
            else: 
                with tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir() ) as f: 
                    path = f.name
                path = self.c.post(url, content=xml, headers={'Content-Type':'text/xml',  'Accept':'application/x-bag'}, path=f.name)
                return tables.open_file(path, 'r')


    def fetchblob(self, url, path=None, **param):
        """
            Requests for a blob from the data_service

            @param filename: filename of the blob
            @param xml: xml to be posted along with the file
            @param params: params will be added to url query
        """
        url = self.c.prepare_url(url, **params)
        return self.c.fetch(url, path=path, headers={'Content-Type':'text/xml', 'Accept': 'application/x-bag' })


    def postblob(self, filename, xml=None, path=None, method="POST", **params):
        """
            Create Multipart Post with blob and xml tags

            @param filename: filename of the blob
            @param xml: xml to be posted along with the file
            @param params: params will be added to url query
        """
        import_service_url = self.service_url('import',path='transfer')
        if import_service_url is None:
            raise 'Could not find import service to post blob.'
        
        filename = normalize_unicode(filename)
        
        url = self.c.prepare_url(import_service_url, **params)
        if isinstance(filename, basestring):
            
            with open(filename, 'rb') as f:
                fields = {'file': (filename, f, mimetypes.guess_type(filename)[0])} #not sure if all filenames should be decoded from utf8
                data = None                                                                      #also have not tested on python3 yet
                if xml!=None:
                    data = {}
                    if isinstance(xml, etree._Element):
                        fields['file_resource'] = etree.tostring(xml)
                    else:
                        fields['file_resource'] = xml
                
                return self.c.post(url, content=None, files=fields, headers={'Accept': 'text/xml'}, path=path, method=method)
#    def post_streaming_blob(self, filename, xml=None, **params):
#        """
#        Requires requests_toolbet
#        """
#        try:
#            from requests_toolbelt import MultipartEncoder
#        except ImportError:
#            print 'Does not have requests_toolbelt'
#            return
#        
#        url = self.c.prepare_url('import/transfer',**params)
#        
#        if isinstance(filename, basestring):
# 
#            fields={'file':(filename, open(filename, 'rb'), 'text/plain')} 
#            
#            if xml!=None:
#                if isinstance( xml, etree):
#                    text = etree.tostring(xml, pretty_print=True)
#                files['file_resource'] = text            
#            
#            files = MultipartEncoder(fields)            
#            
#                r = self.c.bq_post(url, headers=headers, data=files, headers={'Content-Type': files.content_type})
#            return r


    def service_url(self, service_type, path = "" , query = None):
        """
            @param service_type:
            @param path:
            @param query:
            
            @return
        """
        root = self.service_map.get(service_type, None )
        if root is None:
            raise 'Not a service type'
        if query:
            path = "%s?%s" % (path, urllib.urlencode(query))
        return urlparse.urljoin(root, path)


    def _load_services(self):
        """
            @return
        """
        services = self.load (self.bisque_root + "/services")
        smap = {}
        for service in services.tags:
            smap [ service.type ] = service.value
        self.service_map = smap


    #############################
    # Classes and Type
    #############################
    def element(self, ty, **attrib):
        elem = etree.Element(ty, **attrib)


    def append(self, elem, tags=[], gobjects=[], children=[]):
        def append_mex (mex, type_tup):
            type_, elems = type_tup
            for  tg in elems:
                if isinstance(tg, dict):
                    tg = d2xml({ type_ : tg})
                elif isinstance(tg, BQNode):
                    tg = toXml(tg)
                elif isinstance(tg, etree._Element):
                    pass
                else:
                    raise BQException('bad values in tag/gobject list %s' % tg)
                mex.append(tg)

        append_mex(mex, ('tag', tags))
        append_mex(mex, ('gobject', gobjects))
        for elem in children:
            append_mex(mex, elem)


    ##############################
    # Mex
    ##############################
    def update_mex(self, status, tags = [], gobjects = [], children=[], reload=False):
        """save an updated mex with the addition

        @param status:  The current status of the mex
        @param tags: list of etree.Element|BQTags|dict objects of form { 'name': 'x', 'value':'z' }
        @param gobjects: same as etree.Element|BQGobject|dict objects of form { 'name': 'x', 'value':'z' }
        @param children: list of tuple (type, obj array) i.e ('mex', dict.. )
        @param reload:
        
        @return
        """
        mex = etree.Element('mex', value = status, uri = self.mex.uri)
        #self.mex.value = status
        #mex = toXml(self.mex)
        def append_mex (mex, type_tup):
            type_, elems = type_tup
            for  tg in elems:
                if isinstance(tg, dict):
                    tg = d2xml({ type_ : tg})
                elif isinstance(tg, BQNode):
                    tg = toXml(tg)
                elif isinstance(tg, etree._Element):
                    pass
                else:
                    raise BQException('bad values in tag/gobject list %s' % tg)
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
            self.mex = fromXml(content, session=self)
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
            return self.update_mex(status, tags=tags, gobjects=gobjects, children=children, reload=False)
        except BQCommError, ce:
            log.error ("Problem during finish mex %s" % ce.headers)
            try:
                return self.update_mex( status='FAILED',tags= [  { 'name':'error_message', 'value':  "Error during saving (status %s)" % ce.status } ] )
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
    # Low-level save
    ##############################
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
            bqo  = fromXml(xml, session=self)
            return bqo
        except BQCommError, ce:
            return None


    def save(self, bqo, url=None, **kw):
        """
            @param bqo:
            @param url:
            @param kw:
            
            @return
        """
        try:
            if url is None and bqo.uri:
                url = bqo.uri
            xml =  toXml(bqo)
            xml = self.postxml(url, xml, **kw)
            return fromXml( xml, session=self)
        except BQCommError, ce:
            log.exception('communication issue while saving %s' % ce)
            return None



