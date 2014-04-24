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
from bq.features.controllers.Feature import calc_wrapper, ImageImport #import base class
from bq.features.controllers import Feature

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

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            polygon       = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            error_code    = tables.Int32Col(pos=3)
            error_message = tables.StringCol(200,pos=4)
            
        return Columns    
    
    @calc_wrapper       
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
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
    
    
        
        
