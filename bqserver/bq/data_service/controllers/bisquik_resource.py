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
   RESTful access to DoughDB resources

"""
import pdb
import logging
import sqlalchemy
import urllib

import  pylons
import transaction
from pylons.controllers.util import abort
from paste.deploy.converters import asbool
from sqlalchemy import desc
from sqlalchemy.orm import Query

import tg
from tg import controllers, redirect, expose, response, request
from tg import require
from tg.controllers import CUSTOM_CONTENT_TYPE
from lxml import etree
from repoze.what.predicates import not_anonymous
from furl import furl

from bq.core import identity
from bq.core.model import metadata, DBSession
from bq.data_service.model  import Taggable, Image, dbtype_from_tag, dbtype_from_name, all_resources
from bq.util.bisquik2db import bisquik2db, db2tree
from bq.util.hash import make_uniq_code, is_uniq_code


from .resource import Resource
from .resource_query import resource_query, resource_load, resource_count, resource_auth, resource_permission, resource_delete, document_permission
from .resource_query import RESOURCE_READ, RESOURCE_EDIT
from .formats import find_formatter

log = logging.getLogger("bq.data_service.bisquik_resource")


#PROTECTED = [ 'module', 'mex', 'system' ]
PROTECTED = [ 'store', 'link', 'dir' ]


def force_dbload(item):
    if item and isinstance(item, Query):
        item = item.first()
    return item


def check_access(query, action=RESOURCE_READ):
    if action == RESOURCE_EDIT and not identity.not_anonymous():
        log.debug ("EDIT denied because annonymous")
        abort(401)
    if query is None:
        return None
    if  isinstance(query, Query):
        query = resource_permission(query, action=action)
    else:
        #   Previously loaded resource .. recreate query but with
        #   permission check
        #query = resource_load (self.resource_type, query.id)
        query = resource_load ((query.xmltag, query.__class__), query.id)
        query = resource_permission (query, action=action)

    resource = force_dbload(query)
    if resource is None:
        log.info ("Permission check failure %s" % query)
        if identity.not_anonymous():
            abort(403)
        else:
            abort(401)
    #log.debug ("PERMISSION: user %s : %s" % (user_id, resource))
    return resource


class PixelHandler (object):
    'redirector to image service'
    def __init__(self, baseuri):
        self.baseuri = baseuri

    def _default(self, *path, **kw):
        r = force_dbload (tg.request.bisque.parent)
        url = furl ('/image_service/%s' % r.resource_uniq)
        url.path.segments.extend (path)
        url.args = kw
        log.debug ('REDIRECT %s ' % url.url)
        redirect (base_url=url.url)


class ResourceAuth(Resource):
    'Handle resource authorization records'

    def __init__(self, baseuri):
        self.baseuri = baseuri

    def create(self, **kw):
        return int


    def dir(self, **kw):
        'Read the list of authorization records associated with the parent resource'
        #baseuri = request.url
        format = kw.pop('format', None)
        view = kw.pop('view', None)
        resource = check_access(request.bisque.parent, RESOURCE_READ)
        baseuri = self.baseuri
        log.info ("AUTH %s  %s" % (resource, request.environ))
        auth = resource_auth (resource)
        response = etree.Element('resource', uri="%s%s/auth" % (baseuri, resource.uri))
        tree = db2tree (auth,  parent = response, view=view,baseuri=baseuri)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)

    def replace_all(self, resource, xml, **kw):
        return self.new (None, xml, **kw)
    def replace(self, resource, xml, **kw):
        return self.new (None, xml, **kw)
    def modify(self, factory, xml, **kw):
        return self.new (factory, xml, **kw)

    def new(self, factory,  xml, notify=True, **kw):
        'Create/Modify resource auth records'
        format = None
        baseuri = self.uri
        #resource = force_dbload(request.bisque.parent)
        #baseuri = resource.uri
        resource = check_access( request.bisque.parent, RESOURCE_EDIT)
        log.debug ("AUTH %s with %s" % (resource, xml))
        #DBSession.autoflush = False
        resource = resource_auth (resource,  action=RESOURCE_EDIT, newauth=etree.XML(xml),
                                  notify=asbool(notify))
        response = etree.Element('resource', uri=baseuri)
        tree = db2tree (resource,  parent = response, baseuri=baseuri)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        transaction.commit()
        return formatter(response)

RESOURCE_HANDLERS = {
    'auth'   : ResourceAuth ,
    'pixels' : PixelHandler ,
}



class BisquikResource(Resource):
    """Provide access to the data server.  Exposes a RESTful
    interface to database resources (as found in tag_model
    """
    children = {}
    cache = True

    @classmethod
    def get_child_resource(cls, token):
        child_cls = RESOURCE_HANDLERS.get (token)
        if child_cls:
            return child_cls (cls.baseurl)
        child = cls.children.get (token, None)
        if not child:
            child = BisquikResource(token, url=cls.baseurl)
            cls.children[token]= child
        return child

    def __init__(self, table = None, url = None, **kw):
        super(BisquikResource, self).__init__(uri = url, **kw)
        self.__class__.baseurl = self.baseurl = url
        self.resource_name = table
        if table:
            self.resource_type = dbtype_from_tag(table)

    def error(self, tg_errors=None):
        return tg_errors

    def create(self, **kw):
        return self.resource_type

    def force_dbload(self, item):
        if item and isinstance(item, Query):
            item = item.first()
        return item

    def load(self, token, **kw):
        log.debug ("Load %s" % token)
        try:
            if is_uniq_code(token):
                return resource_load (self.resource_type, uniq = token)
            return resource_load(self.resource_type, ident=int(token))
        except ValueError, e:
            abort (404)
        except Exception:
            log.exception ('While loading:')
            abort(404)

    def load_parent(self, parent = None, action=RESOURCE_READ):
        parent = getattr(request.bisque, 'parent', parent)
        return self.force_dbload(parent)

    def check_access(self, query, action=RESOURCE_READ):
        if action == RESOURCE_EDIT and self.resource_name in PROTECTED:
            log.debug ("PROTECTED RESOURCE")
            abort(403)
        if action == RESOURCE_EDIT and not identity.not_anonymous():
            log.debug ("EDIT denied because annonymous")
            abort(401)

        if query is None:
            return None
        if  isinstance(query, Query):
            query = document_permission(query, action=action)
            log.debug ("PERMISSION:query %s" % query)
        else:
            #   Previously loaded resource .. recreate query but with
            #   permission check
            log.debug ("PERMISSION: loaded object %s %s" % ((query.xmltag, query.__class__), query.id))
            query = resource_load ((query.xmltag, query.__class__), ident=query.id)
            query = document_permission (query, action=action)

        resource = self.force_dbload(query)
        if resource is None:
            log.info ("Permission check failure %s = %s" % (query, resource))
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        #log.debug ("PERMISSION: user %s : %s" % (user_id, resource))

        return resource

    def resource_output (self, resource, response=None, view=None,
                         format=None, progressive=False, **kw):
        #if response is None:
        log.debug ("resource_outtput %s", self.uri)
        DBSession.flush()
        if isinstance(resource , list):
            response = etree.Element('resource')
            db2tree (resource, view = view, parent = response, baseuri=self.uri)
        elif resource is not None:
            response = db2tree (resource, view = view, parent = response, baseuri=self.uri, **kw)
        #transaction.commit()
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)


    def dir(self, **kw):
        """GET /ds/images : fetch group of object

        Create a listing of the resource.  Several options are allowed
        view={short,full,deep},[clean],[canonical],
        tags=tag expression i.e. [TAG:]VAL [AND|OR [TAG:]VAL]+
        xxx=val match an attribute on the resorce
        """

        view  = kw.pop('view', 'short')
        tag_query = kw.pop('tag_query', '')
        tag_order = kw.pop('tag_order', '')
        wpublic = kw.pop('wpublic', None)
        format = kw.pop('format', None)
        offset = int(kw.get ('offset', 0))
        progressive = kw.pop('progressive', False)
        permcheck = kw.pop('permcheck', None)  # disallow from web side as will be pass in kw
        #limit = kw.pop('limit', None)
        log.info ('DIR  %s %s' , request.url, self.uri)
        #  Do not use loading
        parent = getattr(request.bisque,'parent', None)
        #specials = set(['tag_names', 'tag_values', 'gob_types'])
        if kw.pop('noparent', None):
            parent = False
        user_id = identity.get_user_id()
        if parent is None and view!='count':
            if not isinstance (view, basestring):
                abort (400, "Illegal view parameter %s" % view)
            viewmap = { None: 1000000, 'short':1000000, 'full' : 10000, 'deep' : 1000 }
            maxlimit = viewmap.get (view, 10000)
            limit = kw.pop ('limit', None) or maxlimit
            limit = min(int(limit), maxlimit)
            kw['limit'] = str(limit)
            log.debug ("limiting top level to %s", limit)
        else:
            limit = None

        params = kw.copy()
        newparams = dict (view=view, offset=offset, limit=limit,
                          tag_query=tag_query, tag_order=tag_order,
                          format=format, wpublic=wpublic)
        #params.update ( [(k, unicode(v).encode('utf8') ) for k,v in newparams.items() if v ])
        params.update ( newparams)
        params = dict ( [(k, unicode(v).encode('utf8') ) for k,v in params.items() if v  ])

        request_uri = "%s?%s" % ( request.path, urllib.urlencode (params))

        if view=='count':
            limit=None
            count = resource_count(self.resource_type,
                                   parent = parent,
                                   user_id = user_id,
                                   tag_query = tag_query,
                                   tag_order = tag_order,
                                   wpublic = wpublic,
                                   **kw)
            xtag = self.resource_type[1].xmltag
            response = etree.Element ('resource', uri=request_uri)
            etree.SubElement(response, 'tag', name="count", value=str(count), type="number")
        else:
            # Never return more than 1000 items in a top level query
            resources = resource_query (self.resource_type,
                                        parent=parent,
                                        user_id= user_id,
                                        tag_query = tag_query,
                                        tag_order = tag_order,
                                        wpublic = wpublic,
                                        #limit = limit,
                                        **kw)
            response = etree.Element('resource', uri=request_uri)
            db2tree (resources,
                     parent=response,
                     view=view,
                     baseuri = self.uri,
                     progressive=progressive,
                     **kw)


        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type

        text_response =  formatter(response)
        #ex = etree.XML (text_response)
        #log.debug ("text_response %d" % len(ex) )
        return text_response


    @expose(content_type='text/xml') # accept_format="text/xml")
    #@require(not_anonymous())
    def new(self, factory,  xml, **kw):
        """POST /ds/image : Create a reference to the image in the local database
        """
        view=kw.pop('view', None)
        format = kw.pop('format', None)
        log.info ("NEW: %s %s " %(request.url, xml) )

        # Create a DB object from the document.
        #if  not identity.not_anonymous():
        #    pylons.response.status_int = 401
        #    return '<response status="FAIL">Permission denied</response>'

        parent = self.load_parent()
        log.debug ("NEW: parent %s " % parent)
        parent = self.check_access(parent, RESOURCE_EDIT)
        resource = bisquik2db(doc=xml, parent = parent)
        log.info ("NEW: => %s " % resource )
        if resource is None:
            resource = etree.Element ('resource')
            resource.text = "FAIL"
        return self.resource_output(resource, view=view,format=format)

    @expose(content_type='text/xml') #, accept_format="text/xml")
    #@identity.require(identity.not_anonymous())
    def replace_all(self, resource,  xml, **kw):
        '''PUT /ds/image/1/gobjects  --> Replace contents of gobjects with doc
        '''
        log.info ('REPLACE_ALL %s %s' % (request.url, xml))
        parent = self.load_parent()
        resource = None
        if parent:
            resource = self.check_access(parent, RESOURCE_EDIT)
            DBSession.autoflush = False
            log.info('REPLACE %s in %s' % (self.resource_name , parent))
            log.debug ("replace: %s => %s" %(xml, resource))
            # Here we clear the specific type (tag,gobject) etc. and

            parent.clear([ self.resource_name ])
            resource = bisquik2db(doc=xml, parent=parent)
        if resource is None:
            resource = etree.Element ('resource')
            resource.text = "FAIL"
        return self.resource_output(resource, **kw)

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def delete_all(self, **kw):
        """delete a container of objects
        DELETE /ds/images/1/gobjects
        """
        parent = self.load_parent()
        log.info ('DELETE_ALL %s' % (request.url))
        resource = self.check_access(parent, RESOURCE_EDIT)
        parent.clear([self.resource_name])
        #transaction.commit()
        if resource is None:
            resource = etree.Element ('resource')
        return self.resource_output(resource, **kw)

    @expose()
    def get(self, resource, **kw):
        """GET /ds/images/1 : fetch the resource
        """
        log.info ('GET  %s' , request.url)
        view=kw.pop('view', 'short')
        format = kw.pop('format', None)
        resource = self.check_access(resource)
        log.info ("GET ==>%s" % resource)

        return self.resource_output(resource, view=view, format=format, **kw)


    @expose(content_type='text/xml') #, format='xml')
    def modify(self, resource, xml, **kw):
        '''PUT /ds/image/1  --> Replace all contents with doc
        '''
        view=kw.pop('view', None)
        log.info ('MODIFY %s %s' % (request.url, xml))
        resource = self.check_access(resource, RESOURCE_EDIT)
        parent = self.load_parent()
        DBSession.autoflush = False
        old = resource.clear()
        #pdb.set_trace()
        log.debug ("MODIFY: parent=%s resource=%s" % (parent, resource))
        resource = bisquik2db (doc=xml, resource=resource, parent=parent, replace=True)
        log.info ('MODIFIED: ==> %s ' %(resource))
        return self.resource_output (resource, view=view)

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def append(self, resource, xml, **kw):
        '''POST /ds/images/1/  : append the document to the resource
        Append value of the resource based on the args
        '''

        view=kw.pop('view', None)
        log.info ('APPEND %s %s' % (request.url, xml))
        resource = self.check_access(resource, RESOURCE_EDIT)
        #parent = self.load_parent()
        resource = bisquik2db (doc=xml, parent=resource) #, resource = resource)
        log.info ('APPEND/update: ==> %s ' % (resource))
        return self.resource_output (resource, view=view)

    @expose(content_type="text/xml")
    #@identity.require(identity.not_anonymous())
    def delete(self, resource, **kw):
        """DELETE /ds/images/1/tags/2 : delete a specific resource
        """
        log.info ('DELETE %s' % (request.url))
        resource = self.check_access(resource, RESOURCE_EDIT)
        response = etree.Element ('resource')
        if resource is not None:
            uri = resource.uri
            resource_delete(resource, user_id = identity.get_user_id())
            response.set ('uri', uri)
        return self.resource_output(resource=None, response=response, **kw)


    @expose()
    def check(self, resource, **kw):
        """HEAD /ds/images/1 : Check ability to read resource
        """
        log.info ('HEAD  %s' % (request.url))
        view=kw.pop('view', 'short')
        format = kw.pop('format', None)
        resource = self.check_access(resource)
        log.info ("HEAD ==>%s" % resource)
        resource = etree.Element ('resource')
        return self.resource_output(resource, **kw)
