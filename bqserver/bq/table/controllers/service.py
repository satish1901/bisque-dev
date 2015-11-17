###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2015 by the Regents of the University of California     ##
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
Table server : access to tabular data, e.g. files CSV, HDF5, or other services...

DESCRIPTION
===========

URL:

/table/ID[/PATH1/PATH2/...][/RANGE][/COMMAND:PARS]

RANGE:
    defines region of interest within an N-D matrix, only valid if the path points to a matrix element
    range specifies a comma separated list of ranges for N-D data
    dimension order is column wise: i,j,k,... column, row, ....
    elements start at 0
    empty element means full range
    i - each range item can be a simple integer defining one element in that dimension,
    i:j - colon separated elements define range
    i:-j - minus sign defines element positions from the end

    ex:
    /table/00-XXXXX/mynode123/mytable123/12:15  - defines raws 12 through 15
    /table/00-XXXXX/mynode123/mytable123/12:15,2:3  - defines cells in raws 12 through 15 and cols 2 thtough 3


COMMAND:
    info - returns elemnets within a path, column headers, sizes and datatypes
           info call on an HDF5 root will list all available nodes
           info call on a CSV file will list column headers, column sizes and datatypes
           info call on an Excel root will list all available sheets
    format - xml,json,csv - format:json


RESTful API
=============

    GET - reads elements in the requested range returning in the requested format
          specified either by HTTP Content negotiation (Accept header) - Accept: text/csv
          or a format command - format:csv
    PUT - replaces elements in the requested range from data posted in one of supported formats
          defined by the HTTP Content-Type header - Content-Type: application/json
    POST - same as PUT
    DELETE - removes elements if possible

Responses:
    400 Bad Request
    401 Unauthorized
    500 Internal Server Error
    501 Not Implemented


Examples:

For HDF5 input
-----------------

/table/00-XXXXX/mynode123/mytable123/info/format:json
/table/00-XXXXX/mynode123/mytable123/12:16/format:json


For CSV input
----------------

/table/00-XXXXX/info/format:json
/table/00-XXXXX/12:16/format:xml



ARCHITECTURE
==============

  url_string
      |
[input driver] - consumes URL path while possible, reads data and returns the rest of uninterpreted URL path plus numpy matrix with data
      |
numpy_array, sub_url_string
      |
[operations] - operates on data matrix and removes its own operations from path
      |
numpy_array, sub_url_string
      |
[output driver] - converts numpy matrix into output format and streams out
      |
    stream

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, request, response, require
from repoze.what import predicates
from bq.core.service import ServiceController
from pylons.controllers.util import abort

# imports for table server
from lxml import etree
import sys
import inspect
from datetime import datetime
import urllib
import cStringIO as StringIO
from urllib import quote
from urllib import unquote
import inspect
from itertools import *
from bqapi import *

from bq.core import identity
from bq import data_service
from bq import blob_service

log = logging.getLogger("bq.table")

import csv
try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import pandas as pd
except ImportError:
    log.info('Pandas was not found but required for table service!')

try:
    import json
except ImportError:
    log.info('Json was not found but needed for JSON output...')

from .plugin_manager import PluginManager
from .table_base import TableBase
from .table_exporter import TableExporter
from .table_operation import TableOperation

################################################################################
# misc
################################################################################

def get_arg(table, name, defval=None, **kw):
    v = kw.get(name, defval)
    idx = [i for i, elem in enumerate(table.path) if name in elem]
    if len(idx)>0:
        return table.path[idx[0]]

def is_arg(table, name):
    idx = [i for i, elem in enumerate(table.path) if name in elem]
    return len(idx)>0

# simply accept two characters for range: ":" or ";" due to parsing error in turbogears for ":"
def parse_subrange(rng):
    #rng = urllib.unquote(rng)
    v = rng.split(';', 1) if ';' in rng else rng.split(':', 1)
    return [int(i) for i in v]

################################################################################
# TableController
################################################################################

class TableController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "table"

    def __init__(self, server_url):
        super(TableController, self).__init__(server_url)
        self.baseuri = server_url
        self.basepath = os.path.dirname(inspect.getfile(inspect.currentframe()))

        self.importers = PluginManager('import', os.path.join(self.basepath, 'importers'), TableBase)
        self.exporters = PluginManager('export', os.path.join(self.basepath, 'exporters'), TableExporter)
        self.operations = PluginManager('operation', os.path.join(self.basepath, 'operations'), TableOperation)
        self.operations.plugins['format'] = None # format is a virtual operation, exporters are used here
        self.operations.plugins['info'] = None # virtual operation driving exporter function

        log.info('Table service started...')

    #@expose('bq.table.templates.index')
    @expose(content_type='text/xml')
    def index(self, **kw):
        """Add your service description here """
        response = etree.Element ('resource', uri=self.baseuri)
        etree.SubElement(response, 'method', name='%s/ID[/PATH1/PATH2/...][/RANGE][/COMMAND:PARS]'%self.baseuri, value='Executes operations for a given table ID.')
        return etree.tostring(response)

    def check_access(self, uniq):
        resource = data_service.resource_load (uniq = uniq)
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    @expose()
    def _default(self, *args, **kw):
        """find export plugin and run export"""
        log.info ("STARTING table (%s): %s", datetime.now().isoformat(), request.url)
        path = request.url.replace(self.baseuri, '').split('/')
        path = [urllib.unquote(p) for p in path if len(p)>0]
        log.debug("Path: %s", path)

        # /table/ID[/PATH1/PATH2/...][/RANGE][/COMMAND:PARS]
        if len(path)<1:
            abort(400, 'Element ID is required as a first parameter, ex: /table/00-XXXXX/format:xml' )
        uniq = path.pop(0)

        # check permissions
        resource = self.check_access(uniq)
        log.debug('Resource: %s', etree.tostring(resource))

        # load table
        table = None
        for n, r in self.importers.plugins.iteritems():
            table = r(uniq, resource, path, url=request.url)
            if table is not None and table.isloaded() == True:
                break;
        log.debug('Inited table: %s',str(table))

        # range read
        candidate = table.path[0].split(':')[0]
        if candidate not in self.operations.plugins:
            try:
                rng = table.path.pop(0)
                rng = rng.split(',') # split for per-dimension ranges
                rng = [parse_subrange(i) for i in rng] # split for within dimension ranges
            except Exception:
                abort(400, 'Malformed range request')
            table.read(rng=rng)
        #else: # full read is not permitted anymore
        #    table.read()
        log.debug('Loaded table: %s', str(table))

        # operations consuming the rest of the path
        i = 0
        a = table.path[i] if len(table.path)>i else None
        while a is not None:
            a = a.split(':',1)
            op,arg = a if len(a)>1 else a + [None]
            if op in self.operations.plugins and self.operations.plugins[op] is not None:
                table.path.pop(0)
                self.operations.plugins[op]().execute(table, arg)
            else:
                i += 1
            a = table.path[i] if len(table.path)>i else None
        log.debug('Processed table: %s', str(table))

        # export
        out_format = get_arg(table, 'format:', defval='format:xml', **kw).replace('format:', '')
        out_info   = is_arg(table, 'info')
        log.debug('Format: %s, Info: %s', out_format, out_info)
        if out_format in self.exporters.plugins:
            if out_info is True:
                r = self.exporters.plugins[out_format]().info(table)
            else:
                r = self.exporters.plugins[out_format]().export(table)
            log.info ("FINISHED (%s): %s", datetime.now().isoformat(), request.url)
            return r

        log.info ("FINISHED (%s): %s", datetime.now().isoformat(), request.url)
        abort(400, 'Requested export format (%s) is not supported'%out_format )

#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  TableController(uri)
    #directory.register_service ('table', service)
    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'table', 'public'))]

#def get_model():
#    from bq.table import model
#    return model

__controller__ =  TableController
