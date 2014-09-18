# -*- mode: python -*-
""" EHD library
"""
import tables
from bq.features.controllers.Feature import calc_wrapper, ImageImport, rgb2gray #import base class
from bq.features.controllers import Feature
from pyVRLLib import extractEHD, extractHTD
from pylons.controllers.util import abort
import logging
import uuid
import numpy as np
from bq.image_service.controllers.locks import Locks
from PIL import Image

log = logging.getLogger("bq.features")

class EHD(Feature.BaseFeature):
    """
        Initalizes table and calculates the Edge Histogram descriptor to be
        placed into the HDF5 table

        scale = 6
        rotation = 4
    """
    #initalize parameters
    name = 'EHD'
    resource = ['image']
    description = """Edge histogram descriptor also known as EHD"""
    length = 80
    confidence = 'poor' #gets different values on different machines, not sure what is causing the issue
    
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:           
                im = rgb2gray(im)
            im = np.asarray(im)        
            descriptors=extractEHD(im)
        
        #initalizing rows for the table
        return [descriptors]

#class HTD(Feature.BaseFeature):
#    """
#        Initalizes table and calculates the HTD descriptor to be
#        placed into the HDF5 table
#        
#        scale = 6
#        rotation = 4
#    """
#    #initalize parameters
#    name = 'HTD'
#    resource = ['image']
#    description = """Homogenious Texture Descriptor also called HTD is a texture descritpor
#    which applies the gabor filter with 6 different scales and 4 orientations. After applying
#    the 24 different gabor filters the mean and standard deviation of all the pixels are 
#    calculated and the descriptor is returned"""
#    length = 48 
#    confidence = 'good'
#        
#    @calc_wrapper
#    def calculate(self, **resource):
#        
#        #importing images from bisque
#        image_uri = resource['image']
#        with ImageImport(image_uri) as imgimp:
#            #log.debug('Image Location: %s'%imgimp.path)
#            #im=cv2.imread(str(imgimp), cv2.CV_LOAD_IMAGE_GRAYSCALE)
#            im = imgimp.from_tiff2D_to_numpy()
#            
#            if len(im.shape)==3:           
#                im = rgb2gray(im)
#                
#            im = np.asarray(im)
#            descriptor,label = extractHTD(im)
#        #log.debug('descriptor : %s'%str(descriptor))
#        return [descriptor] #calculating descriptor and return
#    
#    
#class mHTD(Feature.BaseFeature):
#    """
#        Initalizes table and calculates the HTD descriptor to be
#        placed into the HDF5 table
#
#        scale = 6
#        rotation = 4
#    """
#    #initalize parameters
#    name = 'mHTD'
#    resource = ['image','mask']
#    parameter = ['label']
#    description = """Homogenious Texture Descriptor also called HTD is a texture descritpor
#    which applies the gabor filter with 6 different scales and 4 orientations. After applying
#    the 24 different gabor filters the mean and standard deviation of all the pixels are 
#    calculated and the descriptor is returned. Requires a mask along with the image"""
#    length = 48
#
#
#    def cached_columns(self):
#        """
#            Columns for the cached tables
#        """
#        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
#
#        class Columns(tables.IsDescription):
#            idnumber  = tables.StringCol(32,pos=1)
#            feature   = tables.Col.from_atom(featureAtom, pos=2)
#            label     = tables.Int32Col(pos=3) 
#
#        return Columns
#        
#    def output_feature_columns(self):
#        """
#            Columns for the output table for the feature column
#        """
#        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
#
#        class Columns(tables.IsDescription):
#            image   = tables.StringCol(2000,pos=1)
#            mask    = tables.StringCol(2000,pos=2)
#            feature_type  = tables.StringCol(20, pos=3)
#            feature = tables.Col.from_atom(featureAtom, pos=4)
#            label   = tables.Int32Col(pos=5)
#            
#        return Columns
#
#    def output_error_columns(self):
#        """
#            Columns for the output table for the error columns
#        """
#        class Columns(tables.IsDescription):
#            image         = tables.StringCol(2000,pos=1)
#            mask          = tables.StringCol(2000,pos=2)
#            feature_type  = tables.StringCol(20, pos=3)
#            error_code    = tables.Int32Col(pos=4)
#            error_message = tables.StringCol(200,pos=5)
#            
#        return Columns
#
#    
#    @calc_wrapper  
#    def calculate(self, **resource):
#        image_uri = resource['image']
#        mask_uri = resource['mask']
#        
#        
#        with ImageImport(image_uri) as imgimp:
#            with Feature.ImageImport(mask_uri) as maskimp:
#
#                im = imgimp.from_tiff2D_to_numpy()
#                im = rgb2gray(im)
#
#                mask = maskimp.from_tiff2D_to_numpy()
#
#                if len(mask.shape)==3:
#                    mask = rgb2gray(mask)
#                       
#                im=np.asarray(im)
#                mask = np.asarray(mask)                    
#                descriptors,labels = extractHTD(im, mask=mask) #calculating descriptor
#            
#        #initalizing rows for the table
#        return descriptors, labels  
  
    