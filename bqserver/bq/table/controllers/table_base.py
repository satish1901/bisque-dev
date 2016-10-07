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
Table base for importerters

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import logging
import pkg_resources
from pylons.controllers.util import abort

log = logging.getLogger("bq.table.base")

try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import pandas as pd
except ImportError:
    log.info('Pandas was not found but required for table service!')


__all__ = [ 'TableBase' ]

#---------------------------------------------------------------------------------------
# Table base
#---------------------------------------------------------------------------------------

class TableBase(object):
    '''Formats tables into output format'''

    name = ''
    version = '1.0'
    ext = 'table'
    mime_type = 'text/plain'

    # general functionality defined in the base class

    def __str__(self):
        r = self.resource #etree.tostring(self.resource) if self.resource is not None else 'None'
        m = self.data.shape if self.data is not None else 'None'
        t = type(self.t)
        return 'TableBase(m: %s, t: %s res: %s, path: %s)'%(m, t, r, self.path)

    def isloaded(self):
        """ Returns table information """
        return self.t is not None


    # functions to be defined in the individual drivers

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        self.path = path
        self.resource = resource
        self.uniq = uniq
        self.url = kw['url'] if 'url' in kw else None

        self.subpath = None # list containing subpath to elements within the resource
        self.tables = None # {'path':.., 'type':..} for all available tables in the resource
        self.t = None # represents a pointer to the actual element being operated on based on the driver
        self.data = None # Numpy array or pandas dataframe
        self.offset = 0
        self.headers = None
        self.types = None
        self.sizes = None

    def close(self):
        """Close table"""
        abort(501, 'Import driver must implement Close method')

    def as_array(self):
        if isinstance(self.data, pd.core.frame.DataFrame):
            return self.data.as_matrix()   # convert to numpy array
        else:
            return self.data

    def as_table(self):
        if isinstance(self.data, pd.core.frame.DataFrame):
            return self.data
        else:
            if self.data.ndim == 1:
                return pd.DataFrame(self.data)
            else:
                raise RuntimeError("cannot convert multi-dim array into dataframe")

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty
        return { 'headers': self.headers, 'types': self.types }

    def read(self, **kw):
        """ Read table cells and return """
        if 'rng' in kw and kw.get('rng') is not None:
            row_range = kw.get('rng')[0]
            self.offset = row_range[0] or 0 if len(row_range)>0 else 0
        else:
            self.offset = 0
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'Write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'Delete not implemented')
