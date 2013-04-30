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
from bq.util.paths import data_path
from bq.image_service.controllers.locks import Locks
from pylons.controllers.util import abort


FEATURES_STORAGE_FILE_DIR = data_path('features')
FEATURES_TABLES_FILE_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR ,'feature_tables\\')
FEATURES_TEMP_IMAGE_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR,'feature_temp_images\\')
FEATURES_TEMP_file_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR,'temp_files\\')
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
            Initializes the Feature table 
        """ 
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        if self.parameter_info:
            parameterAtom = tables.Atom.from_type(self.parameter_format, shape=(len(self.parameter_info)))
        class Columns(tables.IsDescription):
                idnumber  = tables.UInt32Col(pos=1)
                feature   = tables.Col.from_atom(featureAtom, pos=2)
                if self.parameter_info:
                    parameter = tables.Col.from_atom(parameterAtom, pos=3)
        self.Columns=Columns
    
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
            
###############################################################
# Image Import
###############################################################
class ImageImport():
    """ imports an image from image service and saves it in the feature temp image dir """
    def __init__(self, uri):
        import urllib, urllib2, cookielib
        self.uri=uri
        content = urllib.urlopen(self.uri)
        d =[random.choice(string.ascii_lowercase + string.digits) for x in xrange(10)]
        s = "".join(d)
        file = 'image'+ str(s)+'.tiff'
        self.path = os.path.join( FEATURES_TEMP_IMAGE_DIR, file)
        
#        if not content:
#            abort(404, 'Image not found')
#        
#        with Locks(None, self.path):
#            f = open(self.path, 'wb') 
#            f.write(content.read())
#            f.flush()
#            f.close()
        
        #Hack for amir
        #except only from data_service so cannot run image_service operations
        from bq.api.comm import BQServer
        from bq.api.util import fetch_image_pixels
        username = 'botanicam'
        password = 'plantvrl'

        Session=BQServer()
        Session.authenticate_basic(username,password,'http://bisque.ece.ucsb.edu')
        content=Session.fetch( uri )
        
        if not content:
            abort(404, 'Image not found')
            
        f = open(self.path, 'wb')
        f.write(content)  
        f.flush()
        f.close()
        
    def returnpath(self):       
        return self.path
    
    def __del__(self):
        """ When the ImageImport object is deleted the image path is removed for the temp dir """
        os.remove(self.path)
        try:
            os.remove(self.path)
        except:
            pass
        


############################################################### 
# Temp Import
############################################################### 

class TempImport():
    """ Keeps track of temp files """
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
    """ Keeps track of XML """
    def __init__(self, uri):
#        from lxml import etree
#        import urllib, urllib2, cookielib
#        self.uri = uri
#        content = urllib.urlopen(uri)
#        self.tree=etree.XML(content.read())
        
        #hack for amir
        from bq.api.comm import BQSession
        username = 'botanicam'
        password = 'plantvrl'
        self.uri = uri
        BQ=BQSession()
        BQ.init_local(username,password,bisque_root=r'http://bisque.ece.ucsb.edu',create_mex=False)
        self.tree = BQ.fetchxml(self.uri)
        
        
    def returnxml(self):       
        return self.tree
    
    def __del__(self):
        pass







