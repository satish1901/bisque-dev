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
import os
import logging
import string
import urllib
import urlparse
import itertools
import shutil
from lxml import etree
from datetime import datetime
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from paste.deploy.converters import asbool
from contextlib import contextmanager

import tg
from tg import expose, config, require, abort
from tg.controllers import RestController, TGController
from repoze.what import predicates

from bq.core import  identity
from bq.core.identity import set_admin_mode
from bq.core.model import DBSession
#from bq.core.service import ServiceMixin
#from bq.core.service import ServiceController
from bq.exceptions import IllegalOperation, DuplicateFile, ServiceError
from bq.util.paths import data_path
from bq.util.compat import OrderedDict

from bq import data_service

from . import blob_drivers

log = logging.getLogger('bq.blobs.mounts')


#################################################
#  Define helper functions for NT vs Unix/Mac
#
if os.name == 'nt':
    def move_file (fp, newpath):
        with open(newpath, 'wb') as trg:
            shutil.copyfileobj(fp, trg)

    def data_url_path (*names):
        path = data_path(*names)
        if len(path)>1 and path[1]==':': #file:// url requires / for drive lettered path like c: -> file:///c:/path
            path = '/%s'%path
        return path

    def url2localpath(url):
        path = urlparse.urlparse(url).path
        if len(path)>0 and path[0] == '/':
            path = path[1:]
        try:
            return urllib.unquote(path).decode('utf-8')
        except UnicodeEncodeError:
            # dima: safeguard measure for old non-encoded unicode paths
            return urllib.unquote(path)

    def localpath2url(path):
        path = path.replace('\\', '/')
        url = urllib.quote(path.encode('utf-8'))
        if len(path)>3 and path[0] != '/' and path[1] == ':':
            # path starts with a drive letter: c:/
            url = 'file:///%s'%url
        else:
            # path is a relative path
            url = 'file://%s'%url
        return url

else:
    def move_file (fp, newpath):
        log.debug ("moving file %s", fp.name)
        if os.path.exists(fp.name):
            oldpath = os.path.abspath(fp.name)
            shutil.move (oldpath, newpath)
        else:
            with open(newpath, 'wb') as trg:
                shutil.copyfileobj(fp, trg)

    data_url_path = data_path

    def url2localpath(url):
        url = url.encode('utf-8') # safegurd against un-encoded values in the DB
        path = urlparse.urlparse(url).path
        return urllib.unquote(path)

    def localpath2url(path):
        url = urllib.quote(path.encode('utf-8'))
        #if len(url)>1 and url[0] == '/':
        url = 'file://%s'%url
        return url


@contextmanager
def optional_cm(cm, *args, **kw):
    """Create a special contect manager to not duplicate code
    See http://bugs.python.org/issue10049
    """
    if cm is None:
        yield None
    else:
        with cm(*args, **kw) as v:
            yield v


@contextmanager
def opener_cm (path):
    "open a filename or return the already opened file"
    if hasattr(path, 'read'):
        yield path
    else:
        with open(path, 'rb') as f:
            yield f


# PathServer
def get_tag(elem, tag_name):
    els = elem.xpath ('./tag[@name="%s"]' % tag_name)
    if len(els) == 0:
        return None
    return els



#  Load store parameters
OLDPARMS = dict (date='',
                 dirhash='',
                 filehash='',
                 filename='',
                 filebase='',
                 fileext='')
def load_default_drivers():
    stores = OrderedDict()
    store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ]
    log.debug ('requested stores = %s' , store_list)
    for store in store_list:
        # pull out store related params from config
        params = dict ( (x[0].replace('bisque.stores.%s.' % store, ''), x[1])
                        for x in  config.items() if x[0].startswith('bisque.stores.%s.' % store))
        if 'mounturl' not in params:
            if 'path' in params:
                path = params.pop ('path')
                params['mounturl'] = string.Template(path).safe_substitute(OLDPARMS)
                log.warn ("Use of deprecated path (%s) in  %s driver . Please change to mounturl and remove any from %s", path, store, OLDPARMS.keys())
            else:
                log.error ('cannot configure %s without the mounturl parameter' , store)
                continue
        log.debug("params = %s" , params)
        #driver = make_storage_driver(params.pop('path'), **params)
        #if driver is None:
        #    log.error ("failed to configure %s.  Please check log for errors " , str(store))
        #    continue
        stores[store] = params
    return stores


###########################################################################


class MountServer(TGController):
    """ Manipulate
    """
    def __init__(self, url):
        super(MountServer, self).__init__()
        self.drivers = load_default_drivers()
        log.info ("Loaded drivers %s", self.drivers)


    #############################################################
    # Web funs
    #
    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def _default(self, *path, **kw):
        """ Dispatch based on request method GET, ...
        """
        method = tg.request.method
        if  method == 'GET':
            return self._get(list(path), **kw)
        elif method in ( 'POST', 'PUT'):
            return self._post(list(path), **kw)
        elif method == 'DELETE':
            return self._delete(list(path), **kw)
        abort(400)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def index(self):
        #stores = etree.Element ('resource', resource_type='stores')
        #for k,v in self.drivers.items():
        #    etree.SubElement(stores, 'store', name = k, resource_unid=k, value=v.top)

        root = self._create_root_mount()
        return etree.tostring(root)


    def _get(self, path, **kw):
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

        q = self._load_mount_path(store_name=store_name, path = path, view=view, **kw)
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

    def _post(self, path, **kw):
        log.info ("POST/PUT %s with %s" ,  path, kw)
        if len(path)==0:
            return self.index()
        store_name = path.pop(0)
        q = self.add_mount_path (store_name, path, **kw)
        return etree.tostring(q)

    def _delete(self, path, **kw):
        log.info ("DELETE %s with %s" ,  path, kw)
        if len(path)==0:
            return self.index()
        store_name = path.pop(0)
        if self.delete_mount_path(store_name, path, **kw):
            return "<response/>"


    ######################
    # Core
    def _create_root_mount(self):
        'create/find hidden root store for each user'

        root = data_service.query('store', resource_unid='(root)', view='full')
        if len(root) == 0:
            return  self._create_default_mounts()
        if len(root) == 1:
            return self._create_default_mounts(root[0])
        elif len(root) > 1:
            log.error("Root store created more than once: %s ", etree.tostring(root))
            return None

        return root[0]

    def _create_default_mounts(self, root=None):
        'translate system stores into mount (store) resources'

        #for x in range(subtrans_attempts):
        #    with optional_cm(subtrans):
        update = False
        user_name  = identity.current.user_name
        if  root is None:
            update  = True
            root = etree.Element('store', name="(root)", resource_unid="(root)")
            etree.SubElement(root, 'tag', name='order', value = ','.join (self.drivers.keys()))
            for store_name,driver in self.drivers.items():
                mount_path = string.Template(driver['mount']).safe_substitute(datadir = data_url_path(), user = user_name)
                etree.SubElement(root, 'store', name = store_name, resource_unid=store_name, value=mount_path)
        else:
            storeorder = get_tag(root, 'order')
            if storeorder is None:
                log.warn ("order tag missing from root store adding")
                storeorder = etree.SubElement(root, 'tag', name='order', value = ','.join (self.drivers.keys()))
                update = True
            elif len(storerder) == 1:
                storeorder = storeorder[0]
            else:
                log.warn("Multible order tags on root store")

            # Check for store not already initialized
            user_stores   = dict ((x.get ('name'), x)  for x in root.xpath('store'))
            for store_name, driver in self.drivers.items():
                if store_name not in user_stores:
                    store = etree.SubElement (root, 'store', name = store_name, resource_unid = store_name)
                    ordervalue = [ x.strip() for x in storeorder.get ('value', '').split(',') ]
                    if storename not in ordervalue:
                        ordervalue.append(storename)
                        storeorder.set ('value', ','.join(ordervalue))

                else:
                    store = user_stores[store_name]
                if store.get ('value') is None:
                    mounturl = driver.get ('mounturl')
                    mounturl = string.Template(mounturl).safe_substitute(datadir = data_url_path(), user = user_name)
                    # ensure no $ are left
                    mounturl = mounturl.split('$', 1)[0]
                    store.set ('value', mounturl)
                    log.debug ("setting store %s value to %s", store_name, mounturl)
                    update = True

        if update:
            log.debug ("updating %s", etree.tostring(root))
            return data_service.update(root, new_resource=root, view='full')
        return root


    def _create_user_mount (self, root_mount, mount_name, mount_url):
        'create a new user mount given a url'
        store = etree.Element('store', name = mount_name, resource_unid=mount_name, value=mount_url)
        data_service.new_resource(store, parent = root_mount)


    ###############################################
    # Store operators
    # A store path is the user friendly list of names

    def _load_store(self, store_name):
        'Simply load the store named'
        root = self._create_root_mount()
        storelist = root.xpath("store[@name='%s']" % store_name)
        if len(storelist) == 0:
            log.warn('No store named %s' , store_name)
        if len(storelist) != 1:
            log.error ('Multiple named stores')
        else:
            return storelist[0]
        return None

    def _load_mount_path (self, store_name, path, **kw ):
        """load a store resource from store
        """
        path = list(path)   # make a copy to leave argument alone
        view = kw.pop('view', 'full')
        q = self._load_store(store_name)
        #log.debug ('ZOOM %s', q.get ('uri'))
        while q and path:
            el= path.pop(0)
            q = data_service.query(parent=q, resource_unid=el, view='full', )
            if len(q) != 1:
                log.error ('multiple names (%s) in store level %s', el, q.get('uri'))
                return None
            q = q[0]
        if kw:
            # might be limitin result
            q = data_service.get_resource(q, view=view, **kw)
        return q

    def add_mount_path(self, store_name, path, resource_uniq=None, resource_name=None, **kw):
        """Insert a URL path
        """
        store = self._load_store(store_name)
        if store is None:
            store = store_name
        return self._create_full_path(store, path, resource_uniq, resource_name, **kw)

    def delete_mount_path (self, store_name, path, **kw):
        """ Delete an store element and all below it

        :param path: A string (url) of the path
        :type  path: str
        """

        value = None
        if len(path) and path[-1] == 'value':
            value = path.pop()
        if len(path)==0:
            return False
        q = self._load_mount_path (store_name, path)
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



    #################################
    # blobsrv API
    def valid_store_ref(self, resource):
        """Test whether the resource  is on a store can be read by the user
        @param resource: a binary resource
        @return : a store resource
        """
        stores = self._get_stores()

        storeurls =  resource.get ('value')
        if storeurls is not None:
            storeurls = [ storeurls]
        else:
            storeurls = [x.text for x in resource.xpath('value') ]

        for store_name, store in stores.items():
            prefix = store.get ('value')
            log.debug ("checking %s and %s" ,  prefix, storeurls[0])
            # KGK: TEMPORARY .. this should check readability by the driver instead of simply the prefix
            # ugly should be in driver at least
            driver = self._get_driver(store)
            if driver.valid (storeurls[0]):
                # All *must* be valid for the same store
                for storeurl in storeurls[1:]:
                    if not driver.valid (storeurl):
                        raise IllegalOperation('resource %s spread across different stores %s', resource.get('resource_uniq'), storeurls)
                return store
        return None

    def store_blob(self, resource, fileobj = None, rooturl=None):
        """store a blob to a mount

        A resource contains:

          1.  A reference to a previously stored file with its
              storeurl i.e. irods://host/path/file.ext in resource.value

          2.  A relative location i.e. dir1/dir2/file.ext in the
              resource name which can be stored in the 1st store available
              by the users ordering on the root store

          3.  a fixed store location i.e. /irods_home/dir1/dir2/file.ext which must match a store name

        """
        stores = self._get_stores()
        log.debug ("Available stores: %s", stores.keys())

        storepath = resource.get ('name')
        if storepath[0]=='/':
            # This is a fixed store name i.e. /local or /irods and must be stored on the specific mount
            _, store_name, storepath = storepath.split ('/', 2)
            if store_name not in stores:
                raise IllegalOperation("Illegal store name %s", store_name)
            stores = dict( (store_name, stores[store_name]) )
        else:
            # A relative name.. could be a reference store only
            if fileobj is None:
                store = self.valid_store_ref (resource)
                if  store:
                    stores = dict( (store.get ('name'), store) )

        storeurl = lpath = None
        log.debug ("Trying mounts %s", stores.keys())
        for store_name, store in stores.items():
            try:
                storeurl,lpath =  self._save_store (store, storepath, resource, fileobj,rooturl)
                break
            except IllegalOperation, e:
                log.debug ("failed %s store on %s with %s", storepath, store_name, e )
                store_url = lpath = None

        if storeurl is None:
            log.error ('storing %s failed (%s)', storepath, storeurl)

        return storeurl, lpath


    def _save_store(self, store, storepath, resource, fileobj=None, rooturl=None):
        'store the file to the named store'

        if  fileobj:
            driver   = self._get_driver(store)
            if driver.readonly:
                raise IllegalOperation('readonly store')

            storeurl = urlparse.urljoin (driver.mount_url, storepath)
            storeurl, localpath = driver.push (storeurl, fileobj)
            resource.set('value', storeurl)
        else:
            storeurl, localpath = self._save_storerefs (store, storepath, resource, rooturl)



        if asbool(config.get ('bisque.blob_service.store_paths', True)):
            self.insert_mount_path (store, storepath.split('/'), resource)
        return storeurl, localpath

    def _save_storerefs(self, store, storepath, resource, rooturl):
        """store a resource with storeurls already in place.. these may be ona true store or simply reside locally
        @param store: a store resource
        @param storepath: a path on store where to put the resource
        @param resource: a resource with storeurls
        @param rooturl: the root of the storeurls
        """

        def setval(n, v):
            n.set('value', v)
        def settext(n, v):
            n.text = v

        driver = self._get_driver(store)

        refs = resource.get ('value')
        if refs is not None:
            refs = [ (resource, setval, blob_drivers.split_subpath(refs), storepath) ]
        else:
            refs = [ (x, settext, blob_drivers.split_subpath(x.text), None) for x in resource.xpath ('value') ]

        # Assume the first URL is special and the others are related which can be used
        # to calculate storepath

        movingrefs = []
        for node, setter, (storeurl, subpath), storepath in refs:
            if storeurl.startswith (driver.mount_url):
                # Already valid
                continue
            localpath  = self._force_storeurl_local(storeurl)
            if os.path.isdir(localpath):
                movingrefs.extend ( (None, None, (fpath, subpath), fpath[len(localpath):]) for fpath in blob_drivers.walk_deep(localpath))
            elif os.path.exists(localpath):
                if storepath is None:
                    storepath = storeurl[len(rooturl):]
                movingrefs.append ( (node, setter, (localpath, subpath), storepath) )
            else:
                log.error ("store_refs: Cannot access %s of %s ", storeurl, etree.tostring(node))


        if movingrefs and driver.readonly:
            raise IllegalOperation('readonly store')

        for node, setter, (localpath, subpath),  storepath in movingrefs:
            with open (localpath, 'rb') as fobj:
                storeurl = urlparse.urljoin (driver.mount_url, storepath)
                storeurl, localpath = driver.push (storeurl, fobj)
                if not node:
                    node = etree.SubElement(resource, 'value')
                    node.text = "%s%s" % (storeurl, subpath)
                else:
                    setter(node, "%s%s" % (storeurl, subpath))



    def _force_storeurl_local(self, storeurl):
        """User available drivers to fetch a local copy of the storeurl and return path
        @param storeurl: a valid storeurl
        @return : (A local fileyststem path, rootportion)  or None
        """
        # KGK: temporary simplification
        if storeurl.startswith ('file://'):
            return blob_drivers.url2localpath(storeurl)
        return None

    def fetch_blob(self, resource):
        'return a (set) path(s) for a resource'

        log.debug ("fetch_blob %s", resource.get ('resource_uniq'))
        store = self.valid_store_ref (resource)
        if  store is None:
            log.error ('Not a valid store ref in  %s' , etree.tostring (resource))
            return None
        driver = self._get_driver(store)
        uniq     = resource.get('resource_uniq')
        bloburls = resource.get('value')
        if bloburls is not None:
            bloburls = [ bloburls ]
        else:
            bloburls  = [ x.text for x in resource.xpath('value') ]

        log.debug ("fetch_blob %s -> %s", resource.get ('resource_uniq'), bloburls)

        files = []
        sub = ''
        for storeurl in bloburls:
            localblob = driver.pull (storeurl)
            if localblob is None:
                log.error ("Failed to fetch blob for %s of %s during pull %s", uniq, bloburls, storeurl)
                return None
            sub = sub or localblob.sub
            if localblob.files:
                files.extend(localblob.files)
            else:
                files.append(localblob.path)
        if len(files) == 0:
            log.error ('fetch_blob: no files fetched for %s ', uniq)
            return None
        log.debug('fetch_blob for %s url=%s localpath=%s sub=%s', uniq, bloburls, files[0], sub)
        return blob_drivers.Blobs(files[0], sub, files)


    def _find_store(self, storeurl):
        """return a store(mount)  by the storeurl
        """
        root = data_service.query('store', resource_unid='(root)', view='full')
        #figure  where to store blob
        #store_order = get_tag (root, 'order')
        #if store_order is None:
        #    store_order = config.get('bisque.blob_service.stores','')

        #for store_name in [x.strip() for x in store_order.split(',')]:
        #    pass
        for store in root.xpath('./store'):
            store_prefix = store.get('value')
            if storeurl.startswith (store_prefix):
                store_name = store.get ('name')
                return store


    def _get_stores(self):
        "Return a list of store resources in the users ordering"

        root = data_service.query('store', resource_unid='(root)', view='full')
        if len(root) != 1:
            raise IllegalOperation ("root store not valid %s", etree.tostring (root))
        root = root[0]
        store_order = get_tag (root, 'order')
        if store_order is None:
            store_order = config.get('bisque.blob_service.stores','')
        else:
            store_order = store_order[0].get ('value')

        stores = OrderedDict()
        for store_name in (x.strip() for x in store_order.split(',')):
            store_el = root.xpath('./store[@name="%s"]' % store_name)
            if not store_el or len(store_el) > 1:
                log.warn ("store %s does not exist in %s", store_name, etree.tostring(root))
                continue
            store = store_el[0]
            stores[store_name] = store
        return stores


    def _get_driver(self, store):
        "Create a  driver  for the user store"
        store_name = store.get ('name')
        driver_opts = dict(self.drivers.get (store_name))

        # Replace any default driver opts with tags
        storetags = store.xpath('tag')
        driver_opts.update ( (x.get ('name'), x.get ('value')) for x in storetags )

        log.debug ("after store tags %s" , driver_opts)
        if not driver_opts.get ('credentials'):
            driver_opts['credentials']=''

        driver_opts['path'] = mount_path = store.get ('value')
        driver_opts['mount_url' ] = mount_path

        # get a driver to use
        #KGK : maybe use a timeout cache here so the connection can be reused?
        log.debug ('making store driver: %s', driver_opts)
        driver = blob_drivers.make_storage_driver(**driver_opts)
        return driver



    ##############################
    # services for mounts

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
            resource = root = etree.Element ('store', name = store, resource_unid = store)
            store = self._create_root_mount()

        parent = store
        while parent is not None and path:
            el = path.pop(0)
            if not el:
                continue
            q  = data_service.query(parent=parent, resource_unid=el, view='full', cache=False)
            if len(q) == 0:
                # no element we are done
                path.insert(0, el)
                break
            if len(q) > 1:
                log.error ('multiple names (%s) in store level %s', el, q.get('uri'))
                #path.insert(0, el)
                parent = q[0]
                break
            parent = q[0]
        # any left over path needs to be created
        log.debug ("create: at %s rest %s", (parent is not None) and parent.get ('uri'), path)
        while len(path)>1:
            nm = path.pop(0)
            if root is None:
                resource = root = etree.Element ('dir', name=nm, resource_unid = nm)
            else:
                resource = etree.SubElement (resource, 'dir', name=nm, resource_unid=nm)
        # The last element might be dir or a link
        if len(path)==1:
            nm = resource_name or path.pop(0)
            if root is None:
                resource = root = etree.Element ('link' if resource_uniq else 'dir', name=nm, resource_unid = nm)
            else:
                resource = etree.SubElement (resource, 'link' if resource_uniq else 'dir', name=nm, resource_unid=nm)

            if resource_uniq:
                resource.set ('value', resource_uniq)
            # create the new resource
            log.debug ("New resource %s at %s " , etree.tostring(root), (parent is not None) and parent.get ('uri'))
            q = data_service.new_resource(resource=root, parent=parent)
        return q



    def _insert_mount_path(self, store, mount_path, resource, **kw):
        """ insert a store path into the store resource

        This will create a store element if does not exist
        :param path: a blob path for the store
        """
        log.info("Insert_mount_path create %s path %s ", str(store), str(mount_path))

        return self._create_full_path(store, mount_path, resource.get ('resource_uniq'), resource.get('resource_name'), **kw)


    def insert_mount_path(self, store, mount_path, resource, **kw):
        subtrans = None
        repeats = 2
        if asbool(config.get ('bisque.blob_service.store_paths.subtransaction', True)):
            repeats = 8
            subtrans = DBSession.begin_nested
        for x in range(1, repeats+1):
            try:
                with optional_cm(subtrans):
                    return self._insert_mount_path (store, mount_path, resource, **kw)
            except IntegrityError:
                log.exception ('Integrity Error caught on attempt %s.. retrying %s', x, mount_path)

        log.error('StoreError: tried too many attempts %s.. not inserting %s', x, mount_path)
        return None







