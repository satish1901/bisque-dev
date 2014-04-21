# -*- mode: python -*-
""" Base Feature library
"""


import os
import tables
import bq
import random
import numpy as np
import logging
import string
import uuid
import urllib2
import shutil
import socket
import tempfile

from tg import abort
from webob import Request

from bq import image_service
from bq.image_service.controllers.locks import Locks
from bq.core import identity
from bq.util import http
#from bq.features.controllers.service import FeatureServiceError
from .var import FEATURES_STORAGE_FILE_DIR,FEATURES_TABLES_FILE_DIR,FEATURES_TEMP_IMAGE_DIR
#from bq.features.controllers.service import FeatureServiceError
log = logging.getLogger("bq.features")

#wrapper for the calculator function so the output
#is in the correct format to be easily placed in the tables
def calc_wrapper(func):
    def calc(self,kw):
        id = self.returnhash(**kw)

        results = func(self,**kw) #runs calculation
        column_count = len(self.Columns.columns)-1 #finds length of columns to determin how to parse
        if column_count == 1:
            results=tuple([results])

        rows=[]
        for i in range(len(results[0])): #iterating though rows returned

            if self.cache: #check for cache to see how to build the table
                row = tuple([id])
            else:
                for input in self.resource: 
                    row +=  tuple([kw[input]])
                row += tuple([self.name])

            #allows for varying column length
            for j in range(column_count): #iterating through columns returned
                row += tuple([results[j][i]])
            rows.append(row)
        return rows

    return calc

###############################################################
# Feature Object
###############################################################
class BaseFeature(object):
    """
        Initalizes Feature table and calculates descriptor to be
        placed into the HDF5 table
    """
    #initalize feature attributes

    #feature name (the feature service will refer to the feature by this name)
    name = 'Feature'

    #A short descriptio of the feature
    description = """Feature vector is the generic feature object. If this description is
    appearing in the description for this feature no description has been provided for this
    feature"""

    version = '0.0.0'

    #parent class tag
    child_feature = []

    #Limitations that may be imposed on the feature
    limitations = """This feature has no limitation"""

    #required resource type(s)
    resource = ['image']

    #parameters that will be shown on the output
    parameter = []

    #length of the feature
    length = 0

    #format the features are stored in
    feature_format = "float32"

    #option for feature not to be stored to any table
    cache = True

    #option of turing on the index
    index = True

    #Number of characters to use from the hash to name
    #the tables
    hash = 2

    #list of feature catagories. ex. color,texture...
    type = []
    
    #Confidence stands for the amount of a features correctness based on the unittest comparison.
    #good - feature compares exactly with the linux and windows binaries
    #fair - feature is within %5 mismatch of either linux and windows binaries
    #poor - feature is greater than %5 mismatch of either linux and windows binaries
    #untested - feature has not been tested in the unittest comparison
    confidence = 'untested'

    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)
        self.columns()

    def localfile(self,hash):
        """
            returns the path to the table given the hash
        """
        return os.path.join( self.path, hash[:self.hash]+'.h5')


    def returnhash(self, **kw):
        """
            returns a hash given all the uris
        """
        uri = ''
        for r in self.resource:
            uri += str(kw[r]) #combines all the uris together to form the hash
        uri_hash = uuid.uuid5(uuid.NAMESPACE_URL, uri)
        uri_hash = uri_hash.hex
        return uri_hash


    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)

        self.Columns = Columns


    def createtable(self,filename):
        """
            Initializes the Feature table returns the column class
        """

        #creating table
        with Locks(None, filename):
            with tables.openFile(filename,'a', title=self.name)  as h5file:
                table = h5file.createTable('/', 'values', self.Columns, expectedrows=1000000000)

                if self.index: #turns on the index
                    table.cols.idnumber.removeIndex()
                    table.cols.idnumber.createIndex()

                table.flush()
        return


    def outputTable(self,filename):
        """
        Output table for hdf output requests and uncached features
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Col.from_atom(featureAtom, pos=3)

        with Locks(None, filename): 
            with tables.openFile(filename,'a', title=self.name) as h5file:
                outtable = h5file.createTable('/', 'values', Columns, expectedrows=1000000000)
                outtable.flush()
                
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            error_code    = tables.Int32Col(pos=3)
            error_message = tables.StringCol(200,pos=4)

        with Locks(None, filename): 
            with tables.openFile(filename,'a', title=self.name) as h5file:
                outtable = h5file.createTable('/', 'errors', Columns, expectedrows=1000000000)
                outtable.flush()

        return

    @calc_wrapper
    def calculate(self, **resource):
        """
            place holder for feature calculations
        """
        return [0]



###############################################################
# Image Import
###############################################################
class ImageImport:
    """ 
        request an image from the bisque system or from a 3rd party 
        system
    """
    
    def __enter__(self):
        return self
    
    def __init__(self, uri):
        self.uri = uri
        self.tmp_flag = 0 #set a flag to if a temp file was made
        from bq.config.middleware import bisque_app

        if 'image_service' in uri:
            #finds image resource though local image service
            self.uri=uri
            try:
                self.path = image_service.local_file(uri)
                log.debug("path: %s"% self.path)
                if not self.path:
                    log.debug('Not found in image_service internally: %s'%uri)
                else:
                    return 
            except Exception: #Resulting from a 403 in image service, needs to be handled better
                log.debug('Not found in image_service internally: %s'%uri)

        with tempfile.NamedTemporaryFile(dir=FEATURES_TEMP_IMAGE_DIR, prefix='image', delete=False) as f:
            self.tmp_flag = 1 #tmp file is create, set flag
            self.path = f.name
            try:
                req = Request.blank(uri)
                req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
                req.headers['Accept'] = 'text/xml'
                log.debug("begin routing internally %s" % uri)
                response = req.get_response(bisque_app)
                log.debug("end routing internally: status %s" % response.status_int)
                if response.status_int == 200:
                    f.write(response.body)
                    return 
                if response.status_int in set([401,403]):
                    log.debug("User is not authorized to read resource internally: %s",uri)
                    #raise ValueError('User is not authorized to read resource internally: %s') 

                # Try to route externally
                req = Request.blank(uri)
                req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
                req.headers['Accept'] = 'text/xml'
                log.debug("begin routing externally: %s" % uri)
                response = http.send(req)
                log.debug("end routing externally: status %s" % response.status_int)
                if response.status_int == 200:
                    f.write(response.body)
                    return 
                else:
                    log.debug("User is not authorized to read resource externally: %s",uri)
            except:
                log.exception ("While retrieving URL %s" % uri)


    def __str__(self):
        return self.path
        
    def path(self):
        return self.path
    
    def __exit__(self,type,value,traceback):
        if self.tmp_flag:
            try:
                os.remove(self.path)
            except OSError:
                pass        


###############################################################
# Mex Validation
###############################################################

#needs to be replaced with a HEAD instead of using a GET
def mex_validation(**resource):
    """
    Checks the mex of the resource to see if the user has access to all the resources
    """
    from bq.config.middleware import bisque_app
    for r in resource.keys():
        log.debug("resource: %s"% resource[r])

        try:
            # Try to route internally
            req = Request.blank(resource[r])
            req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
            log.debug("Mex %s" % identity.mex_authorization_token())
            req.headers['Accept'] = 'text/xml'
            log.debug("begin routing internally %s" % resource[r])
            resp = req.get_response(bisque_app)
            log.debug("end routing internally: status %s" % resp.status_int)
            if resp.status_int == 200:
                continue
            elif resp.status_int in set([401,403]):
                log.debug("User is not authorized to read resource internally: %s",resource[r])

            # Try to route externally
            req = Request.blank(resource[r])
            req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
            req.headers['Accept'] = 'text/xml'
            log.debug("begin routing externally: %s" % resource[r])
            resp = http.send(req)
            log.debug("end routing externally: status %s" % resp.status_int)
            if resp.status_int == 200:
                continue
            else:
                log.debug("User is not authorized to read resource: %s",resource[r])
                return False
        except:
            log.exception ("While retrieving URL %s" % resource[r])
            return False

    return True

###############################################################
# Temp Import
###############################################################

#None of the features use this 
#
#class TmpFiles():
#    """
#        Stores temporary files produced by features extractors
#    """
#    def __enter__(self):
#        pass
#
#    def __exit__(self,type,value,traceback):
#        try:
#            os.remove(self.path)
#        except OSError:
#            pass
#
#    def __init__(self, ''):
#        s = "".join([random.choice(string.ascii_lowercase + string.digits) for x in xrange(10)])
#        file = 'temp'+ str(s)+'.'+filetype
#        self.path = os.path.join( FEATURES_TEMP_IMAGE_DIR, file)
#        
#    def open(self):
#        self.f = open(self.path)
#        self.status = 'Open'
#        return self.f
#    
#    def close(self):
#        if self.status == 'Open':
#            self.f.close()
#            del self.f
#            status = 'Closed'
#    
#    def returnpath(self):
#        return self.path
#    
#    def returnstatus(self): 
#        self.status 
#    
#    def __del__(self):
#        """ When the ImageImport object is deleted the image path is removed for the temp dir """
#        try:
#            os.remove(self.path)
#        except OSError:
#            pass

###############################################################
# XML Import
###############################################################

def xml_import(uri):
    """ Import XML from another service and returns the tree """
    from lxml import etree
    import urllib, urllib2, cookielib
    uri = uri
    from bq.config.middleware import bisque_app
    try: 
        # Try to route internally
        req = Request.blank(uri)
        req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
        req.headers['Accept'] = 'text/xml'
        log.debug("begin routing internally %s" % uri)
        response = req.get_response(bisque_app)
        log.debug("end routing internally: status %s" % response.status_int)
        if response.status_int == 200:
            try:
                return etree.fromstring(response.body) 
            except: #find specific error
                log.exception ("Was not proper XML format: URL %s" % uri)
                return

    except:
        log.exception ("While retrieving URL %s" % uri)
        return


###############################################################
# Features Misc.
###############################################################

def rgb2gray(im):
    """
        @im - numpy matrix of mxnx3
        @return - 0.299 Ch1 + 0.587 Ch2 + 0.114 Ch3 (mxn numpy matrix)
    """
    im = np.asarray(im)
    assert len(im.shape) == 3, TypeError('Must be a mxnx3 matrix')
    assert im.shape[2] == 3, TypeError('Must be a mxnx3 matrix')
    return np.dot(im[...,:3], [0.299, 0.587, 0.144])


def gray2rgb(im):
    """
        @im - numpy matrix of mxn
        @return - [ch1,ch1,ch1] (mxnx3 numpy matrix)
    """
    im = np.asarray(im)
    assert len(im.shape) == 2, TypeError('Must be a mxn matrix')
    return np.concatenate([im[..., np.newaxis] for i in range(3)], axis=2)
