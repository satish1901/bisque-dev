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
from tg import request
from PIL import Image, ImageDraw
from bq import image_service
from bq.core import identity
from bqapi.comm import BQServer
from bq.util import http
from lxml import etree
from webob.request import Request, environ_from_url
from bq.features.controllers.exceptions import FeatureServiceError, InvalidResourceError, FeatureExtractionError
from .var import FEATURES_STORAGE_FILE_DIR,FEATURES_TABLES_FILE_DIR,FEATURES_TEMP_IMAGE_DIR



from bq.data_service.controllers.resource_query import RESOURCE_READ
from bq.data_service.controllers.resource_query import resource_permission
from bq.data_service.model import Taggable, DBSession
log = logging.getLogger("bq.features")



def request_internally(url):
    """
        Makes a request on the give url internally. If it finds url without errors the content
        of the body is returned else None is returned
        
        @param url - the url that is requested internally
        
        @return body - body of the response
    """
    # 
    from bq.config.middleware import bisque_app
    req = Request.blank('/')
    req.environ.update(request.environ)
    req.environ.update(environ_from_url(url))
    log.debug("Mex %s" % identity.mex_authorization_token())  
    req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
    req.headers['Accept'] = 'text/xml'        
    log.debug("begin routing internally %s" % url)
    resp = req.get_response(bisque_app)
    log.debug("end routing internally: status %s" % resp.status_int)
    if resp.status_int < 400:
        return resp.body
    else:
        log.debug("User is not authorized to read resource internally: %s",url)
        return None


def request_externally(url):
    """
        Makes a request on the give url externally. If it finds url without errors the content
        of the body is returned else None is returned
        
        @param url - the url that is requested externally
        
        @return body - body of the response
    """
    req = Request.blank(url)
    req.headers['Authorization'] = "Mex %s" % identity.mex_authorization_token()
    req.headers['Accept'] = 'text/xml'
    log.debug("begin routing externally: %s" % url)
    resp = http.send(req)
    log.debug("end routing externally: status %s" % resp.status_int)
    if resp.status_int < 400:
        return resp.body
    else:
        log.debug("User is not authorized to read resource: %s" % url)
        return None


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

    #there are currently only 3 resources in the feature server
    #image, mask, gobject
    #required resource type(s)
    resource = ['image']
    
    #additional resources type(s)
    additional_resource = None

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
    
    #will turn off the feature in the feature service if set to true
    disabled = False
    
    #Confidence stands for the amount of a features correctness based on the unittest comparison.
    #good - feature compares exactly with the linux and windows binaries
    #fair - feature is within %5 mismatch of either linux and windows binaries
    #poor - feature is greater than %5 mismatch of either linux and windows binaries
    #untested - feature has not been tested in the unittest comparison
    confidence = 'untested'

    def __init__ (self):
        self.path = os.path.join(FEATURES_TABLES_FILE_DIR, self.name)

    def localfile(self, hash):
        """
            returns the path to the table given the hash
        """
        return os.path.join(self.path, hash[:self.hash]+'.h5')

    @staticmethod
    def hash_resource(feature_resource):
        """
            returns a hash given all the uris
        """
        query = []
        if feature_resource.image: query.append('image=%s' % feature_resource.image)
        if feature_resource.mask: query.append('mask=%s' % feature_resource.mask)
        if feature_resource.gobject: query.append('gobject=%s' % feature_resource.gobject)
        query = '&'.join(query)
        resource_hash = uuid.uuid5(uuid.NAMESPACE_URL, query.encode('ascii'))
        resource_hash = resource_hash.hex
        return resource_hash

    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length))
        return {
            'idnumber': tables.StringCol(32, pos=1),
            'feature' : tables.Col.from_atom(featureAtom, pos=2)
        }
        
    def workdir_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length))
        return {
            'image'   : tables.StringCol(2000, pos=1),
            'mask'    : tables.StringCol(2000, pos=2),
            'gobject' : tables.StringCol(2000, pos=3),
            'feature' : tables.Col.from_atom(featureAtom, pos=4)
        }

    def calculate(self, resource):
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
                urlparse.parse_qsl(o.query)
                query_arg = urlparse.parse_qsl(o.query, keep_blank_values=True)
                
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
                # Try to route externally
                response = request_internally(self.uri)
                if response is None:
                    self.path = None
                else:
                    f.write(response)
                
                # Try to route externally
                response = request_externally(self.uri)
                if response is None:
                    self.path = None
                    log.debug("User is not authorized to read resource externally: %s",self.uri)
                    raise Exception("Error Code: %s User is not authorized to read resource externally: %s",(response.status_int,self.uri))
                else:
                    f.write(response)
                    
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

def check_access(ident, action=RESOURCE_READ):
    """
        Checks for element in the database. If found returns True else returns 
        False
        
        @param ident  - resource uniq or resource id
        @param action - resource action on the database (default: RESOURCE_READ)
        
        @return bool
    """
    query = DBSession.query(Taggable).filter_by (resource_uniq = ident)
    resource = resource_permission (query, action=action).first()
    log.debug('Result from the database: %s'%resource)
    if resource is None:
        return False
    return True

                
#needs to be replaced with a HEAD instead of using a GET
def mex_validation(resource):
    """
    Checks the mex of the resource to see if the user has access to all the resources
    """
    resource_list = [i for i in resource if i is not ''] #remove all none resoures
    for r in resource_list:
        log.debug("resource: %s"%r)
        try:
            #route through the database
            o = urlparse.urlsplit(r)
            url_path = o.path.split('/')
            log.debug('url_path :%s'% url_path)
            if url_path[0] == 'data_service' or url_path[0] == 'image_service': #check for data_service
                ident = url_path[-1]
                if check_access(ident) is True:
                    continue #check next resource
                #else try another route
            
            # Try to route internally through bisque 
            if request_internally(r) is not None:
                continue #check next resource

            # Try to route externally
            if request_externally(r) is None:
                return False #after checking every path resource was not found
            
        except:
            log.exception ("While retrieving URL %s" %str(resource))
            return False
    return True

def fetch_resource(uri):
    log.debug("resource: %s"%uri)
    try:
        # Try to route internally through bisque 
        response = request_internally(uri)
        if response is not None:
            return response

        # Try to route externally
        response = request_externally(uri)
        if response is not None:
            return response
        
    except:
        raise FeatureServiceError(404, 'Url: %s, Resource was not found' % uri)


###############################################################
# Features Misc.
###############################################################

def gobject2mask(uri, im):
    """
        Converts a gobject with a shape into
        a binary mask
        
        @param: uri - gobject uris
        @param: im - image matrix
        
        @return: mask
    """
    valid_gobject = set(['polygon','circle','square','ellipse','rectangle','gobject'])
    
    mask = np.zeros([])
    #add view deep to retrieve vertices
    
    uri_full = BQServer().prepare_url(uri, view='full')
    
    response = fetch_resource(uri_full)
    #need to check if value xml
    try:
        xml = etree.fromstring(response)
    except etree.XMLSyntaxError:
        raise FeatureExtractionError(None, 415, 'Url: %s, was not xml for gobject' % uri)
    
    #need to check if its a valid gobject
    if xml.tag not in valid_gobject:
        raise FeatureExtractionError(None, 415, 'Url: %s, Gobject tag: %s is not a valid gobject to make a mask' % (uri,xml.tag))
    
    if xml.tag in set(['gobject']):
        tag = xml.attrib.get('type')
        if tag is None:
            raise FeatureExtractionError(None, 415, 'Url: %s, Not an except gobject' % (uri,xml.tag))
    else:
        tag = xml.tag
        
    col = im.shape[0]
    row = im.shape[1]
    img = Image.new('L', (row, col), 0)
        
    if tag in set(['polygon']):
        contour = []
        for vertex in xml.xpath('vertex'):
            x = vertex.attrib.get('x')
            y = vertex.attrib.get('y')
            if x is None or y is None:
                raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have x or y coordinate' % uri)
            contour.append((int(float(x)),int(float(y))))
        if len(contour)<2:
            raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have enough vertices' % uri)
#        import pdb
#        pdb.set_trace()
        ImageDraw.Draw(img).polygon(contour, outline=255, fill=255)
        mask = np.array(img)
    
    if tag in set(['square']):
        #takes only the first 2 points
        contour = []
        for vertex in xml.xpath('vertex'):
            x = vertex.attrib.get('x')
            y = vertex.attrib.get('y')
            if x is None or y is None:
                raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have x or y coordinate' % uri)
            contour.append((int(float(x)),int(float(y))))
        if len(contour)<2:
            raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have enough vertices' % uri)

        (x1,y1)= contour[0]
        (x2,y2)= contour[1]
        py = np.min([y1, y2])
        px = np.min([x1, x2])
        side = np.abs(x1-x2)
        contour = [(px,py),(px,py+side),(px+side,py+side),(px+side, py)]
        ImageDraw.Draw(img).polygon(contour, outline=255, fill=255)
        mask = np.array(img)
        
    
    if tag in set(['rectangle']):
        #takes only the first 2 points
        contour = []
        for vertex in xml.xpath('vertex'):
            x = vertex.attrib.get('x')
            y = vertex.attrib.get('y')
            if x is None or y is None:
                raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have x or y coordinate' % uri)
            contour.append((int(float(x)),int(float(y))))
        if len(contour)<2:
            raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have enough vertices' % uri)

        (x1,y1)= contour[0]
        (x2,y2)= contour[1]
        y_min = np.min([y1, y2])
        x_min = np.min([x1, x2])
        y_max = np.max([y1, y2])
        x_max = np.max([x1, x2])
        contour = [(x_min, y_min), (x_min, y_max), (x_max, y_max), (x_max, y_min)]
        ImageDraw.Draw(img).polygon(contour, outline=255, fill=255)
        mask = np.array(img)
        
        
    if tag in set(['circle','ellipse']): #ellipse isnt supported really, its just a circle also
        #takes only the first 2 points
        contour = []
        for vertex in xml.xpath('vertex'):
            x = vertex.attrib.get('x')
            y = vertex.attrib.get('y')
            if x is None or y is None:
                raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have x or y coordinate' % uri)
            contour.append((int(float(x)),int(float(y))))
        if len(contour)<2:
            raise FeatureExtractionError(None, 415, 'Url: %s, gobject does not have enough vertices' % uri)

        (x1,y1) = contour[0]
        (x2,y2) = contour[1]
        
        r = np.sqrt(np.square(int(float(x2))-int(float(x1)))+
                    np.square(int(float(y2))-int(float(y1))))
        bbox = (int(float(x1))-r, int(float(y1))-r, int(float(x1))+r, int(float(y1))+r)
        ImageDraw.Draw(img).ellipse(bbox, outline=255, fill=255)
        mask = np.array(img)
    return mask


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
