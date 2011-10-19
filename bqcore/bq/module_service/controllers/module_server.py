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

   The module server coordinate the execution of modules otherwise
   known as MEX.

   Clients can request an execution of a particular module by
   preparing a MEX document (see XXX) and POST it the module server.
   The module server finds an appropiate engine (i.e. a node that can
   actually execute the module), registers the MEX and launches it on
   the engine.  It then return the mex uri so that the client can
   periodically check the mex status untile FINISHED or FAILED

   The module server also responds to requests by engines (engine_server)
   for inclusion/exclustion the compute grid.   Each engine has a
   number of installed modules which it communicates the module server
   in a registration document.
   


   module-> engine_list 


"""
import copy
import Queue
import time
import logging
import thread
import threading
import tg

from lxml import etree
from datetime import datetime, timedelta
from paste.proxy import make_proxy
from pylons.controllers.util import abort
from tg import controllers, expose, config
import tgscheduler

from bq import data_service
from bq.util import http
from bq.util.xmldict import d2xml, xml2d
from bq.core.identity import user_admin, not_anonymous, get_user_pass
from bq.core.permission import *
from bq.core.exceptions import RequestError
from bq.core.controllers.proxy import exposexml


log = logging.getLogger('bq.module_server')

from repoze.what import predicates 
from bq.core.service import ServiceController
from bq.module_service import model

from bq.core.model import DBSession as session

from bq.data_service.controllers.resource import Resource
from bq.data_service.controllers.bisquik_resource import BisquikResource
from bq.data_service import resource_controller
from bq.data_service.model import Service, Module, Tag, ModuleExecution as Mex
from bq.util.bisquik2db import bisquik2db, db2tree, load_uri



class MexDelegate (Resource):
    def __init__(self,  url, runner = None):
        super(MexDelegate, self).__init__(uri = url)
        self.runner = runner

    def remap_uri (self, mex):
        mexid = mex.get('uri').rsplit('/',1)[1]
        log.debug ('remap -> %s' % self.url)
        mex.set ('uri', "%s%s" % (self.url, mexid))

    def load(self, token):
        log.debug ("load of %s " % tg.request.url)
        return load_uri(tg.request.url)

    def create(self, **kw):
        return ""

    @expose(content_type='text/xml')
    def dir(self, **kw):
        data_service.query 
        parent = self.parent
        log.info ('DIR %s ' % parent)
        return ""
    
    
    @expose()
    def new(self, factory, xml, **kw):
        mex = etree.XML (xml)
        if mex.tag == "request":
            mex = mex[0]
        mex = self.create_mex(mex)
        response = etree.tostring(mex)
        #log.debug ("return MEX=%s" % response)
        tg.response.headers['Content-Type'] = 'text/xml'
        return response

                        
    def create_mex(self, mex):
        if mex.get('status') is None:
            mex.set ('status', "PENDING")
        etree.SubElement(mex, 'tag',
                         name="start-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))

        log.info ("MexDelegate %s" % etree.tostring (mex))
        #kw.pop('view', None)
        #response =  self.delegate.new (factory, mex, view='deep',**kw)
        mex = data_service.new_resource (mex, view='deep')
        self.remap_uri(mex)
        mex_id = mex.get('uri').rsplit('/', 1)[1]
        if self.runner:
            self.runner.submit (mex_id)
        return mex

    @expose()
    def modify(self, resource, xml, **kw):
        """
        Modify the mex in place.  Use to update status
        """
        #return self.delegate.modify (resource, xml, **kw)
        log.debug('MEX MODIFY')
        mex = etree.XML (xml)
        mex = check_mex(mex)
        mex = data_service.update(mex, view='deep')
        self.remap_uri (mex)
        tg.response.headers['Content-Type'] = 'text/xml'
        return etree.tostring (mex)

    @expose()
    def get(self, resource, **kw):
        """
        fetches the resource, and returns a representation of the resource.
        """
        mex = data_service.get_resource(resource, view='deep')
        log.debug ("dataservice fetch -> %s" % etree.tostring(mex))
        self.remap_uri (mex)

        tg.response.headers['Content-Type'] = 'text/xml'
        return etree.tostring (mex)
        
    @expose()
    def append(self, resource, xml, **kw):
        """
        Append a value to the mex
        """
        log.debug('MEX APPEND')
        mex = etree.XML(xml)
        mex = check_mex(mex)
        mex = data_service.update(mex, view='deep')
        #mex =  data_service.append_resource (resource, xml, **kw)
        self.remap_uri (mex)
        tg.response.headers['Content-Type'] = 'text/xml'
        return etree.tostring (mex)
        

    @expose(content_type="text/xml")
    def delete(self, resource,  **kw):
        """
        Delete the resource from the database
        """
        raise abort(501)

def read_xml_body():
    clen = int(tg.request.headers.get('Content-Length')) or 0
    content = tg.request.headers.get('Content-Type')
    if content.startswith('text/xml') or content.startswith('application/xml'):
        return etree.XML(tg.request.body_file.read(clen))
    return None


def create_mex(module_url, **kw):
    module = data_service.get_resource(module_url, view='deep')
    inputs = module.xpath('./tag[@name="inputs"]')
    inputs = inputs and inputs[0]
    real_params = dict(kw)
    mex = etree.Element('mex', status = 'PENDING', module = module_url)
    #mex_inputs = etree.SubElement(mex, 'tag', name='inputs')
    for mi in inputs:
        param_name = mi.get('value').split(':')[0].strip('$')
        log.debug ('param check %s' % param_name)
        if param_name in real_params:
            param_val = real_params.pop(param_name)
            #etree.SubElement(mex_inputs, 'tag',
            etree.SubElement(mex, 'tag',
                             name = param_name,
                             value= param_val)
            log.debug ('param found %s=%s' % (param_name, param_val))
            
    return mex
        

def check_mex(mex):
    if mex.tag == "request":
        mex = mex[0]
    if mex.get ('status') in ['FINISHED', 'FAILED']:
        etree.SubElement(mex, 'tag',
                         name="end-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))
        
    return mex

        
        
class ModuleDelegate (BisquikResource):
    cache = False
    def __init__(self, baseurl, module_uri, engine_uri):
        super(ModuleDelegate, self).__init__("modules", uri=baseurl)
        self.children['mex'] = MexDelegate(baseurl)

from repoze.what.predicates import not_anonymous
from tg import require
#from repoze.what.predicates import Any, is_user, has_permission

from lxml.html import builder as E
class ServiceDelegate(controllers.WSGIAppController):
    """Create a proxy for the particular service addressable
    by the module name
    """
    
    def __init__(self, service_url, module, mexurl):
        self.module = module
        self.mexurl = mexurl
        if not service_url[-1] =='/':
            service_url = service_url + '/'
            
        proxy = make_proxy(config, service_url)
        super(ServiceDelegate, self).__init__(proxy)

    #@require(not_anonymous(msg='You need to log-in to run a module'))
    @expose()
    def _default (self, *args, **kw):
        log.info ("Service proxy request %s" % ('/'.join(args)) )
        html = super(ServiceDelegate, self)._default(*args, **kw)
        return html
        #html = etree.HTML (html[0])
        #self.add_title(html, 'HELLO')
        #return etree.tostring(html)

    # Example process
    #def add_title(self, html, title):
    #    head = html.xpath('./head')
    #    head = (len(head) and head[0]) or None
    #    if head is None:
    #        head = E.HEAD()
    #        html.insert (0, head)
    #    el = head.xpath('./title')
    #    el = (len(el) and el[0]) or None
    #    if el is  None:
    #        el = E.TITLE(title)
    #    else:
    #        el.text = title
    #    head.insert(0, el)

    @require(not_anonymous(msg='You need to log-in to run a module'))
    @expose(content_type='text/xml')
    def execute(self, **kw):
        log.debug ('EXECUTE %s with %s' % (self.module, kw))
        mex = read_xml_body()
        if mex is None:
            mex = create_mex(self.module, **kw)
        else:
            mex.set('status', 'PENDING')
            mex.set('module', self.module)

        etree.SubElement(mex, 'tag',
                         name="start-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))
            
        mex = data_service.new_resource (mex, view='deep')
        self.remap_uri(mex)
        return etree.tostring (mex)

    def remap_uri (self, mex):
        mexid = mex.get('uri').rsplit('/',1)[1]
        log.debug ('remap -> %s' % self.mexurl)
        mex.set ('uri', "%s%s" % (self.mexurl, mexid))


class ModuleServer(ServiceController):
    service_type = "module_service"
    
    def __init__(self, server_url = None):
        super(ModuleServer, self).__init__(uri = server_url)

        self.runner = None
        self.__class__.mex = self.mex = MexDelegate (self.url + 'mex',
                                                     self.runner)
        self.__class__.modules = self.modules = resource_controller ("modules" , cache=False )
        self.__class__.engine = self.engine = EngineResource (server_url,
                                                              self.modules)
        self.load_services()

    def load_services(self):
        services = session.query(Service)
        for service in services:
            log.debug ("FOUND SERVICE: %s" %service)
            status = service.findtag('status')
            if not status or status.value == "disabled":
                continue
            log.debug ("      SERVICE: %s enabled"  %service)
            engine = service.engine
            module = service.module
            name = engine.rsplit('/',1)[1] 

            setattr(self.__class__, name , ServiceDelegate(engine, module, self.mex.url))
            log.info ("SERVICE PROXY %s -> %s " % (name, engine))
            

        #self.runner.start()

    @expose(content_type='text/xml')
    def default(self, *path, **kw):
        log.info ("default : %s" % str(path))
        kw['wpublic']='1'
        #kw['view'] = 'deep'
        return self.modules.default(*path, **kw)

    @expose(content_type='text/xml')
    def index (self, **kw):
        """Return the list of active modules as determined by the registered services
        """
        kw['wpublic']='1'
        kw.setdefault ('view','short')
        xml= self.modules.default(**kw)
        modules = etree.XML(xml)
        log.debug ("Got %s " % xml)
        
        for module in modules.findall ('module'):
            enabled = False
            del module.attrib['codeurl']
            #module.attrib['codeurl'] = "%s%s" %( self.url , module.get('name'))
            services = session.query(Service).filter_by (module = module.get ('uri'))
            for service in services:
                log.debug ("FOUND SERVICE: %s" %service)
                status = service.findtag('status')
                if status and status.value != "disabled":
                    enabled = True
                    log.debug ("      SERVICE: %s enabled"  %service)
            if not enabled:
                modules.remove (module)
        result = etree.tostring(modules)
        return result


    @expose(content_type='text/xml')
    def register_engine(self, **kw):
        'Helper method .. redirect post to engine resource'
        return self.engine.default (**kw)

    def execute(self, module_uri, **kw):
        mex = etree.Element ('mex', module = module_uri)
        for k,v in kw.items():
            # KGK: Filter by module items?
            etree.SubElement(mex, 'tag', name=k, value=v)
        log.info ("EXECUTE %s" % etree.tostring (mex))
        return self.mex.create_mex(mex)
    


    @expose('bq.module_service.templates.register')
    def register_module(name, module):
        return dict ()
    @expose(content_type="text/xml")
    def services(self):
        x = d2xml (self.servicelist())
        return etree.tostring(x)
        

    def begin_internal_mex(self, name=None):
        mex = etree.Element('mex', status="SESSION")
        etree.SubElement(mex, 'tag',
                         name="start-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))

        #kw.pop('view', None)
        #response =  self.delegate.new (factory, mex, view='deep',**kw)
        mex = data_service.new_resource (mex, view='deep')
        #return mex.get ('uri').rsplit('/', 1)[1]
        return mex.get('uri')
        
    def end_internal_mex(self, mexid):
        mex = etree.Element('mex', status="FINISHED", uri='http://localhost/ds/mex/%s' % mexid)
        etree.SubElement(mex, 'tag',
                         name="end-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))
        mex = data_service.update (mex)

        

#######################################
# ENGINE
class EngineResource (Resource):
    """Manage the Engine resources through the web

    Engines are WebAddressable modules
    Class allows engine to register and withdraw availability
    to execute module classes
    """
    def __init__(self, url, module_resource):
        super(EngineResource, self).__init__(uri = url)
        #self.url = url
        self.module_resource = module_resource

    @expose()
    def dir(self, **kw):
        """Show all endpoint for modules
        """
        
        response = etree.Element ('resource', url=self.url)

        for s in  session.query(Service):
            service = etree.SubElement(response,'service',
                                       uri=s.uri,
                                       module=s.module,
                                       engine=s.engine)
            #etree.SubElement(service, 'tag', name='module', value=s.module)
            #etree.SubElement(service, 'tag', name='engine', value=s.engine)

        tg.response.headers['Content-Type'] = 'text/xml'
        return etree.tostring (response)

    def load(self, token, **kw):
        """
        loads and returns a resource identified by the token.
        """
        return ""

    def create(self, **kw):
        """
        returns a class or function which will be passed into the self.new 
        method. 
        """
        return ""


    def register_module (self, module_def):
        name = module_def.get ('name')
        ts   = module_def.get ('ts')
        
        modules = data_service.query ('module', name=name, view="deep")
        m = (len(modules) and modules[0]) or None
        # Create a new module only if newer

        if m is not None:
            log.info ('module %s : new=%s current=%s' % (name,ts, m.get('ts')))
            if ts > m.get('ts'):
                module_def.set('uri', m.get('uri'))
                module_def.set('ts', str(datetime.now()))
                m = data_service.update(module_def, replace_all=True)
                log.debug("Updating new module definition with: " + etree.tostring(m))
        else:
        #if m is None or ts > str(m.ts):
            log.debug ("CREATING NEW MODULE: %s " % name)
            m = data_service.new_resource(module_def)
            #m = bisquik2db (doc = module_def)
            #module = db2tree (m, baseuri = self.module_resource.baseurl)
        return m

    def new(self, resource, xml, **kw):
        """ Create a new endpoint or endpoint set
        Allows an engine to register a set of modules in a single
        request
        """
        self.invalidate ("/ms/")
        log.debug ("engine_register:new %s" % xml)
        if isinstance (xml, etree._Element):
            resource = xml
        else:
            resource = etree.XML (xml)
        for module_def in resource.getiterator('module'):
            codeurl = module_def.get ('codeurl')
            engine_url = module_def.get ('engine_url', None)
            if codeurl is None or not codeurl.startswith('http://'):
                if engine_url is not None:
                    log.debug ("Engine_url is deprecated. please use codeurl ")
                    codeurl = engine_url
                    module_def.set('codeurl', engine_url)
            if codeurl is None or not codeurl.startswith('http://'):
                log.error ("Could not determine module codeurl during registration")
                raise abort(400)

            module = self.register_module(module_def)
            module_def.set ('uri', module.get ('uri'))

            service = session.query(Service).filter_by (
                module = module.get ('uri'),
                engine = engine_url).first()

            if module_def.get ('status') == 'disabled':
                if service:
                    status = service.findtag('status', True)
                    status.value = "disabled"
                    continue
            
            if not service:
                service = Service ()
                service.module = module.get('uri')
                service.engine = engine_url
                session.add(service)
            log.debug("updating contact of %s", service.uri)
            contact = service.findtag('last-contact', True)
            #contact.name = 'last-contact'
            contact.value = str(datetime.now())
            contact.type  = 'datetime'
            status = service.findtag('status', True)
            #status.name = 'status'
            status.value= 'enabled'

        return etree.tostring (resource)

    def modify(self, resource, xml, **kw):
        """
        Modify the mex in place.  Use to update status
        """
        raise abort(501)
        

    def get(self, resource, **kw):
        """
        fetches the resource, and returns a representation of the resource.
        """
        if resource:
            return etree.tostring (resource)

    def append(self, resource, xml, **kw):
        """ Register a new engine resource
        """

    def delete(self, resource,  **kw):
        """ Delete the engine resource 
        """
    
