import numpy as nm
import ctypes as ct
import inspect, os
import warnings

path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
_VRLLib_warp = nm.ctypeslib.load_library('_VRLLib_warp', path)

#EHD
_VRLLib_warp.extractEHD.argtypes = [nm.ctypeslib.ndpointer(dtype = nm.int),\
                                     ct.c_int, ct.c_int,\
                                    nm.ctypeslib.ndpointer(dtype = nm.double)]
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
        tmp = nm.asarray(im)
        rows, cols = tmp.shape
        im = tmp.astype(nm.intc)
        result = nm.empty([1,80], dtype=nm.double)
        _libehd.extractEHD(im, rows, cols, result)
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
        im = tmp.astype(np.intc)
        result = np.empty([1,48], dtype=np.double)
        _libhtd.extractHTD(im, rows, cols, result)
        return result
    except ValueError:
        warnings.warn("Requires a grayscale numpy image", UserWarning)
        return

