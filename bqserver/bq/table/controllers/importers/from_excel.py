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
Excel table importer
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import logging
import pkg_resources
from pylons.controllers.util import abort

from bq import blob_service

__all__ = [ 'TableExcel' ]

log = logging.getLogger("bq.table.import.excel")

try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import xlrd
except ImportError:
    log.info('Xlrd was not found but required for Excel tables!')

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

#---------------------------------------------------------------------------------------
# Importer: Excel
# TODO: identify if header is present
# TODO: only read the requested number of rows
#---------------------------------------------------------------------------------------

class TableExcel(TableBase):
    '''Formats tables into output format'''

    name = 'excel'
    version = '1.0'
    ext = ['xls', 'xlsx']
    mime_type = 'application/vnd.ms-excel'

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        super(TableExcel, self).__init__(uniq, resource, path, **kw)

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.t = None
        self.info()

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty

        if self.tables is None:
            try:
                self.t = pd.ExcelFile(self.filename)
            except Exception:
                return None
            self.tables = self.t.sheet_names

        if len(self.tables)==1: # if only one sheet is present
            self.subpath = self.tables[0]
            if len(self.path)>0 and self.path[0] == self.subpath:
                self.path.pop(0)
        elif len(self.path)>0 and self.path[0] in self.tables: # if path is provided for a sheet
            self.subpath = self.path.pop(0)
        else: # if no path is provided, use first sheet
            self.subpath = self.tables[0]

        if self.headers is None or self.types is None:
            data = pd.read_excel(self.t, self.subpath, nrows=10)
            self.headers = [extjs_safe_header(x) for x in data.columns.values.tolist()] # extjs errors loading strings with dots
            self.types = data.dtypes.tolist() #data.dtypes.tolist()[0].name
        log.debug('Excel types: %s, header: %s', str(self.types), str(self.headers))
        return { 'headers': self.headers, 'types': self.types }

    def read(self, **kw):
        """ Read table cells and return """
        super(TableExcel, self).read(**kw)
        rng = kw.get('rng')
        log.debug('rng %s', str(rng))

        skiprows = 0
        nrows = None # not supported for Excel
        usecols = None
        if rng is not None:
            row_range = rng[0]
            if len(row_range)>0:
                skiprows = row_range[0] if len(row_range)>0 else 0
                nrows    = row_range[1]-skiprows+1 if len(row_range)>1 else 1
        log.debug('skiprows %s, nrows %s, usecols %s', skiprows, nrows, usecols)
        self.data = pd.read_excel(self.t, self.subpath, skiprows=skiprows, nrows=nrows, parse_cols=usecols )
        log.debug('Data: %s', str(self.data.head()))
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'Excel write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'Excel delete not implemented')

