# -*- mode: python -*-
""" HAR library
"""
import cv2
import cv
import numpy as np
from mahotas.features import haralick
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort

class HAR(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    #parameters
    file = 'features_har.h5'
    name = 'HAR'
    description = """Haralick Texure Features"""
    length = 13 
    parameter_info = ['row']
    
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing 

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        #calculate descriptor 
        descritptors = haralick(im)
        #initalizing rows for the table
        for i, descriptor in enumerate(descritptors):
            self.setRow(uri, idnumber, descriptor,i)
            

class LBP(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_lbp.h5'
    name = 'LBP'
    description = """Linear Binary Patterns: radius = 5 and points = 5"""
    length = 8
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
         #calculating descriptor\
        radius = 5
        points = 5
        descritptor = lbp(im,radius,points)
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
        
            
class LBPbro(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_lbpbro.h5'
    name = 'LBPbro'
    description = """Linear Binary Patterns"""
    length = 108
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
         #calculating descriptor\
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]
        else:
            scale=imagesize[0]
        
        l=lbp(im,scale,8)
        
        b=lbp(im,scale/2,8)
        
        p=lbp(im,scale/4,8)
        
        descriptor = np.concatenate((l,b,p))
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
        
        
class PFTAS(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_pftas.h5'
    name = 'PFTAS'
    description = """parameter free Threshold Adjacency Statistics"""
    length = 162 
    
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')

        descritptor = pftas(im)
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
            
class TAS(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_tas.h5'
    name = 'TAS'
    description = """Threshold Adjacency Statistics"""
    length = 162 
    
    def appendTable(self, uri, idnumber):
        """ Append descriptors to TAS h5 table """
        #initalizing
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        descriptor = tas(im)
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
            
class ZM(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_zm.h5'
    name = 'SURF'
    description = """Zernike Moment"""
    length = 25
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
       
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        radius=8
        degree=8
        descritptor = zernike_moments(im,radius,degree)
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)