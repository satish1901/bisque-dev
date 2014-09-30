# -*- mode: python -*-
""" HAR library
"""

import numpy as np
from mahotas.features import haralick,lbp,pftas,tas,zernike_moments
from pylons.controllers.util import abort
from bq.features.controllers.Feature import ImageImport, rgb2gray,gray2rgb #import base class
from bq.features.controllers import Feature
from bq.features.controllers.exceptions import FeatureExtractionError
from bqapi.comm import BQServer
from PIL import Image


def except_image_only(resource):
    if resource.image is None:
        raise FeatureExtractionError(resource, 400, 'Image resource is required')
    if resource.mask:
        raise FeatureExtractionError(resource, 400, 'Mask resource is not accepted')
    if resource.gobject:
        raise FeatureExtractionError(resource, 400, 'Gobject resource is not accepted')

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
        
        
    def calculate(self, resource):
        #initalizing 
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='gray')
        with Feature.ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
        
        im = np.uint8(im)
        #calculate descriptor 
        descritptors = np.hstack(haralick(im))

        #initalizing rows for the table
        return descritptors
            
            
class HARColored(Feature.BaseFeature):
    """
        Initalizes table and calculates the colored HAR descriptor to be
        placed into the HDF5 table.    
    """
    #parameters
    name = 'HARColored'
    description = """Haralick Texure Features with colored image input"""
    length = 169
        
        
    def calculate(self, resource):
        #initalizing 
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='display')
        with Feature.ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())
        
        #calculate descriptor 
        descritptors = np.hstack(haralick(im))

        #initalizing rows for the table
        return descritptors 


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
        
    def calculate(self, resource):
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='gray')
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im=np.asarray(im)
            
             #calculating descriptor
            radius = 5
            points = 5
            descriptor = lbp(im,radius,points)
            
        #initalizing rows for the table
        return descriptor
        
        
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
    
    def calculate(self, resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='gray')
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
 
            im = np.asarray(im)
            im = np.uint8(im)
            descriptor = pftas(im)
            
        #initalizing rows for the table
        return descriptor
    
class PFTASColored(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'PFTASColored'
    description = """parameter free Threshold Adjacency Statistics"""
    length = 162 
    confidence = 'good' 
    
    def calculate(self, resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='display')        
        with ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())

            im = np.asarray(im)
            im = np.uint8(im)
            descriptor = pftas(im)
            
        #initalizing rows for the table
        return descriptor
            
class TAS(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'TAS'
    description = """Threshold Adjacency Statistics"""
    length = 54 
    confidence = 'good' 
    
    def calculate(self, resource):
        """ Append descriptors to TAS h5 table """
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image 
        image_uri = BQServer().prepare_url(image_uri, remap='gray')
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im=np.asarray(im) 
            im = np.uint8(im)
            descriptor = tas(im)
            
        #initalizing rows for the table
        return descriptor

class TASColored(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'TASColored'
    description = """Threshold Adjacency Statistics"""
    length = 162 
    confidence = 'good' 
    
    def calculate(self, resource):
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='display')          
        with ImageImport(image_uri) as imgimp:
            im = np.uint8(imgimp.from_tiff2D_to_numpy())

            im=np.asarray(im) 
            im = np.uint8(im)
            descriptor = tas(im)
            
        #initalizing rows for the table
        return descriptor
            
            
class ZM(Feature.BaseFeature):
    """
    """
    
    #parameters
    name = 'ZM'
    description = """Zernike Moment"""
    length = 25
    confidence = 'good' 
        
    def calculate(self, resource):
        #initalizing
        except_image_only(resource)
        
        image_uri = resource.image
        image_uri = BQServer().prepare_url(image_uri, remap='gray')        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
                
            im=np.asarray(im)        
            radius=8
            degree=8
            descritptor = zernike_moments(im,radius,degree)
            
        #initalizing rows for the table
        return descritptor
    