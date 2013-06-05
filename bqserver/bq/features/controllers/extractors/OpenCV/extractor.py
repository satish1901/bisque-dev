# -*- mode: python -*-
""" OpenCV Feature
"""
import cv2
import cv
import logging
import numpy as np
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort
log = logging.getLogger("bq.features")

class BRISK(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_brisk.h5'
    name = 'BRISK'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    parameter_info = ['x','y','response','size','angle','octave']
    
        
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to BRISK h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.BRISK().detect(im)                             # keypoints
        
        log.debug('fs: %s' %len(fs))
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("BRISK")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

class BRISKc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_briskc.h5'
    name = 'BRISKc'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    parameter_info = ['x','y','response','size','angle','octave']
    

        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/5
        else:
            scale=imagesize[0]/5
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("BRISK")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

            
class ORB(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_orb.h5'
    name = 'ORB'
    description = """The algorithm uses FAST in pyramids to detect stable keypoints, selects the 
    strongest features using FAST response, finds their orientation using first-order moments and
    computes the descriptors using BRIEF (where the coordinates of random point pairs (or k-tuples)
    are rotated according to the measured orientation).
    This explination was taken from opencv documention on orb and the algorithm iself was taken from
    the opencv library"""
    length = 32
    contents = 'several points are described in an image, each will have a position: X Y Scale'
    parameter_info = ['x','y','response','size','angle','octave']
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to ORB h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im      
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.ORB().detect (im)                             # keypoints
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("ORB")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

class ORBc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_orbc.h5'
    name = 'ORBc'
    description = """The algorithm uses FAST in pyramids to detect stable keypoints, selects the 
    strongest features using FAST response, finds their orientation using first-order moments and
    computes the descriptors using BRIEF (where the coordinates of random point pairs (or k-tuples)
    are rotated according to the measured orientation).
    This explination was taken from opencv documention on orb and the algorithm iself was taken from
    the opencv library"""
    length = 32
    contents = 'several points are described in an image, each will have a position: X Y Scale'
    parameter_info = ['x','y','response','size','angle','octave']
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to ORB h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im      
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]
        else:
            scale=imagesize[0]
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("ORB")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

class SIFT(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_sift.h5'
    name = 'SIFT'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 128
    parameter_info = ['x','y','response','size','angle','octave']
    
        
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.SIFT().detect(im)                             # keypoints
        
        log.debug('fs: %s' %len(fs))
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)


class SIFTc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_siftc.h5'
    name = 'SIFTc'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 128
    parameter_info = ['x','y','response','size','angle','octave']
    
        
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/3
        else:
            scale=imagesize[0]/3
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)   # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

class SIFTg(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_siftg.h5'
    name = 'SIFTg'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 128
    parameter_info = ['x','y','response','size','angle','octave']
    
        
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        
 
        
        Session = BQSession().init_local('admin','admin',bisque_root='http://128.111.185.26:8080')
        data = Session.fetchxml(uri+'?view=deep,clean') #needs to be changed only for prototyping purposes
        vertices=data.xpath('point/vertex')
        log.debug('vertices: %s' % vertices)
        resource_uniq = data.attrib['resource_uniq']
        Im = Feature.ImageImport('http://128.111.185.26:8080/image_service/images/'+resource_uniq) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        fs=[]
        for vertex in vertices:
            fs.append(cv2.KeyPoint(float(vertex.attrib['x']),float(vertex.attrib['y']),50))  # keypoints
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)
                
class SURF(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_surf.h5'
    name = 'SURF'
    description = """Speeded Up Robust Features also know as SURF"""
    length = 64 
    parameter_info = ['x','y','laplacian','size','direction','hessian']
    temptable = []
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
        extended = 0
        HessianThresh = 400
        nOctaves = 3
        nOctaveLayers = 4

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        (kpts,descriptors)=cv.ExtractSURF(cv.fromarray(im), None, cv.CreateMemStorage(), (extended, HessianThresh, nOctaves, nOctaveLayers)) #calculating descriptor
        
        #initalizing rows for the table
        for i in range(0,len(descriptors)):
            parameters=[kpts[i][0][0],kpts[i][0][1],kpts[i][1],kpts[i][2],kpts[i][3],kpts[i][4]]
            self.setRow(uri, idnumber, descriptors[i], parameters)

    
class SURFc(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_surfc.h5'
    name = 'SURFc'
    description = """Speeded Up Robust Features also know as SURF"""
    length = 128 
    parameter_info = ['x','y','response','size','angle','octave']
    temptable = []
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing
        extended = 0
        HessianThresh = 400
        nOctaves = 3
        nOctaveLayers = 4

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]
        else:
            scale=imagesize[0]
        
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        descriptor_extractor = cv2.DescriptorExtractor_create("SURF")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)

class FREAKc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_freakc.h5'
    name = 'FREAKc'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    parameter_info = ['x','y','response','size','angle','octave']
    

        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/10
        else:
            scale=imagesize[0]/10
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("FREAK")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            self.setRow(uri, idnumber, [None], [None])
        
        #initalizing rows for the table
        else:
            for i in range(0,len(descriptors)):
                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
                self.setRow(uri, idnumber, descriptors[i], parameter)
            