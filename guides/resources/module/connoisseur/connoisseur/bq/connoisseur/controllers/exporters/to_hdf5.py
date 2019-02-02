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

import tables
import pandas as pd

__all__ = [ 'ExporterGobs2HDF5' ]

log = logging.getLogger("bq.connoisseur.export.hdf")

from bq.util.mkdir import _mkdir
from bq.util.locks import Locks

from bq.connoisseur.controllers.exporter_base import ExporterBase
from bq.connoisseur.controllers.utils import get_color_html, compute_measures

#---------------------------------------------------------------------------------------
# exporters: Csv
#---------------------------------------------------------------------------------------

class ExporterGobs2HDF5 (ExporterBase):
    '''Formats tables as CSV'''

    name = 'gobs2hdf'
    version = '1.0'
    ext = ['h5', 'hdf5', 'h5ebsd']
    mime_type = 'application/x-hdf'
    mime_input = 'table/gobs'

    def __str__(self):
        return 'Exports graphical objects into HDF-5, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points/points:10/format:hdf'

    def format(self, token, args):
        """ converts table to HDF5 """

        # GobsTable = np.dtype([
        #     ('gobject',    tables.StringCol(10)),
        #     ('type',       tables.StringCol(50)),
        #     ('vertices',   tables.VLArray()),

        #     Col.from_atom(atom, pos=None)

        #     ('accuracy',   tables.Float32Col()),
        #     ('goodness',   tables.Float32Col()),
        #     ('confidence', tables.Float32Col()),
        # ])

        data = {
            'gobject': [],
            'type': [],
            'vertices': [],
            'accuracy': [],
            'goodness': [],
            'confidence': [],
            #'color': [],
        }

        for i, r in enumerate(token.data):
            m_g, m_a, m_c = compute_measures (r)
            data['gobject'].append(r['gob'])
            data['type'].append(r['label'])
            data['vertices'].append([ (v[1],v[0]) for v in r['vertex'] ])
            data['accuracy'].append(m_a)
            data['goodness'].append(m_g)
            data['confidence'].append(m_c)
            #data['color'].append(get_color_html(r['id']))

        df = pd.DataFrame(data)

        workdir = args['_workdir']
        _mkdir (workdir)

        filename = '%s_%s.h5'%(token.name, args['_filename'])
        output_file = os.path.join(workdir, filename)

        with Locks(None, output_file, failonexist=True) as l:
            if l.locked: # the file is not being currently written by another process
                df.to_hdf(output_file, 'table', append=False)

        # return results
        if os.path.exists(output_file):
            with Locks(output_file):
                pass

        return token.setFile(path=output_file, mime=self.mime_type, filename=filename)


    # def to_hdf5(self, filename):
    #     header = self.header()
    #     CellMFI = np.dtype([
    #         (header[0], tables.UInt64Col()),
    #         (header[1], tables.StringCol(50)),
    #         (header[2], tables.Float32Col()),
    #         (header[3], tables.Float32Col()),
    #         (header[4], tables.UInt64Col()),
    #         (header[5], tables.Float32Col()),
    #         (header[6], tables.Float32Col()),
    #         (header[7], tables.Float32Col()),
    #         (header[8], tables.Float32Col()),
    #     ])

    #     h5file = tables.open_file(filename, mode = "w", title = "MFI profiles")
    #     #group = h5file.create_group("/", 'detector', 'Detector information')
    #     #table = h5file.create_table(group, 'readout', CellMFI, "Readout example")

    #     filters = tables.Filters(complevel=1, complib='zlib')
    #     table = h5file.create_table('/', 'profiles', description=CellMFI, title="MFI profiles", expectedrows=self.num_cells(), filters=filters)

    #     p = table.row
    #     for i in range(self.num_cells()):
    #         r = self.row(i)
    #         p[header[0]] = r[0]
    #         p[header[1]] = r[1]
    #         p[header[2]] = r[2]
    #         p[header[3]] = r[3]
    #         p[header[4]] = r[4]
    #         p[header[5]] = r[5]
    #         p[header[6]] = r[6]
    #         p[header[7]] = r[7]
    #         p[header[8]] = r[8]

    #         p.append()
    #     table.flush()
    #     h5file.close()

    #     return filename

