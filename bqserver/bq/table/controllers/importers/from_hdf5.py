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
HDF table importer
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

__all__ = [ 'TableHDF' ]

log = logging.getLogger("bq.table.import.hdf")

try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import tables
except ImportError:
    log.info('Tables was not found but required for Excel tables!')

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
# Importer: HDF
# TODO: not reading ranges
# TODO: proper parsing of sub paths
#---------------------------------------------------------------------------------------

class TableHDF(TableBase):
    '''Formats tables into output format'''

    name = 'hdf'
    version = '1.0'
    ext = ['h5', 'hdf5']
    mime_type = 'application/x-hdf'

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        super(TableHDF, self).__init__(uniq, resource, path, **kw)

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
                self.t = pd.HDFStore(self.filename)
            except Exception:
                return None
            self.tables = self.t.keys()

        if len(self.tables)==1: # if only one sheet is present
            self.subpath = self.tables[0]

        # paths should be URL encoded when submitted vai the URL API
        #['/arrays/Vdata table: PerBlockMetadataCommon']
        #encoded: /arrays/Vdata%20table%3A%20PerBlockMetadataCommon

        # iterate over the path and remove if matched
        if len(self.path)>0: # if path is provided for a sheet
            p = ['']
            matched = None
            for i in range(len(self.path)):
                p.append(self.path[i])
                pp = '/'.join(p)
                log.debug('Testing presense: "%s" in %s', pp, str(self.tables))
                if pp in self.tables:
                    log.debug('Found: "%s" in %s', pp, str(self.tables))
                    self.subpath = pp
                    matched = i
                    break
            if matched is not None:
                del self.path[0:matched+1]
        else: # if no path is provided, use first sheet
            self.subpath = self.tables[0]
        log.debug('HDF subpath: %s, path: %s', self.subpath, str(self.path))

        if self.headers is None or self.types is None:
            #data = pd.read_hdf(self.t, self.subpath, start=1, stop=10) # start and stop don't seem to be working
            data = pd.read_hdf(self.t, self.subpath)
            self.headers = [extjs_safe_header(x) for x in data.columns.values.tolist()] # extjs errors loading strings with dots
            self.types = data.dtypes.tolist() #data.dtypes.tolist()[0].name
        log.debug('HDF types: %s, header: %s', str(self.types), str(self.headers))
        return { 'headers': self.headers, 'types': self.types }

    def read(self, **kw):
        """ Read table cells and return """
        super(TableHDF, self).read(**kw)
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
        #self.data = pd.read_hdf(self.t, self.subpath, start=skiprows+1, stop=skiprows+nrows, columns=usecols )
        self.data = pd.read_hdf(self.t, self.subpath, columns=usecols )
        # start and stop don't seem to be working
        self.data = self.data[skiprows:skiprows+nrows]
        log.debug('Data: %s', str(self.data.head()))
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'HDF write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'HDF delete not implemented')

