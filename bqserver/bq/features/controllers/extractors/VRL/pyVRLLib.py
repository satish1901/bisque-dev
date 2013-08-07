import numpy as np
import ctypes as ct
import inspect, os
import warnings

path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
path=path+'/lib' 
_VRLLib_warp = np.ctypeslib.load_library('_VRLLib', path)

#EHD
_VRLLib_warp.extractEHD.argtypes = [np.ctypeslib.ndpointer(dtype = np.int),\
                                     ct.c_int, ct.c_int,\
                                    np.ctypeslib.ndpointer(dtype = np.double)]
_VRLLib_warp.extractEHD.restype  = ct.c_void_p

#HTD
_VRLLib_warp.extractHTD.argtypes = [np.ctypeslib.ndpointer(dtype = np.int),\
                                     ct.c_int, ct.c_int,\
                                    np.ctypeslib.ndpointer(dtype = np.double)]
_VRLLib_warp.extractHTD.restype  = ct.c_void_p


def extractEHD(im):
    """
    Takes a numpy grayscale image matrix and outputs an
    Edge Histogram Descriptor
    """
    try:
        tmp = np.asarray(im)
        rows, cols = tmp.shape
        im = tmp.astype(np.int)
        result = np.empty([80], dtype=np.double)
        _VRLLib_warp.extractEHD(im, rows, cols, result)
        return result
    except ValueError:
        warnings.warn("Requires a grayscale numpy image", UserWarning)
        return


def extractHTD(im):
    """
    Takes a numpy grayscale image matrix and outputs an
    Edge Histogram Descriptor
    """
    tmp = np.asarray(im)
    try:
        rows, cols = tmp.shape
        im = tmp.astype(np.int)
        result = np.empty([48], dtype=np.double)
        _VRLLib_warp.extractHTD(im, rows, cols, result)
        return result
    except ValueError:
        warnings.warn("Requires a grayscale numpy image", UserWarning)
        return

