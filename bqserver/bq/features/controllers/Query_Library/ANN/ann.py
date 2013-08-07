#!/usr/bin/env python
# encoding: utf-8
"""libANN (Apriximate Nearest Neighbors library) python interface

Copyright (C) 2008, Robert Hetland

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
import ctypes
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np

import sys
import inspect, os

__all__ = ['kd_tree']

import os 


def _cstruct(*fields):
  class SpecificStruct(object):
    """C structure usable from python.
    
    Use a._pointer to pass the data as a pointer to structure in
    ctypes.
    
    """
    
    _dtype = np.dtype(list(fields))
    
    def __init__(self, **kw):
        self.__dict__['_array'] = np.zeros((),dtype=self._dtype)
        for k,v in kw.iteritems(): 
            self._array[k] = v

    def _getdata(self): return self._array.ctypes.data
    
    pointer = property(_getdata, doc='ctypes data pointer to struct')
    
    def __getattr__(self, field):
        return self._array[field]
    
    def __setattr__(self, field, value):
        self._array[field] = value
  return SpecificStruct


class kd_tree(object):
    """K-Dimensional tree class.
    
    This class creates a k-dimensional tree for fast lookup of nearest points.
    The closest points can be found using the varoious search methods.  See
    ANN documentation for more details.
    
    Methods
    -------
    kd_tree.search : Find k nearest points in kd_tree.
    kd_tree.priority_search : Find nearest points using priority method.
    kd_tree.fixed_radius_search : Find nearest points within a given radius.
    kd_tree.print_tree : Print tree to standard output.
    kd_tree.save_kd_tree : Saves tree to file
    
    Properties
    ----------
    kd_tree.dimension  : Dimension of space
    kd_tree.Npoints    : Number of points
    kd_tree.bucketsize : Bucket size
    kd_tree.split      : Split rule
    
    If calc_statistics is True, then these properties are also defined,
    
    kd_tree.n_lf       : Number of leaves (including trivial)
    kd_tree.n_tl       : Number of trivial leaves (no points)
    kd_tree.n_spl      : Number of splitting nodes
    kd_tree.depth      : Depth of tree
    kd_tree.sum_ar     : Sum of leaf aspect ratios
    kd_tree.avg_ar     : Average leaf aspect ratio
    
    Examples
    --------
    >>> import numpy as np
    >>> x = np.mgrid[-1:1:100j, -1:1:100j].reshape(2, -1).T
    >>> q = np.vstack((np.linspace(-1, 1, 23), np.zeros(23))).T
    >>> tree = ann.kd_tree(x)
    >>> idx, d2 = tree.search(q, k=4)
    >>> idx[]
    >>> q[15]
    array([ 0.36363636,  0.        ])
    >>> x[idx[15]]
    array([[ 0.33333333,  0.11111111],
           [ 0.33333333, -0.11111111],
           [ 0.55555556,  0.11111111],
           [ 0.55555556, -0.11111111]])
    
    """
    
    # Load in ANN library wrapper
    _ann = None
    pathprime = os.getcwd()
    path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) #find current dir of the file
    os.chdir(path) #need to change dir to get ANN.dll to work
    
    #for directory in path:
    try:
        _ann = np.ctypeslib.load_library('_libann_wrap', path)
    except:
        pass
    
    if _ann is None:
        raise '_libann_wrap not found in'
    
    os.chdir(pathprime)
    
    # Specify ANN wrapper functional APIs
    _ann.init_kd_tree.argtypes = [ \
            ndpointer(dtype='d', ndim=2, flags='CONTIGUOUS,ALIGNED'),\
            c_int, c_int, c_int, c_int, ctypes.POINTER(ctypes.POINTER(c_double)) ]
    
    _ann.init_kd_tree.restype = c_void_p

    _ann.import_kd_tree.argtypes = [c_void_p, ]

    _ann.import_kd_tree.restype = c_void_p
    
    _ann.kd_tree_print.argtypes = [c_void_p, ]
    
    _ann.kd_tree_get_stats.argtypes = [c_void_p, ]
    
    _ann.kd_tree_delete.argtypes = [c_void_p, ctypes.POINTER(ctypes.POINTER(c_double)), c_bool]
    
    _ann.kd_tree_search.argtypes = [ \
            c_void_p, \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED'),\
            c_int, c_int, c_double, \
            ndpointer(dtype='i', flags='CONTIGUOUS,ALIGNED'), \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED') ]
    
    _ann.kd_tree_priority_search.argtypes = [ \
            c_void_p, \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED'),\
            c_int, c_int, c_double, \
            ndpointer(dtype='i', flags='CONTIGUOUS,ALIGNED'), \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED') ]
    
    _ann.kd_tree_fixed_radius_search.argtypes = [ \
            c_void_p, \
            c_double, \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED'),\
            c_int, c_int, c_double, \
            ndpointer(dtype='i', flags='CONTIGUOUS,ALIGNED'), \
            ndpointer(dtype='d', flags='CONTIGUOUS,ALIGNED') ]
    
    _ann.kd_tree_save.argtypes = [ \
                                  c_void_p,\
                                  c_char_p, \
                                  c_bool ]
	
	

	
    def __init__(self, inputs , import_kd_tree = False, bucketsize = 1, split = 'SUGGEST', 
                 calc_statistics = True, copy = False, ):
        '''
        Initialize kd-tree object.
        
        Parameters
        ----------
        inputs : ndarray or str
            ndarray: A 2D array defining the points; shape=(points, dimensions)
            str: filename of a kd_tree to import
            
        import_kd_tree: boolean
            Flag to decide on whether to import or not. Default is False. If True 
            the inputs has to be a file name and only calc_statistics is taken into
            account for the parameters else if False the inputs has to be a ndarray.
            
        bucketsize : int
            size of smallest point groupings.  Default is 1.
            
        split : string
            'STD'       the optimized kd-splitting rule
            'MIDPT'     midpoint split
            'FAIR'      fair split
            'SL_MIDPT'  sliding midpoint splitting method
            'SL_FAIR'   sliding fair split method
            'SUGGEST'   the libANN authors' suggestion for best -- DEFAULT
            
        calc_statistics : boolean
            Flag to calculate statistics of the kd-tree.  Default is True.
            
        copy : boolean
            Flag to make a copy of the `points` array. Default is True. If
            False, the point array must be dtype='d' and order='C', otherwise
            a copy will be made anyways. Care must be taken when copy is
            False, as creating two seqential kd-tree instances with the same
            data can result in a segmentation fault, when the memory of the
            first instance is freed.
        
        Returns
        -------
        kd_tree : object

        '''
            
        # Make a copy of the points if requested or needed.
        # Ensure the data type is double, and byte order is 'C' in
        # order to be correctly passed to the libANN wrapper function.
        
        self.import_kd_tree=import_kd_tree
        if import_kd_tree == False:
            self.points = np.array(inputs, copy=copy, dtype='d', order='C')
            
            
            assert self.points.ndim == 2, \
                "Points must be a 2D array, with shape (nPoints, dimension)."
            
            split_dict = { 'STD'      : 0,
                           'MIDPT'    : 1,
                           'FAIR'     : 2,
                           'SL_MIDPT' : 3,
                           'SL_FAIR'  : 4,
                           'SUGGEST'  : 5 }
            
            assert split in split_dict.keys(), \
                """split must be one of:
                    'STD', 'MIDPT', 'FAIR', 'SL_MIDPT', 'SL_FAIR', 'SUGGEST'."""
            
            self.bucketsize = bucketsize
            self.split = split
            self.nPoints, self.dimension = inputs.shape
            pts_pointer = ctypes.POINTER(ctypes.POINTER(c_double))() #initalizing pointer
            self._kd_tree = self._ann.init_kd_tree(self.points,
                                                   self.nPoints,
                                                   self.dimension,
                                                   self.bucketsize,
                                                   split_dict[self.split],
                                                   pts_pointer)
            self.pts_pointer=pts_pointer
            
        elif import_kd_tree == True:
            self.pts_pointer=None
            try:
                self._kd_tree = self._ann.import_kd_tree(inputs)
                f = open(inputs,'r')
                f.readline()
                line = f.readline()
                data = line.split()
                self.nPoints = int(data[2])
                self.dimension = int(data[1])
        
            except IOError:
                raise 'input is neither a numpy array or a file name'
            except TypeError:
                raise 'input is neither a numpy array or a file name'
        else:
            print 'TypeError: Require Boolean Input'

          
        if calc_statistics:
            statistics = _cstruct(('n_lf', c_int),
                                  ('n_tl', c_int),
                                  ('n_spl', c_int),
                                  ('depth', c_int),
                                  ('sum_ar', c_double),
                                  ('avg_ar', c_double))()
            
            self._ann.kd_tree_get_stats(self._kd_tree, statistics.pointer)
            self.n_lf  = int(statistics.n_lf)
            self.n_tl  = int(statistics.n_tl)
            self.n_spl = int(statistics.n_spl)
            self.depth = int(statistics.depth)
            self.sum_ar = float(statistics.sum_ar)
            self.avg_ar = float(statistics.avg_ar)


    def search(self, qpoints, k=1, eps=0.0):
        """Find k nearest points in kd_tree.
        
        Parameters
        ----------
        qpoints : ndarray
            A 2D array defining the query points; shape=(points, dimensions)
        k : integer
            Number of nearest points to find
        eps : real
            The acceptable error in nearest point search.
            See libANN documentation for more information.
        
        Returns
        -------
        idx : ndarray
            An array of integers, such that `points`[idx] returns the closest
            points to `qpoints`; shape=(len(qpoints), k)
        d2 : ndarray
            An array of the squared distances between the `k` nearest `points`
            and the `qpoints`; shape=(len(qpoints), k)
        
        """
        if k>self.nPoints:
            k=self.nPoints
        qpoints = asarray(qpoints, dtype='d', order='C')
        assert qpoints.ndim == 2, \
            """Query points must be a 2D array, with shape
                (nPoints, dimension)."""
        
        nQPoints, dimension = qpoints.shape
        
        assert dimension == self.dimension, \
            """Query points must have the same dimension as points.
                [dimension = %d]""" \
                % self.dimension
        idx = empty((nQPoints, k), dtype='i', order='C')
        dist2 = empty((nQPoints, k), dtype='d', order='C')
        self._ann.kd_tree_search(self._kd_tree, qpoints, nQPoints, \
                                 k, eps, idx, dist2)
        return idx, dist2
    
    def priority_search(self, qpoints, k=1, eps=0.0):
        """Find k nearest points in kd_tree using priority search method.
        
        See the libANN documentation for more information on the different
        search methods.
        
        Parameters
        ----------
        qpoints : ndarray
            A 2D array defining the query points; shape=(points, dimensions)
        k : integer
            Number of nearest points to find
        eps : real
            The acceptable error in nearest point search.
            See libANN documentation for more information.
        
        Returns
        -------
        idx : ndarray
            An array of integers, such that `points`[idx] returns the closest
            points to `qpoints`; shape=(len(qpoints), k)
        d2 : ndarray
            An array of the squared distances between the `k` nearest `points`
            and the `qpoints`; shape=(len(qpoints), k)
        
        """
        if k>self.nPoints:
            k=self.nPoints
            
        qpoints = asarray(qpoints, dtype='d', order='C')
        assert qpoints.ndim == 2, \
            """Query points must be a 2D array, with shape
                (nPoints, dimension)."""
        
        nQPoints, dimension = qpoints.shape
        
        assert dimension == self.dimension, \
            """Query points must have the same dimension as points.
                [dimension = %d]""" \
                % self.dimension
        idx = empty((nQPoints, k), dtype='i', order='C')
        dist2 = empty((nQPoints, k), dtype='d', order='C')
        self._ann.kd_tree_priority_search(self._kd_tree, \
                                 qpoints, nQPoints, \
                                 k, eps, idx, dist2)
        return idx, dist2
    
    def fixed_radius_search(self, qpoints, radius, k=1, eps=0.0):
        """Find up to k nearest points within a fixed radius.
        
        See the libANN documentation for more information on the different
        search methods.
        
        Parameters
        ----------
        qpoints : ndarray
            A 2D array defining the query points; shape=(points, dimensions)
        radius : real
            The maximum radius within which to search for nearest points.
        k : integer
            Number of nearest points to find
        eps : real
            The acceptable error in nearest point search.
            See libANN documentation for more information.
        
        Returns
        -------
        idx : ndarray
            An array of integers, such that `points`[idx] returns the closest
            points to `qpoints`; shape=(len(qpoints), k).
            
            Values of -1 are used to fill the index matrix when there are
            fewer than k points found within `radius` of the query point.
        d2 : ndarray
            An array of the squared distances between the `k` nearest `points`
            and the `qpoints`; shape=(len(qpoints), k).
        
        """
        if k>self.nPoints:
            k=self.nPoints
            
        qpoints = asarray(qpoints, dtype='d', order='C')
        assert qpoints.ndim == 2, \
            """Query points must be a 2D array, with shape
                (nPoints, dimension)."""
        
        nQPoints, dimension = qpoints.shape
        
        assert dimension == self.dimension, \
            """Query points must have the same dimension as points.
                [dimension = %d]""" \
                % self.dimension
        idx = empty((nQPoints, k), dtype='i', order='C')
        dist2 = empty((nQPoints, k), dtype='d', order='C')
        self._ann.kd_tree_fixed_radius_search(\
                                 self._kd_tree, \
                                 radius, 
                                 qpoints, nQPoints, \
                                 k, eps, idx, dist2)
        return idx, dist2
    
    def print_tree(self):
        """Print the KD tree to standard output."""
        self._ann.kd_tree_print(self._kd_tree)
    
    def __del__(self):
        """delete KD tree"""  
        self._ann.kd_tree_delete(self._kd_tree, self.pts_pointer, self.import_kd_tree)
        del self.pts_pointer
        
    def save_kd_tree(self, filename):
        """Saves the kd tree object to a file
        Parameters
        ----------
        filename : String

        Output
        ------
        file
        """
        self._ann.kd_tree_save(self._kd_tree , filename, 1)
        



if __name__ == '__main__':
    import numpy as np
    from numpy import random
    
    dim = 3
    
    N = 100
    points = random.rand(N, dim)
    qpoints = random.rand(1, dim)
    tree = kd_tree(points)
##    idx, d2 = tree.search(qpoints, k=5)
##    print idx
##    print d2
##    tree.save_kd_tree('atree')

    ##tree.import_kd_tree('atree')
##    idx, d2 = tree.search(qpoints, k=5)
##    print idx
##    print d2
    
##    # tree.print_tree()
##    
##    Ni = 10
##    qpoints = random.rand(N, dim)
##    idx, d2 = tree.search(qpoints, k=5)
##    idx_pr, d2_pr = tree.priority_search(qpoints, k=5)
##    idx_fr, d2_fr = tree.fixed_radius_search(qpoints, 1.0, k=5)
##    
##    print 'SOME STATISTICS'
##    print 'Number of leaves : ', tree.n_lf
##    print 'Number of trivial leaves : ', tree.n_tl
##    print 'Average aspect ratio : ', tree.avg_ar
##    print ''
##    print 'SOME BASIC SANITY CHECKS'
##    print 'Search and priority search return the same indicies : ', \
##           np.all(idx == idx_pr)
##    print 'Search and fixed radius search return the same indicies : ', \
##     np.all(idx == idx_fr)


