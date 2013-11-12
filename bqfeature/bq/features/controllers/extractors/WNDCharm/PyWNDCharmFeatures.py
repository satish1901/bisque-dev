from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np
import sys
import inspect, os
import cv2

path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
path=path+'/lib' 
_WNDCharmFeatures = np.ctypeslib.load_library('_WNDCharmLib', path)

def WNDCharmFeatures( im, featuresize, extractor, transform1, transform2, is_color_transform):
    """
        Interface with the WNDCharm in C++
    """
    tmp = np.asarray(im)
    _WNDCharmFeatures.WNDCharmFeatures.argtypes = [
        np.ctypeslib.ndpointer(dtype = np.intc ),                                       
        c_int,
        c_int,
        c_char_p,
        c_char_p,
        c_char_p,
        np.ctypeslib.ndpointer(dtype = np.double),
        c_bool,
        ]
    _WNDCharmFeatures.WNDCharmFeatures.restype = c_void_p
    
    if len(tmp.shape)==3:
        (height,width,channel)=tmp.shape
        color = 1
    else:
        (height,width)=tmp.shape
        color = 0

    if is_color_transform==color:
        im = tmp.astype(np.intc)
        feature = np.empty([featuresize], dtype=np.double)
        _WNDCharmFeatures.WNDCharmFeatures( im, height, width, extractor, transform1, transform2, feature, color )
    else:
        print 'Warning: Incorrect Image Channels'
        feature = None
    return feature


def extractWNDCharmFeature(im, feature_name):
    """
        Given the feature name and the numpy image matrix ReturnWNDCharmFeature returns
        the feature from WNDCharm
    """
    from PyWNDCharmFeatureList import feature_list
    feature_info=feature_list[feature_name]
    if not feature_info:
        print "Not included in the feature list"
        return
    else:
        return WNDCharmFeatures(im,feature_info[3],feature_info[0],"Empty Transform","Empty Transform",feature_info[5])


if __name__ == '__main__':
    #test code
    image_path = 'test.jpg'
    im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
    #im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
    featuresize = 48
    extractor = "Comb Four Moments"
    transform1 = "Empty Transform"
    transform2 = "Empty Transform"
    color = 0 
    feature = extractWNDCharmFeature(im, 'Object_Feature')

