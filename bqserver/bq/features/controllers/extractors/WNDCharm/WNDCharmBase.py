from PyWNDCharmFeatureList import feature_list
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
    
    @Feature.wrapper
    def calculate(self, uri):
        """ Append descriptors to SIFT h5 table """
        
        feature_info=feature_list[self.name]
        tranforms=feature_info[1:3]
        #adds the correct delimiter
        if uri.count('?')<1:
            uri+='?'
        else:
            uri+='&'
        
        args = []
        if feature_info[4] == True:
            #force the image to 3 channels prefered rgb
            args.append('remap=display')
        else:
            #force the image to be 1 channel
            args.append('remap=grey')
            
        for t in tranforms:
            if t!="Empty Transform":
                if t=="Hue Transform":
                    args.append('depth=8,d')
                    args.append('transform=rgb2hsv') #converts rgb to hsv and then selects the hue channel
                    args.append('remap=1')
                    args.append('format=png') #forces the tiff to output in a format cv2.imread can handle
                else:
                    args.append('transform='+t)
        args.append('format=tiff') #return tiff format
        uri += '&'.join(args)
        
        log.debug('WNDCharm uri: %s'% uri)
        Im = Feature.ImageImport(uri,'tiff') #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_UNCHANGED) #CV_LOAD_IMAGE_UNCHANGED CV_LOAD_IMAGE_ANYDEPTH
        # extract the feature keypoints and descriptor
        im=np.asarray(im)
        log.debug('im: %s'% im)
        if not im.any():
            abort(415, 'Format was not supported')
        extractWNDCharmFeature = feature_info[0]
        descriptor = extractWNDCharmFeature(im)
        del Im 
 
            
        #initalizing rows for the table
        return [descriptor]
