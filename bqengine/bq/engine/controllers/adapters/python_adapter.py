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
import sys
import traceback
import itertools
import logging
from tg import config
from lxml import etree

from bq.core import identity
from base_adapter import BaseAdapter

MODULE_BASE = config.get ('bisque.engine_service.local_modules', '')
log = logging.getLogger('bq.engine_service.adapters.python')

class PythonAdapter(BaseAdapter):
    '''Interface to a local python interpreter'''
    def __init__(self):
        pass
    def check(self, module):
        return True

    def execute(self, module, mex):
        log.debug ("module : " + etree.tostring(module))
        log.debug ("mex : " + etree.tostring(mex))
        module_name = module.get('name')
        module_path = module.get('path')
        input_nodes = []
        input_nodes = self.prepare_inputs(module, mex)
        #options = self.prepare_options(module=module, mex=mex)
        #arguments = options.get("argument_style", None)
        #if arguments and arguments.get('value') == 'named':
        params = ['"%s"'%(i.get('value')) for i in input_nodes]
        #up = identity.get_user_pass()
        #if up[0] is not None:
        #    log.debug ("user=" + str(up))
        #    params +=  ['user="%s"' % up[0], 'password="%s"' % up[1]]
        # Add the authentication token 
        #params.append ('"%s"' % identity.mex_authorization_token() )
        

        inputs= ",".join(params)

        log.debug ("MODULE_BASE %s " % MODULE_BASE)
        path = os.path.abspath ( os.path.join(MODULE_BASE, module_name))
        log.debug ("appending %s to sys.path" % path)
        sys.path.append(path)
        olddir = os.getcwd () 
        os.chdir (path)
        commands = [
            'from %s import %s' % (module_name, module_name),
            'result = %s().main(%s)' % (module_name, inputs),
            'print result', 
            ]
        try:
            result = ""
            for c in commands:
                log.debug ("python: "+c )
                exec (c) in locals()
            mex.set('status', 'FINISHED')
            # FOR Some reason cannot us result for values
            #if result != "OK"
            #  mex.set ('status', 'FAILED')
            #  etree.SubElement(mex, 'tag', name="ERROR", value=result)
                
        except:
            log.warn ("Python module FAILED")
            mex.set('status', 'FAILED')
            excType, excVal, excTrace  = sys.exc_info()
            msg = (" Execption in adaptor:" + str (excVal) 
                   + "   Exception:\n"
                   + "  \n".join(traceback.format_exception(excType,excVal, excTrace)))
            etree.SubElement(mex, 'tag',
                             name = "ERROR",
                             value = msg)
            
        os.chdir (olddir)
        log.debug("python done: " + str(result))

        # TODO python output processing

        #
        #for o in module.xpath('./tag[@name="formal-output"]'):
        #    mex.append (etree.Element('tag', name=o.attrib['value'],
        #                              value = resources.pop(0)))


