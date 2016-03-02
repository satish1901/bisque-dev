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
CSV table exporter
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import logging

__all__ = [ 'ExporterJSON' ]

log = logging.getLogger("bq.table.export.json")

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

from bq.table.controllers.table_exporter import TableExporter

#---------------------------------------------------------------------------------------
# exporters: Json
#---------------------------------------------------------------------------------------

class ExporterJSON (TableExporter):
    '''Formats tables as Json'''

    name = 'json'
    version = '1.0'
    ext = 'json'
    mime_type = 'application/json'

    def info(self, table):
        super(ExporterJSON, self).info(table)
        v = {}
        if table.headers:
            # has headers => this is a leaf object (table or matrix)
            v["headers"] = table.headers
            v["types"] = table.types
            #if table.sizes is not None:
            #    v["sizes"] = table.sizes
        if table.tables is not None:
            v["group"] = table.tables
        #log.debug(v)
        return json.dumps(v)

    def format(self, table):
        """ converts table to JSON """
        #return table.data.to_json()
        data = table.as_array().tolist()
        if hasattr(data, "strip") or   \
           (not hasattr(data, "__getitem__") and   \
            not hasattr(data, "__iter__")):
            # data is not a list/tuple => wrap it
            data = [ data ]
        v = {
            'offset': table.offset,
            'data': data,
            'headers': table.headers,
            'types': table.types,
        }
        #if table.sizes is not None:
        #    v["sizes"] = table.sizes
        return json.dumps(v)