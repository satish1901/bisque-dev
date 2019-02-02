###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
## Copyright (c) 2017-2018 by the Regents of the University of California    ##
## Copyright (c) 2017-2018 (C) ViQi Inc                                      ##
## All rights reserved                                                       ##
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
##        software must display the following acknowledgment: This product   ##
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
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

# default imports
import os
import logging

from cStringIO import StringIO
import csv
import pandas as pd

from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses
from bq.connoisseur.controllers.importer_base import ImporterBase

log = logging.getLogger("bq.connoisseur.import.csv")

hxyz = ['x', 'y', 'z', 't', 'c']
hgobs = ['gobject', 'vertices']

def validate_header(h, hh):
    if len(h)<2: return False
    sz = min(len(h), len(hh))
    for i in range(sz):
        if h[i].lower() != hh[i].lower():
            return False
    return True

#---------------------------------------------------------------------------------------
# importers: Csv
# the CSV format is: X,Y,Z,T,C or gobject,vertices,...
#---------------------------------------------------------------------------------------

class ImporterCSV2Points (ImporterBase):
    '''Formats tables as CSV'''

    name = 'csv2points'
    version = '1.0'
    ext = 'csv'
    mime_type = 'points'
    mime_input = 'text/csv'

    def __str__(self):
        return 'Imports CSV as points input, ex: POST "Content-Type: text/csv"  body: CSV document'

    def format(self, data, args):
        """ converts table to CSV """

        df = pd.read_csv(StringIO(data))
        out = []

        # test headers for formatting
        h = df.columns.values.tolist() # pylint: disable=no-member
        if validate_header(h, hxyz) is True:
            # read xyz
            for i in range(df.shape[0]):
                out.append((df['y'][i], df['x'][i]))
        elif validate_header(h, hgobs) is True:
            # read gobs
            for i in range(df.shape[0]):
                v = df['vertices'][i].split(',')
                out.append((v[1], v[0]))
        else:
            raise ConnoisseurException(responses.UNSUPPORTED_MEDIA_TYPE, 'Importer %s: unsupported format'%(self.name))

        # produce [(x,y), (x,y), ...]
        args['_points'] = out
