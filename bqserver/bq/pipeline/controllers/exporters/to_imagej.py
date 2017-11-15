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
ImageJ pipeline exporter
"""

# default imports
import os
import fnmatch
import copy
import logging

from bq.pipeline.controllers.pipeline_exporter import PipelineExporter

__all__ = [ 'ExporterImageJ' ]

log = logging.getLogger("bq.pipeline.export.imagej")

#---------------------------------------------------------------------------------------
# exporters: ImageJ
#---------------------------------------------------------------------------------------

def json_to_imagej(pipeline):
    res = ''
    
    for step_id in range(0,len(pipeline)-1):
        if pipeline[str(step_id)]['__Label__'] == 'endblock':
            line = '}'
        elif pipeline[str(step_id)]['__Label__'] == 'enddo':
            line = '} while(' + ','.join([param.values()[0] for param in pipeline[str(step_id)]['Parameters']]) + ');'
        elif pipeline[str(step_id)]['__Label__'] in ['for', 'if', 'while']:
            line = pipeline[str(step_id)]['__Label__'] + '(' + ';'.join([param.values()[0] for param in pipeline[str(step_id)]['Parameters']]) + ') {'
        elif pipeline[str(step_id)]['__Label__'] == 'else':
            line = '} else {'
        elif pipeline[str(step_id)]['__Label__'] == 'startdo':
            line = 'do {'
        else:
            resvar = None
            params = []
            for param in pipeline[str(step_id)]['Parameters']:
                if 'resvar' in param.keys():
                    resvar = param.values()[0]
                else:
                    params.append(param.values()[0])
            if pipeline[str(step_id)]['__Label__'] == 'assign':
                # assignment
                line = (resvar + ' = ' if resvar is not None else '') + ','.join(params) + ';'
            else:
                # fct call
                line = (resvar + ' = ' if resvar is not None else '') + pipeline[str(step_id)]['__Label__'] + '(' + ','.join(params) + ');'
        res += line + '\n'
    return res

class ExporterImageJ (PipelineExporter):
    '''Formats pipelines in ImageJ format'''

    name = 'imagej'
    version = '1.0'
    ext = 'ijm'
    mime_type = 'text/plain'

    def get_pre_post_ops(self, pipeline):
        """returns the pre/post pipeline operations"""
        res = { 'PreOps' : [], 'PostOps': [] }
        for step_id in range(0,len(pipeline)-1):
            step_name = pipeline[str(step_id)]['__Label__']
            if step_name == 'BisQueLoadImage':
                res['PreOps'] += [ {'service':'image_service', 'id':'@INPUT', 'ops':'/format:tiff', 'filename':'input.tif'} ]
            elif step_name == 'BisQueSaveImage':
                name = self._get_parameters(pipeline[str(step_id)], 'arg0')[0]
                if name.startswith('"'):
                    name = name.strip('"')
                    fullname = name+'.tif'
                else:
                    # in case name is a variable, try to find the name chosen at runtime from the file system
                    name = ''
                    fullname = '__BisQueSaveImage__*.tif'
                new_op = {'service':'postblob', 'type':'image', 'name':name, 'filename':fullname}
                if '*' in fullname:
                    new_op['rmprefix'] = '__BisQueSaveImage__'
                    new_op['rmsuffix'] = '.tif'
                res['PostOps'] += [ new_op ]
        return res
        
    def bisque_to_native(self, pipeline):
        """converts BisQue... steps into ImageJ steps"""
        pipeline_res = { '__Header__': pipeline['__Header__'] }
        new_step_id = 0
        for step_id in range(0,len(pipeline)-1):
            step_name = pipeline[str(step_id)]['__Label__']
            if step_name == 'BisQueLoadImage':
                pipeline_res[str(new_step_id)] = copy.deepcopy(pipeline[str(step_id)])
                pipeline_res[str(new_step_id)]['__Label__'] = 'open'
                pipeline_res[str(new_step_id)]['Parameters'] = [{'arg0': '"input.tif"'}]
                new_step_id += 1
            elif step_name == 'BisQueSaveImage':
                name = self._get_parameters(pipeline[str(step_id)], 'arg0')[0]
                # in case name is a variable, add a unique prefix for later
                name = name.strip('"') if name.startswith('"') else '"__BisQueSaveImage__" + %s' % name
                pipeline_res[str(new_step_id)] = copy.deepcopy(pipeline[str(step_id)])
                pipeline_res[str(new_step_id)]['__Label__'] = 'saveAs'
                pipeline_res[str(new_step_id)]['Parameters'] = [{'arg0': '"Tiff"'}, {'arg1': name}]
                new_step_id += 1
            else:
                pipeline_res[str(new_step_id)] = copy.deepcopy(pipeline[str(step_id)])
                pipeline_res[str(new_step_id)]['__Meta__']['module_num'] = str(new_step_id+1)
                new_step_id += 1
        return pipeline_res

    def _get_parameters(self, step, param_name):
        res = []
        for param in step['Parameters']:
            if param.keys()[0] == param_name:
                res.append(param[param_name].strip())
        return res
    
    def format(self, pipeline):
        """ converts pipeline to ImageJ format """
        pipeline = pipeline.data
        if not pipeline or '__Header__' not in pipeline or pipeline['__Header__']['__Type__'] != 'ImageJ':
            # wrong pipeline type
            return None        
        return json_to_imagej(pipeline) + '\nrun("Close All");\n'
