# -*- mode: python -*-
""" EHD library
"""

import cv2
import cv

from bq.features.controllers import Feature #import base class

class EHD(Feature.Feature):
    """
        Initalizes table and calculates the Edge Histogram descriptor to be
        placed into the HDF5 table

        scale = 6
        rotation = 4
    """
    #initalize parameters
    file = 'features_ehd.h5'
    name = 'EHD'
    description = """Edge histogram descriptor also known as EHD"""
    length = 80 
    temptable = []
        
    def appendTable(self, uri, idnumber):
        #initalizing
        import include.EHD.extractEHD as ehd

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im    
        
        descriptors=ehd.extract(im)
        
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptors)

class HTD(Feature.Feature):
    """
        Initalizes table and calculates the HTD descriptor to be
        placed into the HDF5 table
        
        DISCLAIMER: This feature is RAM intensive and will CRASH 
        a machine if the image block it is use to calculate for is 
        TOO BIG.

        scale = 6
        rotation = 4
    """
    #initalize parameters
    file = 'features_htd.h5'
    name = 'HTD'
    description = """Homogenious Texture Descriptor also called HTD is a texture descritpor
    which applies the gabor filter with 6 different scales and 4 orientations. After applying
    the 24 different gabor filters the mean and standard deviation of all the pixels are 
    calculated and the descriptor is returned"""
    limitations = """Since the nresponses to the filters are computationally heavy to calculate
    the input has been limited to only images that are 1000 by 1000 pixels"""
    length = 48 
    temptable = []
    
    def appendTable(self, uri, idnumber):
        
        #importing images from bisque
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im    
        
        #check size and return a warning  
        if max(im.shape)>1000:
            abort('Warning: Image is too large for HTD. Must be smaller than 1000 by 1000.')
        
        descriptors = htd.extract(im) #calculating descriptor

        #initalizing rows for the table
        self.setRow(uri,idnumber,descriptors)