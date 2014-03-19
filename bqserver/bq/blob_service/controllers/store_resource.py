###############################################################################
##  Bisque                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011,2012                           ##
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
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY         ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE         ##
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR        ##
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR           ##
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,     ##
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,       ##
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR        ##
## PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF    ##
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING      ##
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS        ##
## SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.              ##
##                                                                           ##
## The views and conclusions contained in the software and documentation     ##
## are those of the authors and should not be interpreted as representing    ##
## official policies, either expressed or implied, of <copyright holder>.    ##
###############################################################################
"""
SYNOPSIS
========
blob_service


DESCRIPTION
===========
Store resource all special clients to simulate a filesystem view of resources.
"""




#import sys
import logging

from lxml import etree
from datetime import datetime
from datetime import timedelta

import tg
from tg import expose, flash, config, require, abort
from tg.controllers import RestController, TGController

from bq.core.identity import set_admin_mode
#from bq.core.service import ServiceMixin
#from bq.core.service import ServiceController
from bq.core import  identity
from bq.exceptions import IllegalOperation, DuplicateFile, ServiceError
from bq.util.timer import Timer
from bq.util.compat import OrderedDict
from bq.util.dotnested import parse_nested

from bq import data_service

from . import blob_storage


log = logging.getLogger('bq.blobs.store_resource')

def load_stores():
    stores = OrderedDict()
    store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ]
    log.debug ('requested stores = %s' , store_list)
    for store in store_list:
        # pull out store related params from config
        params = dict ( (x[0].replace('bisque.stores.%s.' % store, ''), x[1])
                        for x in  config.items() if x[0].startswith('bisque.stores.%s.' % store))
        if 'path' not in params:
            log.error ('cannot configure %s without the path parameter' , store)
            continue
        log.debug("params = %s" % params)
        driver = blob_storage.make_storage_driver(params.pop('path'), **params)
        if driver is None:
            log.error ("failed to configure %s.  Please check log for errors " , str(store))
            continue
        stores[store] = driver
    return stores


class StoreGenerator(object):
    "routines to generate a store resource"
    def __init__(self, stores):
        self.stores = stores

    def create_trees(self, name = None):
        stores = self.stores
        toplevel = data_service.query('image|file', view='query')

        def match_store (path):
            best = None
            best_top = 0
            for k,store in stores.items():
                if store.valid (path) and len(store.top) > best_top:
                    best = store
                    best_top = len(store.top)
                    best.name = k
            return best

        stores_resource = {}
        for r in toplevel:
            if  r.value is None:
                log.warn ( "BADVAL %s %s %s %s", r.resource_type, r.resource_uniq,  r.name, r.value)
                continue
            store = match_store (r.value)
            # If only dealing with  store 'name' then skip others
            if store is None:
                log.warn ( "NOSTORE %s %s %s %s", r.resource_type, r.resource_uniq,  r.name, r.value)
                continue

            # Skip if not name selected
            if name is not None and name != store.name:
                continue

            if r.value.startswith (store.top):
                path = r.value[len(store.top):]
            else:
                path = r.value

            # For each store, make a path string for each loaded resource
            el = stores_resource.setdefault (store.name, {})
            el[path] = r
            #print path

        # We parse the paths into a set of nested dicts .
        nested = {}
        for k,p in stores_resource.items():
            nested[k] = parse_nested(p, sep = '/')
        return  nested


    def create_stores (self, nested):
        """ Use the dictionary to save/create a store resource
        @return : list of  found stores as etree store resources
        """

        def visit_level(root, d):
            count = 0
            for k,v in d.items():
                if isinstance (v, dict):
                    subroot = etree.SubElement (root, 'dir', name = k)
                    visit_level(subroot, v)
                else:
                    xv = etree.SubElement (root, 'link', name=(v.resource_name or 'filename%s' %count), value = str(v.resource_uniq))
                    count += 1

        stores = []
        for store, paths in nested.items():
            root = etree.Element('resource', resource_type='store', name=store, value = self.stores[store].top)
            visit_level (root, paths)
            stores.append (root)
        return stores

    def save_store(self, root):
        log.info ("saving %s named %s " , root.get ('resource_type'), root.get('name'))
        new_store = data_service.new_resource(root)
        return new_store


###########################################################################
# PathServer
###########################################################################


class StoreServer(TGController):
    """ Manipulate store paths
    """
    def __init__(self):
        super(StoreServer, self).__init__()
        self.stores = load_stores()

    def load_path (self, store_name, path, **kw ):
        """load a store resource from store
        """
        view = kw.pop('view', 'full')
        q = data_service.query('store', name=store_name, view='full')
        if len(q) == 0:
            log.warn('No store named %s' % store_name)
            return None
        if len(q) != 1:
            log.error ('Multiple named stores')
            return None
        q = q[0]
        #log.debug ('ZOOM %s', q.get ('uri'))
        while path:
            el= path.pop(0)
            q = data_service.query(parent=q, name=el, view='full', )
            if len(q) != 1:
                log.error ('multiple names (%s) in store level %s', el, q.get('uri'))
                return None
            q = q[0]
        if kw:
            # might be limitin result
            q = data_service.get_resource(q, view=view, **kw)
        return q

    def find_matching_store(self, path):
        """Find a store based on the path *best* prefix

        :param path: a url path
        :type  path: str
        :return: A tuple (Store, relative path)
        """
        best = None
        stores = self.stores
        for name,store  in stores.items():
            new_path = store.valid (path)
            if new_path:
                store = data_service.query('store', name=name,view='full')
                if len(store) == 0:
                    store = None
                    partial = name + new_path[len(stores[name].top):]
                elif len(store) == 1:
                    store = store[0]
                    partial = new_path[len(stores[name].top):]
                else:
                    log.error ('multiple  store found %s  - %s', best, new_path)
                    break
                log.debug ("Matched %s %s ", name, partial)
                return store, partial.split ('/')
        return None,None

    def find_path(self, path, resource_uniq, **kw):
        root = None
        log.info("find %s ", path)
        store, path = self.find_matching_store (path)
        if store is None:
            return None
        parent = store
        while parent and path:
            el = path.pop(0)
            if not el:
                continue
            q  = data_service.query(parent=parent, name=el, view='full')
            if len(q) != 1:
                return None
            if path:
                parent = q[0]
        # If here the q is your uncle
        return q


    #@smokesignal.on(SIG_NEWBLOB)
    def insert_path(self, path, resource_uniq=None, resource_name=None, **kw):
        """ insert a store path into the store resource

        :param path: a string path for the store
        """
        root = None
        log.info("Insert %s into store", path)
        store, path = self.find_matching_store (path)
        if store is None:
            # No matching store has been created, but one may have matched.
            if path is None:
                # No store matched so no Path either.
                return None
            # we will create a new store (for user) for this path
            resource = root = etree.Element ('store', name = path.pop(0) )

        parent = store
        while parent and path:
            el = path.pop(0)
            if not el:
                continue
            q  = data_service.query(parent=parent, name=el, view='full')
            if len(q) != 1:
                #log.error ('multiple names (%s) in store level %s', el, q.get('uri'))
                path.insert(0, el)
                break
            parent = q[0]
        # any left over path needs to be created
        log.debug ("at %s rest %s", parent and parent.get ('uri'), path)
        elements = []
        while len(path)>1:
            nm = path.pop(0)
            if root is None:
                resource = root = etree.Element ('dir', name = nm)
            else:
                resource = etree.SubElement (resource, 'dir', name=nm)
        # The last element might be dir or a link
        if len(path)==1:
            nm = resource_name or path.pop(0)
            if root is None:
                resource = root = etree.Element ('link' if resource_uniq else 'dir', name = nm)
            else:
                resource = etree.SubElement (resource, 'link' if resource_uniq else 'dir', name=nm)

            if resource_uniq:
                resource.set ('value', resource_uniq)
            # create the new resource
            log.debug ("New resource %s at %s " , etree.tostring(root), parent and parent.get ('uri'))
            q = data_service.new_resource(resource=root, parent=parent)
        return q


    def delete_path (self, path, **kw):
        """ Delete an store element and all below it

        :param path: A string (url) of the path
        :type  path: str
        """
        q = self.find_path (path)
        data_service.del_resource(q)


    @expose(content_type='text/xml')
    def _default(self, *path, **kw):
        #set_admin_mode()
        log.debug ("STORE: Got %s and %s" ,  path, kw)
        origview = kw.pop('view', 'short')
        value = None
        path = list(path)
        store_name = path.pop(0)
        if len(path) and path[-1] == 'value':
            value = path.pop()
            view = 'query'
            origkw = kw
            kw = {}
        else:
            view = 'full'



        q =  self.load_path(store_name=store_name, path = path, view=view, **kw)
        if q is None:
            abort (404, "bad store path %s" % path)
        if value is not None:
            limit = origkw.pop('limit', None)
            offset = origkw.pop('offset', 0)
            resp = etree.Element('resource')
            for el in q[offset: limit and (int(limit) + int(offset))]:
                if el.tag == 'link':
                    r = data_service.get_resource (el.get ('value'), view=origview, **origkw)
                    if r is not None:
                        resp.append(r)
                    else:
                        log.warn ('element %s was not fetched', etree.tostring(el))
                else:
                    resp.append(el)
            q = resp

        return etree.tostring(q)

    @expose(content_type='text/xml')
    #@require(identity.not_anonymous())
    def create(self, name= None):
        gen = StoreGenerator(self.stores)
        trees = gen.create_trees(name)
        stores = gen.create_stores (trees)
        for root in stores:
            store = gen.save_store(root)
        return etree.tostring (store)


    @expose(content_type='text/xml')
    def index(self):
        stores = etree.Element ('resource', resource_type='stores')
        for k,v in self.stores.items():
            etree.SubElement(stores, 'store', name=k, value=v.top)
        return etree.tostring(stores)

    @expose(content_type='text/xml')
    def append(self, path=None,  resource_uniq=None,  **kw):
        if path is None:
            path = tg.request.body

        self.insert_path (path, resource_uniq)






