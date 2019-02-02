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

"""
Image class: keeps image related info and returns pixels as np array needed by the classifiers
"""

__author__    = "Dmitry Fedorov"
__version__   = "1.0"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara, ViQi Inc"

import sys
import logging
import numpy as np
from PIL import Image
import skimage.io

from bq import image_service
from bq import data_service

log = logging.getLogger("bq.connoisseur.ximage")

################################################################################
# XImage - wrapper around image resource
################################################################################

class XImage(object):
    """ keeps image related info and returns pixels as np array needed by the classifiers
    """

    def __init__(self, uniq=None, base_url=None):
        self.infos = {}
        if base_url is not None:
            self.base_url = base_url.replace('/data_service/', '/image_service/')
            self.uniq = self.base_url.split('/image_service/')[1]
        else:
            self.uniq = uniq
            self.base_url = '/image_service/%s'%(self.uniq)

    def info(self, url=None):
        url = url or 'original'
        if url not in self.infos:
            info = image_service.info (self.uniq)
            self.infos[url] = info
        return self.infos[url]

    def size(self, url=None):
        info = self.info(url=url)
        return (info['image_num_y'], info['image_num_x'])

    def pixels(self, operations=None, dtype=None):
        operations = operations or 'slice=,,1,1&depth=8,d,u&format=png'
        image_url = '%s?%s'%(self.base_url, operations)
        log.debug('Getting local path for: %s', image_url)
        out_file = image_service.local_file(image_url)
        log.debug('Image file path: %s', out_file)

        # # load using PIL
        # pic = Image.open(out_file)
        # if dtype is not None:
        #     pix = np.array(pic, dtype=dtype)
        # else:
        #     pix = np.array(pic)

        # load using skimage
        pix = skimage.io.imread(out_file)
        pix = np.squeeze(pix)
        if dtype is not None:
            pix = pix.astype(dtype=dtype)

        log.debug('Loaded image %s from %s', pix.shape, out_file)
        return pix

    def get_resource(self, view='deep'):
        resource = data_service.resource_load (uniq=self.uniq, view=view)
        return resource

