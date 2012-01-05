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
  module service
"""
import os
import pkg_resources
from bq.core.service import service_registry
from bq.exceptions import RequestError
from controllers.module_server import ModuleServer

def find_server(server):
    return service_registry.find_service ('module_service')

def uri():
    server = find_server('module_service')
    return server.uri

def register_engine(body, server = None ):
    '''request registration of the engine to the module server
    given the module URI and the ElementTree Module descriptor
    '''
    if server is None:
        server = service_registry.find_service ('module_service')
    if server:
        return server.register_engine (body = body)
    raise RequestError ("no server available")



def begin_internal_mex(**kw):
    """Begin an internal mex for tracking changes from users"""
    server = service_registry.find_service ('module_service')
    return server.begin_internal_mex(**kw)

def end_internal_mex(mexid):
    server = service_registry.find_service ('module_service')
    return server.end_internal_mex(mexid)

def execute(module_uri, **kw):
    """Execute the module specified(create a mex request)
       Use the passed arguments to create the mex i.e.
       execute('/module/10', image_url='/ds/image/1', threshhold='90')
       <mex module_uri='/module/10'>
         <tag name='image_url' value='/ds/image/1' >
         ...
       </mex>
    """
    server = _preferred
    return server.execute(module_uri, **kw)
    

def begin_execute (mex_request, server = None):
    if server is None: server = service_registry.find_service ('module_service')
    return server.begin_execute (mex_request)

def end_execute (mex_request, server = None):
    if server is None: server = service_registry.find_service ('module_service')
    return server.end_execute (mex_request)
    
def heartbeat(hbdoc, server = None):
    if server is None: server = service_registry.find_service ('module_service')
    return server.heartbeat(hbdoc)

def engines(server = None):
    if server is None: server = service_registry.find_service ('module_service')
    return server.engine.dir()


def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    #log.debug ("initialize " + uri)
    service =  ModuleServer(uri)
    return service


def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqcore")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'module_service', 'public'))]

def get_model():
    from bq.module_service import model
    return model

__controller__ =  ModuleServer
