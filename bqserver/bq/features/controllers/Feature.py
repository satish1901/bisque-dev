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

import bq
#from bq.image_service.controllers.service import local_file
from bq.image_service.controllers.locks import Locks
from pylons.controllers.util import abort
from bq import image_service

from .var import FEATURES_STORAGE_FILE_DIR,FEATURES_TABLES_FILE_DIR,FEATURES_TEMP_IMAGE_DIR

log = logging.getLogger("bq.features")


#Needed Changes
# Temp directory needs to be built properly
# maybe should use python api to import


############################################################### 
# Feature Object
############################################################### 
class Feature(object):
    """
        Initalizes Feature table and calculates descriptor to be
        placed into the HDF5 table
    """
    #initalize parameters
    name = 'Feature'
    file = 'features_feature.h5'
    ObjectType = 'Feature'
    description = """Feature vector is the generic feature object. If this description is 
    appearing in the description for this feature no description has been provided for this 
    feature"""
    limitations = """This feature has no limitation"""
    length = 0
    feature_format = "float32"
    parameter_format = "float32"
    parameter_info = []
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.file)
        self.temptable = []
    
    
    def initalizeTable(self):
        """
            Initializes the Feature table returns the column class
        """ 
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        if self.parameter_info:
            parameterAtom = tables.Atom.from_type(self.parameter_format, shape=(len(self.parameter_info)))
        class Columns(tables.IsDescription):
                idnumber  = tables.StringCol(32,pos=1)
                feature   = tables.Col.from_atom(featureAtom, pos=2)
                if self.parameter_info:
                    parameter = tables.Col.from_atom(parameterAtom, pos=3)
        self.Columns = Columns
        return
    
    def indexTable(self,table):
        """
            information for table to know what to index
        """
        table.cols.idnumber.removeIndex()
        table.cols.idnumber.createIndex()
    
    def appendTable(self, uri, idnumber):
        """
            Append features and parameters to the table   
        """    
        descriptors=[] #calculating descriptor
        #initalizing rows for the table
        parameters = []
        self.setRow(uri, idnumber, descriptors, parameters)
        return
    

    def setRow(self,uri, idnumber, feature, parameters = []):
        """
            allocate data to be added to the h5 tables
            
            Each entry will append a row to the data structure until data
            is dumped into the h5 tables after which data structure is reset.
        """
        temprow = {'feature':feature, 'idnumber':idnumber, 'uri':uri}
        if parameters and self.parameter_info:
            temprow['parameter'] = parameters
        self.temptable.append(temprow)
        return
            
            
###############################################################
# Image Import
###############################################################
class ImageImport():
    """ imports an image from image service and saves it in the feature temp image dir """
    def __init__(self, uri,file_type='tiff'):
        
        
        if uri.find('image_service')<1:        
            import urllib, urllib2, cookielib
            self.uri=uri
            header = {'Accept':'text/xml'}
            req = urllib2.Request(url=uri,headers=header)
            #req.add_header('Referer', 'http://www.python.org/')
            try:
                content = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                if e.code>=400:
                    abort(404)
                else:
                    log.debug('Response Code: %s'%e.code)
                    log.exception('Failed to get a correct http response code')
                    abort(500)
       
            d =[random.choice(string.ascii_lowercase + string.digits) for x in xrange(10)]
            s = "".join(d)
            file = 'image'+ str(s)+'.'+file_type
            
            self.path = os.path.join( FEATURES_TEMP_IMAGE_DIR, file)
                
            
            with Locks(None, self.path):
                f = open(self.path, 'wb') 
                f.write(content.read())
                f.flush()
                f.close()
        else:
            self.path = image_service.local_file(uri)
            log.debug("path: %s"% self.path)
            if self.path is None:
                abort(404)
        
    def returnpath(self):
        return self.path


############################################################### 
# Temp Import
############################################################### 

class TempImport():
    """Deals with file produced by feature extractors"""
    status = 'Closed'
    def __init__(self, filetype):
        s = "".join([random.choice(string.ascii_lowercase + string.digits) for x in xrange(10)])
        file = 'temp'+ str(s)+'.'+filetype
        self.path = os.path.join( FEATURES_TEMP_IMAGE_DIR, file)
        
    def open(self):
        self.f = open(self.path)
        self.status = 'Open'
        return self.f
    
    def close(self):
        if self.status == 'Open':
            self.f.close()
            del self.f
            status = 'Closed'
    
    def returnpath(self):       
        return self.path
    
    def returnstatus(self): 
        self.status 

#removed for debuging
#    def __exit__(self):
#        self.close()
#        try:
#            os.remove(self.path)
#        except:
#            pass
    
    def __del__(self):
        """ When the ImageImport object is deleted the image path is removed for the temp dir """
        try:
            os.remove(self.path)
        except:
            pass

############################################################### 
# XML Import
############################################################### 

class XMLImport():
    """ Import XML from another service and returns the tree """
    def __init__(self, uri):
        from lxml import etree
        import urllib, urllib2, cookielib
        self.uri = uri
        
        header = {'Accept':'text/xml'}
        req = urllib2.Request(url=uri,headers=header)
        try:
            content = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            if e.code>=400:
                abort(404)
            else:
                log.debug('Response Code: %s'%e.code)
                log.exception('Failed to get a correct http response code')
                abort(500)        
        content = urllib.urlopen(uri)
        
        try:
            self.tree=etree.XML(content.read())
        except etree.XMLSyntaxError:
            abort(415, 'Requires: XML format')
            
#        #hack for amir
#        from bq.api.comm import BQSession
#        username = 'user'
#        password = 'pass'
#        self.uri = uri
#        BQ=BQSession()
#        BQ.init_local(username,password,bisque_root=r'http://bisque.ece.ucsb.edu',create_mex=False)
#        self.tree = BQ.fetchxml(self.uri)
        
        
    def returnxml(self):       
        return self.tree
    
    def __del__(self):
        pass







