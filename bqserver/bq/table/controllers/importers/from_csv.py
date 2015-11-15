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

try:
    import json
except ImportError:
    log.info('Json was not found but needed for JSON output...')


from bq.table.controllers.table_base import TableBase

################################################################################
# misc
################################################################################

def extjs_safe_header(s):
    if isinstance(s, basestring):
        return s.replace('.', '_')
    return s

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

        has_header = True
        #dialect = False
        filename = None

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.info()
        self.t = True

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty
        if self.headers is None or self.types is None:
            with open(self.filename, 'rb') as f:
                buf = f.read(1024)
                try:
                    self.has_header = csv.Sniffer().has_header(buf)
                except csv.Error:
                    self.has_header = True
            if self.has_header is True:
                data = pd.read_csv(self.filename, skiprows=0, nrows=10 )
            else:
                data = pd.read_csv(self.filename, skiprows=0, nrows=10, header=None )
            self.headers = [extjs_safe_header(x) for x in data.columns.values.tolist()] # extjs errors loading strings with dots
            self.types = data.dtypes.tolist() #data.dtypes.tolist()[0].name
        log.debug('CSV types: %s, header: %s', str(self.types), str(self.headers))
        return { 'headers': self.headers, 'types': self.types }

    def read(self, **kw):
        """ Read table cells and return """
        super(TableCSV, self).read(**kw)
        rng = kw.get('rng')
        log.debug('rng %s', str(rng))

        #nrows: Number of rows to read out of the file. Useful to only read a small portion of a large file
        #usecols: a subset of columns to return, results in much faster parsing time and lower memory usage
        #skiprows: A collection of numbers for rows in the file to skip. Can also be an integer to skip the first n rows
        skiprows = 0
        nrows = None
        usecols = None
        if rng is not None:
            row_range = rng[0]
            if len(row_range)>0:
                skiprows = row_range[0] if len(row_range)>0 else 0
                nrows    = row_range[1]-skiprows+1 if len(row_range)>1 else 1
        log.debug('skiprows %s, nrows %s, usecols %s', skiprows, nrows, usecols)
        if self.has_header is True:
            self.data = pd.read_csv(self.filename, skiprows=skiprows, nrows=nrows, usecols=usecols )
        else:
            self.data = pd.read_csv(self.filename, skiprows=skiprows, nrows=nrows, usecols=usecols, header=None )
        log.debug('Data: %s', str(self.data.head()))
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'CSV write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'CSV delete not implemented')

