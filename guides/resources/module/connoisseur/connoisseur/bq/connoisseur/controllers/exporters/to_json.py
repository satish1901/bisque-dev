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
import datetime as dt
import json
import numpy as np

__all__ = [ 'ExporterGobs2JSON' ]

log = logging.getLogger("bq.connoisseur.export.json")

from bq.connoisseur.controllers.exporter_base import ExporterBase
from bq.connoisseur.controllers.utils import get_color_html, compute_measures

#---------------------------------------------------------------------------------------
# Json serializer
#---------------------------------------------------------------------------------------

class ExtEncoder(json.JSONEncoder):
    def default(self, o): # pylint: disable=method-hidden
        if isinstance(o, (dt.datetime, dt.date, dt.time)):
            return o.isoformat()
        elif isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()

        return json.JSONEncoder.default(self, o)

#---------------------------------------------------------------------------------------
# exporters: Json
#---------------------------------------------------------------------------------------

class ExporterGobs2JSON (ExporterBase):
    '''Formats tables as Json'''

    name = 'gobs2json'
    version = '1.0'
    ext = 'json'
    mime_type = 'application/json'
    mime_input = 'table/gobs'

    def __str__(self):
        return 'Exports graphical objects into JSON, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points/points:10/format:json'

    def format(self, token, args):
        """ converts table to JSON """

        data = []
        for i, r in enumerate(token.data):
            m_g, m_a, m_c = compute_measures (r)
            data.append({
                'gobject': r['gob'],
                'vertices': [[v[1], v[0]] for v in r['vertex']],
                'label': r['label'],
                'accuracy': m_a,
                'goodness': m_g,
                'confidence': m_c,
                #'color': get_color_html(r['id']),
            })

        v = {
            'name': token.name,
            'data': data,
        }

        filename = '%s_%s.json'%(token.name, args['_filename'])
        return token.setData(data=json.dumps(v, cls=ExtEncoder), mime=self.mime_type, filename=filename)
