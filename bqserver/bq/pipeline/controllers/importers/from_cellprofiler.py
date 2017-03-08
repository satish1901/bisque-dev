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
CellProfiler pipeline importer
"""


# default imports
import os
import logging
import pkg_resources
from pylons.controllers.util import abort

from bq import blob_service
from bq.pipeline.controllers.pipeline_base import PipelineBase

__all__ = [ 'PipelineCP' ]

log = logging.getLogger("bq.pipeline.import.cellprofiler")




#---------------------------------------------------------------------------------------
# Importer: CellProfiler
#---------------------------------------------------------------------------------------

class PipelineCP(PipelineBase):
    name = 'cellprofiler'
    version = '1.0'
    ext = ['cp', 'cppipe']

    def __init__(self, uniq, resource, path, **kw):
        super(PipelineCP, self).__init__(uniq, resource, path, **kw)

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.data = {}
        raw_pipeline = []
        with open(self.filename, 'r') as pipeline_file:
            is_header = True
            indent = 0
            step = {}
            step_id = 0
            header = { '__Type__': 'CellProfiler' }
            for line in pipeline_file:
                line = line.rstrip('\r\n')
                if is_header and len(line) == 0:
                    # end of header reached
                    self.data['__Header__'] = header
                    is_header = False
                elif is_header and not line.startswith('CellProfiler Pipeline'):
                    toks = line.split(':')
                    tag = toks[0]
                    val = ':'.join(toks[1:])
                    header[tag] = val
                elif not is_header and len(line) == 0 and step:
                    # end of step reached
                    # check if step should be marked special (incompatible, modified)
                    self.data[str(step_id)] = self._validate_step(step)
                    step = {}
                    step_id += 1
                elif not is_header and not line.startswith(' '):
                    # start of new pipeline step
                    # format of line is:
                    # <Step Label>:[<meta_tag>:<meta_val>|<meta_tag>:<meta_val>| ... |<meta_tag>:<meta_val>]
                    toks = line.split(':')
                    tag = toks[0]
                    val = ':'.join(toks[1:]).lstrip('[').rstrip(']')
                    step = { "__Label__": tag, "__Meta__": {}, "Parameters": [] }
                    # TODO: use better parser that handles escapes ('\')
                    for metas in val.split('|'):
                        meta_toks = metas.split(':')
                        meta_tag = meta_toks[0]
                        meta_val = ':'.join(meta_toks[1:])
                        step['__Meta__'][meta_tag] = meta_val
                elif not is_header and line.startswith(' '):
                    # step parameter
                    toks = line.strip().split(':')
                    tag = toks[0]
                    val = ':'.join(toks[1:])
                    step['Parameters'].append( {tag:val} )                    
                    
    def _validate_step(self, step):
        # mark actions not compatible with BisQue
        if step['__Label__'] in ['OverlayOutlines']:
            step['__Meta__']['__compatibility__'] = 'incompatible'
        return step

    def __repr__(self):
        return str(self.data)
    