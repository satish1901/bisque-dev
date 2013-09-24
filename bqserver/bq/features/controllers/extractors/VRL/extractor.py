# -*- mode: python -*-
""" EHD library
"""

import cv2
import cv
import tables
from bq.features.controllers import Feature #import base class
from pyVRLLib import extractEHD, extractHTD
from pylons.controllers.util import abort
import logging
import uuid
import numpy as np
log = logging.getLogger("bq.features")

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
    resource = ['image']
    description = """Edge histogram descriptor also known as EHD"""
    length = 80 
    
    @Feature.wrapper    
    def calculate(self, **kw):
        #initalizing

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im    
        im = np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        descriptors=extractEHD(im)
        
        #initalizing rows for the table
        return [descriptors]

class HTD(Feature.Feature):
    """
        Initalizes table and calculates the HTD descriptor to be
        placed into the HDF5 table
        
        scale = 6
        rotation = 4
    """
    #initalize parameters
    file = 'features_htd.h5'
    name = 'HTD'
    resource = ['image']
    description = """Homogenious Texture Descriptor also called HTD is a texture descritpor
    which applies the gabor filter with 6 different scales and 4 orientations. After applying
    the 24 different gabor filters the mean and standard deviation of all the pixels are 
    calculated and the descriptor is returned"""
    length = 48 
    
    @Feature.wrapper   
    def calculate(self, **kw):
        
        #importing images from bisque
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im

        im = np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        return [extractHTD(im)] #calculating descriptor and return
    
class mHTD(Feature.Feature):
    """
        Initalizes table and calculates the HTD descriptor to be
        placed into the HDF5 table

        scale = 6
        rotation = 4
    """
    #initalize parameters
    file = 'features_htd.h5'
    name = 'mHTD'
    resource = ['image','mask']
    description = """Homogenious Texture Descriptor also called HTD is a texture descritpor
    which applies the gabor filter with 6 different scales and 4 orientations. After applying
    the 24 different gabor filters the mean and standard deviation of all the pixels are 
    calculated and the descriptor is returned. Requires a mask along with the image"""
    length = 48

    def returnhash(self,**resouce):
        image_uri = resouce['image']
        mask_uri = resouce['mask']
        uri_hash = uuid.uuid5(uuid.NAMESPACE_URL, str(image_uri)+str(mask_uri)) #combine the uris into one hash
        uri_hash = uri_hash.hex
        return uri_hash

    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            label     = tables.Int32Col(pos=3) 
        self.Columns = Columns

    
    @Feature.wrapper   
    def calculate(self, **resouce):
        image_uri = resouce['image']
        mask_uri = resouce['mask']
        
        #importing images from bisque
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im = cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im    
        
        #importing mask from image service
        Mask = Feature.ImageImport(mask_uri)
        mask_path = Mask.returnpath()
        mask = cv2.imread(mask_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Mask  
         
 
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
                
        mask = np.asarray(mask)
        if not mask.any():
            abort(415, 'Format was not supported')
            
        descriptors,labels = extractHTD(im, mask=mask) #calculating descriptor
            

        #initalizing rows for the table
        return descriptors, labels  
    
    