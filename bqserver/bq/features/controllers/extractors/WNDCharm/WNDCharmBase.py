from PyWNDCharmFeatureList import feature_list
from PyWNDCharmFeatures import extractWNDCharmFeature
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort
import cv2
import numpy as np
import logging
log = logging.getLogger("bq.features")

class WNDCharm(Feature.Feature): #base WNDCharm feature class
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_WNDCharmBase'+'.h5'
    name = 'WNDCharmBase'
    description = """This is the WNDCharm Base Class. Is not a feature in the feature server."""
    length = 0
    
    
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SIFT h5 table """
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE) #CV_LOAD_IMAGE_UNCHANGED
        # extract the feature keypoints and descriptor
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        descriptor = extractWNDCharmFeature(im,self.name)
        del Im 
 
            
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
