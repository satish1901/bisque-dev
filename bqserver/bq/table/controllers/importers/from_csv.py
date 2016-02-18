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
CSV table importer
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import sys
import logging
import pkg_resources

from bq import blob_service

__all__ = [ 'TableCSV' ]

log = logging.getLogger("bq.table.import.csv")

import csv
try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import pandas as pd
except ImportError:
    log.info('Pandas was not found but required for table service!')

from bq.table.controllers.table_base import TableBase

################################################################################
# misc
################################################################################

def extjs_safe_header(s):
    if isinstance(s, basestring):
        return s.replace('.', '_')
    return s

def _get_headers_types(data, startcol=None, endcol=None):
    headers = [extjs_safe_header(x) for x in data.columns.values.tolist()[slice(startcol, endcol, None)]] # extjs errors loading strings with dots
    types = [t.name for t in data.dtypes.tolist()[slice(startcol, endcol, None)]] #data.dtypes.tolist()[0].name
    return (headers, types)

#---------------------------------------------------------------------------------------
# Importer: CSV
#---------------------------------------------------------------------------------------

class TableCSV(TableBase):
    '''Formats tables into output format'''

    name = 'csv'
    version = '1.0'
    ext = 'csv'
    mime_type = 'text/csv'

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        super(TableCSV, self).__init__(uniq, resource, path, **kw)

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.t = None
        self.has_header = True
        self.info()

    def close(self):
        """Close table"""
        self.t = None

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty
        with open(self.filename, 'rb') as f:
            buf = f.read(1024)
            try:
                self.has_header = csv.Sniffer().has_header(buf)
            except csv.Error:
                self.has_header = True
        try:
            if self.has_header is True:
                data = pd.read_csv(self.filename, skiprows=0, nrows=10 )
            else:
                data = pd.read_csv(self.filename, skiprows=0, nrows=10, header=None )
        except Exception:
            return None
        if self.has_header:
            self.headers, self.types = _get_headers_types(data)
        self.sizes = [sys.maxint, data.shape[1]]   # TODO: rows set to maxint for now
        self.t = True
        log.debug('CSV types: %s, header: %s, sizes: %s', str(self.types), str(self.headers), str(self.sizes))
        return { 'headers': self.headers, 'types': self.types, 'sizes': self.sizes }

    def read(self, **kw):
        """ Read table cells and return """
        super(TableCSV, self).read(**kw)
        rng = kw.get('rng')
        log.debug('rng %s', str(rng))
        data = pd.read_csv(self.filename, nrows=1)   # to get the shape later
        sizes = [sys.maxint, data.shape[1]]   # TODO: rows set to maxint for now
        startrows = [0]*2
        endrows   = [1]*2
        if rng is not None:
            for i in range(min(2, len(rng))):
                row_range = rng[i]
                if len(row_range)>0:
                    startrows[i] = row_range[0] if len(row_range)>0 and row_range[0] is not None else 0
                    endrows[i]   = row_range[1]+1 if len(row_range)>1 and row_range[1] is not None else sizes[i]
                    startrows[i] = min(sizes[i], max(0, startrows[i]))
                    endrows[i]   = min(sizes[i], max(0, endrows[i]))
                    if startrows[i] > endrows[i]:
                        endrows[i] = startrows[i]
        log.debug('startrows %s, endrows %s', startrows, endrows)
        
        usecols = range(startrows[1], endrows[1])
        if endrows[0] > startrows[0] and endrows[1] > startrows[1]:     
            if self.has_header is True:
                self.data = pd.read_csv(self.filename, skiprows=startrows[0], nrows=endrows[0]-startrows[0], usecols=usecols )
            else:
                self.data = pd.read_csv(self.filename, skiprows=startrows[0], nrows=endrows[0]-startrows[0], usecols=usecols, header=None )
            self.sizes = [self.data.shape[0], endrows[1]-startrows[1]]
        else:
            self.data = pd.DataFrame()   # empty table
            self.sizes = [0 for i in range(self.data.ndim)]
        log.debug('Data: %s', str(self.data.head()) if self.data.ndim > 0 else str(self.data))
        if self.has_header:
            self.headers, self.types = _get_headers_types(data, startrows[1], endrows[1])
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'CSV write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'CSV delete not implemented')

