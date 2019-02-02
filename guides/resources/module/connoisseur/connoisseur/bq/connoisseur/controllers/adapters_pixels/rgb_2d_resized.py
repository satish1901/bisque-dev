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
import scipy

log = logging.getLogger("bq.connoisseur.adapters_pixels.rgb_2d_resized")

from bq.connoisseur.controllers.adapter_base import AdapterPixelsBase
from bq.connoisseur.controllers.utils import image_patch
from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses

#---------------------------------------------------------------------------------------
# AdapterRGB2DResized
# parameters:
#    <tag name="adapter_data" value="rgb_2d_resized">
#        <tag name="accept_gobjects" value="point,polygon" type="string,list" />
#        <tag name="width" value="6000" type="number" />
#        <tag name="height" value="6000" type="number" />
#    </tag>
#---------------------------------------------------------------------------------------

class AdapterRGB2DResized (AdapterPixelsBase):

    name = 'rgb_2d_resized'
    version = '1.0'

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        etree.SubElement (node, 'tag', name='accept_gobjects', value='point,polygon', type='string,list')
        etree.SubElement (node, 'tag', name='width', type='number', value='300')
        etree.SubElement (node, 'tag', name='height', type='number', value='200')
        etree.SubElement (node, 'tag', name='patch_width', type='number', value='0')
        etree.SubElement (node, 'tag', name='patch_height', type='number', value='0')

    def __init__(self, model=None, args=None, image=None, **kw):
        self.pix = None
        self.si = 1.0
        self.sj = 1.0
        self.patch_width = 0
        self.patch_height = 0
        super(self.__class__, self).__init__(model, args, image)

    def __str__(self):
        return 'Returns 2D pixel patches for a given gob from a resized image'

    def init(self, model, args, image, **kw):
        """ init adapter data if needed, for example, load an image in memory """
        super(self.__class__, self).init(model, args, image)

        log.debug('Pars: %s', self.pars)
        self.patch_width = self.pars.get('patch_width', self.model.db_patch_size[0])
        self.patch_height = self.pars.get('patch_height', self.model.db_patch_size[1])
        width = self.pars.get('width', 0)
        height = self.pars.get('height', 0)
        op = 'slice=,,1,1&resize={0},{1},BC,MX&depth=8,d,u&fuse=display&format=tiff'.format(width, height)
        self.pix = image.pixels(operations=op)
        W,H = self.pix.shape[0:2]

        # compute scaling factor
        Worig,Horig = image.size()
        if Worig!=W or Horig!=H:
            self.si = float(W) / Worig
            self.sj = float(H) / Horig
            log.debug('Original image is larger, use scaling factors: %s,%s', self.si, self.sj)

    def get_adapted_image_size(self):
        """ returns (H,W) of the whole as seen by this adapter """
        if self.pix is None:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'AdapterRGB2DResized: image was not properly initialized')
        return self.pix.shape[0:2]

    def get_adapted_image_scale(self):
        """ returns scale for (y,x,z,t) of the whole as seen by this adapter """
        return (self.si, self.sj, 1.0, 1.0)

    def get_adapted_image_patch(self, gob, **kw):
        """ return image pixels for a given gobject as a numpy array """
        if self.pix is None:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'AdapterRGB2DResized: image was not properly initialized')

        c = gob.centroid()
        i = int(c[1]*self.si)
        j = int(c[0]*self.sj)
        # print 'Requested gob: %s'%(gob)
        # print 'Scaled i,j: %s,%s'%(i,j)
        # print 'Patch size: %s'%(self.model.db_patch_size)
        # print 'Pix size: %s'%(str(self.pix.shape))

        if self.patch_width==0 and self.patch_height==0 or self.patch_width==self.model.db_patch_size[0] and self.patch_height==self.model.db_patch_size[1]:
            return image_patch(self.pix, i, j, self.model.db_patch_size[1], self.model.db_patch_size[0])
        else:
            p = image_patch(self.pix, i, j, self.patch_height, self.patch_width)
            return scipy.misc.imresize(p, (self.model.db_patch_size[1], self.model.db_patch_size[0]), interp='bilinear')

