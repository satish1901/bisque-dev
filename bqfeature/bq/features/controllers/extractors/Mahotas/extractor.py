# -*- mode: python -*-
""" HAR library
"""

import numpy as np
from mahotas.features import haralick,lbp,pftas,tas,zernike_moments
from pylons.controllers.util import abort
from bq.features.controllers.Feature import calc_wrapper, ImageImport, rgb2gray,gray2rgb #import base class
from bq.features.controllers import Feature
from PIL import Image


class HAR(Feature.BaseFeature):
    """
        Initalizes table and calculates the HAR descriptor to be
        placed into the HDF5 table.
    """
    #parameters
    name = 'HAR'
    description = """Haralick Texure Features"""
    length = 13*4
    confidence = 'good'     
        
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing 
        image_uri = resource['image']
        with Feature.ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
            if len(im.shape)==3:
                im = rgb2gray(im)
        
        im = np.uint8(im)
        #calculate descriptor 
        descritptors = np.hstack(haralick(im))

        #initalizing rows for the table
        return [descritptors]
            
            
class HARColored(Feature.BaseFeature):
    """
        Initalizes table and calculates the colored HAR descriptor to be
        placed into the HDF5 table.    
    """
    #parameters
    name = 'HARColored'
    description = """Haralick Texure Features with colored image input"""
    length = 169
        
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing 
        image_uri = resource['image']
        with Feature.ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
            if len(im.shape)==2:
                im = gray2rgb(im)
            
        
        #calculate descriptor 
        descritptors = np.hstack(haralick(im))

        #initalizing rows for the table
        return [descritptors]    


class LBP(Feature.BaseFeature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'LBP'
    description = """Linear Binary Patterns: radius = 5 and points = 5"""
    length = 8
    confidence = 'good' 
        
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:
                im = rgb2gray(np.uint8(im))
            
            im=np.asarray(im)
            
             #calculating descriptor
            radius = 5
            points = 5
            descriptor = lbp(im,radius,points)
            
        #initalizing rows for the table
        return [descriptor]
        
            
#class LBPbro(BaseFeature):
#    """
#        Initalizes table and calculates the SURF descriptor to be
#        placed into the HDF5 table.
#    """
#    
#    #parameters
#    file = 'features_lbpbro.h5'
#    name = 'LBPbro'
#    description = """Linear Binary Patterns"""
#    length = 108
#        
#    @Feature.wrapper
#    def calculate(self, **resource):
#        """ Append descriptors to SURF h5 table """
#        #initalizing
#        image_uri = resource['image']
#
#        with Feature.ImageImport(image_uri) as imgimp:
#            im=cv2.imread(str(imgimp), cv2.CV_LOAD_IMAGE_GRAYSCALE)
#    
#            if im==None:
#                raise ValueError('Format was not supported')
#    
#            im=np.asarray(im)
#            
#             #calculating descriptor\
#            imagesize=im.shape
#            if imagesize[0]>imagesize[1]:
#                scale=imagesize[1]
#            else:
#                scale=imagesize[0]
#            
#            l=lbp(im,scale,8)
#            
#            b=lbp(im,scale/2,8)
#            
#            p=lbp(im,scale/4,8)
#            
#            descriptor = np.concatenate((l,b,p))
#            
#        #initalizing rows for the table
#        return [descriptor]
        
        
class PFTAS(Feature.BaseFeature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'PFTAS'
    description = """parameter free Threshold Adjacency Statistics"""
    length = 54 
    confidence = 'good' 
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:
                im = rgb2gray(np.uint8(im))  
 
            im = np.asarray(im)
            im = np.uint8(im)
            descriptor = pftas(im)
            
        #initalizing rows for the table
        return [descriptor]
    
class PFTASColored(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'PFTASColored'
    description = """parameter free Threshold Adjacency Statistics"""
    length = 162 
    confidence = 'good' 
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
            if len(im.shape)==2:
                im = gray2rgb(im) 

            im = np.asarray(im)
            im = np.uint8(im)
            descriptor = pftas(im)
            
        #initalizing rows for the table
        return [descriptor]
            
class TAS(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'TAS'
    description = """Threshold Adjacency Statistics"""
    length = 54 
    confidence = 'good' 
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to TAS h5 table """
        #initalizing
        image_uri = resource['image'] 
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:
                im = rgb2gray(np.uint8(im))  

            im=np.asarray(im) 
            im = np.uint8(im)
            descriptor = tas(im)
            
        #initalizing rows for the table
        return [descriptor]

class TASColored(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'TASColored'
    description = """Threshold Adjacency Statistics"""
    length = 162 
    confidence = 'good' 
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to TAS h5 table """
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
            if len(im.shape)==2:
                im = gray2rgb(im) 

            im=np.asarray(im) 
            im = np.uint8(im)
            descriptor = tas(im)
            
        #initalizing rows for the table
        return [descriptor]
            
            
class ZM(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'ZM'
    description = """Zernike Moment"""
    length = 25
    confidence = 'good' 
        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            if len(im.shape)==3:
                im = rgb2gray(np.uint8(im))
                
            im=np.asarray(im)        
            radius=8
            degree=8
            descritptor = zernike_moments(im,radius,degree)
            
        #initalizing rows for the table
        return [descritptor]
    