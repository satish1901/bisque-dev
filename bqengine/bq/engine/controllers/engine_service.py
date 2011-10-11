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

"""
import os
import logging
import pkg_resources
import traceback, sys
import os,socket
import logging
import urlparse
import Queue
from datetime import datetime
from copy import deepcopy
import threading, thread
import time
from lxml import etree

from pylons.controllers.util import abort
import tg
from tg import config, controllers, expose, redirect, override_template


from pylons.i18n import ugettext as _, lazy_ugettext as l_
from repoze.what import predicates 

from bq import  module_service
from bq.core.service import ServiceController, BaseController
from bq.core.exceptions import EngineError, RequestError
from bq.core.identity  import get_user_pass
#from bq.core.proxy import ProxyRewriteURL
from bq.core.commands.configfile import ConfigFile

from bq.util.hostutils import same_host
from bq.util import http
from bq.util.http.thread_pool import ThreadPool, makeRequests

from adapters import MatlabAdapter, PythonAdapter, ShellAdapter, RuntimeAdapter

log = logging.getLogger('bq.engine_service')

MODULE_PATH = config.get('bisque.engine_service.local_modules', 'modules')
HEARTBEAT   = config.get('bisque.engine_service.hb');
engine_root = '/'.join ([config.get('bisque.server') , 'engine_service'])

def method_unavailable (msg=None):
    abort(403)
    
def method_not_found():
    abort(404)

def server_unavailable ():
    abort(503)

def illegal_operation():
    abort(501)



def read_xml_body():
    clen = int(tg.request.headers.get('Content-Length')) or 0
    content = tg.request.headers.get('Content-Type')
    if content.startswith('text/xml') or content.startswith('application/xml'):
        return etree.XML(tg.request.body_file.read(clen))
    return None

class HeartBeat (threading.Thread):
    """A thread used to communicate runtime information when engine is active
    
    The HB is activate whenever the engine is executing a module.
    The HB messages are sent to the message_service with status information 
    """

    def __init__(self, es, name="asynchb"):
        threading.Thread.__init__(self, name=name)
        self.requests = Queue.Queue()
        self.es = es
        self.setDaemon(True)
        self.timeout = None;
        #self.pool = ThreadPool (4)

    def run(self):
        
        #self.hb()
        log.debug ('hb.run')
        while 1:
            log.debug ('begin run')
            
            try:
                #self.pool.poll()
                
                func, data, respfunc = self.requests.get(True, self.timeout)
                self.es.lock.acquire()
                if self.es.jobs > 0:
                    self.timeout= HEARTBEAT
                self.es.lock.release()

                if (func is None):
                    self.hb()
                    continue
                
            except Queue.Empty, e:
                self.es.lock.acquire()
                if self.es.jobs == 0:
                    # after proccessing any requests
                    # turn off processing until next wakeup.
                    self.timeout=None
                self.es.lock.release()
                self.hb()
                continue
            

            response = None
            try:
                largs = data[0]
                kwargs = data[1]
                response = func(*largs, **kwargs)
                if respfunc:
                    respfunc(response)
            except (socket.error, RequestError), val:
                log.debug ("Caught error in heartbeat: %s" % val)
                self.requests.put ( (func, data, respfunc), block=True)
                log.debug ("                         : %s retry in 5 ", func)
                time.sleep(5)
                
            except:
                excType, excVal, excTrace  = sys.exc_info()
                log.error ("In heartbeat request:\n"
                           + "   function " + str (func) + ":" +str(data) +"->" + str(response) + "\n"
                           + "   Exception:\n"
                           + "   ".join(traceback.format_exception(excType,excVal, excTrace))
                           )
               

    def hb(self, job=None):
        hb = etree.Element ('heartbeat', status = self.es.status, jobs = str(self.es.jobs), uri = self.es.url)
        if job:
            hb.append(job)
        try:
            resp = module_service.heartbeat(hb)
            log.debug("HB response is " + etree.tostring(resp))
                    
            if resp.get('ack') == 'UNKNOWN' and self.es.status != 'busy':
                response = module_service.register_engine(body = etree.tostring(self.es.engine))
                self.es.addmodules(response)
        except: 
            log.debug("MS Server Heartbeat failed")

            

    def request(self, func, respfunc=None, *largs, **kw):
        self.requests.put ( (func, [largs, kw] , respfunc), block=True)

    def wakeup(self):
        self.requests.put ( (None, [[], {}] , None), block= True)

""" REMOVED

    def new_mex (self, adapterfun, module, mex,
                 callback=None, callexc=None):
        mexs = makeRequests (adapterfun, ((module, mex), {}),
                            self.mex_success,
                            self.mex_exception)
        for m in mexs:
            m.user_call = callback
            m.user_exc  = callexc
            m.mex = mex
            m.module = module
            self.pool.putRequest (m, timeout=30)
            return m
            
    def mex_success(self, work_req, result):
        if work_req.user_call:
            work_req.user_call(m.mex)

    def mex_exception(self, work_req, exc):
        if work_req.user_exc:
            work_req.user_exc(m.mex, exc)
    def wait(self, work_req):
        self.pool.wait_for (work_req)

"""

def initialize_available_modules(engines):
    '''Load a local directory with installed modules.

    Return a list of loaded module xml descriptors
    '''
    available = []
    unavailable = []
    log.debug ("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW") 
    log.debug (MODULE_PATH) 
    log.debug ("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW") 
    for g in os.listdir(MODULE_PATH):
        #log.debug ("Registering Module: " + str(g))    
        #xmlfile = MODULE_PATH +'/'+ g + '/' + g + '.xml'

        ### Check that we are in a module and it is enabled.
        cfg = os.path.join(MODULE_PATH, g, 'runtime-bisque.cfg')
        if not os.path.exists(cfg):
            log.debug ("Skipping %s : no runtime-bisque.cfg" % g)
            continue
        cfg = ConfigFile (cfg)
        mod_vars = cfg.get (None, asdict = True)
        enabled = mod_vars.get('module_enabled', 'False') == "True"
        status = (enabled and 'enabled') or 'disabled'
        if not enabled :
            log.debug ("Skipping %s : disabled" % g)
            continue
        ### Check that there is a valid Module descriptor
        xmlfile = unicode(os.path.join (MODULE_PATH, g, g + '.xml'))
        if not os.path.exists(xmlfile):
            continue
        log.debug ("found module at %s" % xmlfile)
        module_root = etree.parse (open(xmlfile)).getroot()
        ts = os.stat(xmlfile)
        # for elem in module_root:
        if module_root.tag == "module":
            module_name = module_root.get('name')
            module_path = module_root.get('path')
            module_type = module_root.get('type')
            module_root.set('ts', str(datetime.fromtimestamp(ts.st_mtime)))
            engine = engines.get(module_type, None)
            if engine and engine.check (module_root): 
                # a = dict (elem.attrib)
                # newmod = etree.Element('module', **a)
                # for el in elem.getiterator():
                #     if el.tag == 'input':
                #     etree.SubElement(newmod, 'tag', name="formal_input",
                #     value = el.attrib['name'])
                module_root.set('engine_url', engine_root + '/'+module_name)
                module_root.set('status', status)
                #module_root.set('codeurl', engine_root + '/'+module_name)
                available.append(module_root)
            else:
                unavailable.append ( module_name)
                log.debug("Skipping %s : engine_check failed" % module_name)
                
    return available, unavailable
            
class EngineServer(ServiceController):
    service_type = "engine_service"

    def __init__(self, server_url = None):
        super(EngineServer, self).__init__(server_url)
        
        self.lock = thread.allocate_lock()
        
        self.hb = HeartBeat(self)
        self.hb.start()

        self.modules = {}
        self.status = "free"
        self.jobs = 0
        self.running = {}
        self.module_by_name = {}
        self.resource_by_name = {}

        #self.module_resource = EngineResource()
        self.engines = { 'matlab': MatlabAdapter(),
                         'python': PythonAdapter(),
                         'shell' : ShellAdapter(),
                         'runtime' : RuntimeAdapter(),
                         #'lam' : LamAdapter(),
                         }
        modules, unavailable = initialize_available_modules(self.engines)
        log.debug ('found modules= %s' % str(modules))
        self.engine = etree.Element ('engine', uri = engine_root,
                                     status = self.status, jobs = str(self.jobs))
        for m in modules:
            self.engine.append (m)
            self.module_by_name [m.get("name")] = m
        self.unavailable = unavailable
        self.hb.request(module_service.register_engine, body = etree.tostring(self.engine), respfunc = self.addmodules)

        #response = module_service.register_engine(engine)
        #for mod in response:
        #    self.modules[mod.attrib['uri']] = mod
    
    @expose('bq.engine.templates.engine_modules')
    def index(self):
        """Return the list of available modules urls"""

        modules = [ ("%s/%s" % (self.url, k), k) for k in self.module_by_name.keys()]
        return dict(modules=modules)


    @expose(content_type="text/xml")
    def default(self, *path, **kw):
        log.debug ('in default %s' % str( path) )
        path = list(path)
        if len(path) > 0:
            module_name = path.pop(0)

            if module_name in self.unavailable:
                method_unavailable("Module is disabled")
            
            module_resource  =   self.resource_by_name.get (module_name, None)
            if module_resource is None:
                log.warn ("No module by name of %s" % module_name)
                method_not_found()

            return module_resource.default(*path, **kw)
        return super(EngineServer, self).default(*path, **kw)
        
    def addmodules(self, response):
        if not isinstance(response, etree._Element):
            response = etree.XML(response)
        #self.modules = {}
        self.lock.acquire()
        if response.get ('error', None) != None:
            time.sleep(10)
            self.hb.request(module_service.register_engine, body = etree.tostring (self.engine), respfunc = self.addmodules)
        for mod in response:
            #log.debug("Response = " + etree.tostring(response))
            if 'uri' not in mod.attrib:
                log.error ('addmodules BAD module' + etree.tostring (mod))
                continue
            log.debug("Adding module %s %s" % (mod.get('name'),  mod.attrib['uri']))

            module_xml = deepcopy(mod)
            self.modules[mod.attrib['uri']] =  module_xml
            setattr(EngineServer, mod.get('name'), EngineModuleResource(module_xml))

        log.debug("Modules =  " + str(self.modules))
        self.lock.release()

    @expose(content_type="text/xml")
    def status1(self):
        return self.status_()

    def status_(self):
        response = etree.Element ('response')
        etree.SubElement (response, 'engine', uri = self.url,
                          status = self.status, jobs = str(self.jobs))
        return etree.tostring(response)

        

    @expose()
    def module_list (self):
        return str(self.modules)



    ########################################################
    # Programmatic access
        


class AsyncRequest:

    class HttpThread(threading.Thread):
        def __init__(self, id, requests):
            threading.Thread.__init__(self, name="HttpThread"+str(id))
            self.requests = requests
            self.setDaemon(True)

        def run(self):
            while 1:
                req = self.requests.get (True)
                log.debug ("awake with " + str (req))
                try:
                    resp, content = http.xmlrequest(req[0], req[1], req[2], req[3], userpass=req[6])
                except:
                    resp, content  =  ({ 'status': "404" }, None)
    
                callback = req[4]
                if callback:
                    callback (resp, content, req[5])


    def __init__(self, numthreads):
        self.requests = Queue.Queue()
        self.threads = []
        for i in range(numthreads):
            self.threads = self.HttpThread(i, self.requests)
            self.threads.start()

    def request(self, target, method="GET", body=None, headers=None, callback=None, calldata=None, user_pass=None):
        self.requests.put ( (target, method, body, headers, callback, calldata, user_pass), True)



class RemoteEngineServer(object):
    def __init__(self):
        #self.url = serverurl
        self.async = AsyncRequest(5)
        
        
    def execute(self, mextree, server_url, callback=None, calldata=None, up=None):
        if not up:
            up = get_user_pass ()
        log.debug ('user_pass' + str(up))

        body = ProxyRewriteURL.for_output(etree.tostring(mextree))
        log.debug ("POST " + body)
        self.async.request(server_url+'/mex_execute',
                           "POST", 
                           body,
                           {'content-type':'text/xml' },
                           callback,
                           calldata,
                           user_pass= up)


from tg import require
from repoze.what.predicates import not_anonymous
from bq.config.middleware import public_file_filter
class EngineModuleResource(BaseController):
    """Convert the local module into one accessable as a web resource"""

    adapters = { 'matlab': MatlabAdapter(),
                 'python': PythonAdapter(),
                 'shell' : ShellAdapter(),
                 'runtime' : RuntimeAdapter(),
                 }


    def filepath(self,*path):
        return os.path.join (MODULE_PATH, self.name, *path)


    def __init__(self, module_xml):
        """Create a web endpoint for the module"""
        self.running = {}
        self.module_xml = module_xml
        self.module_uri = module_xml.get('uri')
        self.name       = module_xml.get('name')

        static_path = os.path.join (MODULE_PATH, self.name, 'public')
        if os.path.exists(static_path):
            log.info ("adding static path %s" % static_path)
            public_file_filter.add_path(static_path,
                                        static_path,
                                        "/engine_service/%s" % self.name)

    def serve_entry_point(self, node, default='Entry point was not found...', **kw):
        """Provide a general way to serve an entry point"""

        from pylons.controllers.util import forward
        from paste.fileapp import FileApp    
        
        if isinstance(node, str) is True:
            node = self.module_xml.xpath(node)
        
        text = default   
        if not node is None:
            node = node[0]
            type = node.get('type', None)
            if type == 'file':
                path = self.filepath(node.get('value'))
                if os.path.exists(path):
                    return forward(FileApp(path))
                
            else:
                text = node.get ('value', None)
                if node.get ('value', None) is None:
                    # Using a <value><![CDATA]</value>
                    text = (node[0].text)
        
        if text is None:
            abort(404)
        return text

#    def load(self, token, **kw):
#        """Find the specified execution by the MexID"""
#        return self.running[token]

    def definition_as_dict(self):
        def _xml2d(e, d, path=''):
            for child in e:
                name  = '%s%s'%(path, child.get('name', ''))
                value = child.get('value', None) 
                ttype = child.get('type', None)                 
                if not value is None:
                    if not name in d:
                        d[name] = value
                    else:
                        if isinstance(d[name], list):
                            d[name].append(value)
                        else:
                            d[name] = [d[name], value]
                    if not ttype is None:
                        d['%s.type'%name] = ttype
                d = _xml2d(child, d, path='%s%s/'%(path, child.get('name', '')))
            return d

        d = _xml2d(self.module_xml, {})
        d['module/name'] = self.name
        d['module/uri']  = self.module_uri 
        if not 'title' in d: d['title'] = self.name
        return d
        

    @expose()
    def index(self, **kw):
        """Return interface of the Module

        A default interface will be generate if not defined by the
        module itself.
        """
        node = self.module_xml.xpath('//tag[@name="interface"]')
        if not node:
            override_template(self.index, "genshi:bq.engine.templates.default_module")
            return dict (module_uri  = self.module_uri,
                         module_name = self.name,
                        module_def = self.definition_as_dict(),
                         extra_args  = kw
                         )
        return self.serve_entry_point(node)        

    @expose()
    def interface(self, **kw):
        """Provide Generate a module interface to be used"""
        node = self.module_xml.xpath('//tag[@name="interface"]')
        if not node:
            override_template(self.interface, "genshi:bq.engine.templates.default_module")
            return dict (module_uri  = self.module_uri,
                         module_name = self.name,
                         module_def = self.definition_as_dict(),                         
                         extra_args  = kw
                         )
        return self.serve_entry_point(node)

    @expose()
    def help(self, **kw):
        """Return the help of the module"""
        help_text =  "No help available for %s" % self.name
        return self.serve_entry_point('//tag[@name="help"]', help_text)

    @expose()
    def thumbnail(self, **kw):
        """Return the thumbnail of the module"""
        return self.serve_entry_point('//tag[@name="thumbnail"]', 'No thumbnail found')

    @expose()
    def description(self, **kw):        
        """Return the textual desfription of the module"""
        return self.serve_entry_point('//tag[@name="description"]', 'No description found')

    @expose(content_type="text/xml")
    def definition(self, **kw):
        # rewrite stuff here for actual entry points
        return etree.tostring(self.module_xml)

    @expose()
    def status (self):
        """Return  executions of the Module"""

    @expose()
    def public(self, *path, **kw):
        """Deliver static content for the Module"""
        log.debug ("in Static %s %s" % (str(path), str(kw)))

        static_path = os.path.join (MODULE_PATH, self.name, 'public', *path)
        if os.path.exists(static_path):
            cont = open(static_path)
            return cont.read()

        raise abort(404)
        
        
#    def create(self, **kw):
#        """Used by new for the factory"""
#        return ""
    
#    def new(self, factory, xml, **kw):
#        """Start an execution a new execution"""
#        #
#        mex = etree.XML(xml)
#        log.debug ("New execution of %s" % etree.tostring(mex))
#        mex = self.start_execution(mex)
#        response =  etree.tostring(mex)
#        log.debug ("return %s " % response)
#        return response

    def get(self, resource, **kw):
        """Return the interface of the  specified module execution"""

    def append(self, resource, xml, **kw):
        """Send new data the specified module execution"""

    
    @expose(content_type='text/xml')
    @require(not_anonymous(msg='You need to log-in to run a module'))    
    def execute(self, entrypoint = 'main'):
        mex = read_xml_body()
        if mex is not None:
            log.debug ("New execution of %s" % etree.tostring(mex))
            mex = self.start_execution(mex)
            response =  etree.tostring(mex)
            log.debug ("return %s " % response)
            return response
        else:
            illegal_operation()
        
    def start_execution(self, mextree):
        """Start the execution of the mex for this module"""
        b, mexid = mextree.get ('uri').rsplit('/',1)
        log.debug ('engine: execute %s' % (mexid))
        module = self.module_xml
        try:
            try:
                #up = get_user_pass ()
                #log.debug ('user_pass' + str(up))
                self.running [mexid] = mextree
                mex_moduleuri = mextree.get ('module')
                log.debug ('moduleuri ' + str(mex_moduleuri))
                #if mex_moduleuri != module.get ('uri'):
                #    return None
                adapter_type = module.get('type')
                adapter = self.adapters.get(adapter_type, None)
                if not adapter:
                    log.debug ('No adaptor for type %s' % (adapter_type))
                    raise EngineError ('No adaptor for type %s' % (adapter_type))
                exec_id = adapter.execute (module, mextree)
                mextree.append(etree.Element('tag', name='execution_id', value=str(exec_id)))
                
                #if not mextree.get ('asynchronous'):
                #    mextree.set('status', "FINISHED")

            except EngineError, e:
                log.exception ("EngineError")
                mextree.set('status', 'FAILED')
                mextree.append(etree.Element('tag', name='error_message', value=str(e)))
                log.debug ('QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ' + str(e))
                tg.response.status_int = 500
            except:
                log.exception ("Execption in adaptor:" )
                mextree.set('status', 'FAILED')
                excType, excVal, excTrace  = sys.exc_info()
                trace =  " ".join(traceback.format_exception(excType,excVal, excTrace))
                mextree.append (etree.Element ('tag',name='execption_trace', value=str(trace)))
                tg.response.status_int = 500

        finally:
            #module_service.end_execute(mextree)
            self.running.pop(mexid, None)
            #if not self.running:
            #    self.status = "free"
            #    self.jobs = self.jobs-1
            return mextree


##########################################
#  Module accesible 


_preferred = None
_servers = {} 
def initialize(uri=None):
    global _preferred, _servers
    
    server = None
    server_url = config.get('bisque.engine_service.local_server', None)
    if server_url:
        server = EngineServer(server_url)
        _preferred = _servers[server_url] = server
    
    else:
        server = RemoteEngineServer()
        _preferred = server
        
    #server_url = config.get('bisquik.engine_service.remote', None)
    #if server_url:
    #    server = RemoteEngineServer(server_url)
    #    _preferred = _servers[server_url] = server
                
    log.debug ("initialize servers: " + str(_servers))
    return _preferred

def preferred_server(): return _preferred

def find_server(server_uri):
    global _servers
    global _preferred
    server = _servers.get(server_uri, None)

    if not server:
        return _preferred
    
    return server

    #if not server:
        #net = urlparse.urlsplit(server_uri)[1]
        #if same_host (net):
            #log.debug('created local server' + server_uri)
            #server = EngineServer(server_uri)
        #else:
            #log.debug('created remote server' + server_uri)
            #server = RemoteEngineServer(server_uri)
        #_servers[server_uri]  = server
    #log.debug ("find_servers: " + str(_servers))
    #return server

def execute(mextree, server_uri, **kw):
    log.debug ("ALL servers: " + str(_servers))
    log.debug ("using server: " + str(server_uri))
    server = find_server(server_uri)

    log.debug ("args " + str(kw))
    return server.execute(mextree, server_uri, **kw)





def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  EngineServer(uri)
    #directory.register_service ('engine', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqengine")
    package_path = pkg_resources.resource_filename(package,'.')
    return [(package_path, os.path.join(package_path, 'bq', 'engine', 'public'))]

#def get_model():
#    from engine import model
#    return model

__controller__ =  EngineServer
