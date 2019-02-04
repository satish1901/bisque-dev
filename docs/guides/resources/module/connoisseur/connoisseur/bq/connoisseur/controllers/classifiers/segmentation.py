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
Connoisseur: segmentation
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

from tg import expose, request, response, require, config

import os
import logging
import math
from lxml import etree

#pylint: disable=import-error
import numpy as np
from PIL import Image
import skimage.io
from skimage.morphology import disk
from skimage.filters.rank import median
from scipy import ndimage as ndi
from scipy.ndimage.morphology import distance_transform_edt
from skimage.morphology import watershed
from skimage.feature import peak_local_max
#from skimage.segmentation import slic
import math
import pyvoro
import os.path

from bq import image_service
from bq.util.mkdir import _mkdir
from bq.util.locks import Locks

log = logging.getLogger("bq.connoisseur.classifier_segmentation")

from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses
from bq.connoisseur.controllers.classifier_base import ClassifierBase
from bq.connoisseur.controllers.utils import image_patch, get_color_tuple_by_label
from bq.connoisseur.controllers.data_token import DataToken
from bq.connoisseur.controllers.classifiers.points import distribute_points, get_class_info, get_sample_confidence
from bq.connoisseur.controllers.gobjects import point

#---------------------------------------------------------------------------------------
# classifier: segmentation
#---------------------------------------------------------------------------------------

class ClassifierSegmentation (ClassifierBase):
    '''Semantic segmentation'''

    name = 'segmentation'
    version = '1.0'
    color_modes = ['ids', 'colors']
    side = 5000

    def __str__(self):
        return 'Segments image into semantic regions, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:segmentation[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/colors:ids]'

    def classify(self, image, model, args):
        ''' segment image produicing a semantic mask
        '''
        num_points = int(args.get('points', 10))
        border = int(args.get('border', 0))
        my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
        my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
        my_confidence = float(args.get('confidence', 0))

        # color output mode
        color_mode = args.get('colors', 'ids')
        if color_mode not in self.color_modes:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Requested color mode "%s" is not supported'%color_mode)

        # compute output file name and test cached result
        workdir = args['_workdir']
        _mkdir (workdir)
        filename = '%s_%s_conf%.2f_a%s_c%s_n%s_b%s.png'%(image.uniq, color_mode, my_goodness, my_accuracy, my_confidence, num_points, border)
        output_file = os.path.join(workdir, filename)

        with Locks(None, output_file, failonexist=True) as l:
            if l.locked: # the file is not being currently written by another process
                self.do_classify(image, model, args, output_file, color_mode)

        # return results
        if os.path.exists(output_file):
            with Locks(output_file):
                pass

        return DataToken(data=output_file, mime='image/png', name='Segments', filename=filename)

    def do_classify(self, image, model, args, output_file, color_mode):
        ''' segment image producing a semantic mask
        '''
        Worig,Horig = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([Worig,Horig])/100.0))
        my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
        my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
        my_confidence = float(args.get('confidence', 0))

        # get uniformly distributed points over the original image
        pts, num_points_x, num_points_y, sw, sh = distribute_points(num_points, Worig, Horig, border, equal=False, return_all=True)

        # estimate superpixel size of the scaled down image
        W=self.side; sx=1.0
        if max(Worig, Horig)>W:
            sx = float(W) / max(Worig, Horig)
        sw = int(round(sw*sx)) # this provides an approximate number of centroids as requested

        # load SLIC super-pixel segmented image
        log.debug('Requesting superpixels of size: %s', int(sw))
        seg = image.pixels(operations='slice=,,1,1&resize=%s,%s,BC,MX&depth=8,d,u&transform=superpixels,%s,0.1&format=tiff'%(self.side, self.side, sw))
        W,H = seg.shape[0:2]

        # compute scaling factors
        sx=1.0; sy=1.0
        if Worig!=W or Horig!=H:
            sx = float(W) / Worig
            sy = float(H) / Horig
            log.debug('Classify: Original image is larger, use scaling factors: %s,%s', sx, sy)

        # find segments to classify
        label_offset = 1 # region prop function uses 0 as background, we bump the class number and later subtract
        segments = skimage.measure.regionprops(seg+label_offset, cache=True)
        num_segs = len(segments)
        log.debug('Segmented the image into %s segments', num_segs)
        if num_segs<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Segmentation classifier: no results')

        # get uniformly distributed points per segment in full image space
        points_per_segment = [None]*num_segs
        for i,p in enumerate(points_per_segment):
            points_per_segment[i] = []
        for x,y in pts:
            v = seg[int(round(x*sx)), int(round(y*sx))]
            points_per_segment[v].append((x,y))

        # augment point list with segment centroids in full image space
        for i,s in enumerate(segments):
            x,y = s.centroid
            x,y = (x/sx, y/sy)
            if x>border and y>border and x<=Worig-border and y<=Horig-border:
                v = s.label-label_offset
                points_per_segment[v].append((x,y))

        # classify segments based on their points
        adapter = model.create_adapter_pixels(model=model, args=args, image=image)
        segment_colors = [0]*num_segs
        for i,s in enumerate(segments):
            #log.debug('i: %i, label: %s', i, s.label)
            samples = points_per_segment[s.label-label_offset]
            output_classes = []
            for p in samples:
                x = int(round(p[0]))
                y = int(round(p[1]))
                try:
                    #pix = image_patch(pim, x, y, model.db_patch_size[1], model.db_patch_size[0])
                    pix = adapter.get_adapted_image_patch(gob=point(x=y, y=x))
                    out_class,goodness = model.classify(pix)
                    label, accuracy, ignored = get_class_info(model, out_class, at_goodness=my_goodness)
                    confidence = get_sample_confidence(accuracy, goodness)
                    if goodness >= my_goodness and accuracy >= my_accuracy and confidence >= my_confidence and ignored is False:
                        output_classes.append(out_class)
                except Exception:
                    log.debug('x: %s y: %s', x,y)
                    log.debug('Pix shape: %s', pix.shape)
                    log.exception('Exception in image_patch/model.classify')

            if len(output_classes)>0:
                out_class = np.bincount(output_classes).argmax()
                #log.debug('%s detected %s from classes: %s', i, out_class, output_classes)
                segment_colors[i] = out_class+label_offset

        I,J = seg.shape[0:2]
        if color_mode == 'ids':
            for j in range(J):
                for i in range(I):
                    v = segment_colors[seg[i,j]]
                    seg[i,j] = v
            seg = seg.astype(np.uint16)
            skimage.io.imsave(output_file, seg)

            #seg = seg.astype(np.uint16)
            #seg = median(seg, disk(35))
            #skimage.io.imsave('%s_colors_med_goodness_%.2f.tif'%(output_file, my_goodness), seg)
        elif color_mode == 'colors':
            img = np.zeros((I, J, 3), dtype=np.uint8)
            for j in range(J):
                for i in range(I):
                    v = segment_colors[seg[i,j]]
                    out_class = v-label_offset
                    #img[i,j,:] = get_color_tuple(out_class)
                    try:
                        label = model.classes_model_by_id[out_class].get('label')
                        img[i,j,:] = get_color_tuple_by_label(label)
                    except Exception:
                        pass
            skimage.io.imsave(output_file, img)


