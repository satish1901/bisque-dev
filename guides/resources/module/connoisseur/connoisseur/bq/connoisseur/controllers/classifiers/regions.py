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
Connoisseur: region classifiers
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
from skimage.feature import peak_local_max, corner_peaks
import pyvoro
#from scipy.spatial import ConvexHull

log = logging.getLogger("bq.connoisseur.classifier_regions")

try:
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union, unary_union
except Exception:
    log.info('Warning: Shapely could not be loaded, region detection will be disabled!')

from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses
from bq.connoisseur.controllers.classifier_base import ClassifierBase
from bq.connoisseur.controllers.utils import get_color_html, image_patch
from bq.connoisseur.controllers.data_token import DataToken
from bq.connoisseur.controllers.gobjects import point
from bq.connoisseur.controllers.classifiers.points import distribute_points, get_class_info, get_sample_confidence

#---------------------------------------------------------------------------------------
# classifier: partition image into regions producing low-res polygons
# This method guarantees full image partitioning covering the area of the uncertain samples
#---------------------------------------------------------------------------------------

class ClassifierSubstrate (ClassifierBase):

    name = 'substrate'
    version = '1.0'

    def __str__(self):
        return 'Partitions image into convex regions, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:substrate[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' partition image into regions producing low-res polygons
        This method guarantees full image partitioning covering the area of the uncertain samples
        '''

        Worig,Horig = image.size()
        num_points = int(args.get('points', 100))
        border = float(args.get('border', 5))
        border = int(round(border*np.mean([Worig,Horig])/100.0))
        my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
        my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
        my_confidence = float(args.get('confidence', 0))

        # uniform sampling
        pts, num_points_x, num_points_y, sw, sh = distribute_points(num_points, Worig, Horig, border, equal=False, return_all=True)

        # load image
        # pim = image.pixels(operations='slice=,,1,1&resize=6000,6000,BC,MX&depth=8,d,u&format=png')
        # W,H = pim.shape[0:2]

        # # compute scaling factor
        # sx=1.0; sy=1.0
        # if Worig>W or Horig>H:
        #     sx = float(W) / Worig
        #     sy = float(H) / Horig
        #     log.debug('Classify: Original image is larger, use scaling factors: %s,%s', sx, sy)

        adapter = model.create_adapter_pixels(model=model, args=args, image=image)

        # classify points
        results = []
        for x,y in pts:
            #pix = image_patch(pim, int(x*sx), int(y*sy), model.db_patch_width, model.db_patch_height)
            pix = adapter.get_adapted_image_patch(gob=point(x=y, y=x))
            out_class,goodness = model.classify(pix)
            label, accuracy, ignored = get_class_info(model, out_class, at_goodness=my_goodness)
            confidence = get_sample_confidence(accuracy, goodness)

            if goodness >= my_goodness and accuracy >= my_accuracy and confidence >= my_confidence and ignored is False:
                #print '%s,%s classified as "%s" with %s goodness score'%(x, y, predicted_class, goodness)
                #log.debug('%s,%s classified as "%s" with %s goodness score'%(x, y, predicted_class, goodness))
                results.append({
                    'x': x,
                    'y': y,
                    'id': out_class,
                    'goodness': goodness,
                })

        if len(results)<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Regions classifier: no results')

        #------------------------------------------------------
        # init dense grid with measurements
        #------------------------------------------------------

        label_offset = 1 # region prop function uses 0 as background, we bump the class number and later subtract

        def img_to_pp (p):
            return (int(round((p[0]-border)/sw)), int(round((p[1]-border)/sh)))

        def pp_to_img (p):
            return (int(round(p[0]*sw+border)), int(round(p[1]*sh+border)))

        # create a grid with class labels
        Gi = num_points_y
        Gj = num_points_x+1
        G = np.zeros((Gi, Gj), dtype=np.uint8)
        C = np.zeros((Gi, Gj), dtype=np.double)
        for r in results:
            x,y = img_to_pp((r['x'], r['y']))
            idx = r['id']
            goodness = r['goodness']
            G[y,x] = idx+label_offset
            C[y,x] = goodness

        #skimage.io.imsave(grid_file, G)

        #------------------------------------------------------
        # compute quasi-convex region centroids
        #------------------------------------------------------

        results = []
        for idx in range(model.number_classes_in_model):
            GG = np.zeros((Gi, Gj), dtype=np.uint8)
            for i in range(0,Gi):
                for j in range(0,Gj):
                    if G[i,j] == idx+label_offset:
                        GG[i,j] = 255
                    else:
                        GG[i,j] = 0
            #grid_flt_file = 'D:\\develop\\caffe\\regions\\grid_%s.tif'%(idx)
            #skimage.io.imsave(grid_flt_file, GG)

            # ensure boundary is background
            GGG = np.zeros((Gi+2, Gj+2), dtype=np.uint8)
            GGG[1:Gi+1, 1:Gj+1] = GG
            distance = distance_transform_edt(GGG)
            distance = distance[1:Gi+1, 1:Gj+1]

            #grid_flt_file = 'D:\\develop\\caffe\\regions\\grid_%s_distance.tif'%(idx)
            #skimage.io.imsave(grid_flt_file, distance)

            #local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((3, 3)), labels=GG)
            local_maxi = corner_peaks(distance, indices=False, footprint=np.ones((3, 3)), labels=GG)
            markers = ndi.label(local_maxi)[0]
            labeled = watershed(-distance, markers, mask=GG)
            segments = skimage.measure.regionprops(labeled, intensity_image=C, cache=True)

            for i,r in enumerate(segments):
                c = r.centroid
                w = r.area
                #w = r.convex_area
                #goodness = r.max_intensity
                goodness = r.mean_intensity
                label, accuracy, ignored = get_class_info(model, out_class, at_goodness=0)
                confidence = get_sample_confidence(accuracy, goodness)

                y,x = pp_to_img(c)
                out_class = idx
                results.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'area': w,
                    'area_seg': w,

                    'id': out_class,
                    #'color': get_color_html(out_class),
                    'label': label,
                    'accuracy': accuracy,
                    'goodness': goodness,
                    'confidence': confidence,
                })

        if len(results)<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Region classifier: no results')

        #------------------------------------------------------
        # compute Voronoi polygons
        #------------------------------------------------------

        points = [[r['x'], r['y']] for r in results]
        bounds = [[0.0, Worig], [0.0, Horig]]
        radii  = [r['w'] for r in results]

        cells = pyvoro.compute_2d_voronoi(
            points,
            bounds,
            2.0, # block size
            radii = radii
        )

        for i in range(len(results)):
            results[i]['gob'] = 'polygon'
            results[i]['vertex'] = [(p[0], p[1]) for p in cells[i]['vertices']]
            results[i]['area'] = cells[i]['volume']

        # hierarchical passes over samples whose classes have child models

        # return results
        return DataToken(data=results, mime='table/gobs', name='Substrate')


#---------------------------------------------------------------------------------------
# classifier: Regions
#---------------------------------------------------------------------------------------

class ClassifierRegions (ClassifierBase):

    name = 'regions'
    version = '1.0'

    # bounding box for images processed internally
    side = 5000

    def __str__(self):
        return 'Partitions image into simple semantic regions, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:regions[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def get_polygons(self, image, model, args):
        ''' partition image into regions producing low-res polygons
        This method does not guarantee full image partitioning by removing the uncertain regions
        '''

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
        log.debug('Regions classifier: requesting superpixels of size: %s', sw)
        pix = image.pixels(operations='slice=,,1,1&resize=%s,%s,BC,MX&depth=8,d,u&transform=superpixels,%s,0.8&format=tiff'%(self.side, self.side, sw))
        W,H = pix.shape[0:2]

        # get regional centroids
        label_offset = 1 # region prop function uses 0 as background, we bump the class number and later subtract
        segments = skimage.measure.regionprops(pix+label_offset, cache=True)
        num_segs = len(segments)
        log.debug('Regions classifier: segmented the image into %s segments', num_segs)
        if num_segs<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Regions classifier: no results')

        # compute scaling factors
        sx=1.0; sy=1.0
        if Worig!=W or Horig!=H:
            sx = float(W) / Worig
            sy = float(H) / Horig
            log.debug('Regions classifier: Original image is larger, use scaling factors: %s,%s', sx, sy)

        # scale params to resized image
        border = int(round(border*sx))

        # get regional centroids in original image space
        points = []
        for i,s in enumerate(segments):
            x,y = s.centroid
            if x>border and y>border and x<=W-border and y<=H-border:
                points.append((x/sx, y/sy))

        # classify regional centroids

        # load image
        #pim = image.pixels(operations='slice=,,1,1&resize=6000,6000,BC,MX&depth=8,d,u&format=png')
        #W,H = pim.shape[0:2]
        adapter = model.create_adapter_pixels(model=model, args=args, image=image)

        # classify points
        results = []
        for x,y in points:
            #pix = image_patch(pim, int(x), int(y), model.db_patch_width, model.db_patch_height)
            pix = adapter.get_adapted_image_patch(gob=point(x=y, y=x))
            out_class,goodness = model.classify(pix)
            label, accuracy, ignored = get_class_info(model, out_class, at_goodness=0)
            confidence = get_sample_confidence(accuracy, goodness)
            results.append({
                'x': x,
                'y': y,
                'id': out_class,
                'label': label,
                'ignored': ignored,
                'accuracy': accuracy,
                'goodness': goodness,
                'confidence': confidence,
            })

        if len(results)<1:
            raise ConnoisseurException(responses.NO_CONTENT, 'Regions classifier: no results')

        #------------------------------------------------------
        # compute Voronoi polygons
        #------------------------------------------------------
        log.debug('Regions classifier: computing Voronoi')
        points = [[r['x'], r['y']] for r in results]
        bounds = [[0.0, Worig], [0.0, Horig]]
        #radii  = [r['w'] for r in results]

        # log.debug('Regions classifier: bounds %s', bounds)
        # log.debug('Regions classifier: points %s', points)

        cells = pyvoro.compute_2d_voronoi(
            points,
            bounds,
            2.0, # block size
            #radii = radii
        )

        log.debug('Regions classifier: producing polygons')
        for i in range(len(results)):
            results[i]['gob'] = 'polygon'
            results[i]['vertex'] = [(p[0], p[1]) for p in cells[i]['vertices']]
            results[i]['area'] = cells[i]['volume']

        return results


    def classify(self, image, model, args):
        ''' partition image into regions producing low-res polygons
        This method does not guarantee full image partitioning by removing the uncertain regions
        '''

        results = self.get_polygons(image, model, args)

        # filter out polygons below requested goodness
        my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
        my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
        my_confidence = float(args.get('confidence', 0))

        results = [v for v in results if v['goodness']>=my_goodness and v['accuracy'] >= my_accuracy and v['confidence'] >= my_confidence and v['ignored'] is False ]

        # hierarchical passes over samples whose classes have child models

        # return results
        return DataToken(data=results, mime='table/gobs', name='Regions')


#---------------------------------------------------------------------------------------
# classifier: Detection
#---------------------------------------------------------------------------------------

def split(u, v, points):
    # return points on left side of UV
    return [p for p in points if np.cross(p - u, v - u) < 0]

def extend(u, v, points):
    if not points:
        return []

    # find furthest point W, and split search to WV, UW
    w = min(points, key=lambda p: np.cross(p - u, v - u))
    p1, p2 = split(w, v, points), split(u, w, points)
    return extend(w, v, p1) + [w] + extend(u, w, p2)

def convex_hull(points):
    # find two hull points, U, V, and split to left and right search
    u = min(points, key=lambda p: p[0])
    v = max(points, key=lambda p: p[0])
    left, right = split(u, v, points), split(v, u, points)

    # find convex hull on each side
    return [v] + extend(u, v, left) + [u] + extend(v, u, right) + [v]

def group_connected_polygons(P):
    #from shapely.geometry import Polygon
    #p1=Polygon([(0,0),(1,1),(1,0)])
    #p2=Polygon([(0,1),(1,0),(1,1)])
    #print p1.intersects(p2)

    groups = [[P.pop()]]
    while len(P)>0:
        p = P.pop()
        found = False
        for g in groups:
            for pp in g:
                p1 = set([(round(v[0]), round(v[1])) for v in p['vertex']])
                p2 = set([(round(v[0]), round(v[1])) for v in pp['vertex']])
                #log.debug('Computing intersection of %s and %s', p1, p2)
                if len(p1.intersection(p2))>1:
                    g.append(p)
                    found = True
                    #log.debug('Sets are intersecting: %s', g)
                    break
                #else:
                #    log.debug('No intersections')
            if found is True:
                break
        if found is False:
            groups.append([p])
    #log.debug('Detected groups: %s', groups)
    return groups

def combine_polygons(group):
    # points = []
    # for p in group:
    #     for v in p['vertex']:
    #         points.append([v[0], v[1]])
    # hull = convex_hull(np.array(points))
    # return [(p[0], p[1]) for p in hull]

    # use polygon union instead of convexhull
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union, unary_union

    polygons = []
    for p in group:
        polygons.append(Polygon([(round(v[0]), round(v[1])) for v in p['vertex']]))
    u = unary_union(polygons)
    try:
        return list(u.exterior.coords) #pylint: disable=no-member
    except Exception:
        return list(u.geoms[0].exterior.coords) #pylint: disable=no-member

def groups_params(group):
    area = []
    accuracy = []
    goodness = []
    confidence = []
    for p in group:
        area.append(p['area'])
        accuracy.append(p['accuracy'])
        goodness.append(p['goodness'])
        confidence.append(p['confidence'])
    return area, accuracy, goodness, confidence

class ClassifierDetection (ClassifierRegions):
    '''Partitions image into combined semantic regions'''

    name = 'detection'
    version = '1.0'

    def __str__(self):
        return 'Partitions image into combined semantic regions, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID/method:detection[/points:10][/goodness:95][/accuracy:95][/confidence:95][/border:300][/format:csv]'

    def classify(self, image, model, args):
        ''' partition image into regions producing combined polygons
        This method does not guarantee full image partitioning by removing the uncertain regions
        '''
        results = self.get_polygons(image, model, args)

        # filter out polygons below requested goodness
        my_goodness = float(args.get('goodness', model.minimum_goodness*100))/100.0
        my_accuracy = float(args.get('accuracy', model.minimum_accuracy*100))
        my_confidence = float(args.get('confidence', 0))

        results = [v for v in results if v['goodness']>=my_goodness and v['accuracy'] >= my_accuracy and v['confidence'] >= my_confidence and v['ignored'] is False ]

        #log.debug('Combining %s polygons', len(results))

        # first find out how many classes are present
        present_classes = set()
        for v in results:
            present_classes.add(v['id'])

        #log.debug('Found classes: %s', present_classes)

        # combine adjacent polygons with the same class
        results_compbined = []
        for c in present_classes:
            P = []
            for v in results:
                # separate polygons of a certain label
                if c == v['id']:
                    P.append(v)

            #log.debug('For class %s found polygons: %s', c, len(P))

            # find convex hull for connected groups
            groups = group_connected_polygons(P)
            #log.debug('Found %s groups', len(groups))
            for g in groups:
                vrtx = combine_polygons(g)
                label = g[0]['label']
                area, accuracy, goodness, confidence = groups_params(g)
                #log.debug('Convex hull: %s', vrtx)

                results_compbined.append({
                    'id': c,
                    'gob': 'polygon',
                    'vertex': vrtx,
                    'label': label,
                    'area': np.cumsum(area),
                    'accuracy': np.average(accuracy),
                    'goodness': np.average(goodness),
                    'confidence': np.average(confidence),
                })

        results = results_compbined
        # hierarchical passes over samples whose classes have child models

        # return results
        return DataToken(data=results, mime='table/gobs', name='Detection')
