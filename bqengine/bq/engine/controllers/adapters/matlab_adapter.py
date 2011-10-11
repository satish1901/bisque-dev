###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
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
SYNOPSIS
========


DESCRIPTION
===========

  Matlab adaptor for bisquik modules

"""
from tg import config
import os
import sys
import itertools
import logging
import thread
from lxml import etree
from bq.core.exceptions import EngineError
from bq.core import identity
from base_adapter import BaseAdapter

MATLAB_MODULE_ROOT=config.get('bisque.engine_service.local_modules', '')
#MATLAB_WS_PATH=+'/interface/'
log = logging.getLogger('bq.engine_service.adapters.matlab')

# try:
#     import numpy
#     ndarray = numpy.ndarray
# except ImportError:
#     import Numeric
#     ndarray = Numeric.ArrayType



class MatlabAdapter(BaseAdapter):
    '''Interface to a local matlab instance'''
    def __init__(self):
        if not os.getenv('MLABRAW_CMD_STR'):
            os.environ['MLABRAW_CMD_STR']='matlab -nosplash -nodesktop'
            os.putenv('MLABRAW_CMD_STR', 'matlab -nosplash -nodesktop')
        self.matlab_mlabraw_can_convert = ('double', 'char')
        self.matlab_checked = False
        self.matlab_installed = False
    
    def check(self, module):
        if not self.matlab_checked:
            self.matlab_checked = True
            try:
                from mlabwrap import mlabraw
                _engine = mlabraw.open(os.getenv("MLABRAW_CMD_STR", ""))
                mlabraw.close(_engine)
                #from mlabwrap import mlabraw
                #mlabraw.close()
                #except (ImportError, mlabraw.error):
                self.matlab_installed = True
            except ImportError:
                log.warn('engine failed to load (mlabwrap unavailable):%s' % module.get('name'))
        return self.matlab_installed 

    def execute(self, module, mex):
        log.debug ("module : " + etree.tostring(module))
        log.debug ("mex : " + etree.tostring(mex))
        ''' Create MATLAB input and ouput variables '''
        module_name = module.get('name')
        module_path = module.get('path')
        # inputs
        input_nodes = self.prepare_inputs(module, mex)
        params = ["'%s'"%(i.get('value', '')) for i in input_nodes]
        # user and password 
        #up = identity.get_user_pass()
        #if up[0] is not None:
        #    params +=  ["'%s'" % up[0], "'%s'" % up[1]]
        #
        # Add the authentication token 
        #params.append ( identity.mex_authorization_token() )
        inputs= ",".join(params)
        output_nodes = self.prepare_outputs(module, mex)
        params = ["%s"% i for i in output_nodes]
        outputs = " ".join(params)
        ''' Run MATLAB thread '''
        self.thread_launch (module, mex, inputs, outputs, module_name, module_path)
        return mex.get('uri')

    def thread_launch(self, module, mex, inputs, outputs, module_name, module_path):
        self._engine = None
        from mlabwrap import mlab
        from mlabwrap import mlabraw
        ''' Create MATLAB function '''
        func_name = "[%s ErrorMsg ] = %s ( %s ) " % ( outputs, module_name, inputs )
        log.debug ('FUNCTION: ' +  func_name)
        
        self._engine = mlabraw.open(os.getenv("MLABRAW_CMD_STR", ""))
        try:
            #''' Open MATLAB engine '''
            #''' Add MATLAB paths '''
            for x in [ module_path]:
               #p = MATLAB_MODULE_ROOT+'/' + x
               p = unicode(os.path.join (MATLAB_MODULE_ROOT, x))
               log.debug ('adding matlab path' +  p)
               mlabraw.eval(self._engine, "addpath(genpath('"+p+"'))")
            mlabraw.eval(self._engine, "addpath('"+MATLAB_MODULE_ROOT+"')")
            mlabraw.eval(self._engine, "javaaddpath('"+MATLAB_MODULE_ROOT+'/../lib/bisque.jar'+"')")
            mlabraw.eval(self._engine, "import bisque.*")
            #''' Run MATLAB function '''
            mlabraw.eval(self._engine, func_name)
            #''' Get MATLAB errors '''
            errors =  self.matlab_get("ErrorMsg") 
            log.debug("MATLAB ERRORS: " + str(errors))
            if errors:
                raise EngineError (errors)
            else:
                #''' Get MATLAB outputs '''
                outputs = self.prepare_outputs(module, mex)
                log.debug("MATLAB OUTPUTS: " + str(outputs))
                if len(outputs) > 0:
                    outputs_matlab =  self.matlab_get_values(outputs)
                    for i in range(len(outputs_matlab)):
                        mex.append(etree.Element('tag', name=str(outputs[i]), value=str(outputs_matlab[i]), type='formal-output' ))
        finally:
            #''' Close MATLAB engine '''
            if self._engine:
                mlabraw.close(self._engine)
        
    def matlab_var_type(self, varname):
        from mlabwrap import mlab
        from mlabwrap import mlabraw
        mlabraw.eval(self._engine, "TMP_CLS__ = class(%s);" % varname)
        res_type = mlabraw.get(self._engine, "TMP_CLS__")
        mlabraw.eval(self._engine, "clear TMP_CLS__;")
        return res_type
        
    def matlab_set(self, name, value):
        from mlabwrap import mlab
        from mlabwrap import mlabraw
        mlabraw.put(self._engine, name, value)        
    
    def matlab_get_values(self, varnames):
        from mlabwrap import mlab
        from mlabwrap import mlabraw
        res = []
        #if varnames is None: raise ValueError("No varnames") #to prevent clear('')
        for varname in varnames:
            res.append(self.matlab_get(varname))
        mlabraw.eval(self._engine, "clear('%s');" % "','".join(varnames))
        return res
    
    def matlab_get(self, name, remove=False):
        from mlabwrap import mlab
        from mlabwrap import mlabraw
        varname = name
        vartype = self.matlab_var_type(varname)
        if vartype in self.matlab_mlabraw_can_convert:
            var = mlabraw.get(self._engine, varname)
#             if type(var) is ndarray:
#                 if self._flatten_row_vecs and Numeric.shape(var)[0] == 1:
#                     var.shape = var.shape[1:2]
#                 elif self._flatten_col_vecs and Numeric.shape(var)[1] == 1:
#                     var.shape = var.shape[0:1]
#                 if self._array_cast:
#                     var = self._array_cast(var)
        else: raise ValueError("No varnames")        
        if remove:
            mlabraw.eval(self._engine, "clear('%s');" % varname)
        return var
