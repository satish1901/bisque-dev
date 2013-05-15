from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np
import sys
import inspect, os

path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
path=path+'/lib' 
_WNDCharmFeatures = np.ctypeslib.load_library('_WNDCharmLib', path)


def WNDCharmFeatures(filename,featuresize, extractor, transform1, transform2):
    """
        Interface with the WNDCharm in C++
    """
    _WNDCharmFeatures.WNDCharmFeatures.argtypes = [ \
            c_char_p,\
            c_char_p,\
            c_char_p,\
            c_char_p,\
            np.ctypeslib.ndpointer(dtype = np.double),\
            ]
    _WNDCharmFeatures.WNDCharmFeatures.restype = c_void_p
    
    feature = np.empty([90], dtype=np.double)
    _WNDCharmFeatures.WNDCharmFeatures(filename, extractor, transform1, transform2, feature )
    
    return feature[:featuresize]


def ReturnWNDCharmFeature(feature_name,image_file):
    """
        Given the feature name and the image file name ReturnWNDCharmFeature returns
        the feature from WNDCharm
        All the features that this calculates are in the WNDCharmFeatureList.py file
    """
    from PyWNDCharmFeatureList import feature_list
    
    feature_info=feature_list[feature_name]
    if not feature_info:
        print "Not included in the feature list"
        return
    elif feature_info[4]==True:
        print "Require Grey Scale: Given Colored Image"
        return
    else:
        return WNDCharmFeatures(image_file,feature_info[3],feature_info[0],feature_info[1],feature_info[2])

