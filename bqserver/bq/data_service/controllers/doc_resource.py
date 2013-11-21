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
import logging
import tg
import  pylons

from tg import controllers, redirect, expose, response, request
from tg import require,config

from lxml import etree
from repoze.what.predicates import not_anonymous


from bq.core import identity
#from bq.model import metadata, DBSession 
#from bq.DS.model  import Taggable, Image, dbtype_from_name, all_resources
#from bq.util.bisquik2db import bisquik2db, db2tree

#from resource import Resource
#from resource_query import db_query
#from resource_query import resource_query, resource_load, resource_count

log = logging.getLogger("bq.data_service")
from formats import find_formatter

from bq.data_service.model import BQStoreManager


#xmldb = config.get ('bisque.dburl', 'sqlxml://memory')
xmldb = config.get ('bisque.dburl', 'dbxml://docs.dbx')


class XMLDocumentResource(controllers.RestController):
    """Provide access to the data server.  Exposes a RESTful
    interface to database resources (as found in tag_model
    """

    def __init__(self):
        self.store = BQStoreManager.get_manager(xmldb)

    @expose(content_type="text/xml")
    def get_all(self, *kw):
        log.debug ("GET_ALL")
        docs = self.store.dir()
        doc = etree.Element ('resource')
        for d in docs:
            etree.SubElement (doc, 'doc', name=d )
        return etree.tostring(doc)

    @expose(content_type="text/xml")
    def post(self, *path, **kw):
        docid = "/".join ([''] + list (path))
        xml = request.body_file.read()
        log.debug ("POST %s %s " % (str(path), xml))
        if len(path)==0:
            doc = self.store.create (xml)
            return str(doc)
        doc, elem = self.store.update(docid, xml)
        return etree.tostring(elem)
    
    @expose(content_type="text/xml")
    def get(self, *path, **kw):
        docid = "/".join ([''] + list (path))
        log.debug ("GET %s " % docid)

        view  = kw.pop('view', None)
        tag_query = kw.pop('tag_query', '').strip('"')
        tag_order = kw.pop('tag_order', '')
        wpublic = kw.pop('wpublic', None)
        format = kw.pop('format', None)
        offset = int(kw.get ('offset', 0))
        progressive = kw.pop('progressive', False)

        doc, elem = self.store.fetch (docid)

        if doc is None:
            elem = etree.Element('resource')

        log.debug ("doc %s # %s " % (doc, elem))
            
        return etree.tostring(elem)
    
    @expose(content_type="text/xml")
    def put(self, *path, **kw):
        docid = "/".join ([''] + list (path))
        xml = request.body_file.read()
        log.debug ("PUT %s <- %s" % (docid, xml))
        doc, elem = self.store.update(docid, xml)
        return etree.tostring(elem)
        

    @expose(content_type="text/xml")
    def delete(self, *path, **kw):
        log.debug ("DELETE %s " % str(path))
        self.store.delete(path)
        return ""


class OLDSTUFF():
    children = dict()

    @classmethod
    def get_child_resource(cls, token):
        child = cls.children.get (token, None)
        if not child:
            child = XMLDocumentResource (token, url=cls.baseurl)
            cls.children[token]= child
        return child

    def __init__(self, table = None, url = None):
        self.__class__.baseurl = self.baseurl = url
        self.resource_name = table
        if table:
            self.resource_type = dbtype_from_name(table)
    
    def error(self, tg_errors=None):
        return tg_errors

    def create(self, **kw):
        """Create a new empty element at this point"""
        return store.new (self.path)

    def load(self, token):
        """Load the document or element at the path"""
        return store.fetch(self.path)

    def force_dbload(self, item):
        if item and isinstance(item, Query):
            item = item.first()
        return item
        
    
    def load_parent(self, parent = None):
        parent = getattr(self, 'parent', parent)
        return self.force_dbload(parent)

    @expose(content_type="application/xml")
    def dir(self, **kw):
        """Create a listing of the resource.  Several options are allowed
        view={normal,full,deep},
        tags=tag expression i.e. [TAG:]VAL [AND|OR [TAG:]VAL]+
        xxx=val match an attribute on the resorce
        """
        
        view  = kw.pop('view', None)
        tag_query = kw.pop('tag_query', '').strip('"')
        tag_order = kw.pop('tag_order', '')
        wpublic = kw.pop('wpublic', None)
        format = kw.pop('format', None)
        offset = int(kw.get ('offset', 0))
        progressive = kw.pop('progressive', False)
        log.debug ("DIR")
        #  Do not use loading 
        parent = getattr(self,'parent', None)

        result = store.tag_query (tag_query, tag_order, view,
                                  document = self.document)

        response = etree.Element ('resource')
        if view=='count':
            xtag = self.resource_type[1].xmltag
            etree.SubElement(response, xtag, count = str(result))
        else:
            response.append(result.root())
        
        return formatter(response)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        
        return formatter(response)


    @expose(content_type='text/xml') # accept_format="text/xml")
    #@require(not_anonymous())
    def new(self, factory,  xml, **kw):
        '''Create a reference to the image in the local database'''
        # Create a DB object from the document.
        if  not not_anonymous():
            abort (401)

        doc = store.new(self.path, xml, self.parent.document)
        return doc.read()

    @expose(content_type='text/xml') #, accept_format="text/xml")
    #@identity.require(identity.not_anonymous())
    def replace_all(self, resource,  xml, **kw):
        '''PUT /ds/image/1/gobjects  --> Replace contents of gobjects with doc
        '''
        resource = store.replace (self.path, xml)
        
        resource = self.force_dbload(resource)
        parent = self.parent.document
        if parent:
            log.debug('REPLACE ' + self.resource_name + " in " + str(parent))
            parent.clear([ self.resource_name ])
            DBSession.flush() #?Needed?
            log.debug ("replace: %s => %s" %(xml, str(resource)))
            bisquik2db(doc=xml, parent = parent)
            return self.get(resource, **kw)
        return "<response>FAIL</response>"

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def delete_all(self, **kw):
        log.debug("delete_all " )
        store.delete (self.path)
        return "<response/>"
        
        
    @expose()
    def get(self, resource, **kw):
        log.debug ('GET: %s' %(resource))
        view=kw.pop('view', None)
        format = kw.pop('format', None)
        resource =  store.fetch (self.path, view=view)
        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type']  = content_type
        return formatter(resource)
            

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def modify(self, resource, xml, **kw):
        """PUT /ds/image/1  --> Replace all contents with doc
           Change the value of the resource based on the args"""
        

        store.replace (self.path, xml)
        #parent = self.load_parent()
        resource = self.force_dbload(resource)
        log.debug ('MODIFY: %s <- %s ' %( str (resource),  xml ))
        resource.clear()
        DBSession.flush()
        bisquik2db (doc=xml, parent=resource)
        log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
                   (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
        DBSession.flush()
        return self.get(resource, **kw)

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def append(self, parent_resource, xml, **kw):
        '''Append value of the resource based on the args'''
#        if  not identity.not_anonymous():
#            cherrypy.response.status = 401    
#            return "<response>FAIL</response>"
        log.debug ('APPEND/update: ' + xml)
        parent = self.load_parent(parent_resource)
        resource = bisquik2db (doc=xml, parent=parent)
        log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
                   (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
        DBSession.flush()
        return self.get(resource, **kw)

    @expose(content_type="application/xml")
    #@identity.require(identity.not_anonymous())
    def delete(self, resource, **kw):
        resource = self.force_dbload(resource)
        log.debug("DELETE %s (%s) by (%s)" % (str(resource), resource.owner_id, identity.get_user_id()))
#        if  not identity.not_anonymous():
#            cherrypy.response.status = 401    
#            return "<response>FAIL</response>"

        try:
            if identity.get_user_id() == resource.owner_id:
                DBSession.delete(resource)
                #DBSession.flush()
                return "<response/>"
        except:
            pass
        return '<response>Error in deleting resource</response>'
            

    def get_last_modified_date(self, resource=None):
        """ returns the last modified date of the resource. """
        return store.modified (self, resource)

    def get_entity_tag(self, resource=None):
        return md5.new(str(self.get_last_modified_date(resource))).hexdigest()

        # Calculate a deep etag on container
        
            
        
            
