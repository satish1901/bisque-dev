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

 Base engine adaptor for common code
 
"""
import copy
import logging
from lxml import etree
from bq.core import identity

log = logging.getLogger('bq.engine_service.mexparser')

def local_xml_copy(root):
    b, id = root.get ('uri').rsplit ('/', 1)
    #path = '/tmp/%s%s' % (root.tag, id)
    path = os.path.join(tempfile.gettempdir(), "%s%s" % (root.tag, id))
    f = open (path, 'w')
    f.write (etree.tostring (root))
    f.close()
    return path

class MexParser(object):

    def prepare_inputs (self, module, mex):
        '''Scan the module definition and the mex and match input
        formal parameters creating a list of actual parameters in the
        proper order (sorted by index)

        '''

        # ? dima - client_server, look at any find_service('client_service') in any api file
        mex_specials = { 'mex_url'      : mex.get('uri'),
                         'bisque_token' : identity.mex_authorization_token(),
                         'module_url'   : module.get ('uri'),
                         #'bisque_root'  : '',
                         #'client_server': '',
                         }

        # Pass through module definition looking for inputs
        # for each input find the corresponding tag in the mex
        # Warn about missing inputs
        input_nodes = []
        formal_inputs = module.xpath('./tag[@name="inputs"]')
        formal_inputs = formal_inputs and formal_inputs[0]
        actual_inputs = mex.xpath('./tag[@name="inputs"]')
        if len( actual_inputs )==0:
            # no inputs in mex
            return []
        actual_inputs = actual_inputs and actual_inputs[0]


        for mi in formal_inputs:
            # pull type off and markers off
            found = None
            #param_name = mi.get('value').split(':')[0].strip('$')
            param_name = mi.get('name')
            #log.debug ("PARAM %s" % param_name)
            if param_name in mex_specials:
                log.debug ("PARAM special %s=%s" % ( param_name, mex_specials[param_name]))
                found = etree.Element('tag',
                                      name=param_name,
                                      value = mex_specials[param_name])
                input_nodes.append (found)
            else:
                found = actual_inputs.xpath ('./tag[@name="%s"]'%param_name)
                log.debug ("PARAM %s=%s" % (param_name, found))
                input_nodes +=  copy.deepcopy(found)
            if found is None:
                log.warn ('missing input for parameter %s' % mi.get('value'))

        # Add the index 
        for i, node in enumerate(input_nodes):
            if 'index' in node.keys():
                continue
            node.set ('index', str(i))

        input_nodes.sort (lambda n1,n2: cmp(int(n1.get('index')), int(n2.get('index'))))
        return input_nodes

    
    def prepare_outputs (self, module, mex):
        '''Scan the module definition and the mex and match output
        parameters creating a list in the proper order
        '''
        # Pass through module definition looking for inputs
        # for each input find the corresponding tag in the mex
        # Warn about missing inputs
        output_nodes = []
        outputs = module.xpath ('./tag[@name="outputs"]')
        ouptuts = outputs and outputs[0]
        for mi in outputs:
            if mi.get('name') == 'outputs': continue
            # pull type off and markers off
            param_name = mi.get('value').split(':')[0].strip('$')
            output_nodes.append ( param_name )
            #found = mex.xpath ('./tag[@name="%s"]'%param_name)
            #if not found:
            #    log.warn ('missing input for parameter %s' % mi.get('value'))
            #output_nodes += found
        return output_nodes


    def prepare_options (self, module, mex):
        """Find the module options on the module definition and make
        available as a dict
        """
        options = {}
        for x in (module, mex):
            execute = x.xpath ('./tag[@name="execute_options"]')
            execute = execute  and execute[0]
            log.debug ("options %s" % execute )
            for opt in execute:

                options[opt.get('name')] = opt.get('value')

        log.debug("options=%s" % options)
        return options

        
    def prepare_mex_params(self, module, mex):
        'Create list of params based on execution options: named or positional'
        input_nodes = self.prepare_inputs(module=module, mex=mex)
        options     = self.prepare_options (module=module, mex=mex)
        arguments = options.get("argument_style", None)
        if arguments is not None and arguments == 'named':
            params = ['%s=%s'%(i.get('name'), i.get('value')) for i in input_nodes]
        else:
            params = [ i.get('value', '') for i in input_nodes ]
        return params

    def prepare_submexes(self, module, mex):
        "Find and return list  of toplevel submex"
        mexes = mex.xpath('/mex/mex')
        return [ self.prepare_mex_params(module, mx) for mx in mexes ] 

    def process_iterables(self, module, mex):
        'extract iterables from the mex as tuple i.e.  iterable_tag_name, dataset_url'
        iterable = mex.xpath('./tag[@name="execute_options"]/tag[@name="iterable"]')
        if len(iterable):
            mex_inputs = mex.xpath('./tag[@name="inputs"]')[0]
            iterable_tag_name = iterable[0].get('value')
            dataset_tag = mex_inputs.xpath('./tag[@name="%s"]' % iterable_tag_name)[0]
            return ( iterable_tag_name, dataset_tag.get('value'))
        return None
