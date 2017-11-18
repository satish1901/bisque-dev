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
ImageJ pipeline importer
"""


# default imports
import os
import logging
import pkg_resources
import tempfile
import re
import copy
from pylons.controllers.util import abort

from bq import blob_service
from bq.pipeline.controllers.pipeline_base import PipelineBase
from bq.pipeline.controllers.exporters.to_imagej import json_to_imagej

__all__ = [ 'PipelineIJ' ]

log = logging.getLogger("bq.pipeline.import.imagej")




#---------------------------------------------------------------------------------------
# Importer: CellProfiler
#---------------------------------------------------------------------------------------

def _get_parameters(step, param_name):
    res = []
    for param in step['Parameters']:
        if param.keys()[0] == param_name:
            res.append(param[param_name].strip())
    return res
    
def upload_imagej_pipeline(uf, intags):
    # analyze ImageJ macro and replace illegal operations with BisQue operations
    pipeline = {}
    with open(uf.localpath(), 'r') as fo:
        pipeline = imagej_to_json(fo)
    uf.close()
    # walk the pipeline and replace any incompatible steps with BisQue steps as well as possible
    new_pipeline = { '__Header__': pipeline['__Header__'] }
    new_step_id = 0
    old_step_id = 0
    converted_cnt = 0   # TODO: only keep up to 10 interactive params... URL gets too big otherwise
    had_save_img = False
    had_save_res = False
    for step_id in range(old_step_id, len(pipeline)-1):
        new_pipeline[str(new_step_id)] = copy.deepcopy(pipeline[str(step_id)])
        new_pipeline[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
        if pipeline[str(step_id)]['__Label__'] == 'open':
            new_pipeline[str(new_step_id)]['__Label__'] = 'BisQueLoadImage'
            new_pipeline[str(new_step_id)]['Parameters'] = []
            new_step_id += 1
        elif pipeline[str(step_id)]['__Label__'] in ['saveAs'] and _get_parameters(pipeline[str(step_id)], 'arg0').lower() == 'tiff' and not had_save_img:
            new_pipeline[str(new_step_id)]['__Label__'] = 'BisQueSaveImage'
            out_name = _get_parameters(pipeline[str(step_id)], 'arg1')
            new_pipeline[str(new_step_id)]['Parameters'] = [{'arg0' : out_name[0] if len(out_name)>0 else '"output.tif"' }]
            had_save_img = True
            new_step_id += 1
        elif pipeline[str(step_id)]['__Label__'] in ['saveAs'] and _get_parameters(pipeline[str(step_id)], 'arg0').lower() == 'results' and not had_save_res:
            new_pipeline[str(new_step_id)]['__Label__'] = 'BisQueSaveResults'
            out_name = _get_parameters(pipeline[str(step_id)], 'arg1')
            new_pipeline[str(new_step_id)]['Parameters'] = [{'arg0' : out_name[0] if len(out_name)>0 else '"output.csv"' }]
            had_save_res = True
            new_step_id += 1
        else:
            # keep all others unchanged
            # but check if some parameters could be treated as "interactive"
            new_pipeline[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
            new_parameters = []            
            for param in new_pipeline[str(new_step_id)]['Parameters']:
                param_key, param_val = param.items()[0]
                if converted_cnt < 10 and any([phrase in param_key.lower() for phrase in ['threshold', 'size', 'diameter', 'distance', 'smoothing', 'bound', 'difference', 'intensity']]):
                    try:
                        float(param_val)    # is this a number?
                        param_val = "@STRPARAM@%s" % str(param_val)
                        converted_cnt += 1
                    except ValueError:
                        pass   # skip non-numerical parameters for now
                new_parameters.append({param_key:param_val})
            new_pipeline[str(new_step_id)]['Parameters'] = new_parameters
            new_step_id += 1

    new_pipeline['__Header__']['ModuleCount'] = str(len(new_pipeline)-1)
    # write modified pipeline back for ingest
    ftmp = tempfile.NamedTemporaryFile(delete=False)
    ftmp.write(json_to_imagej(new_pipeline))
    ftmp.close()
    # ingest modified pipeline
    res = []
    with open(ftmp.name, 'rb') as fo:
        res = [blob_service.store_blob(resource=uf.resource, fileobj=fo)]
    return res

def imagej_to_json(pipeline_file):
    # TODO: write real parser
    # TODO: FUNCTION DEF!!!
    # TODO: MACRO DEF NOT SUPPORTED!!!
    # TODO: COMMENTS WITH /* */
    data = {}
    step_id = 0
    data['__Header__'] = { '__Type__': 'ImageJ' }
    for fline in pipeline_file:
        line = fline.rstrip('\r\n').strip()
        if line == '' or line.startswith('//'):
            continue
        if line == '}':
            # end of block
            line = 'endblock();'
        elif line.startswith('} while'):
            # end of "do {...} while" block
            line = 'enddo(' + line.split('(',1)[1]
        elif any([line.startswith(fct) for fct in ['for (', 'for(', 'while (', 'while(', 'if (', 'if(']]):
            # start of block
            line = line.rstrip('{').rstrip()
            line = line.replace(';', ',')
            line += ';'
        elif any([line.startswith(fct) for fct in ['} else {', '}else{']]):
            line = 'else();'
        elif any([line.startswith(fct) for fct in ['do {', 'do{']]):
            # start of block
            line = 'startdo();'
        if re.match(r"((?P<lexpr>\w+)\s*=\s*)?(?P<namespace>\w+\.)?(?P<function>\w+)\s*\((\s*(?P<arg1>[^,]+)\s*(,\s*(?P<arg2>[^,]+))*)?\s*\);$", line) is not None:
            # some fct call          
            toks = line.split('(',1)
            tag = toks[0].strip()
            params = toks[1].rstrip(');').split(',') if len(toks) > 1 else []
            params = [{'arg'+str(argidx) : params[argidx].strip()} for argidx in range(0,len(params)) if params[argidx].strip() != '']
            toks = tag.split('=',1)
            if len(toks) > 1:
                tag = toks[1].strip()
                params.append({'resvar' : toks[0].strip() })
            step = { "__Label__": tag, "__Meta__": {}, "Parameters": params }
        elif re.match(r"(?P<lexpr>\w+)\s*=\s*(?P<rexpr>.+);$", line) is not None:
            # assignment op
            matchdict = re.match(r"(?P<lexpr>\w+)\s*=\s*(?P<rexpr>.+);$", line).groupdict()
            step = { "__Label__": "assign", "__Meta__": {}, "Parameters": [{'arg0': matchdict['rexpr']}, {'resvar': matchdict['lexpr']}] }
        else:
            abort (400, 'ImageJ macro line "%s" cannot be parsed' % fline.rstrip('\r\n').strip())
        data[str(step_id)] = _validate_step(step)
        step_id += 1
    return data

def _validate_step(step):
    # mark actions not compatible with BisQue
    if step['__Label__'].startswith('BisQue'):
        step['__Meta__']['__compatibility__'] = 'bisque'
    elif step['__Label__'] in ['Crop']:  #TODO: check for other ignored steps
        step['__Meta__']['__compatibility__'] = 'ignored'
    elif any([step['__Label__'].startswith(pre) for pre in ['Dialog.']]) or step['__Label__'] in ['open', 'save', 'saveAs']:  #TODO: check for other incompatible steps
        step['__Meta__']['__compatibility__'] = 'incompatible'
    return step

class PipelineIJ(PipelineBase):
    name = 'imagej'
    version = '1.0'
    ext = ['ijm']

    def __init__(self, uniq, resource, path, **kw):
        super(PipelineIJ, self).__init__(uniq, resource, path, **kw)

        # allow to initialize with JSON directly 
        self.filename = None
        self.data = kw.get('data', None)
        if self.data:
            return

        # try to load the resource binary
        b = blob_service.localpath(uniq, resource=resource) or abort (404, 'File not available from blob service')
        self.filename = b.path
        self.data = {}
        raw_pipeline = []
        with open(self.filename, 'r') as pipeline_file:
            self.data = imagej_to_json(pipeline_file)
            
    def __repr__(self):
        return str(self.data)