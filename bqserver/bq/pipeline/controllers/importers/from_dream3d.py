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
import tempfile
from pylons.controllers.util import abort

from bq import blob_service
from bq.pipeline.controllers.pipeline_base import PipelineBase
from bq.pipeline.controllers.exporters.to_dream3d import json_to_dream3d

__all__ = [ 'PipelineDream3D' ]

log = logging.getLogger("bq.pipeline.import.dream3d")




#---------------------------------------------------------------------------------------
# Importer: Dream.3D
#---------------------------------------------------------------------------------------

def _get_parameters(step, param_name):
    res = []
    for param in step['Parameters']:
        if param.keys()[0] == param_name:
            res.append(param[param_name].strip())
    return res

def _set_parameter(step, param_name, param_value):
    for param in step['Parameters']:
        if param.keys()[0] == param_name:
            param[param_name] = param_value

def upload_dream3d_pipeline(uf, intags):
    # analyze DREAM.3D pipeline and replace illegal operations with BisQue operations
    pipeline = {}
    #uf.ensurelocal('/tmp/murks.json')   #!!!
    with open(uf.localpath(), 'r') as fo:
        pipeline = dream3d_to_json(fo)
    uf.close()
    # walk the pipeline and replace any incompatible steps with BisQue steps as well as possible
    new_pipeline = { '__Header__': pipeline['__Header__'] }
    new_step_id = 0
    old_step_id = 0
    for step_id in range(old_step_id, len(pipeline)-1):
        if pipeline[str(step_id)]['__Label__'] == 'Read H5EBSD File':
            new_pipeline[str(new_step_id)] = { '__Label__': 'BisQueLoadTable',
                                               'Parameters': [{'Filename': 'input.h5'}],
                                               '__Meta__': {'module_num': str(new_step_id+1)}
                                             }
            new_step_id += 1
            new_pipeline[str(new_step_id)] = pipeline[str(step_id)]
            new_pipeline[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
            _set_parameter(new_pipeline[str(new_step_id)], 'InputFile', 'input.h5')
            new_step_id += 1
        elif pipeline[str(step_id)]['__Label__'] == 'Write DREAM.3D Data File':
            new_pipeline[str(new_step_id)] = pipeline[str(step_id)]
            new_pipeline[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
            _set_parameter(new_pipeline[str(new_step_id)], 'OutputFile', 'output.h5')
            new_step_id += 1
            outname = _get_parameters(pipeline[str(step_id)], 'OutputFile')[0]
            new_pipeline[str(new_step_id)] = { '__Label__': 'BisQueSaveTable',
                                               'Parameters': [{'Filename': os.path.basename(outname)}],
                                               '__Meta__': {'module_num': str(new_step_id+1)}
                                             }
            new_step_id += 1
        else:
            new_pipeline[str(new_step_id)] = pipeline[str(step_id)]
            new_pipeline[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
            new_step_id += 1
    new_pipeline['__Header__']['ModuleCount'] = str(len(new_pipeline)-1)
    # write modified pipeline back for ingest
    ftmp = tempfile.NamedTemporaryFile(delete=False)
    ftmp.write(json_to_dream3d(new_pipeline))
    ftmp.close()
    # ingest modified pipeline
    res = []
    with open(ftmp.name, 'rb') as fo:
        res = [blob_service.store_blob(resource=uf.resource, fileobj=fo)]
    return res
        
def dream3d_to_json(pipeline_file):
    data = {}
    raw_pipeline = pipeline_file.read()
    pipeline = json.loads(raw_pipeline)
    for key in pipeline:
        if key == 'PipelineBuilder':
            # store pipeline metadata in header
            header = { '__Type__': 'Dream.3D' }
            for header_key in pipeline[key]:
                header[header_key] = pipeline[key][header_key]
            data['__Header__'] = header
        else:
            # store pipeline steps as they are except for label
            step = { "__Label__": pipeline[key]['Filter_Human_Label'], "__Meta__": {}, "Parameters": [] }
            for step_key in sorted(pipeline[key]):
                if step_key in ['Filter_Name', 'FilterVersion']:
                    step['__Meta__'][step_key] = pipeline[key][step_key]
                elif step_key != 'Filter_Human_Label':
                    step['Parameters'].append({ step_key: pipeline[key][step_key] })
            data[key] = _validate_step(step)
    return data

def _validate_step(step):
    # mark actions not compatible with BisQue
    if step['__Label__'].startswith('BisQue'):
        step['__Meta__']['__compatibility__'] = 'bisque'
    elif (step['__Label__'] == 'Read H5EBSD File' and _get_parameters(step, 'InputFile')[0] != 'input.h5') or \
         (step['__Label__'] == 'Write DREAM.3D Data File' and _get_parameters(step, 'OutputFile')[0] != 'output.h5'):  #TODO: check for other incompatible steps
        step['__Meta__']['__compatibility__'] = 'incompatible'
    return step

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
            self.data = dream3d_to_json(pipeline_file)
                
    def __repr__(self):
        return str(self.data)