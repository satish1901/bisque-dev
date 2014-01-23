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
    name = 'WNDCharmBase'
    description = """This is the WNDCharm Base Class. Is not a feature in the feature server."""
    length = 0
    
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        image_uri = resource['image']
        feature_info=feature_list[self.name]
        tranforms=feature_info[1:3]
        #adds the correct delimiter
        if image_uri.count('?')<1:
            image_uri+='?'
        else:
            image_uri+='&'
        
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
                    args.append('format=tiff') #forces the tiff to output in a format cv2.imread can handle
                else:
                    args.append('transform='+t)
        args.append('format=tiff') #return tiff format
        image_uri += '&'.join(args)
        
        log.debug('WNDCharm uri: %s'% image_uri)
        Im = Feature.ImageImport(image_uri,'tiff') #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_UNCHANGED) #CV_LOAD_IMAGE_UNCHANGED CV_LOAD_IMAGE_ANYDEPTH
        # extract the feature keypoints and descriptor
        if im==None:
            raise ValueError('Format was not supported')
            #abort(415, 'Format was not supported')

        im = np.asarray(im)        
        extractWNDCharmFeature = feature_info[0]
        descriptor = extractWNDCharmFeature(im)
        del Im 
 
            
        #initalizing rows for the table
        return [descriptor]
