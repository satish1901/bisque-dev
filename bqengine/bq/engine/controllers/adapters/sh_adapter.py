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
from tg import config
from lxml import etree
from StringIO import StringIO

from bq.core import identity
from base_adapter import BaseAdapter

from subprocess import call, PIPE

MODULE_BASE = config.get ('bisque.engine_service.local_modules', '')
log = logging.getLogger('bq.engine_service.adapters.python')

class ShellAdapter(BaseAdapter):
    '''Interface to a execute a shell script

    codeurl --p1=vl --p2=
    '''
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
        # Pass through module definition looking for inputs
        # for each input find the corresponding tag in the mex
        # Warn about missing inputs
        
        input_nodes = self.prepare_inputs(module=module, mex=mex)
        options = self.prepare_options(module=module, mex=mex)
        
        #up = identity.get_user_pass()
        #if up[0] is not None:
        #    for k,v in zip(['user','password'], up):
        #        input_nodes.append (etree.Element('tag', name=k, value=v))

        arguments = options.get("argument_style", None)
        if arguments and arguments.get('value') == 'named':
            params = ['--%s=%s'%(i.get('name'), i.get('value')) for i in input_nodes]
        else:
            params = [ i.get('value') for i in input_nodes ]
        olddir = os.getcwd () 
        module_dir = os.path.join(MODULE_BASE, module_name)
        os.chdir (module_dir)
        #command = 
        command_line = [ module_path ]
        command_line.extend (params)
        
        b, id = mex.get ('uri').rsplit ('/', 1)
        f = open ('/tmp/mex%s' %id, 'w')
        f.write (etree.tostring (mex))
        f.close()
                 
        try:
            log.debug ("Exec of %s in %s " % (command_line, module_dir) )
            retcode = call(command_line,
                           cwd=module_dir,
                           stdin=open ('/tmp/mex%s' %id))
        except Exception, e:
            log.exception ("During exec of %s: %s" % (command_line, e))


        os.chdir (olddir)
        log.debug ("Shell Returned: %s " %(retcode))
        return id
