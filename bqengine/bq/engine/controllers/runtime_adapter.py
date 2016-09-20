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

"""
import os
import logging
import tempfile
from tg import config
from lxml import etree
from StringIO import StringIO
from subprocess import call, PIPE, Popen, STDOUT

from bq.exceptions import EngineError
from bq.util.paths import bisque_path, config_path
from bq.util.copylink import copy_link


from base_adapter import BaseAdapter

from bq.core import identity

from .module_run import ModuleRunner

MODULE_BASE = config.get('bisque.engine_service.local_modules', bisque_path('modules'))
log = logging.getLogger('bq.engine_service.adapters.runtime')



class RuntimeAdapter(BaseAdapter):
    '''Interface to a execute a runner (engine module)
    '''
    def __init__(self):
        pass
    def check(self, module):
        module_name = module.get('name')
        #module_path = module.get('path').split(' ')[-1]
        #command = os.path.join(MODULE_BASE, module_name, module_path)
        #if not os.path.exists (command):
        #    log.debug ("Failed to find module at %s" % command)
        #    return False

        current_dir = os.getcwd()
        try:
            module_dir = module.get ('path')
            #log.debug ("Currently in %s" % current_dir)
            log.debug ("Checking %s in %s" % (module_name,  module_dir))

            os.chdir(module_dir)
            m = ModuleRunner()
            if not m.check (module_tree = module):
                return False

            async =  module.xpath('//tag[@name="asynchronous"]')
            if len(async):
                async[0].set('value', 'True')
            else:
                module.append(etree.Element('tag', name='asynchronous', value='True'))
            return True
        finally:
            os.chdir(current_dir)

    def execute(self, module, mex, pool):
        log.debug ("module : " + etree.tostring(module))
        log.debug ("mex : " + etree.tostring(mex))
        module_name = module.get('name')
        module_path = module.get('path')
        input_nodes = []
        # Pass through module definition looking for inputs
        # for each input find the corresponding tag in the mex
        # Warn about missing inputs

        params = []
        #input_nodes = self.prepare_inputs(module=module, mex=mex)
        #options= self.prepare_options (module=module, mex=mex)
        #arguments = options.get("argument_style", None)
        #if arguments is not None and arguments.get('value') == 'named':
        #    params = ['%s=%s'%(i.get('name'), i.get('value')) for i in input_nodes]
        #else:
        #    params = [ i.get('value') for i in input_nodes ]

        params.append ('start')
        #command = os.path.join(module_dir, module_path)
        #command_line = module_path.split(' ')
        command_line = []
        command_line.append('-d')
        command_line.extend (params)

        module_dir = module_path
        current_dir = os.getcwd()
        try:
            log.info ("Currently in %s" % os.getcwd())
            log.info ("Exec of %s '%s' in %s " % (module_name, ' '.join(command_line), module_dir))
            #copy_link ( config_path('runtime-bisque.cfg'), module_dir)

            os.chdir(module_dir)
            m = ModuleRunner()
            m.main(arguments=command_line,
                   mex_tree=mex,
                   module_tree=module,
                   bisque_token = identity.mex_authorization_token(),
                   pool = pool)
            os.chdir(current_dir)
            #process = Popen(command_line, cwd=module_dir, stdout=PIPE, stderr=PIPE)
            #stdout,stderr = process.communicate()
            #log.debug ("Process ID: %s " %(process.pid))
            #if process.returncode != 0:
            #    raise EngineError("Non-zero exit code",
            #                      stdout = stdout,
            #                      stderr = stderr)
            #return process.pid

        except Exception, e:
            os.chdir(current_dir)
            log.exception ("During exec of %s: %s" % (command_line, e))
            mex.set ('value', 'FAILED')
            etree.SubElement(mex, 'tag',
                             name = "error_message",
                             value = "During exec of %s: %s" % (command_line, e))
            if isinstance(e, EngineError):
                raise
            else:
                raise EngineError('Exception in module: %s' % command_line,
                                  #stdout = stdout,
                                  #stderr = stderr,
                                  exc = e)
