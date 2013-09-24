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


#wrapper for the calculator function so the output
#is in the correct format to be easily placed in the tables
def wrapper(func):
    def calc(self,kw):
        id = self.returnhash(**kw)
        #id = uuid.uuid5(uuid.NAMESPACE_URL, str(uri)) #no longer stores ids
        #id = id.hex

        results = func(self,**kw)
        column_count = len(self.Columns.columns)-1 #finds length of columns to determin hoe to parse
        if column_count==1:
            results=tuple([results])
        
        rows=[]   
        for i in range(len(results[0])): #iterating though rows returned
            
            if self.cache: #check for cache to see how to build the table
                row = tuple([id])
            else:
                row = tuple([uri])
                
            for j in range(column_count): #iterating through columns returned
                row += tuple([results[j][i]])
            rows.append(row)
        return rows
    
    return calc

###############################################################
# Feature Object
###############################################################
class Feature(object):
    """
        Initalizes Feature table and calculates descriptor to be
        placed into the HDF5 table
    """
    #initalize parameters
    
    #feature name (the feature service will refer to the feature by this name)
    name = 'Feature'
    
    #A short descriptio of the feature
    description = """Feature vector is the generic feature object. If this description is 
    appearing in the description for this feature no description has been provided for this 
    feature"""
    
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
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)
        self.columns()
    
    def localfile(self,hash):
        return os.path.join( self.path, hash[:self.hash]+'.h5')

    def returnhash(self, **kw):
        image_uri = kw['image']   
        uri_hash = uuid.uuid5(uuid.NAMESPACE_URL, str(image_uri))
        uri_hash = uri_hash.hex
        return uri_hash
    
    def typecheck(self, **kw):
        resource = {}
        for r in self.resource:
            if r not in kw:
                log.debug('Argument Error: %s type was not found'%r)
                abort(404,'Argument Error: %s type was not found'%r)   
            else:
                resource[r]=kw[r]
        return resource
    
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
        with Locks(None, filename), tables.openFile(filename,'a', title=self.name)  as h5file: 
            table = h5file.createTable('/', 'values', self.Columns, expectedrows=1000000000)
            
            if self.index: #turns on the index
                table.cols.idnumber.removeIndex()
                table.cols.idnumber.createIndex()                    
            
            table.flush() 
        return
    
    def indexTable(self,hash):
        """
            information for table to know what to index
        """
        file = os.path.join( self.path, hash+'.h5')
        with Locks(None, self.path), tables.openFile(self.localfile(hash),'a', title=self.name) as h5file:
            table=h5file.root.values
            table.cols.idnumber.removeIndex()
            table.cols.idnumber.createIndex()
    
    @wrapper
    def calculate(self, **resource):
        return [0]
        
            
            
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
            try:
                content = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                if e.code>=400:
                    abort(404)
                else:
                    log.debug('Response Code: %s'%e.code)
                    log.exception('Failed to get a correct http response code')
                    abort(500)
            
            #creates a random feature
            d =[random.choice(string.ascii_lowercase + string.digits) for x in xrange(10)]
            s = "".join(d)
            file = 'image'+ str(s)+'.'+file_type
            
            self.path = os.path.join( FEATURES_TEMP_IMAGE_DIR, file)
                
            
            with Locks(None, self.path):
                with open(self.path, 'wb')as f:
                    f.write(content.read())
                    f.flush()

        else:
            self.uri=uri
            self.path = image_service.local_file(uri)
            log.debug("path: %s"% self.path)
            if self.path is None:
                abort(404)
        
    def returnpath(self):
        return self.path
    
    def __del__(self):
        #check if the temp dir was used
        if self.uri.find('image_service')<1:
            try:
                os.remove(self.path)
            except:
                pass
            
               


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
        
#        header = {'Accept':'text/xml'}
#        req = urllib2.Request(url=uri,headers=header)
#        try:
#            content = urllib2.urlopen(req)
#        except urllib2.HTTPError, e:
#            if e.code>=400:
#                log.debug('XML not found at this URI')
#                abort(404)
#            else:
#                log.debug('Response Code: %s'%e.code)
#                log.exception('Failed to get a correct http response code')
#                abort(500)        
#        content = urllib.urlopen(uri)
#        
#        try:
#            self.tree=etree.XML(content.read())
#        except etree.XMLSyntaxError:
#            abort(415, 'Requires: XML format')
            
        #hack for amir
        from bq.api.comm import BQSession
        username = 'stuff'
        password = 'stuff'
        self.uri = uri
        BQ=BQSession()
        BQ.init_local(username,password,bisque_root=r'http://bisque',create_mex=False)
        self.tree = BQ.fetchxml(self.uri)
        
        
    def returnxml(self):       
        return self.tree
    
    def __del__(self):
        pass







