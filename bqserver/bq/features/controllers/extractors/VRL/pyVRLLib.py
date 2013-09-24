import numpy as np
import ctypes as ct
import inspect, os
import warnings

path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
path=path+'/lib'
_VRLLib_warp= np.ctypeslib.load_library('_VRLLib', path)

#EHD
_VRLLib_warp.extractEHD.argtypes = [np.ctypeslib.ndpointer(dtype = np.int),\
                                     ct.c_int, ct.c_int,\
                                    np.ctypeslib.ndpointer(dtype = np.double)]
_VRLLib_warp.extractEHD.restype  = ct.c_void_p

#HTD
_VRLLib_warp.extractHTD.argtypes = [np.ctypeslib.ndpointer(dtype = np.int),\
                                    np.ctypeslib.ndpointer(dtype = np.int),\
                                    np.ctypeslib.ndpointer(dtype = np.int),\
                                    ct.c_int, ct.c_int, ct.c_int,\
                                    np.ctypeslib.ndpointer(dtype = np.double)]
_VRLLib_warp.extractHTD.restype  = ct.c_void_p


def extractEHD(im):
    """
    Takes a numpy grayscale image matr ix and outputs an
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


def extractHTD(im, mask = None):
    """
    Takes a numpy grayscale image matrix and outputs an
    Edge Histogram Descriptor
    """
    tmp = np.asarray(im)


    try:
        rows, cols = tmp.shape
    except ValueError:
        warnings.warn("Requires a grayscale numpy image", UserWarning)
        return

    #if not mask
    if mask == None:
        mask= np.zeros([rows,cols])

    if tmp.shape!=mask.shape:
        raise "TypeError: The column and row vectors must be equal between"        


    mask_labels = np.unique(mask)
    label_count = len(mask_labels)

    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    mask_labels = mask_labels.astype(np.intc)
    result = np.empty([48*label_count], dtype=np.double)
    _VRLLib_warp.extractHTD(im, mask, mask_labels, label_count, rows, cols, result)
    result = np.reshape(result,(label_count,48))
    return result, mask_labels


if __name__=='__main__':
    from PIL import Image
    import time
    im = Image.open('test.jpg').convert("L")
    im = np.array(im)
    mask = Image.open('mask.gif')
    mask = np.array(mask)
    
    start=time.time()
    feature, label=extractHTD(im)#,mask=mask)
    end=time.time()
    print 'time elapsed: %s'%str(end-start)
    print feature
