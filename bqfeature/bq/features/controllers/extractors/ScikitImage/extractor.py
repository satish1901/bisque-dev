# -*- mode: python -*-
""" MyFeature library
"""

import logging
from lxml import etree
import tables
import numpy as np
from bqapi.comm import BQServer
import random
from bq.features.controllers.utils import image2numpy, except_image_only, fetch_resource
from bq.features.controllers import Feature
from skimage.feature import corner_harris, corner_peaks
from skimage.feature import BRIEF as BRIEF_
from skimage.feature import ORB
from skimage.feature import hog
from skimage.feature import local_binary_pattern


log = logging.getLogger("bq.features.ScikitImage")

class BRIEF(Feature.BaseFeature):
    
    #parameters
    name = 'BRIEF'
    description = """Binary Robust Independent Elementary Features using the corner harris as the keypoint selector"""
    length = 256
    #confidence = 'good'
    parameter = ['x','y']

    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        return {
            'idnumber'  : tables.StringCol(32,pos=1),
            'feature'   : tables.Col.from_atom(featureAtom, pos=2),
            'x'         : tables.Float32Col(pos=3),
            'y'         : tables.Float32Col(pos=4),
        }
    
    def workdir_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        return {
                'image'     : tables.StringCol(2000,pos=1),
                'mask'      : tables.StringCol(2000,pos=2),
                'gobject'   : tables.StringCol(2000,pos=3),
                'feature'   : tables.Col.from_atom(featureAtom, pos=4),
                'x'         : tables.Float32Col(pos=5),
                'y'         : tables.Float32Col(pos=6),
        }

    
    def calculate(self, resource):
        except_image_only(resource)
        im = image2numpy(resource.image, remap='gray')
        keypoints = corner_peaks(corner_harris(im), min_distance=1)
        extractor = BRIEF_()
        extractor.extract(im, keypoints)
        
        #initalizing rows for the table
        return (extractor.descriptors, keypoints[:,0], keypoints[:,1])
    
    
class ORB2(Feature.BaseFeature):
    
    name = 'ORB2'
    description = """Oriented FAST and rotated BRIEF feature detector and binary descriptor extractor"""
    length = 256
    #confidence = 'good'
    parameter = ['x','y','response','scale','orientation']

    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        return {
            'idnumber'    : tables.StringCol(32,pos=1),
            'feature'     : tables.Col.from_atom(featureAtom, pos=2),
            'x'           : tables.Float32Col(pos=3),
            'y'           : tables.Float32Col(pos=4),
            'response'    : tables.Float32Col(pos=5),
            'scale'       : tables.Float32Col(pos=6),
            'orientation' : tables.Float32Col(pos=7),
        }
    
    def workdir_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        return {
                'image'     : tables.StringCol(2000,pos=1),
                'mask'      : tables.StringCol(2000,pos=2),
                'gobject'   : tables.StringCol(2000,pos=3),
                'feature'   : tables.Col.from_atom(featureAtom, pos=4),
                'x'         : tables.Float32Col(pos=5),
                'y'         : tables.Float32Col(pos=6),
                'response'    : tables.Float32Col(pos=7),
                'scale'       : tables.Float32Col(pos=8),
                'orientation' : tables.Float32Col(pos=9),
        }
    
    def calculate(self, resource):
        except_image_only(resource)
        im = image2numpy(resource.image, remap='gray')
        extractor = ORB()
        extractor.detect_and_extract(im)
        return (extractor.descriptors, 
                extractor.keypoints[:,0], 
                extractor.keypoints[:,1],
                extractor.responses,
                extractor.scales,
                extractor.orientations)
    
    
class HOG(Feature.BaseFeature):
    name = 'HOG'
    description = """Extract Histogram of Oriented Gradients orientation: 9 pixels per cell: length,width
    cells per block 1,1. Crops the image into a square and extracts HOG"""
    length = 9
    #confidence = 'good'
    
    def calculate(self, resource):
        except_image_only(resource)
        im = image2numpy(resource.image, remap='gray')
        min_length = np.min(im.shape)
        return hog(im, pixels_per_cell=(min_length, min_length), cells_per_block=(1,1))
    
    
#requires the implimetation of input parameters to fs
#class LBP2(Feature.BaseFeature):
#    name = 'LBP2'
#    description = 
#    length = 
#    
#    def calculate(self, resource, **kwargs):
#        """
#            resource: image
#            P: (int) Number of circularly symmetric neighbour set points (quantization of the angular space).
#            R: (float) Radius of circle (spatial resolution of the operator).
#            method: {'default': 'original local binary pattern which is gray scale but not rotation invariant',
#                     'ror': 'extension of default implementation which is gray scale and rotation invariant'
#                     'uniform': 'improved rotation invariance with uniform patterns and finer quantization of 
#                     the angular space which is gray scale and rotation invariant.'
#                     'var': 'rotation invariant variance measures of the contrast of local image texture which 
#                     is rotation but not gray scale invariant.'}
#        """
#        except_image_only(resource)
#        P = kwargs['P']
#        R = kwargs['R']
#        method = kwargs['method']
#        local_binary_pattern(resource.image, P, R, method=method)
        