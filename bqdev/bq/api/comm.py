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
import httplib2
import urlparse
import urllib
import logging
import itertools

from lxml import etree

from bqclass import fromXml, toXml, BQMex, BQNode
from util import parse_qs, make_qs, xml2d, d2xml


log = logging.getLogger('bq.api.comm')

class BQException(Exception):
    "BQException"


class BQServer(object):
    """ A reference to Bisque server
    Allow communucation with a bisque server
    """

    def __init__(self):
        self.http = httplib2.Http()
        self.auth = {}

    def authenticate_mex(self, token):
        self.auth = { 'Mex' : token}

    def authenticate_basic(self, user, pwd):
        import base64
        auth = "Basic " + base64.encodestring("%s:%s" % (user, pwd) ).strip()
        self.auth = { 'Authorization' : auth }

    def prepare_headers(self, user_headers):
        """
        """
        headers = {}
        headers.update (self.auth)
        if user_headers:
            headers.update (user_headers)
        return headers

    def prepare_url (self, url, **params):
        split_url = list( urlparse.urlsplit(url))
        p = parse_qs(split_url[3])
        # Needs to be a list of values i.e. { k:[v] }
        p.update(dict([ (k,[v]) for k,v in params.items()]))
        split_url[3] = make_qs(p)
        url = urlparse.urlunsplit(split_url)
        return url
    
    def fetch(self, url, headers = None):
        headers = self.prepare_headers(headers)
        log.debug("FETCH %s req  header=%s" %  (url, headers))
        header, content = self.http.request(url, headers = headers)
        log.debug("FETCH resp %s, content=%s" % (header, content))
        return content

    def post(self, url, content=None, files=None, headers=None, method="POST"):
        headers = self.prepare_headers(headers)
        log.debug("POST %s req %s, content=%s" % (url, headers, content))
        header, content = self.http.request(url,
                                            headers = headers,
                                            body=content,
                                            method=method)

        log.debug("POST resp %s, content=%s" % (header, content))
        return content


class BQSession(object):
    """Top level Bisque communication object
    """
    def __init__(self):
        self.c = BQServer()
        self.mex = None
        self.services  = {}
        self.new = set()
        self.dirty = set()
        self.deleted = set()


        
    ############################
    # Establish a bisque session
    def init_local(self, user, pwd, moduleuri=None, bisque_root=None):
        """Create a session mex """
        self.bisque_root = bisque_root

        self.c.authenticate_basic(user, pwd)
        self._load_services()

        
        mex = BQMex()
        mex.module = moduleuri
        mex.status = 'RUNNING'
        self.mex = self.save(mex, url=self.service_url('module_service', 'mex'))

        return self

    def init_mex(self, mex_url, auth_token, bisque_root= None):
        self.c.authenticate_mex(auth_token)
        if bisque_root is None:
            mex_tuple = list(urlparse.urlparse (mex_url))
            mex_tuple[2:5] = '','',''
            bisque_root = urlparse.urlunparse(mex_tuple)
            
        self.bisque_root = bisque_root
        self._load_services()
        self.mex = self.load (mex_url, view='deep')
        return self

    def close(self):
        pass

    def fetchxml (self, url, **params):
        """Fetch an xml object from the url

        @param url: A url to fetch from
        @param params: params will be added to url
        """
        url = self.c.prepare_url (url, **params)

        log.debug('fetchxml %s ' % url)
        try:
            content =  self.c.fetch (url, headers = {'Content-Type':'text/xml', 'Accept':'text/xml'})
            return etree.XML(content)
        except:
            log.exception('during fetch of %s %s' % (url, params))
            return None
    
    def postxml(self, url, xml, method="POST", **params):
        log.debug('postxml %s  content %s ' % (url, xml))
        content = etree.tostring(xml)
        url = self.c.prepare_url(url, **params)
        try:
            content =  self.c.post(url, content=content, method=method,
                                   headers = {'Content-Type':'text/xml', 'Accept': 'text/xml' })
            return etree.XML(content)
        except:
            log.exception('during post %s of %s ' % (url, xml))
            return None


    def service_url(self, service_type, path = "" , query = None):
        root = self.service_map[service_type]
        if query:
            path = "%s?%s" % (path, urllib.urlencode(query))
        return urlparse.urljoin(root, path)

    def _load_services (self):
        services = self.load (self.bisque_root + "/services")
        smap = {}
        for service in services.tags:
            smap [ service.type ] = service.value
        self.service_map = smap

    

    ##############################
    # Mex
    ##############################
    def update_mex(self, status, tags = [], gobjects = [], reload=True):
        """save an updated mex with the addition
        
        :param status:  The current status of the mex
        :param tags: list of etree.Element|BQTags|dict objects of form { 'name': 'x', 'value':'z' }
        :param gobjects: same as etree.Element|BQGobject|dict objects of form { 'name': 'x', 'value':'z' }
        """
        self.mex.value = status
        mex = toXml(self.mex)
        def append_mex (mex, type_, elems):
            for tg in elems:
                if isinstance(tg, dict):
                    tg = d2xml({ type_ : tg})
                elif isinstance(tg, BQNode):
                    tg = toXml(tg)
                elif isinstance(tg, etree._Element):
                    pass
                else:
                    raise BQException('bad values in tag/gobject list %s' % tg)
                mex.append(tg)

        append_mex(mex, 'tag', tags)
        append_mex(mex, 'gobject', gobjects)

        #mex = { 'mex' : { 'uri' : self.mex.uri,
        #                  'status' : status,
        #                  'tag' : tags, 
        #                  'gobject': gobjects }}
        content = self.postxml(self.mex.uri, mex, view='deep')
        if reload and content is not None:
            self.mex = fromXml(content, session = self)
            return self.mex
        return None

    def finish_mex(self, status = "FINISHED", tags=[], gobjects=[], msg=None ):
        if msg is not None:
            tags.append( { 'name':'message', 'value': msg })
        return self.update_mex(status, tags, gobjects, reload=False)
                          
    def fail_mex (self, msg):
        self.finish_mex(status='FAILED', msg=msg)

    def _begin_mex (self, moduleuri):
        """create a mex on the server for this run"""


    
    ##############################
    # Low-level save
    ##############################
    def load(self,url, **params):
        """Load a bisque object
        """
        #if view not in url:
        #    url = url + "?view=%s" % view
        xml = self.fetchxml(url, **params)
        if xml.tag == "response":
            xml = xml[0]
        bqo  = fromXml(xml, session=self)
        return bqo

    def save(self, bqo, url=None, **kw):
        if url is None and bqo.uri:
            url = bqo.uri
        xml =  toXml(bqo)
        content = self.postxml(url, xml, **kw)
        if content is not None:
            return fromXml(content, session=self)
        return None




