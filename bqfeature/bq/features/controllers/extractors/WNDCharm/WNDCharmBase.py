from PyWNDCharmFeatureList import feature_list
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort
import numpy as np
import logging
from bq.features.controllers.Feature import BaseFeature, ImageImport, rgb2gray #import base class
from PIL import Image

log = logging.getLogger("bq.features")


def except_image_only(resource):
    if resource.image is None:
        raise FeatureExtractionError(400, 'Image resource is required')
    if resource.mask:
        raise FeatureExtractionError(400, 'Mask resource is not accepted')
    if resource.gobject:
        raise FeatureExtractionError(400, 'Gobject resource is not accepted')

class WNDCharm(BaseFeature): #base WNDCharm feature class
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'WNDCharmBase'
    description = """This is the WNDCharm Base Class. Is not a feature in the feature server."""
    
    def calculate(self, resource):
        """ Append descriptors to h5 table """
        except_image_only(resource)
        image_uri = resource.image
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
                else:
                    args.append('transform='+t)
        args.append('format=tiff') #return tiff format
        image_uri += '&'.join(args)
        
        log.debug('WNDCharm uri: %s'% image_uri)
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            
            # extract the feature keypoints and descriptor
            im = np.asarray(im)        
            extractWNDCharmFeature = feature_info[0]
            descriptor = extractWNDCharmFeature(im)
 
            
        #initalizing rows for the table
        return descriptor