###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
## Copyright (c) 2017-2018 by the Regents of the University of California    ##
## Copyright (c) 2017-2018 (C) ViQi Inc                                      ##
## All rights reserved                                                       ##
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
##        software must display the following acknowledgment: This product   ##
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

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

import os
import re
import logging
from lxml import etree

log = logging.getLogger("bq.connoisseur.adapters_classes.gob_type_replace")

from bq.connoisseur.controllers.adapter_base import AdapterGobjectsBase
from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses

#---------------------------------------------------------------------------------------
# adapters: AdapterGobTypeReplace
# parameters:
#    <tag name="adapter_class" value="gob_type_replace" >

#        <tag name="accept_gobjects" value="point,polygon" type="string,list" />

#        <tag name="ignore_if_match" value="" />
#        <tag name="accept_if_match" value="" />

#        <tag name="level_separator" value="-" />
#        <tag name="level_extract" value="2" type="number" />

#        <tag name="replace_text" value="Primary - " />
#        <tag name="replace_with" value="" />

#        <tag name="trim_spaces" value="true" type="boolean" />

#    </tag>
#---------------------------------------------------------------------------------------

class AdapterGobTypeReplace (AdapterGobjectsBase):
    name = 'gob_type_replace'
    version = '1.0'

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        etree.SubElement (node, 'tag', name='accept_gobjects', value='point,polygon', type='string,list')
        etree.SubElement (node, 'tag', name='ignore_if_match', value='')
        etree.SubElement (node, 'tag', name='accept_if_match', value='')
        etree.SubElement (node, 'tag', name='replace_text', value='')
        etree.SubElement (node, 'tag', name='replace_with', value='')
        etree.SubElement (node, 'tag', name='level_separator', value='')
        etree.SubElement (node, 'tag', name='level_extract', value='0', type='number')
        etree.SubElement (node, 'tag', name='trim_spaces', value='true', type='boolean')

    def __str__(self):
        return 'Extracts node value and returns it while replacing requested elements'

    def init(self, model, args, image, **kw):
        """ init adapter data if needed, for example, parse parameters from the model """
        super(self.__class__, self).init(model, args, image, **kw)
        self.ignore_if_match = self.pars.get('ignore_if_match', '')
        self.accept_if_match = self.pars.get('accept_if_match', '')
        self.replace_text = self.pars.get('replace_text', '')
        self.replace_with = self.pars.get('replace_with', '')
        self.level_separator = self.pars.get('level_separator', '')
        self.level_extract = self.pars.get('level_extract', 0)
        self.trim_spaces = self.pars.get('trim_spaces', True)

    def get_class_name(self, node, **kw):
        """return node class name"""
        s = node.get('type', '')

        # only pass strings that do not match the pattern
        if len(self.ignore_if_match)>0:
            if re.match(self.ignore_if_match, s) is not None:
                return None

        # only pass strings that do not match the pattern
        if len(self.accept_if_match)>0:
            if re.match(self.accept_if_match, s) is None:
                return None

        # replace text
        s = re.sub(self.replace_text, self.replace_with, s)

        # extract a particular level
        if len(self.level_separator)>0 and self.level_extract is not None:
            try:
                s = s.split(self.level_separator)[self.level_extract]
            except Exception:
                return None

        # trim trailing and leading white spaces
        if self.trim_spaces is True:
            s = s.strip()
        return s

