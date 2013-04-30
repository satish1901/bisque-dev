from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np
import sys
import inspect, os

#Notes
#    add masks to all
#    add documentation
#    fix the output of DCD
#    add the other features



path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_MPEG7FexLib = np.ctypeslib.load_library('lib\\_MPEG7FexLib_wrap', path)


def extractCSD(im, descSize=64):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    _MPEG7FexLib.computeCSD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeCSD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([1,descSize], dtype=np.double)
    _MPEG7FexLib.computeCSD(im, descSize, int(rows), int(cols), result)
    return result


def extractSCD(im, descSize=64):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    _MPEG7FexLib.computeSCD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeSCD.restype = c_void_p

    im = tmp.astype(np.intc)
    result = np.empty([1,descSize], dtype=np.double)
    _MPEG7FexLib.computeSCD(im, descSize, int(rows), int(cols), result)
    return result


def extractCLD(im, numYCoef=64, numCCoef = 28):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    _MPEG7FexLib.computeCLD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int, c_int,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeCLD.restype = c_void_p

    im = tmp.astype(np.intc)
    result = np.empty([1,(numYCoef+2*numCCoef)], dtype=np.double)
    _MPEG7FexLib.computeCLD(im, numYCoef, numCCoef, int(rows), int(cols), result)
    return result

# has a varying sized descriptor
# cannot be stored in hdf5 tables right now
#need to fix for a varying output work on it later
def extractDCD(im, normalize=True, variance=False, spatial=False, bin1=32, bin2=32, bin3=32):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    _MPEG7FexLib.computeDCD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ), c_bool, c_bool, c_bool,\
            c_int, c_int, c_int,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.intc)]
    _MPEG7FexLib.computeDCD.restype = c_void_p
    
    _MPEG7FexLib.returnDCD.argtypes = [ \
            c_void_p , c_bool, c_bool,
            np.ctypeslib.ndpointer(dtype = np.double),
            np.ctypeslib.ndpointer(dtype = np.intc)]
    
    _MPEG7FexLib.returnDCD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    
    ndc = np.empty([1,1], dtype=np.intc)
    dcd = _MPEG7FexLib.computeDCD(im, normalize, variance, spatial, bin1, bin2, bin3,int(rows), int(cols), ndc)
    

    if variance:
        dcdlength = 7 * ndc[0,0]
    else:
        dcdlength = 4 * ndc[0,0]
    
    results = np.empty([1,dcdlength], dtype=np.double)
    spatial_output = np.empty([1,1], dtype=np.intc)
    _MPEG7FexLib.returnDCD( dcd, variance, spatial, results, spatial_output)
    
    if spatial:
        return results, spatial_output
    else:
        return results

#need to be fix for grayscale input only
def extractHTD(im, layerFlag=True):
    """needs to be a grayscale image
    """
    tmp = np.asarray(im)
    cols, rows = tmp.shape
    _MPEG7FexLib.computeHTD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_bool,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeHTD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    if layerFlag:
        descSize = 62
    else:
        descSize = 32
        
    result = np.empty([1,descSize], dtype=np.double)
    _MPEG7FexLib.computeHTD(im, layerFlag, int(rows), int(cols), result)
    return result

def extractEHD(im):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    _MPEG7FexLib.computeEHD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeEHD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([1,80], dtype=np.double)
    _MPEG7FexLib.computeEHD(im, int(rows), int(cols), result)
    return result

def extractRSD(im, mask):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    mcols , mrows= mask.shape
    
    if mcols!=cols or mrows!=rows:
        raise "TypeError: The column and row vectors must be equal between"
        
    _MPEG7FexLib.computeRSD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FexLib.computeRSD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    result = np.empty([1,35], dtype=np.double)
    _MPEG7FexLib.computeRSD(im, mask, int(rows), int(cols), result)
    return result






