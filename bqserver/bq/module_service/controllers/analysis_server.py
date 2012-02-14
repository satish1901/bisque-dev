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
import os
import time
import logging
import pkg_resources

from lxml import etree
from datetime import datetime, timedelta
from pylons.controllers.util import abort
from tg import controllers, expose
import tgscheduler

import bq
from bq import data_service
from bq.util import http
from bq.util.xmldict import d2xml, xml2d
from bq.core.identity import user_admin, not_anonymous, get_user_pass
from bq.core.permission import *
from bq.exceptions import RequestError
from bq.core.controllers.proxy import exposexml

from repoze.what import predicates 
from bq.core.service import ServiceController
from bq.module_service import model

from bq.core.model import DBSession 

log = logging.getLogger("bq.module_service.analysis")


class AnalysisServer(ServiceController):
    service_type = "analysis"
    
    def __init__(self, server_url = None):
        super(AnalysisServer, self).__init__(uri = server_url)
        #self.url = server_url

    @expose(template='bq.module_service.templates.browse')
    def index (self, **kw):
        """Return the list of active modules as determined by the registered services
        """
        log.info("ANALYSIS INDEX")
        user = bq.core.identity.get_user()
        if user:
            wpublicVal='false'
        else:
            wpublicVal='true'

        return dict(query=kw.pop('tag_query', None),
                    layout=kw.pop('layout', 1),
                    tagOrder=kw.pop('tag_order', ''),
                    offset=kw.pop('offset', 0),
                    dataset=kw.pop('dataset', '/module_service/'),
                    user_id = "",
                    page = kw.pop('page', 'null'),
                    view  = kw.pop('view', ''),
                    count = kw.pop ('count', '10'),
                    wpublic = kw.pop('wpublic', wpublicVal),
                    analysis = None)



__controller__ = AnalysisServer
def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'module_service', 'public'))]


def initialize(uri):
    log.info ("Starting Analysis Service")
    return  AnalysisServer(uri)
