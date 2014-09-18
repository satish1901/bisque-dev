# -*- mode: python -*-
""" FFTSD library
"""

import tables
import logging
from pylons.controllers.util import abort
from fftsd_extract import FFTSD as fftsd
from lxml import etree
import urllib, urllib2, cookielib
import random
from bq.features.controllers.Feature import calc_wrapper, ImageImport, rgb2gray, gray2rgb  #import base class
from bq.features.controllers import Feature
from hog_extractor import histogram_of_oriented_gradients
#from htd_extractor import homogenious_texture_descriptor

log = logging.getLogger("bq.features")

class FFTSD(Feature.BaseFeature):
    
    #parameters
    file = 'features_fftsd.h5'
    name = 'FFTSD'
    resource = ['polygon']
    description = """Fast Fourier Transform Shape Descriptor"""
    length = 500
    confidence = 'good'
    
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            polygon       = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Col.from_atom(featureAtom, pos=3)
            
        return Columns
  
    
    @calc_wrapper       
    def calculate(self, **resource):
        """ Append descriptors to FFTSD h5 table """
        #initalizing
        polygon_uri = resource['polygon']
        poly_xml=Feature.xml_import(polygon_uri+'?view=deep')
        if poly_xml.tag==self.resource[0]:
            vertices = poly_xml.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append([int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))])
                
        else:
            log.debug('Polygon not found: Must be a polygon gobject')
            raise ValueError('Polygon not found: Must be a polygon gobject') #an excpetion instead of abort so work flow is not interupted
        
        descriptor = fftsd(contour,self.length)
                
        #initalizing rows for the table
        return [descriptor[:500]]
    
    
#class HOG(Feature.BaseFeature):
#    
#    file = 'features_hog.h5'
#    name = 'HOG'
#    description = """Histogram of Orientated Gradients: bin = 9"""
#    length = 9
#    confidence = 'good'    
#        
#    @calc_wrapper       
#    def calculate(self, **resource):
#        """ Append descriptors to HOG h5 table """
#        #initalizing
#        image_uri = resource['image']
#
#        with ImageImport(image_uri) as imgimp:
#            im = imgimp.from_tiff2D_to_numpy()
#            if len(im.shape)==3:
#                im = rgb2gray(im)
#                
#        descriptor = histogram_of_oriented_gradients(im)
#                
#        #initalizing rows for the table
#        return [descriptor]
    
    
class HTD(Feature.BaseFeature):
    
    file = 'feature_htd.h5'
    name = 'HTD'
    description = """Homogenious Texture Descriptor"""
    length = 48
    confidence = 'good'    
        
    @calc_wrapper       
    def calculate(self, **resource):
        """ Append descriptors to HOG h5 table """
        #initalizing
        image_uri = resource['image']

        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:
                im = rgb2gray(im)
                
        descriptor = homogenious_texture_descriptor(im)
                
        #initalizing rows for the table
        return [descriptor]     
    