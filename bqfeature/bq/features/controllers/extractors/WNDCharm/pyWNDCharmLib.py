from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np
import sys
import os
import inspect

#Notes
#    add documentation
#    add the other features
#    have all the features return the correct type

path=os.path.dirname(__file__) #os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
#path=path+'/lib'
path = path+'../../../../src/extractors/WNDCharm/lib'
_WNDCharmLib = np.ctypeslib.load_library('_WNDCharmLib', path)

def extractChebyshevCoefficients(im):
    """
    Chebyshev Coefficients:
        input:
            size: mxn
            type: double
        output:
            size: array[32]
            type: int
    """
    descSize = 32
    tmp = np.asarray(im)
    height, width = tmp.shape

    #initalizing function arguments
    _WNDCharmLib.Chebyshev_Coefficients.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Chebyshev_Coefficients.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Chebyshev_Coefficients(im, int(height), int(width), result)
    return result


def extractChebyshevFourierCoefficients(im):
    """
    Chebyshev Fourier Coefficients:
        input:
            size: mxn
            type: double
        output;
            size: array[32]
            type: int

        target time: 3.84899997711
        array([ 242.,  160.,   68.,   25.,   12.,    6.,    4.,    0.,    2.,
          0.,    0.,    0.,    5.,    0.,    2.,    0.,    0.,    0.,
          1.,    0.,    0.,    0.,    0.,    1.,    0.,    0.,    0.,
          0.,    0.,    0.,    0.,    1.])
    """
    descSize = 32
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Chebyshev_Fourier_Coefficients.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Chebyshev_Fourier_Coefficients.restype = c_void_p

    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Chebyshev_Fourier_Coefficients(im, int(height), int(width), result)
    return result


def extractCombFirstFourMoments(im):
    """
    Comb First Four Moments:
        input:
            size: mxn
            type: double
        output;
            size: array[48]
            type: int
    """
    descSize = 48
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Comb_First_Four_Moments.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Comb_First_Four_Moments.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Comb_First_Four_Moments(im, int(height), int(width), result)
    return result

def extractGaborTextures(im):
    """
    target time: 72.92799
    broken right now
    needs to have imaginary number implemented correctly
    """
    descSize = 7
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Gabor_Textures.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Gabor_Textures.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Gabor_Textures(im,  int(height), int(width), result)
    return result

def extractHaralickTextures(im):
    """
    Haralick Textures:
        input:
            size: mxn
            type: double
        output;
            size: array[28]
            type: float   
    """
    descSize = 28
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Haralick_Textures.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Haralick_Textures.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Haralick_Textures(im, int(height), int(width), result)
    return result

def extractMultiscaleHistograms(im):
    """
    Multiscale Histograms
        input:
            size: mxn
            type: double
        output:
            size: array[24]
            type: double    
    """
    descSize = 24
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Multiscale_Histograms.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Multiscale_Histograms.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Multiscale_Histograms(im, int(height), int(width), result)
    return result

def extractRadonCoefficients(im):
    """
    Radon Coefficients
        input:
            size: mxn
            type: double
        output:
            size: array[12]
            type: double
    """
    descSize = 12
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Radon_Coefficients.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Radon_Coefficients.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Radon_Coefficients(im, int(height), int(width), result)
    return result

def extractTamuraTextures(im):
    """
    Tamura Testures:
        input:
            size: mxn
            type: double
        output;
            size: array[6]
            type: double          
    """
    descSize = 6
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Tamura_Textures.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Tamura_Textures.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Tamura_Textures(im, int(height), int(width), result)
    return result

def extractZernikeCoefficients(im):
    """
    Zernike Coefficients:
        input:
            size: mxn
            type: double
        output;
            size: array[72]
            type: double     
    """
    descSize = 72
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Zernike_Coefficients.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Zernike_Coefficients.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Zernike_Coefficients(im, int(height), int(width), result)
    return result

def extractPixelIntensityStatistics(im):
    """
    Pixel Intensity Statistics
        input:
            size: mxn
            type: double
        output;
            size: array[5]
            type: double    
    """
    descSize = 5
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Pixel_Intensity_Statistics.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Pixel_Intensity_Statistics.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Pixel_Intensity_Statistics(im, int(height), int(width), result)
    return result

def extractColorHistogram(im):
    """
    Color Histogram
        input:
            size: mxn
            type: double
        output;
            size: array[20]
            type: double  
    """
    descSize = 20
    tmp = np.asarray(im)
    height, width, channel = tmp.shape
    _WNDCharmLib.Color_Histogram.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Color_Histogram.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Color_Histogram(im, int(height), int(width), result)
    return result

def extractFractalFeatures(im):
    """
    Fractal Features
        input:
            size: mxn
            type: double
        output;
            size: array[20]
            type: double    
    """
    descSize = 20
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Fractal_Features.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Fractal_Features.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Fractal_Features(im, int(height), int(width), result)
    return result

def extractEdgeFeatures(im):
    """
    Fractal Features
        input:
            size: mxn
            type: double
        output;
            size: array[28]
            type: double   
    """
    descSize = 28
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Edge_Features.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Edge_Features.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Edge_Features(im, int(height), int(width), result)
    return result

def extractObjectFeatures(im):
    """
    Object Features
        input:
            size: mxn
            type: double
        output;
            size: array[34]
            type: double   
    """
    descSize = 34
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Object_Features.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Object_Features.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Object_Features(im, int(height), int(width), result)
    return result

def extractInverseObjectFeatures(im):
    """
    target time: 1.71200013161 (downsampling somewhere)
    """
    descSize = 34
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Inverse_Object_Features.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Inverse_Object_Features.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Inverse_Object_Features(im, int(height), int(width), result)
    return result

def extractGiniCoefficient(im):
    """
    Gini Coefficient
        input:
            size: mxn
            type: double
        output;
            size: array[1]
            type: double 
    """
    descSize = 1
    tmp = np.asarray(im)
    height, width = tmp.shape
    _WNDCharmLib.Gini_Coefficient.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _WNDCharmLib.Gini_Coefficient.restype = c_void_p
    
    im = tmp.astype(np.intc)
    result = np.empty([descSize], dtype=np.double)
    _WNDCharmLib.Gini_Coefficient(im, int(height), int(width), result)
    return result

if __name__ == '__main__':
    import cv2
    import time
    im=cv2.imread('test.jpg',cv2.CV_LOAD_IMAGE_GRAYSCALE) #CV_LOAD_IMAGE_GRAYSCALE CV_LOAD_IMAGE_COLOR
    start=time.time()
    feature=extractChebyshevFourierCoefficients(im)
    end=time.time()
    print 'time elapsed: %s'%str(end-start)  
    
