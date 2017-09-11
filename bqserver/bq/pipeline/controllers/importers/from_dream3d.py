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
Dream.3D pipeline importer
"""


# default imports
import os
import logging
import json

import pkg_resources
from pylons.controllers.util import abort

from bq import blob_service
from bq.pipeline.controllers.pipeline_base import PipelineBase

__all__ = [ 'PipelineDream3D' ]

log = logging.getLogger("bq.pipeline.import.dream3d")




#---------------------------------------------------------------------------------------
# Importer: Dream.3D
#---------------------------------------------------------------------------------------

class PipelineDream3D(PipelineBase):
    name = 'dream3d'
    version = '1.0'
    ext = ['json']

    def __init__(self, uniq, resource, path, **kw):
        super(PipelineDream3D, self).__init__(uniq, resource, path, **kw)

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.data = {}
        raw_pipeline = '{}'
        with open(self.filename, 'r') as pipeline_file:
            raw_pipeline = pipeline_file.read()
        pipeline = json.loads(raw_pipeline)
        for key in pipeline:
            if key == 'PipelineBuilder':
                # store pipeline metadata in header
                header = { '__Type__': 'Dream.3D' }
                for header_key in pipeline[key]:
                    header[header_key] = pipeline[key][header_key]
                self.data['__Header__'] = header
            else:
                # store pipeline steps as they are except for label
                step = { "__Label__": pipeline[key]['Filter_Human_Label'], "__Meta__": {}, "Parameters": [] }
                for step_key in sorted(pipeline[key]):
                    if step_key in ['Filter_Name', 'FilterVersion']:
                        step['__Meta__'][step_key] = pipeline[key][step_key]
                    elif step_key != 'Filter_Human_Label':
                        step['Parameters'].append({ step_key: pipeline[key][step_key] })
                self.data[key] = step