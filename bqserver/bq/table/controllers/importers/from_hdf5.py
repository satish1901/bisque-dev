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
import re
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

def _get_type(n):
    if isinstance(n, tables.group.Group):
        return 'group'
    elif isinstance(n, tables.table.Table):
        return 'table'
    elif isinstance(n, tables.array.Array):
        return 'matrix'
    else:
        log.debug("UNKNOWN TABLE TYPE: %s", type(n))
        return '(unknown)'

def _get_headers_types(node, startcol=None, endcol=None):                
    if isinstance(node, tables.table.Table):
        headers = node.colnames[slice(startcol, endcol, None)]
        types = [node.coltypes[h] if h in node.coltypes else '(compound)' for h in node.colnames[slice(startcol, endcol, None)]]
    elif isinstance(node, tables.array.Array):
        if node.ndim > 1:
            headers = [str(i) for i in range(startcol or 0, endcol or node.shape[1])]
            types = [node.dtype.name for i in range(startcol or 0, endcol or node.shape[1])]
        elif node.ndim > 0:
            headers = [str(i) for i in range(startcol or 0, endcol or 1)]
            types = [node.dtype.name for i in range(startcol or 0, endcol or 1)]
        else:
            headers = ['']
            types = [node.dtype.name]
    else:
        # group node
        headers = []
        types = []
    return ( headers, types )


#---------------------------------------------------------------------------------------
# Importer: HDF
# TODO: not reading ranges
# TODO: proper parsing of sub paths
#---------------------------------------------------------------------------------------

class TableHDF(TableBase):
    '''Formats tables into output format'''

    name = 'hdf'
    version = '1.0'
    ext = ['h5', 'hdf5', 'h5ebsd']
    mime_type = 'application/x-hdf'

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        super(TableHDF, self).__init__(uniq, resource, path, **kw)

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.t = None
        try:
            self.info()
        except Exception:
            # close any open table
            if self.t is not None:
                self.t.close()
            raise

    def _collect_arrays(self, path='/'):
        try:
            node = self.t.getNode(path)
        except tables.exceptions.NoSuchNodeError:
            return []
        if not isinstance(node, tables.group.Group):
            return [ { 'path':path, 'type':_get_type(node) } ]
        return [ { 'path':path.rstrip('/') + '/' + n._v_name, 'type':_get_type(n) } for n in self.t.iterNodes(path) ]

    def close(self):
        """Close table"""
        if self.t:
            self.t.close()

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty
        log.debug("HDF TABLES: %s", str(self.tables))   #!!!

        # TODO: have to find a better way to split path in HDF from operations... this is a hack for now
        end = len(self.path)
        for i in range(len(self.path)):
            if self.path[i] == 'info' or re.match(r"^-?[0-9]*[:;]-?[0-9]*(?:,-?[0-9]*[:;]-?[0-9]*)*$", self.path[i]):
                end = i
                break
        self.subpath = '/' + '/'.join([p.strip('"') for p in self.path[0:end]])  # allow quoted path segments to escape slicing, e.g. /bla/"0:100"/bla
        self.path = self.path[end:]

        if self.tables is None:
            try:
                log.debug("HDF FILENAME: %s", self.filename)   #!!!
                self.t = tables.openFile(self.filename)    # TODO: could lead to problems when multiple workers open same file???
            except Exception:
                raise RuntimeError("HDF file cannot be read")
            self.tables = self._collect_arrays(self.subpath)

        if len(self.tables) == 0:
            # subpath not found
            abort(404, "Object '%s' not found" % self.subpath)

        log.debug('HDF subpath: %s, path: %s', self.subpath, str(self.path))

        node = self.t.getNode(self.subpath or '/')
        self.headers, self.types = _get_headers_types(node)
        self.sizes = node.shape if isinstance(node, tables.array.Array) else None
        log.debug('HDF types: %s, header: %s, sizes: %s', str(self.types), str(self.headers), str(self.sizes))
        return { 'headers': self.headers, 'types': self.types, 'sizes': self.sizes }   

    def read(self, **kw):
        """ Read table cells and return """
        super(TableHDF, self).read(**kw)
        rng = kw.get('rng')
        log.debug('rng %s', str(rng))

        node = self.t.getNode(self.subpath or '/')
        startrows = [0]*node.ndim
        endrows   = [min(50, node.shape[i]) for i in range(node.ndim)]
        if rng is not None:
            for i in range(min(node.ndim, len(rng))):
                row_range = rng[i]
                if len(row_range)>0:
                    startrows[i] = row_range[0] if len(row_range)>0 and row_range[0] is not None else 0
                    endrows[i]   = row_range[1]+1 if len(row_range)>1 and row_range[1] is not None else node.shape[i]
                    startrows[i] = min(node.shape[i], max(0, startrows[i]))
                    endrows[i]   = min(node.shape[i], max(0, endrows[i]))
                    if startrows[i] > endrows[i]:
                        endrows[i] = startrows[i]
        log.debug('startrows %s, endrows %s', startrows, endrows)
        
        if isinstance(node, tables.table.Table):
            self.data = node.read(startrows[0], endrows[0])   # ignore higher dims
            self.sizes = [endrows[0]-startrows[0], 1]
        elif isinstance(node, tables.array.Array):
            if node.ndim >= 1:
                slice_ranges = tuple([slice(startrows[i], endrows[i], None) for i in range(node.ndim)])
                self.sizes = [endrows[i]-startrows[i] for i in range(node.ndim)]
            else:
                slice_ranges = None
                self.sizes = []         
            self.data = node.__getitem__(slice_ranges) if slice_ranges else node.read()
        else:
            self.data = np.empty((), dtype=unicode)   # empty array
            self.sizes = [0 for i in range(node.ndim)]
        log.debug('Data: %s', str(self.data[0]) if len(self.data.shape) > 0 and self.data.shape[0] > 0 else str(self.data))
        self.headers, self.types = _get_headers_types(node, startrows[1] if node.ndim > 1 else None, endrows[1] if node.ndim > 1 else None)
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'HDF write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'HDF delete not implemented')

