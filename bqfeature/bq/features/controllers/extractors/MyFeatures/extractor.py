# -*- mode: python -*-
""" FFTSD library
"""
import cv2
import cv
import tables
import logging
from pylons.controllers.util import abort
from fftsd_extract import FFTSD as fftsd
from lxml import etree
import urllib, urllib2, cookielib
from bq.image_service.controllers.locks import Locks
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
    
    def outputTable(self,filename):
        """
        Output table for hdf output requests and uncached features
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            polygon = tables.StringCol(2000,pos=1)
            feature = tables.Col.from_atom(featureAtom, pos=2)
            
        with Locks(None, filename):
            with tables.openFile(filename,'a', title=self.name) as h5file: 
                outtable = h5file.createTable('/', 'values', Columns, expectedrows=1000000000)
            
        return
    
        
        
