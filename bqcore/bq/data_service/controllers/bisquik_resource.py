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

import  pylons 
from pylons.controllers.util import abort
from sqlalchemy import desc
from sqlalchemy.orm import Query
import tg
from tg import controllers, redirect, expose, response
from tg import require
from tg.controllers import CUSTOM_CONTENT_TYPE

from lxml import etree

from repoze.what.predicates import not_anonymous


from bq.core import identity
from bq.core.model import metadata, DBSession 
from bq.data_service.model  import Taggable, Image, dbtype_from_tag, dbtype_from_name, all_resources
from bq.util.bisquik2db import bisquik2db, db2tree

from resource import Resource
from resource_query import resource_query, resource_load, resource_count, resource_auth, resource_permission
from resource_query import RESOURCE_READ, RESOURCE_EDIT

log = logging.getLogger("bq.data_service.bisquik_resource")

from formats import find_formatter 

class ResourceAuth(Resource):

    def __init__(self, baseuri):
        self.baseuri = baseuri
    def force_dbload(self, item):
        if item and isinstance(item, Query):
            item = item.first()
        return item

    def create(self, **kw):
        return int
    
    def dir(self, **kw):
        format = kw.pop('format', None)
        view = kw.pop('view', None)
        resource = self.force_dbload(self.parent)
        log.info ("AUTH %s" % resource)
        auth = resource_auth (resource, parent = None)
        response = etree.Element('resource', uri="%s%s/auth" % (self.baseuri, resource.uri))
        tree = db2tree (auth,  parent = response, view=view,baseuri=self.baseuri)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)

    def replace_all(self, resource, xml, **kw):
        return self.new (None, xml, **kw)
    def replace(self, resource, xml, **kw):
        return self.new (None, xml, **kw)
    def modify(self, factory, xml, **kw):
        return self.new (factory, xml, **kw)
    
    def new(self, factory,  xml, **kw):
        format = None
        resource = self.force_dbload(self.parent)
        log.debug ("AUTH %s with %s" % (resource, xml))
        resource = self.force_dbload(resource)
        resource = resource_auth (resource, parent = None, action=RESOURCE_EDIT, newauth=etree.XML(xml))
        response = etree.Element('resource')
        tree = db2tree (resource,  parent = response, baseuri=self.baseuri)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)




class BisquikResource(Resource):
    """Provide access to the data server.  Exposes a RESTful
    interface to database resources (as found in tag_model
    """
    children = dict()
    cache = True

    @classmethod
    def get_child_resource(cls, token):
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
            #self.resource_type = dbtype_from_tag(table)
            self.resource_type = dbtype_from_name(table)
            self.children['auth'] = ResourceAuth(url)
    
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
        return resource_load(self.resource_type, id=int(token), action=RESOURCE_READ)

    def load_parent(self, parent = None, action=RESOURCE_READ):
        parent = getattr(self, 'parent', parent)
        return self.force_dbload(parent)

    def check_access(self, query, action=RESOURCE_READ):
        if  action == RESOURCE_EDIT and not identity.not_anonymous():
            abort(401)
        
        if query and isinstance(query, Query):
            query = resource_permission(query, action=action)
        else:
            #   Previously loaded resource .. recreate query but with
            #   permission check
            #query = resource_load (self.resource_type, query.id)
            query = resource_load ((query.xmltag, query.__class__), query.id)
            query = resource_permission (query, action=action)
            
        resource = self.force_dbload(query)
        if resource is None:
            log.info ("Permission check failure %s" % str(query))
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        #log.debug ("PERMISSION: user %s : %s" % (user_id, resource))
            
        return resource

    def resource_output (self, resource, response=None, view=None, 
                         format=None, progressive=False, **kw):
        #if response is None:
        if isinstance(resource , list):
            response = etree.Element('response')
            db2tree (resource, view = view, parent = response, 
                     baseuri=self.baseurl)
        else:
            response = db2tree (resource, view = view, parent = response, 
                                baseuri=self.baseurl)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)
        

    def dir(self, **kw):
        """GET /ds/images : fetch group of object 

        Create a listing of the resource.  Several options are allowed
        view={normal,full,deep},
        tags=tag expression i.e. [TAG:]VAL [AND|OR [TAG:]VAL]+
        xxx=val match an attribute on the resorce
        """
        view  = kw.pop('view', None)
        tag_query = kw.pop('tag_query', '')
        tag_order = kw.pop('tag_order', '')
        wpublic = kw.pop('wpublic', None)
        format = kw.pop('format', None)
        offset = int(kw.get ('offset', 0))
        progressive = kw.pop('progressive', False)
        log.info ('DIR  %s' % (self.browser_url))
        #  Do not use loading 
        parent = getattr(self,'parent', None)

        if view=='count':
            count = resource_count(self.resource_type,
                                   parent = parent,
                                   user_id = self.user_id,
                                   tag_query = tag_query,
                                   tag_order = tag_order,
                                   wpublic = wpublic,
                                   **kw)
            xtag = self.resource_type[1].xmltag
            response = etree.Element ('resource')
            etree.SubElement(response, xtag, count = str(count))
        else:
            resources = resource_query (self.resource_type,
                                        parent=parent,
                                        user_id=self.user_id,
                                        tag_query = tag_query,
                                        tag_order = tag_order,
                                        wpublic = wpublic,
                                        **kw)
            #log.debug ("DIR query " + str(resources))
            response = etree.Element('resource', uri=str(tg.request.url))
            db2tree (resources,
                     parent=response,
                     view=view,
                     baseuri = self.baseurl,
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
        """POST /ds/images : Create a reference to the image in the local database
        POST /ds/images/12/tags
        """
        view=kw.pop('view', None)
        format = kw.pop('format', None)
        log.info ("NEW: %s %s " %(self.browser_url, xml) )
        
        # Create a DB object from the document.
        if  not identity.not_anonymous():
            pylons.response.status_int = 401    
            return '<response status="FAIL">Permission denied</response>'

        parent = self.load_parent()
        if parent:
            parent = self.check_access(parent, RESOURCE_EDIT)
        resource = bisquik2db(doc=xml, parent = parent)
        log.info ("NEW: => %s " %(str(resource)) )
        if resource is not None:
            return self.resource_output(resource, view=view,format=format)
        return "<response>FAIL</response>"

    @expose(content_type='text/xml') #, accept_format="text/xml")
    #@identity.require(identity.not_anonymous())
    def replace_all(self, resource,  xml, **kw):
        '''PUT /ds/image/1/gobjects  --> Replace contents of gobjects with doc
        '''
        log.info ('REPLACE_ALL %s %s' % (self.browser_url, xml))
        resource = self.check_access(resource, RESOURCE_EDIT)
        parent = self.load_parent()
        if parent:
            log.info('REPLACE ' + self.resource_name + " in " + str(parent))
            parent.clear([ self.resource_name ])
            log.debug ("replace: %s => %s" %(xml, str(resource)))
            resource = bisquik2db(doc=xml, parent = parent)
            if resource is not None:
                return self.resource_output(resource, **kw)
        return "<response>FAIL</response>"

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def delete_all(self, **kw):
        """delete a container of objects
        DELETE /ds/images/1/gobjects
        """
        log.info ('DELETE_ALL %s' % (self.browser_url))
        resource = self.check_access(resource, RESOURCE_EDIT)

        parent = self.load_parent()
        parent.clear([self.resource_name])
        return "<response/>"
        
        
    @expose()
    def get(self, resource, **kw):
        """GET /ds/images/1 : fetch the resource
        """
        log.info ('GET  %s' % (self.browser_url))
        view=kw.pop('view', None)
        format = kw.pop('format', None)
        resource = self.check_access(resource)
        log.info ("GET ==>%s" % str(resource))
        
        return self.resource_output(resource, view=view, format=format)
            

    @expose(content_type='text/xml') #, format='xml')
    def modify(self, resource, xml, **kw):
        '''PUT /ds/image/1  --> Replace all contents with doc
        '''
        view=kw.pop('view', None)
        log.info ('MODIFY %s %s' % (self.browser_url, xml))
        resource = self.check_access(resource, RESOURCE_EDIT)

        DBSession.autoflush = False
        #old = resource.clear()
        #pdb.set_trace()
        parent = self.load_parent()
        resource = bisquik2db (doc=xml, resource=resource, parent=parent, replace=True)
        #log.debug ("OLD values %s no parent %s " % (old, [ x for x in old if x.parent_id is None ]))
        log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
                   (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
        log.info ('MODIFY: ==> %s ' %(resource))
        return self.resource_output (resource, view=view)

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def append(self, resource, xml, **kw):
        '''POST /ds/images/1/  : append the document to the resource
        Append value of the resource based on the args
        '''
        log.info ('APPEND %s %s' % (self.browser_url, xml))
        resource = self.check_access(resource, RESOURCE_EDIT)
        #parent = self.load_parent()
        resource = bisquik2db (doc=xml, parent=resource) #, resource = resource)
        log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
                   (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
        #resource = session.merge (resource)
        log.info ('APPEND/update: ==> %s ' % (resource))
        return self.resource_output (resource)

    @expose(content_type="text/xml")
    #@identity.require(identity.not_anonymous())
    def delete(self, resource, **kw):
        """DELETE /ds/images/1/tags/2 : delete a specific resource
        """
        log.info ('DELETE %s' % (self.browser_url))
        resource = self.check_access(resource, RESOURCE_EDIT)
        try:
            if identity.get_user_id() == resource.owner_id:
                DBSession.delete(resource)
                return "<response/>"
        except:
            pass
        return '<response>Error in deleting resource</response>'


        
            

            
