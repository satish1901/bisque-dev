# -*- mode: python -*-
""" FFTSD library
"""
import cv2
import cv
from pylons.controllers.util import abort
from bq.features.controllers import Feature #import base class
from fftsd_extract import FFTSD
from lxml import etree
import urllib, urllib2, cookielib
        
class FFTSD(Feature.Feature):
    
    #parameters
    file = 'features_fftsd.h5'
    name = 'FFTSD'
    description = """Fast Fourier Transform Shape Descriptor"""
    length = 500
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing

        
        self.uri=uri
        #from bq.util.request import Request
        #content = Request(self.uri).get ()
        #content = urllib.urlopen(self.uri+'?view=deep') #import xml
        xml=Feature.XMLImport(self.uri+'?view=deep')
        tree=xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append([int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))])
        else:
            abort(404, 'polygon not found: must be a polygon gobject')
        
        descriptor = FFTSD(contour,self.length)
                
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor[0:500])
    
            

