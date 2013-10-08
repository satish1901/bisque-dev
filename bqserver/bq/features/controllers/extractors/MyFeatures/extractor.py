# -*- mode: python -*-
""" FFTSD library
"""
import cv2
import cv
from pylons.controllers.util import abort
from bq.features.controllers import Feature #import base class
from fftsd_extract import FFTSD as fftsd
from lxml import etree
import urllib, urllib2, cookielib
import random
        
class FFTSD(Feature.Feature):
    
    #parameters
    file = 'features_fftsd.h5'
    name = 'FFTSD'
    resource = ['polygon']
    description = """Fast Fourier Transform Shape Descriptor"""
    length = 500

    @Feature.wrapper        
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        polygon_uri = resource['polygon']
        xml=Feature.XMLImport(polygon_uri+'?view=deep')
        tree=xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append([int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))])
        else:
            log.debug('polygon not found: must be a polygon gobject')
            abort(404, 'polygon not found: must be a polygon gobject')
        
        descriptor = fftsd(contour,self.length)
                
        #initalizing rows for the table
        return [descriptor]
    
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
    
class DTFE(Feature.Feature):
    """
        Dummy Test Feature Extractor
        This extractor is completely useless to calculate any 
        useful feature. 
        Purpose: to test the reliability of the feature service
    """
    #parameters
    file = 'features_dtfe'
    name = 'DTFE'
    description = """Dummy Test Feature Extractor (test feature) Calculates random numbers for features"""
    length = 64
    feature_format = 'int32'
    
    #cache = False
    
    @Feature.wrapper
    def calculate(self, **resource):
        """ Calculates features for DTFE"""
        #initalizing
        image_uri = resource['image']
        descriptor = [random.randint(0, 255) for x in range(64)]
                
        #initalizing rows for the table
        return [descriptor]
        
        
        
        
        
