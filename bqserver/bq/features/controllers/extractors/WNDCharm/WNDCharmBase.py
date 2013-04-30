from PyWNDCharmFeatureList import feature_list
from PyWNDCharmFeatures import ReturnWNDCharmFeature
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort
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

        # extract the feature keypoints and descriptor
        I=Image.open(image_path)
        descriptor = ReturnWNDCharmFeature(self.name,image_path)
        del Im 
 
            
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptor)
