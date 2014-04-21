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
import string
from lxml import etree
from datetime import datetime
from datetime import timedelta

import tg
from tg import expose, flash, config, require, abort
from tg.controllers import RestController, TGController
from repoze.what import predicates

from bq.core import  identity
from bq.core.identity import set_admin_mode
#from bq.core.service import ServiceMixin
#from bq.core.service import ServiceController
from bq.exceptions import IllegalOperation, DuplicateFile, ServiceError
from bq.util.timer import Timer
from bq.util.compat import OrderedDict
from bq.util.dotnested import parse_nested

from bq import data_service

from . import blob_storage


log = logging.getLogger('bq.blobs.store_resource')


class StoreGenerator(object):
    "routines to generate a store resource"
    def __init__(self, drivers):
        self.drivers = drivers

    def create_trees(self, name = None):
        drivers = self.drivers
        toplevel = data_service.query('image|file', view='query')

        def match_store (path):
            best = None
            best_top = 0
            for k,store in drivers.items():
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
                    etree.SubElement (root, 'link', name=(v.resource_name or 'filename%s' %count), value = str(v.resource_uniq))
                    count += 1

        stores = []
        for store, paths in nested.items():
            root = etree.Element('resource', resource_type='store', name=store, value = self.drivers[store].top)
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
    def __init__(self, drivers = None):
        super(StoreServer, self).__init__()
        self.drivers = drivers


    def _create_full_path(self, store, path, resource_uniq=None, resource_name=None, **kw):
        """Create the full path relative to store
        @param store: a string name or etreeElement
        @param path: a path relative to the store
        @param resource_uniq: optional resource to be placed
        @param resource_name: options name of resource
        """

        root = None
        log.debug ("CREATE_PATH %s %s", store, path)
        if isinstance(store, basestring):
            resource = root = etree.Element ('store', name = store)
            store = None

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

    #######################################
    #Blob operators
    # pass a blob url to these

    def find_store_by_blob(self, path):
        """Find a store based on the blob_path *best* prefix

        :param path: a url path
        :type  path: str
        :return: A tuple (Store resource, relative path)
        """
        user_name  = identity.current.user_name
        best = None
        drivers = self.drivers
        for name,driver  in drivers.items():
            if not hasattr(driver, 'user_path'):
                continue
            new_path = driver.valid (path)
            if new_path:
                user_path = string.Template(driver.user_path).safe_substitute(user = user_name)
                if not new_path.startswith(user_path):
                    continue

                store = data_service.query('store', name=name,view='full')
                if len(store) == 0:
                    store = None
                    partial = name + '/' + new_path[len(user_path):]
                elif len(store) == 1:
                    store = store[0]
                    partial = new_path[len(user_path):]
                else:
                    log.error ('multiple  store found %s  - %s', best, new_path)
                    break
                log.debug ("Matched %s %s ", name, partial)
                return store, partial.replace('//','/').split ('/')
        return None,None

    def find_path_by_blob(self, path, **kw):
        "Walk the blob_id path and return the element at end of path or None"
        log.info("find %s ", path)
        store, path = self.find_store_by_blob (path)
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
    def insert_blob_path(self, path, resource_uniq=None, resource_name=None, **kw):
        """ insert a store path into the store resource

        This will create a store element if does not exist

        :param path: a blob path for the store
        """
        log.info("Insert_blob_path %s",  path)
        store, path = self.find_store_by_blob (path)
        if store is None:
            # No matching store has been created, but one may have matched.
            if path is None:
                # No store matched so no Path either.
                return None
            # we will create a new store (for user) for this path
            #resource = root = etree.Element ('store', name = path.pop(0))
            store = path.pop(0)

        log.info("Insert_blob_path create %s path %s ", store, path)
        return self._create_full_path(store, path, resource_uniq, resource_name, **kw)

    def delete_blob_path(self, path):
        """ Delete an element given the blob path
        """
        q = self.find_path_by_blob(path)
        if q:
            data_service.del_resource(q)


    ###############################################
    # Store operators
    # A store path is the user friendly list of names

    def _load_store(self, store_name):
        'Simply load the store named'
        q = data_service.query('store', name=store_name, view='full')
        if len(q) == 0:
            log.warn('No store named %s' % store_name)
            return None
        if len(q) != 1:
            log.error ('Multiple named stores')
            return None
        return q[0]

    def _load_store_path (self, store_name, path, **kw ):
        """load a store resource from store
        """
        path = list(path)   # make a copy to leave argument alone
        view = kw.pop('view', 'full')
        q = self._load_store(store_name)
        #log.debug ('ZOOM %s', q.get ('uri'))
        while q and path:
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

    def insert_store_path(self, store_name, path, resource_uniq=None, resource_name=None, **kw):
        """Insert a URL path
        """
        store = self._load_store(store_name)
        if store is None:
            store = store_name
        return self._create_full_path(store, path,  resource_uniq=None, resource_name=None, **kw)

    def delete_store_path (self, store_name, path, **kw):
        """ Delete an store element and all below it

        :param path: A string (url) of the path
        :type  path: str
        """

        value = None
        if len(path) and path[-1] == 'value':
            value = path.pop()
        if len(path)==0:
            return False
        q = self._load_store_path (store_name, path)
        if q is None:
            log.debug ("Cannot find %s in %s", path, store_name)
            return False
        log.debug ("delete from %s of %s = %s", store_name, path, etree.tostring(q))
        #if  q.tag != 'link':
        #    return False
        data_service.del_resource(q)
        if value is not None:
            data_service.del_resource(q.get ('value'))
        return True


    #############################################################
    # Web funs
    #


    def get(self, path, **kw):
        """ GET from a path /store_name/d1/d2/
        """
        log.info ("GET %s with %s" ,  path, kw)
        origview = kw.pop('view', 'short')
        value = None
        # Some crazy hanlding when de-referencing
        if len(path) and path[-1] == 'value':
            value = path.pop()
            view = 'query'
            origkw = kw
            kw = {}
        else:
            view = 'full'
        # woops just want a list of stores.. index does that
        if len(path)==0:
            return self.index()
        store_name = path.pop(0)

        q =  self._load_store_path(store_name=store_name, path = path, view=view, **kw)
        if q is None:
            #abort (404, "bad store path %s" % path)
            return '<resource/>'
        # crazy value handling (emulate limit and offset)
        if value is not None:
            limit = origkw.pop('limit', None)
            offset = int(origkw.pop('offset', 0))
            resp = etree.Element('resource')
            for el in q[offset: limit and (int(limit) + offset)]:
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

    def post(self, path, **kw):
        log.info ("POST/PUT %s with %s" ,  path, kw)
        if len(path)==0:
            return self.index()
        store_name = path.pop(0)
        return self.insert_store_path (store_name, path, **kw)

    def delete(self, path, **kw):
        log.info ("DELETE %s with %s" ,  path, kw)
        if len(path)==0:
            return self.index()
        store_name = path.pop(0)
        if self.delete_store_path(store_name, path, **kw):
            return "<response/>"


    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def create(self, name= None):
        gen = StoreGenerator(self.drivers)
        trees = gen.create_trees(name)
        stores = gen.create_stores (trees)
        for root in stores:
            store = gen.save_store(root)
        return etree.tostring (store)


    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def index(self):
        stores = etree.Element ('resource', resource_type='stores')
        for k,v in self.drivers.items():
            etree.SubElement(stores, 'store', name=k, value=v.top)
        return etree.tostring(stores)

    @expose(content_type='text/xml')
    def _default(self, *path, **kw):
        """ Dispatch based on request method GET, ...
        """
        method = tg.request.method
        if  method == 'GET':
            return self.get(list(path), **kw)
        elif method in ( 'POST', 'PUT'):
            return self.post(list(path), **kw)
        elif method == 'DELETE':
            return self.delete(list(path), **kw)
        abort(400)





