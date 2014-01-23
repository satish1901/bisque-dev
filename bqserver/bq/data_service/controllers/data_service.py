###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
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

  Data server for local database

"""
import os
import logging
import pkg_resources
import urlparse
import tg

# pylint: disable=E0611
# pylint: disable=E1103

from pylons.i18n import ugettext as _, lazy_ugettext as l_
from lxml import etree
from tg import expose, flash, config
from repoze.what import predicates

from bq.core.service import ServiceController
from bq.data_service.model  import dbtype_from_tag, dbtype_from_name, all_resources
from bq.util.bisquik2db import bisquik2db, load_uri, db2tree, updateDB, parse_uri
from bq.exceptions import BadValue
from bq.core import identity
from bq.util.paths import data_path
from bq.util.urlutil import strip_url_params
from bq.util.hash import make_uniq_code, is_uniq_code

from .bisquik_resource import BisquikResource, force_dbload, check_access
from .resource_query import resource_query, resource_count, resource_load, resource_delete, resource_types, resource_auth
from .resource_query import RESOURCE_READ, RESOURCE_EDIT
from .resource import HierarchicalCache
from .formats import find_formatter
from .doc_resource import XMLDocumentResource
cachedir = config.get ('bisque.data_service.server_cache', data_path('server_cache'))



log = logging.getLogger("bq.data_service")
class DataServerController(ServiceController):
    service_type = "data_service"

    doc = XMLDocumentResource ()

    def __init__(self, url = None):
        super(DataServerController, self).__init__(url)
        self.children = {}
        self.server_cache = HierarchicalCache(cachedir)

    def get_child_resource(self, token, **kw):
        child = self.children.get (token, None)
        if not child:
            child = BisquikResource (token, self.url, **kw)
            self.children[token]= child
        return child

    @expose(content_type='text/xml')
    def index(self):
        #resources = all_resources()
        resource = etree.Element('resource')
        for r in resource_types():
            etree.SubElement(resource, 'resource', name = str(r), uri = self.makeurl(str(r)))

        return etree.tostring(resource)

    @expose()
    def _default(self, *path, **kw):
        #log.debug ('headers:'+ str(cherrypy.request.headers))
        path = list(path)
        log.info ("path = %s %s " , path, kw)
        token = path.pop(0)
        if is_uniq_code(token):
            log.debug('using uniq token')
            resource_controller = self.get_child_resource('taggable')
            path.insert(0,token)
        else:
            resource_controller = self.get_child_resource (token)
        return resource_controller._default (*path, **kw)


    #################################################################
    #################################################################
    # program access
    # Uses etree nodes as internal format
    def cache_check(self, url, user_id=None, **kw):
        args = [ "%s=%s" % (k, v) for k,v in kw.items()]
        full_url = "%s?%s" % (url, "&".join (args))
        if user_id is None and identity.not_anonymous():
            user_id = identity.get_user_id()
        log.debug ("CACHE CHECK url %s" , full_url)
        header, response = self.server_cache.fetch(full_url, user_id)
        return response

    def cache_save(self, url, user_id=None, response=None, **kw):
        args = [ "%s=%s" % (k, v) for k,v in kw.items()]
        full_url = "%s?%s" % (url, "&".join (args))
        log.debug ("CACHE SAVE url %s" , full_url)
        if user_id is None and identity.not_anonymous():
            user_id = identity.get_user_id()
        self.server_cache.save (full_url, {'Content-Type':'text/xml'}, response, user_id)
    def cache_invalidate(self, url, user_id=None):
        if user_id is None and identity.not_anonymous():
            user_id = identity.get_user_id()
        self.server_cache.invalidate(url, user_id)

    def resource_uniq(self, **kw):
        'generate a unique code to be used for a resource'
        return make_uniq_code()

    def new_image(self, resource = None, **kw):
        ''' place the data file in a local '''

        if resource is not None and resource.tag != 'image':
            raise BadValue('new_image resource must be an image: received %s' % resource.tag)

        if resource is None:
            resource = etree.Element ('image')
        for k,v in kw.items():
            resource.set (k, str(v))
        resource = bisquik2db (doc=resource)
        img = db2tree (resource, baseuri= self.url)
        #log.debug ("new image " + etree.tostring(img))
        # Invalidate the top level container i.e. /data_service/images
        self.cache_invalidate(img.get('uri').rsplit('/', 1)[0])
        return img

    def append_resource(self, resource, tree=None, **kw):
        '''Append an element to resource (a node)
        '''
        if isinstance (resource, etree._Element):
            uri = resource.get ('uri')
            resource = load_uri (uri)
        dbresource = bisquik2db(doc=tree, parent=resource)
        r =  db2tree (dbresource, baseuri=self.url, **kw)
        self.cache_invalidate(r.get('uri'))
        return r

    def new_resource(self, resource, parent=None, **kw):
        '''Create a new resouce in the local database based on the
        resource tree given.
        '''
        view = kw.pop('view', None)
        if isinstance(resource, basestring):
            log.debug ('attributes= %s ' , kw )
            resource = etree.Element (resource, **kw)
            log.debug ('created %s ' , resource)
        if parent is None:
            resource.set('resource_uniq', self.resource_uniq())
        node = bisquik2db(doc = resource, parent = parent)
        log.debug ("new_resource %s" , node)
        r =  db2tree (node, baseuri=self.url, view=view)
        # Invalidate the top level container i.e. /data_service/<resource_type>
        self.cache_invalidate(r.get('uri').rsplit('/', 1)[0])
        return r

    def get_resource(self, resource, **kw):
        uri = None
        if isinstance (resource, etree._Element):
            uri = resource.get ('uri')
        elif isinstance(resource, basestring):
            uri,params = strip_url_params(resource)
            params.update(kw)
            kw = params
        #log.debug ("get_resource %s %s",  uri, str(kw))
        if uri is not None:
            response =  self.cache_check(uri, **kw)
            if response:
                log.debug ("get_resource:CACHE response")
                xml =  etree.XML (response)
                return xml
            else:
                net, name, ida, rest = parse_uri(uri)
                resource = load_uri (uri)
                if rest:  # Fetch resource is really a query
                    resource = self.query(resource_tag=rest[-1], parent=resource,**kw)
                    #self.cache_save (uri, response=etree.tostring(resource), **kw)
                    return resource
        xtree = db2tree(resource, baseuri = self.url, **kw)
        uri = uri or xtree.get('uri')
        self.cache_save (uri, response=etree.tostring(xtree), **kw)
        return xtree


    def del_resource(self, resource, **kw):
        uri = None
        if isinstance (resource, etree._Element):
            uri = resource.get ('uri')
        elif isinstance(resource, basestring):
            uri = resource
        if uri is not None:
            resource = load_uri (uri)
        resource_delete(resource)
        self.cache_invalidate(uri)

    def update_resource(self, resource, new_resource=None, replace=True, **kw):
        """update a resource with a new values
        @param resource: an etree element or uri
        @param new_resource:  an etree element if resource is a uri
        @param replace: replace all members (if false then appends only)
        @param kw: view parameters for return
        """

        uri = None
        log.debug ('resource  = %s' ,  resource)
        if isinstance (resource, etree._Element):
            uri = resource.get ('uri')
        elif isinstance(resource, basestring):
            uri = resource
            if new_resource is None:
                raise BadValue('update_resource uri %s needs new_value to update  ' % uri )
        if uri is not None:
            resource = load_uri (uri)
        log.debug ('resource %s = %s' , uri, resource)
        r = bisquik2db(doc=new_resource, resource=resource, replace=replace)
        #response  = etree.Element ('response')
        r =  db2tree (r, baseuri = self.url, **kw)
        self.cache_invalidate(r.get('uri'))
        return r

    def update(self, resource_tree, replace_all=False, **kw):
        view=kw.pop('view', None)
        #if replace_all:
        #    uri = resource_tree.get ('uri')
        #    r = load_uri(resource_tree.get('uri'))
        #    r.clear()
        r = bisquik2db(doc=resource_tree, replace=replace_all)
        #response  = etree.Element ('response')
        r =  db2tree (r, parent=None, view=view, baseuri = self.url)
        self.cache_invalidate(r.get('uri'))
        return r


    def auth_resource(self, resource, action=RESOURCE_READ, auth=None, notify=False, **kw):
        if isinstance(resource, basestring):
            uri = resource
        elif isinstance (resource, etree._Element):
            uri = resource.get ('uri')
        resource = load_uri (uri)
        auth = resource_auth(resource, parent=None, action=action, newauth=auth, notify=notify)
        response = etree.Element ('resource')
        db2tree(auth, parent=response, view=None, baseuri=self.url)
        return response



    def query(self, resource_tag = None,  parent=None, **kw):
        '''Query the local database with expr'''
        resource_type = dbtype_from_tag(resource_tag)
        uri = "%s%s/%s" % (self.url, parent and parent.uri or '', resource_tag or '')

        #log.debug ("query parent=%s tag=%s %s", parent, resource_tag, str(kw))
        response = self.cache_check (uri, **kw)
        if response:
            xml =  etree.XML (response)
            return xml

        if isinstance (parent, etree._Element):
            parent = parent.get ('uri')
        if isinstance(parent, basestring):
            parent = load_uri(parent)
        params = kw.copy()
        view = params.pop('view', None)
        if view == 'count':
            count = resource_count (resource_type,  parent=parent,**params)
            response = etree.Element ('resource')
            etree.SubElement(response, resource_tag, count = str(count))
        else:
            nodelist = resource_query (resource_type, parent=parent, **params)
            full_url = "%s?%s" % (uri, "&".join ("%s=%s" % (k, v) for k,v in kw.items()))
            response  = etree.Element ('resource', uri=full_url)
            db2tree (nodelist, parent=response,
                     view=view, baseuri = self.url)

        self.cache_save (uri, response=etree.tostring(response), **kw)
        #log.debug ("DS: " + etree.tostring(response))
        return response

    def load (self, resource_url, **kw):
        """Simulate a webfetch """
        log.debug ('parsing %s' , resource_url)
        #if resource_url.startswith(self.url):
        url = urlparse.urlsplit (resource_url)
        if url[3]:
            kwargs = dict ([p.split('=') for p in url[3].split('&')])
            kwargs.update (kw)
        else:
            kwargs = kw
        serverpath = urlparse.urlsplit(self.url)[2]
        commonurl = os.path.commonprefix ([serverpath, url[2]])
        requesturl =  url[2][len(commonurl):]
        path = requesturl.split ('/')
        # remove initial /ds
        log.debug ('path server(%s) req(%s) common( %s)' , serverpath,url[2],path )
        log.debug ('passing to self.default %s %s', path[2:] , kwargs )

        format = kwargs.pop('format', None)
        view  = kwargs.pop('view', None)

        parent =None
        controller = None
        while path:
            resource_type = None
            resource = None

            token = path.pop(0)
            if not token: continue

            #resource_type = dbtype_from_tag (token)
            resource_type = dbtype_from_name (token)

            if path:
                token = path.pop(0)
                resource = resource_load (resource_type, ident=int(token))
            if path:
                parent = resource

        response = etree.Element('response')
        if resource is None:
            if view == "count":
                count = resource_count(resource_type, parent=parent, **kwargs)
                xtag = resource_type[0]
                etree.SubElement(response, xtag, count = count)
            else:
                resource = resource_query(resource_type,
                                          parent=parent, **kwargs)

        if view != "count":
            tree = db2tree(resource, baseuri=self.url, view=view,
                           parent=response, **kwargs)

        formatter, content_type  = find_formatter (format)
        return formatter(response)

    def count(self, resource_tag,  **kw):
        log.debug('count %s %s' , resource_tag, kw)
        resource_type = dbtype_from_tag(resource_tag)
        return resource_count (resource_type, **kw)

    def retrieve (self, resource_tag, tag_query = None, **kw):
        view=kw.pop('view', None)
        resource_type = dbtype_from_tag(resource_tag)
        log.debug ('retrieving type %s' , resource_type)
        nodes =  resource_query(resource_type, tag_query, **kw)
        response  = etree.Element ('response')
        db2tree (nodes, parent=response, view=view, baseuri = self.url)
        log.debug("tree converted: %s" , view)
        #log.debug("tree converrted: %s" % etree.tostring(response))

        return response


def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  DataServerController(uri)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'data_service', 'public'))]

def get_model():
    from bq.data_service import model
    return model

__controller__= DataServerController
