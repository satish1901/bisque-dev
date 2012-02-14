# -*- mode: python -*-
"""Main server for data_service}
"""
import os
import logging
import pkg_resources
import tg

from pylons.i18n import ugettext as _, lazy_ugettext as l_
from lxml import etree
from tg import expose, flash
from repoze.what import predicates 


from bq.core.service import ServiceController
from bq.data_service.model  import dbtype_from_tag, dbtype_from_name, all_resources
from bq.util.bisquik2db import bisquik2db, load_uri, db2tree, updateDB


from bisquik_resource import BisquikResource
from resource_query import resource_query, resource_count
from formats import find_formatter 


log = logging.getLogger("bq.data_service")
class data_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "data_service"

    def __init__(self, url):
        super(data_serviceController, self).__init__(url)
        self.children = {}
        
    def get_child_resource(self, token):
        child = self.children.get (token, None)
        if not child:
            child = BisquikResource (token, self.url)
            self.children[token]= child
        return child

    @expose('bq.data_service.templates.resources', content_type='text/xml') #format='xml',
    def index(self):
        resources = all_resources()
        view = None
        resources =[ self.makeurl(str(r)) for r in resources]
        return dict(resources=resources, view=view)

    @expose()
    def _default(self, *path, **kw):
        log.debug ('headers:'+ str(tg.request.headers))
        path = list(path)
        token = path.pop(0)
        resource_controller = self.get_child_resource (token)
        return resource_controller.default (*path, **kw)

    #################################################################
    #################################################################
    # program access
    # Uses etree nodes as internal format

    def new_image(self, **kw):
        ''' place the data file in a local '''
        for k,v in kw.items():
            kw[k] = str(v)
        img = etree.Element ('image', kw)
        resource = bisquik2db (doc=img)
        img = db2tree (resource, baseuri= self.url)
        log.debug ("new image " + etree.tostring(img))
        return img

    def append_resource(self, resource, tree=None, **kw):
        '''Append an element to resource (a node)
        '''
        if isinstance (resource, etree._Element):
            uri = resource.get ('uri')
            resource = load_uri (uri)
        dbresource = bisquik2db(doc=tree, parent=resource)
        #session.save(dbresource)
        #session.flush()

    def new_resource(self, resource, parent=None, **kw):
        '''Create a new resouce in the local database based on the
        resource tree given.
        '''
        log.debug ("new_resource")
        view = kw.pop('view', None)
        if isinstance(resource, str) or isinstance(resource, unicode):
            log.debug ('attributes= %s ' % str(kw) )
            resource = etree.Element (resource, **kw)
            log.debug ('created %s ' % etree.tostring (resource))
        node = bisquik2db(doc = resource, parent = parent)
        result =  db2tree (node, baseuri=self.url, view=view)
        log.debug ("new resouce = %s" % etree.tostring (result))
        return result

    def query(self, resource_tag, tag_query=None, view=None, **kw):
        '''Query the local database with expr'''
        resource_type = dbtype_from_tag(resource_tag)
        nodelist = resource_query (resource_type, tag_query=tag_query, **kw)
        response  = etree.Element ('response')
        db2tree (nodelist, parent=response,
                 view=view, baseuri = self.url)

        #log.debug ("DS: " + etree.tostring(response))
        return response

    def retrieve (self, resource_tag, token):
        view=kw.pop('view', None)
        resource_type = dbtype_from_tag(resource_tag)
        log.debug ('retrieving type ' + str(resource_type))
        nodes =  resource_load(resource_type, id = int(token))
        response  = etree.Element ('response')
        db2tree (nodes, parent=response, view=view, baseuri = self.url)
        log.debug("tree converted: %s" % view)
        #log.debug("tree converrted: %s" % etree.tostring(response))

        return response

    def load (self, resource_url, **kw):
        """Simulate a webfetch """
        log.debug ('parsing ' + resource_url)
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
        log.debug ('passing to self.default ' + str(path[2:]) + str(kwargs) )

        format = kwargs.pop('format', None)
        view  = kw.pop('view', None)

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
                resource = resource_load (resource_type, id=int(token))
            if path:
                parent = resource

        response = etree.Element('response')
        if resource is None:
            if view == "count":
                count = resource_count(resource_type, parent=parent, **kwargs)
                xtag = resource_type.xmltag
                etree.SubElement(response, xtag, count = count)
            else:
                resource = resource_query(resource_type,
                                          parent=parent, **kwargs)

        if view != "count":
            tree = db2tree(resource, baseuri=self.url, parent=response, **kwargs)
        
        formatter, content_type  = find_formatter (format)
        return formatter(response)
        
    def count(self, resource_tag, tag_query=None, **kw):
        log.debug('count %s %s' % (resource_tag, tag_query))
        resource_type = dbtype_from_tag(resource_tag)
        return resource_count (resource_type, tag_query, **kw)


    def update(self, resource_tree, replace_all=False, **kw):
        view=kw.pop('view', None)
        if replace_all:
            uri = resource_tree.get ('uri') 
            r = load_uri(resource_tree.get('uri'))
            r.clear()
        r = bisquik2db(doc=resource_tree)
        #response  = etree.Element ('response')
        return db2tree (r, parent=None, view=view, baseuri = self.url)
    
def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  data_serviceController(uri)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'data_service', 'public'))]

def get_model():
    from bq.data_service import model
    return model

__controller__= data_serviceController
