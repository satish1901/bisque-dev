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
import urlparse
import urllib
from tg import abort
from PIL import Image
from bq import image_service
from bq.core import identity
from bq.util import http
from webob.request import Request, environ_from_url
from bq.features.controllers.exceptions import FeatureServiceError, InvalidResourceError
from .var import FEATURES_STORAGE_FILE_DIR,FEATURES_TABLES_FILE_DIR,FEATURES_TEMP_IMAGE_DIR
log = logging.getLogger("bq.features")

#wrapper for the calculator function so the output
#is in the correct format to be easily placed in the tables

def calc_wrapper(func):
    def calc(self,kw):
        id = self.returnhash(**kw)
        
        results = func(self,**kw) #runs calculation
        log.debug('Successfully calculated feature!')
        column_count = len(self.cached_columns().columns)-1 #finds length of columns to determin how to parse
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

    def __init__ ( self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)

    def localfile( self, hash):
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

    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type( self.feature_format, shape=( self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
        return Columns
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type( self.feature_format, shape=( self.length))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Col.from_atom(featureAtom, pos=3)
        return Columns


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
    
    def __init__(self, uri, try_tiff = True):
        self.uri = uri
        self.path = None
        self.istiff = False
        self.tmp_flag = 0 #set a flag to if a temp file was made
        from bq.config.middleware import bisque_app
        from tg import request
        
        o = urlparse.urlsplit(self.uri)
        
        if 'image_service' in o.path:
            #finds image resource though local image service
            
            if try_tiff == True:
                urlparse.parse_qsl( o.query)
                query_arg = urlparse.parse_qsl( o.query, keep_blank_values=True)
                
                query_arg.append(('format','OME-BigTIFF'))
                query_pairs = query_arg
                
                log.debug( 'query_arg %s'% query_pairs)
                query_str = urllib.urlencode( query_pairs)
                self.istiff = True
                self.uri = urlparse.urlunsplit((o.scheme,o.netloc,o.path,query_str,o.fragment))
            
            try:
                self.path = image_service.local_file(self.uri)
                log.debug("Image Service path: %s"% self.path)
                if not self.path:
                    log.debug('Not found in image_service internally: %s'%self.uri)
                else:
                    return
            except Exception: #Resulting from a 403 in image service, needs to be handled better
                log.debug('Not found in image_service internally: %s'%self.uri)

        with tempfile.NamedTemporaryFile(dir=FEATURES_TEMP_IMAGE_DIR, prefix='image', delete=False) as f:
            self.tmp_flag = 1 #tmp file is create, set flag
            self.path = f.name
            try:
                req = Request.blank('/')
                req.environ.update(request.environ)
                req.environ.update(environ_from_url(self.uri))
                log.debug("Mex %s" % identity.mex_authorization_token())                  
                req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
                req.headers['Accept'] = 'text/xml'
                log.debug("begin routing internally %s" % self.uri)
                response = req.get_response(bisque_app)
                log.debug("end routing internally: status %s" % response.status_int)
                if response.status_int == 200:
                    f.write(response.body)
                    return 
                if response.status_int in set([401,403]):
                    self.path = None
                    log.debug("User is not authorized to read resource internally: %s",self.uri)
                    #raise ValueError('User is not authorized to read resource internally: %s') 

                # Try to route externally
                req = Request.blank(self.uri)
                req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
                req.headers['Accept'] = 'text/xml'
                log.debug("begin routing externally: %s" % self.uri)
                response = http.send(req)
                log.debug("end routing externally: status %s" % response.status_int)
                #if response.status_int == 200:
                if response.status_int < 400:
                    f.write(response.body)
                    return 
                else:
                    self.path = None
                    log.debug("User is not authorized to read resource externally: %s",self.uri)
                    raise Exception("Error Code: %s User is not authorized to read resource externally: %s",(response.status_int,self.uri))

            except:
                self.path = None
                log.exception ("While retrieving URL %s" % uri)


    def from_tiff2D_to_numpy(self):
        """
            Imports a 2D Tiff as numpy array
        """
        try:
            from libtiff import TIFF
        except ImportError:
            log.exception("Failed to import PyLibTiff.")
            try:
                return np.array(Image.open(str(self.path))) #try to return something, pil doesnt support bigtiff
            except IOError:
                log.exception("Not a tiff file!")
                raise InvalidResourceError(415, 'Unsupported media type')            
            

        if self.istiff and self.path:
            try:
                tif = TIFF.open(self.path, mode = 'r')
#                    sample_per_pixel = tif.GetField('SAMPLESPERPIXEL')
#                    sample_format = tif.GetField('SAMPLEFORMAT')
#                    protometric_interpretation = tif.GetFile('PHOTOMETRICINTERPRETATION') #rgb
#                    image_length = tif.GetFile('IMAGELENGTH')
#                    image_width = tif.GetFile('IMAGEWIDTH')
#                    bits_per_sample = tif.GetFile('BITSPERSAMPLE')
#                    strip_length = tif.GetFile('STRIPLENGTH')
                image = []
                for im in tif.iter_images():
                    image.append(im)
                
                if len(image)>1:
                    image = np.dstack(image)
                else:
                    image = image[0]
#                im = tif.read_image()
                
                if len(image.shape) == 2:
                    return image
                elif len(image.shape) == 3:
                    if image.shape[2] == 3:
                        return image
                
                raise InvalidResourceError(415, 'Not a grayscale or RGB image')
                
            except IOError:
                log.exception("Not a tiff file!")
                raise InvalidResourceError(415, 'Unsupported media type')
                
        elif self.path:
            log.debug("format is not a tiff")
            try:
                return np.array(Image.open(str(self.path))) #try to return something, pil doesnt support bigtiff
            except IOError:
                log.exception("File type not supported!")
                raise InvalidResourceError(415, 'Unsupported media type')  
        else:
            log.exception("Cannot import image when no path found!")
            raise InvalidResourceError(404, "Cannot import image when no path found!")

    def __str__(self):
        return self.path
        
    def return_path(self):
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
def mex_validation( **resource):
    """
    Checks the mex of the resource to see if the user has access to all the resources
    """
    from bq.config.middleware import bisque_app
    
    for r in resource.keys():
        log.debug("resource: %s"% resource[r])

        try:
            # Try to route internally
            req = Request.blank('/')
            req.environ.update(request.environ)
            req.environ.update(environ_from_url(resource[r]))
            log.debug("Mex %s" % identity.mex_authorization_token())  
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
#            if resp.status_int == 200:
            if resp.status_int < 400:
                continue
            else:
                log.debug("User is not authorized to read resource: %s" % resource[r])
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
