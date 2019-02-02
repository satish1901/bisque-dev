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
Connoisseur: image classifiers
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"


from tg import expose, request, response, require, config

import os
import logging
import random
import math
from lxml import etree

import numpy as np
from PIL import Image
import skimage.io
from skimage.feature import corner_shi_tomasi, corner_peaks, peak_local_max #pylint: disable=import-error


log = logging.getLogger("bq.connoisseur.classifier_image")

from bq.connoisseur.controllers.exceptions import ConnoisseurException
from bq.connoisseur.controllers.classifier_base import ClassifierBase
from bq.connoisseur.controllers.data_token import DataToken
from bq.connoisseur.controllers.classifiers.points import get_class_info, get_sample_confidence

#---------------------------------------------------------------------------------------
# ClassifierImage: classify the whole image as a patch
#---------------------------------------------------------------------------------------

class ClassifierImage (ClassifierBase):
    '''Classifies whole image as a patch'''

    name = 'image'
    version = '1.0'

    def __str__(self):
        return 'Classifies whole image as a patch, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:image[/format:csv]'

    def classify(self, image, model, args):
        # request image bound by patch size
        ops = 'slice=,,1,1&resize=%s,%s,BC&depth=8,d,u&fuse=display&format=tiff'%(model.db_patch_size[0], model.db_patch_size[1])
        pix = image.pixels(operations=ops)

        # extend the image to patch sizes to keep the aspect ratio
        # skimage.util.pad(array, pad_width, mode, **kwargs)

        out_class,goodness = model.classify(pix)
        label, accuracy, ignored = get_class_info(model, out_class, at_goodness=0)
        confidence = get_sample_confidence(accuracy, goodness)

        W,H = image.size()
        results = [{
            'gob': 'point',
            'vertex': [(W/2,H/2)],
            'label': label,
            'id': out_class,
            'accuracy': accuracy,
            'goodness': goodness,
            'confidence': confidence,
        }]

        return DataToken(data=results, mime='table/gobs', name='Whole image')
