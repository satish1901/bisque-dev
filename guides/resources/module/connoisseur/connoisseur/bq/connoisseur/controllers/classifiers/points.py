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
Connoisseur: point classifiers
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

log = logging.getLogger("bq.connoisseur.classifier_points")

from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses
from bq.connoisseur.controllers.classifier_base import ClassifierBase
from bq.connoisseur.controllers.utils import image_patch
from bq.connoisseur.controllers.data_token import DataToken
from bq.connoisseur.controllers.gobjects import point

#---------------------------------------------------------------------------------------
# misc
#---------------------------------------------------------------------------------------

def get_class_info(model, out_class, at_goodness=0.9):
    c = model.classes_model_by_id[out_class]
    errors = c['error']
    if isinstance(errors, list) is not True or 'goodness' not in c:
        accuracy = 100 - errors
    else:
        goodness = c.get('goodness', 0)
        i = np.argmin(np.abs(np.subtract(goodness, at_goodness)))
        accuracy = 100 - errors[i]

    label = c.get('label')
    ignored = c.get('ignored', False) == True
    return label, accuracy, ignored

def get_sample_confidence(accuracy, goodness):
    confidence = (accuracy/100.0) * goodness * 100.0
    return confidence

#---------------------------------------------------------------------------------------
# uniform sampling
#---------------------------------------------------------------------------------------

def distribute_points(num_points, W, H, border, equal=False, return_all=False):
    ''' distribute points uniformly along the WxH image
        equal forces the number of points to be equal in both dimensions
        in this case horizontal and vertical spacings will not be the same
        otherwise the image aspect ratio is used and the spacings are equal
    '''
    num_points_x = int(round(math.sqrt(num_points)))
    num_points_y = num_points_x
    if equal is False and W != H:
        T = num_points_x + num_points_y
        num_points_x = int(round(T*(float(W)/(W+H))))
        num_points_y = T - num_points_x

    sw = (W-border*2.0) / float(num_points_x-1.0)
    sh = (H-border*2.0) / float(num_points_y-1.0)

    # uniform sampling
    pts = []
    for x in range(num_points_x):
        for y in range(num_points_y):
            pts.append((border+x*sw,border+y*sh))

    if return_all is True:
        return pts, num_points_x, num_points_y, sw, sh
    return pts

#---------------------------------------------------------------------------------------
# base point classifier function
#---------------------------------------------------------------------------------------

def classify_points(image, model, args, pts, name='Points'):
    ''' classify a list of points'''

    adapter = model.create_adapter_pixels(model=model, args=args, image=image)
    my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
    my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
    my_confidence = float(args.get('confidence', 0))

    results = []
    for x,y in pts:
        try:
            pix = adapter.get_adapted_image_patch(gob=point(x=y, y=x))
            out_class,goodness = model.classify(pix)
            label, accuracy, ignored = get_class_info(model, out_class, at_goodness=my_goodness)
            confidence = get_sample_confidence(accuracy, goodness)

            if goodness >= my_goodness and accuracy >= my_accuracy and confidence >= my_confidence and ignored is False:
                #print '%s,%s classified as "%s" with %s goodness score'%(x, y, label, goodness)
                #log.debug('%s,%s classified as "%s" with %s goodness score'%(x, y, label, goodness))
                results.append({
                    'gob': 'point',
                    'vertex': [(x,y)],
                    'label': label,
                    'id': out_class,
                    'accuracy': accuracy,
                    'goodness': goodness,
                    'confidence': confidence,
                })
        except Exception:
            log.debug('x: %s y: %s', x,y)
            log.exception('Exception in image_patch/model.classify')

    if len(results)<1:
        raise ConnoisseurException(responses.NO_CONTENT, 'Point classifier: no results')

    # hierarchical passes over samples whose classes have child models

    # return results
    return DataToken(data=results, mime='table/gobs', name=name)

#---------------------------------------------------------------------------------------
# classifier: Uniformly distributed points - equally spaced in X and Y
#---------------------------------------------------------------------------------------

class ClassifierPoints (ClassifierBase):
    '''Classifies uniformly sampled points'''

    name = 'points'
    version = '1.0'
    equal = False

    def __str__(self):
        return 'Classifies uniformly sampled points, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' uniformly sampled points '''

        if '_points' in args:
            pts = args.get('_points')
            return classify_points(image, model, args, pts, 'Points')

        W,H = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([W,H])/100.0))
        equal = bool(args.get('equal', self.equal))

        # uniform sampling
        pts = distribute_points(num_points, W, H, border, equal=equal)

        return classify_points(image, model, args, pts, 'Uniform points')

#---------------------------------------------------------------------------------------
# classifier: Uniformly distributed points with equal number in X and Y
#---------------------------------------------------------------------------------------

class ClassifierPointsEqual (ClassifierPoints):
    '''Classifies uniformly sampled points with equal number in X and Y'''

    name = 'points_equal'
    version = '1.0'
    equal = True

    def __str__(self):
        return 'Classifies uniformly sampled points (equal number in X and Y), ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points_equal[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

#---------------------------------------------------------------------------------------
# classifier: randomly sampled points
#---------------------------------------------------------------------------------------

class ClassifierPointsRandom (ClassifierBase):
    '''Classifies randomly sampled points'''

    name = 'points_random'
    version = '1.0'

    def __str__(self):
        return 'Classifies randomly sampled points, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points_random[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' randomly sampled points '''

        W,H = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([W,H])/100.0))

        random.seed()
        pts = []
        for i in range(num_points):
            x = random.randint(border, W-border)
            y = random.randint(border, H-border)
            pts.append((x,y))

        return classify_points(image, model, args, pts, 'Random points')

#---------------------------------------------------------------------------------------
# classifier: Salient points
#---------------------------------------------------------------------------------------

class ClassifierSalient (ClassifierBase):
    '''Classifies most salient points'''

    name = 'salient'
    version = '1.0'

    # bounding box for images processed internally
    side = 5000

    def __str__(self):
        return 'Classifies most salient points, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:salient[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' uniformly sampled points '''

        Worig,Horig = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([Worig,Horig])/100.0))

        # get gray scale image for salient point detection
        pix = image.pixels(operations='slice=,,1,1&resize=%s,%s,BC,MX&depth=8,d,u&remap=gray&format=tiff'%(self.side, self.side))
        W,H = pix.shape[0:2]

        # compute scaling factor
        sx, sy = (1.0, 1.0)
        if Worig!=W or Horig!=H:
            sx = float(W) / Worig
            sy = float(H) / Horig
            log.debug('Classify: Original image is larger, use scaling factors: %s,%s', sx, sy)

        # scale params to resized image
        border = int(round(border*sx))
        pts, num_points_x, num_points_y, sw, sh = distribute_points(num_points, W, H, border, equal=False, return_all=True)

        # detect salient points
        pts = corner_peaks(corner_shi_tomasi(pix), min_distance=int(sw*0.3), exclude_border=border, indices=True, num_peaks=num_points)

        # re-scale points
        points = [(p[0]/sx, p[1]/sy) for p in pts]

        return classify_points(image, model, args, points, 'Salient points')

#---------------------------------------------------------------------------------------
# classifier: Centroids
#---------------------------------------------------------------------------------------

class ClassifierCentroids (ClassifierBase):
    '''Classifies regional centroids'''

    name = 'centroids'
    version = '1.0'

    # bounding box for images processed internally
    side = 5000

    def __str__(self):
        return 'Classifies regional centroids, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:centroids[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' uniformly sampled points '''

        Worig,Horig = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([Worig,Horig])/100.0))
        pts, num_points_x, num_points_y, sw, sh = distribute_points(num_points, Worig, Horig, border, equal=False, return_all=True)

        # estimate superpixel size
        W=self.side; sx=1.0
        if max(Worig, Horig)>W:
            sx = float(W) / max(Worig, Horig)
        sw = int(round(sw*sx)) # this provides an approximate number of centroids as requested

        # load SLIC super-pixel segmented image
        log.debug('Requesting superpixels of size: %s', sw)
        pix = image.pixels(operations='slice=,,1,1&resize=%s,%s,BC,MX&depth=8,d,u&transform=superpixels,%s,0.8&format=tiff'%(self.side, self.side, sw))
        W,H = pix.shape[0:2]

        # get regional centroids
        label_offset = 1 # region prop function uses 0 as background, we bump the class number and later subtract
        segments = skimage.measure.regionprops(pix+label_offset, cache=True)
        num_segs = len(segments)
        log.debug('Segmented the image into %s segments', num_segs)
        if num_segs<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Centroids classifier: no results')

        # compute scaling factor
        sx=1.0; sy=1.0
        if Worig!=W or Horig!=H:
            sx = float(W) / Worig
            sy = float(H) / Horig
            log.debug('Classify: Original image is larger, use scaling factors: %s,%s', sx, sy)

        # scale params to resized image
        border = int(round(border*sx))

        points = []
        for i,s in enumerate(segments):
            x,y = s.centroid
            if x>border and y>border and x<=W-border and y<=H-border:
                points.append((x/sx, y/sy))

        return classify_points(image, model, args, points, 'Regional centroids')
