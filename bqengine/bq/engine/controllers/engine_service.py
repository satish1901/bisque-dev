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
import socket
import logging
import urlparse
import Queue
import threading, thread
import time
import subprocess
import multiprocessing
from datetime import datetime
from copy import deepcopy
from lxml import etree

from pylons.controllers.util import abort
import tg
from tg import config, controllers, expose, redirect, override_template


from pylons.i18n import ugettext as _, lazy_ugettext as l_
from repoze.what import predicates 

from bq.core.service import ServiceController, BaseController
from bq.exceptions import EngineError, RequestError

from bq.util.configfile import ConfigFile
from bq.util.hostutils import same_host
from bq.util import http
from bq.util.http.thread_pool import ThreadPool, makeRequests
from bq.util.paths import bisque_path, config_path
from bq.util.copylink import copy_link

from runtime_adapter import RuntimeAdapter

log = logging.getLogger('bq.engine_service')

MODULE_PATH = config.get('bisque.engine_service.local_modules', bisque_path('modules'))
HEARTBEAT   = config.get('bisque.engine_service.hb');
engine_root = '/'.join ([config.get('bisque.server') , 'engine_service'])


def fun(p):
    x = os.system ('/bin/ls')
    return x


def execone(params):
    """ Execute a single process locally """
    #command_line, stdout = None, stderr=None, cwd = None):
    #print "Exec", params
    command_line = params['command_line']
    rundir = params['rundir']
    
    if os.name=='nt':
        exe = which(command_line[0])
        exe = exe or which(command_line[0] + '.exe')
        exe = exe or which(command_line[0] + '.bat')
        if exe is None:
            raise RunnerException ("Executable was not found: %s" % command_line[0])                
        command_line[0] = exe
    print 'CALLing %s in %s' % (command_line,  rundir)
    return subprocess.call(params['command_line'],
                           stdout = open(params['logfile'], 'a'),
                           stderr = subprocess.STDOUT,
                           shell  = (os.name == "nt"),
                           cwd    = rundir,
                           )

def method_unavailable (msg=None):
    abort(503)
    
def method_not_found():
    abort(404)

def server_unavailable ():
    abort(503)

def illegal_operation():
    abort(501)

def read_xml_body():
    "Read the xml body from a TG request"
    clen = int(tg.request.headers.get('Content-Length')) or 0
    content = tg.request.headers.get('Content-Type')
    if content.startswith('text/xml') or content.startswith('application/xml'):
        return etree.XML(tg.request.body_file.read(clen))
    return None

def load_module(module_path, engines = None):
    """load a module XML file if enabled and available

    :param module_path: path to module.xml
    :param engines: A dict of engine adapters i.e.
    """
    module_name = os.path.basename (module_path)
    module_dir = os.path.dirname (module_path)
    cfg = os.path.join(module_dir, 'runtime-module.cfg')
    if not os.path.exists(cfg):
        log.debug ("Skipping %s (%s) : no runtime-module.cfg" % (module_name, cfg))
        return None
    cfg = ConfigFile (cfg)
    mod_vars = cfg.get (None, asdict = True)
    enabled = mod_vars.get('module_enabled', 'true').lower() == "true"
    status = (enabled and 'enabled') or 'disabled'
    if not enabled :
        log.debug ("Skipping %s : disabled" % module_name)
        return None
    ### Check that there is a valid Module descriptor
    if not os.path.exists(module_path):
        return None
    log.debug ("found module at %s" % module_path)
    try:
        with open(module_path) as xml:
            module_root = etree.parse (xml).getroot()
    except etree.XMLSyntaxError:
        log.exception ('while parsing %s' % module_path)
        return None
    bisque_cfg = os.path.join(module_dir,'runtime-bisque.cfg')

    #if  os.path.exists(bisque_cfg):
    #    os.unlink (bisque_cfg)
    #os.link (config_path('runtime-bisque.cfg'), bisque_cfg)
    copy_link (config_path('runtime-bisque.cfg'), bisque_cfg)

    ts = os.stat(module_path)
    # for elem in module_root:
    if module_root.tag == "module":
        module_name = module_root.get('name')
        module_path = module_root.get('path')
        module_type = module_root.get('type')
        module_root.set('ts', str(datetime.fromtimestamp(ts.st_mtime)))
        engine = engines and engines.get(module_type, None)
        if engine and not engine.check (module_root): 
            return None
        module_root.set('engine_url', engine_root + '/'+module_name)
        module_root.set('status', status)
        for x in module_root.iter(tag=etree.Element):
            x.set('permission', 'published')
        return module_root
    return None



def initialize_available_modules(engines):
    '''Load a local directory with installed modules.

    Return a list of loaded module xml descriptors
    '''
    available = []
    unavailable = []
    log.debug ("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW") 
    log.debug ('examining %s ' % MODULE_PATH) 
    log.debug ("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW") 
    for g in os.listdir(MODULE_PATH):
        module_path = os.path.join(MODULE_PATH, g, g + '.xml')
        module_root = load_module(module_path, engines)
        if module_root:
            available.append(module_root)
        else:
            unavailable.append ( g )
            log.debug("Skipping %s : engine_check failed" % g)
                
    return available, unavailable

#################################################################
##            
class EngineServer(ServiceController):
    """Engine server : provide web access to analysis modules
    """
    service_type = "engine_service"

    def __init__(self, server_url = None):
        super(EngineServer, self).__init__(server_url)
        self.modules = {}
        self.status = "free"
        self.jobs = 0
        self.running = {}
        self.module_by_name = {}
        self.resource_by_name = {}
        self.mpool = multiprocessing.Pool(4)

        #self.module_resource = EngineResource()
        self.engines = { #'matlab': MatlabAdapter(),
                         #'python': PythonAdapter(),
                         #'shell' : ShellAdapter(),
                         'runtime' : RuntimeAdapter(),
                         #'lam' : LamAdapter(),
                         }
        modules, unavailable = initialize_available_modules(self.engines)
        log.debug ('found modules= %s' % str(modules))
        self.unavailable = unavailable
        for module in modules:
            setattr(EngineServer, module.get('name'), EngineModuleResource(module, self.mpool))
            self.module_by_name[module.get('name')]  = module

    @expose('bq.engine.templates.engine_modules')
    def index(self):
        """Return the list of available modules urls"""
        server = urlparse.urljoin(config.get('bisque.server'), self.service_type)
        modules = [ ("%s/%s" % (server, k), k) for k in sorted(self.module_by_name.keys())]
        return dict(modules=modules)
    @expose(content_type="text/xml")
    def _default(self, *path, **kw):
        log.debug ('in default %s' % str( path) )
        path = list(path)
        if len(path) > 0:
            module_name = path.pop(0)
            if module_name in self.unavailable:
                method_unavailable("Module is disabled")
        return super(EngineServer, self)._default(*path, **kw)


##################################################################################
##
reserved_io_types = ['system-input']

from tg import require
from repoze.what.predicates import not_anonymous
from bq.config.middleware import public_file_filter
class EngineModuleResource(BaseController):
    """Convert the local module into one accessable as a web resource"""

    adapters = { #'matlab': MatlabAdapter(),
                 #'python': PythonAdapter(),
                 #'shell' : ShellAdapter(),
                 'runtime' : RuntimeAdapter(),
                 }

    def filepath(self,*path):
        return os.path.join (MODULE_PATH, self.name, *path)


    def __init__(self, module_xml, mpool):
        """Create a web endpoint for the module"""
        self.module_xml = module_xml
        self.module_uri = module_xml.get('uri')
        self.name       = module_xml.get('name')
        self.mpool = mpool
        self.define_io() # this should produce lists on required inputs and outputs

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
        if  len(node): # Found at least one xpath match
            node = node[0]
            type = node.get('type', None)
            if type == 'file':
                path = self.filepath(node.get('value'))
                if os.path.exists(path):
                    return forward(FileApp(path).cache_control (max_age=60*60*24*7*6))                   
                
            else:
                text = node.get ('value', None)
                if node.get ('value', None) is None:
                    # Using a <value><![CDATA]</value>
                    text = (node[0].text)
        
        if text is None:
            abort(404)
        return text


    def definition_as_dict(self):
        def _xml2d(e, d, path=''):
            for child in e:
                name  = '%s%s'%(path, child.get('name', ''))
                ttype = child.get('type', None) 
                value = child.get('value', None) 
                if value is not None:
                    if not name in d:
                        d[name] = value
                    else:
                        if isinstance(d[name], list):
                            d[name].append(value)
                        else:
                            d[name] = [d[name], value]
                    #if not ttype is None:
                    #    d['%s.type'%name] = ttype
                        
                d = _xml2d(child, d, path='%s%s/'%(path, child.get('name', '')))
            return d

        d = _xml2d(self.module_xml, {})
        d['module/name'] = self.name
        d['module/uri']  = self.module_uri 
        if not 'title' in d: d['title'] = self.name
        return d



#    <tag name="inputs">
#        <tag name="image_url"    type="image" />
#        <tag name="resource_url" type="resource">
#            <tag name="template" type="template">
#                <tag name="type" value="image" />
#                <tag name="type" value="dataset" />
#                <tag name="selector" value="image" />
#                <tag name="selector" value="dataset" />
#            </tag>            
#        </tag>      
#        <tag name="mex_url"      type="system-input" />
#        <tag name="bisque_token" type="system-input" />
#    </tag>
#    
#    <tag name="outputs">
#         <tag name="MetaData" type="tag" />
#         <gobject name="Gobjects" />
#    </tag>


    def define_io(self):
        
        def define_tempalte(xs):
            l = []
            for i in xs:
                r = i.tag
                n = i.get('name', None) 
                v = i.get('value', None)
                t = i.get('type', None)
                if t in reserved_io_types: continue
                x = { 'resource_type': r, 'name': n, 'value': v, 'type': t, }    

                tmpl = i.xpath('tag[@name="template" and @type="template"]/tag')
                for c in tmpl:
                    nn = c.get('name', None) 
                    vv = c.get('value', None)
                    if not nn in x:
                        x[nn] = vv
                    else:
                        if isinstance(x[nn], list):
                            x[nn].append(vv)
                        else:
                            x[nn] = [x[nn], vv]
                #if 'label' not in x: x['label'] = n
                l.append(x)
            return l        
        
        self.inputs  = define_tempalte( self.module_xml.xpath('//tag[@name="inputs"]/*') )
        self.outputs = define_tempalte( self.module_xml.xpath('//tag[@name="outputs"]/*') )
        log.debug(str(self.inputs))
        log.debug(str(self.outputs))
        

    @expose()
    def index(self, **kw):
        """Return interface of the Module

        A default interface will be generate if not defined by the
        module itself.
        """
        log.debug("index %s" % self.name)
        node = self.module_xml.xpath('//tag[@name="interface"]')
        log.debug('Interface node: '%node)
        if not node or not node[0].get('value', None):
            override_template(self.index, "genshi:bq.engine.templates.default_module")
            return dict (module_uri  = self.module_uri,
                         module_name = self.name,
                         module_def  = self.definition_as_dict(),
                         module_xml  = etree.tostring(self.module_xml),
                         
                         inputs  = self.inputs,
                         outputs = self.outputs,
                         
                         extra_args  = kw
                         )
        return self.serve_entry_point(node)        

    @expose()
    def interface(self, **kw):
        """Provide Generate a module interface to be used"""
        node = self.module_xml.xpath('//tag[@name="interface"]')
        log.debug('Interface node: '%node)
        if not node or not node[0].get('value', None):
            override_template(self.interface, "genshi:bq.engine.templates.default_module")
            return dict (module_uri  = self.module_uri,
                         module_name = self.name,
                         module_def  = self.definition_as_dict(),      
                         module_xml  = etree.tostring(self.module_xml),   
                         
                         inputs  = self.inputs,
                         outputs = self.outputs,                       
                                         
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
        log.debug("execute %s" % self.name)
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
                mex_moduleuri = mextree.get ('type')
                log.debug ('moduleuri ' + str(mex_moduleuri))
                #if mex_moduleuri != module.get ('uri'):
                #    return None
                adapter_type = module.get('type')
                adapter = self.adapters.get(adapter_type, None)
                if not adapter:
                    log.debug ('No adaptor for type %s' % (adapter_type))
                    raise EngineError ('No adaptor for type %s' % (adapter_type))
                exec_id = adapter.execute(module, mextree, self.mpool)
                mextree.append(etree.Element('tag', name='execution_id', value=str(exec_id)))
                
                #if not mextree.get ('asynchronous'):
                #    mextree.set('status', "FINISHED")

            except EngineError, e:
                log.exception ("EngineError")
                mextree.set('value', 'FAILED')
                mextree.append(etree.Element('tag', name='error_message', value=str(e)))
                log.debug ('QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ' + str(e))
                tg.response.status_int = 500
            except:
                log.exception ("Execption in adaptor:" )
                mextree.set('value', 'FAILED')
                excType, excVal, excTrace  = sys.exc_info()
                trace =  " ".join(traceback.format_exception(excType,excVal, excTrace))
                mextree.append (etree.Element ('tag',name='execption_trace', value=str(trace)))
                tg.response.status_int = 500

        finally:
            return mextree




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
