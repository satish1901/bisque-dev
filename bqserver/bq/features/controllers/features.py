# -*- mode: python -*-
"""Main server for features
"""

__module__    = "features"
__author__    = "Dmitry Fedorov, Kris Kvilekval, Carlos Torres and Chris Wheat"
__version__   = "0.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os
import logging
import pkg_resources
import tables
from PytablesMonkeyPatch import pytables_fix
import numpy as np
import sys
import time
import inspect
import numpy as np
import traceback
import pkgutil
import importlib

from pylons.i18n import ugettext as _, lazy_ugettext as l_ 
from pylons.controllers.util import abort
from tg import expose, flash, config, response
from repoze.what import predicates 
from bq.core.service import ServiceController

from lxml import etree
import lxml
from datetime import datetime, timedelta
import urllib

import bq
from bq.util.paths import data_path
from bq.client_service.controllers import aggregate_service
from bq import data_service
from bq.image_service.controllers.locks import Locks
from bq.api.comm import BQServer

import Feature

#query is commented out
#querylibraries
#import Query_Library.ANN.ann as ann

log = logging.getLogger("bq.features")

#FUTURE:
#    Key point and region selection with gobjects (may need to api fixes to fit together everything wait on opinions)* everything will be recieving a unique
#    add private and public access (all images must be public)
#    package server for first release (better way of packaging libraries)
#    adding delete options from the table (admin only command)

#bisque API
#    adding importing 3D 4D and 5D images for higher dimensional feature analysis (api limitation)
#    import images as numpy arrays

#Feature Library maintenance
#    create a VRL descriptor library wrapping C code (if i finish everything else)
#    DOCUMENTATION!!! (it never ends)

#Indexing service
#    requires HDF5 Service
#    Look into libspatialindex
#    tree initalization (while initalizing tree it blocks all the servers) 
#    multiple threads accessing one preloaded tree or set of trees (when reindexing other threads with have to redownload the tree)

#Research
#    Should a new feature module be able to be added even while the server is still active?
#    Think of a better way to format the tables using uniques and commands instead of id tables
#    as the table increases in size hdf5 becomes increasingly harder to search through

#Note (when using the feature server)
#    building xml tree is a big bottle neck (maybe look into returning binary outputs to speed up the loop)


#directories

FEATURES_STORAGE_FILE_DIR = data_path('features')
FEATURES_TABLES_FILE_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR ,'feature_tables\\')
FEATURES_TEMP_IMAGE_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR,'feature_temp_images\\')
FEATURES_TEMP_CSV_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR,'feature_temp_csv\\')

FEATURES_CONTOLLERS_DIR = bq.features.controllers.__path__[0]
EXTRACTOR_DIR = os.path.join(FEATURES_CONTOLLERS_DIR,'extractors')

################################################################# 
###  descriptor tables
#################################################################

class Feature_Modules():
    """
        List of included descriptors:
        SURF, ORB, SIFT, HTD, EHD, CLD, CSD, SCD, DCD
        FREAK, BRISK, TAS, PFTAS, ZM, HAR, ShCoD, FFTSD
        RSD, many more...
        
        Disclaimer:
        The proper use of each feature extractor is documented
        in the extractor module. The documentation is only so good as the
        creator of each extractor module. Some extractors will 
        require different types of urls and the responsibility will
        be left to the user of each extractor
    """
    def __init__(self):
        """
            Initalizes all the objects found in the extraction_library__init__ 
            __all__ object. If one wants to add a new feature to this directory
            to be initialized look at the documentation file in the 
            extraction_library directory.
        """
        self.feature_module_dict = {}
        extractors=[name for module_loader, name, ispkg in pkgutil.iter_modules([EXTRACTOR_DIR]) if ispkg]
        for module in extractors:
            try:
                extractor = importlib.import_module('bq.features.controllers.extractors.'+module+'.extractor') # the module needs to have a file named
                for n,item in inspect.getmembers(extractor):                                                   # extractor.py to import correctly
                    if inspect.isclass(item) and issubclass(item, Feature.Feature):
                        log.debug('Imported Feature: %s'%item.name)
                        self.feature_module_dict[item.name] = item
            except Exception,e:                                   #feature failed to import
                log.debug('Failed Imported Feature: %s'%module)
                traceback.print_exc()
    
    def returnfeature(self, feature_type):
        """
            Returns feature object. If feature object is not found
            the server will return a 404 error 
        """
        try:
            feature_module = self.feature_module_dict[feature_type]
            self.feature_table_class = feature_module
            return self.feature_table_class
        except KeyError:
            abort(404,'feature type:'+feature_type+' not found')

    def returnfeaturelist(self):
        """
            Returns a list of features that are imported in the with the a 
            Feature_Modules instance.
        """
        return self.feature_module_dict.keys()

#################################################################
### IDTable
#################################################################

class IDTable():
    """The class that stores and returns values from the id table"""
    
    def __init__(self):        
        
        from ID import ID
        self.Table = HDF5Table(ID)
        
    def returnID(self, uri):
        """
        Returns the ID of a URI stored in its dictionary.
        If the URL is not stored in the dictionary the function
        creates an ID stores that in the dictionary and returns
        that same ID.
        
        input
        -----
        key : URL (type - string)
        
        output
        ------
        value : ID (type - string)
        """ 
        query = 'uri=="%s"'% str(uri)
        value = self.Table.queryTable(query,'idnumber')
        
        if len(value)>1:
            log.debug('ERROR: Too many values returned from the IDTable')
            value = self.Table.FeatureClass.temptable[0]['idnumber']
            #log.debug('value: %s'%value)
        elif len(value)<1:
            idnumber = int(self.Table.collen()) #returns the length of the idtable to give an id
            self.Table.append(uri,idnumber)
            value = self.Table.FeatureClass.temptable[0]['idnumber'] 
            #log.debug('value: %s'%value)
        else:
            value = value[0]
            
        return value
    
    def returnURI(self,id):
        """
        Returns an ID to a URI stored in its dictionary.
        If the URI is not in its dictionary it returns nothing.
        
        input
        -----
        key : ID (type - string)
        
        output
        ------
        value : URI (type - string)
        """ 
        value = self.Table.queryTableindex(id,'uri')
        value = value[0].strip()
        return value

        
########################################################
###   Feature Tables
########################################################

class FeatureTable():
    
    def __init__(self, HDF5_Table):
        self.HDF5_Table = HDF5_Table #saving HDRFTable object
        
    def return_FeatureObject(self, uri = [], id = [], index = [], short = 0):
        """
        Read table and returns an feature object. If feature is not in the table
        a feature will be calculated. If id is not in the tabel it will return nothing
        
        if short is set to 1 the FeatureObject will have parameters and features removed
        """
        #checks to see if image has been added to pytables 
        if isinstance(index,(int,long )): 
            feature_attributes = {}
            for name in self.HDF5_Table.colnames():
                feature_attributes[name] = self.HDF5_Table.queryTableindex(index, name)
            
            feature_attributes['uri'] = IDTable().returnURI( feature_attributes['idnumber'] )
        
        elif uri and isinstance(id,(int,long)):
            feature_attributes = {}
            query = 'idnumber==%s' %id
            feature_attributes['uri'] = uri
            for name in self.HDF5_Table.colnames():
                feature_attributes[name] = self.HDF5_Table.queryTable(query, name)
            
        
            if not feature_attributes['feature']: #features were not found
                self.HDF5_Table.append(uri, id) #add feature to the table and requery
                #self.HDF5_Table.index()
                for name in self.HDF5_Table.colnames():
                    feature_attributes[name] = self.HDF5_Table.queryTable(query, name)
                    
        
        else:
            abort(500, 'return_FeatureObject does not have the correct input')
            
        feature_object_list=[]
        if short == 1:
            FeatureClass = self.HDF5_Table.Feature()
            setattr(FeatureClass, 'uri', feature_attributes['uri'])
            setattr(FeatureClass, 'id', feature_attributes['idnumber'])
            setattr(FeatureClass, 'value', [])
            setattr(FeatureClass, 'parameter',[])
            feature_object_list.append(FeatureClass)
        
        else:
            for i in range(0,len(feature_attributes['feature'])):
                FeatureClass = self.HDF5_Table.Feature() #creating a list of feature objects
                setattr(FeatureClass, 'uri', uri)
                setattr(FeatureClass, 'id', id)
                setattr(FeatureClass, 'value', feature_attributes['feature'][i])
                if 'parameter' in feature_attributes:
                    setattr(FeatureClass, 'parameter',feature_attributes['parameter'][i])
                else:
                    setattr(FeatureClass, 'parameter',[])
                feature_object_list.append(FeatureClass)
        return feature_object_list



#################################################################
### HDF5 Tables
#################################################################

class HDF5Table():
    """ Class that deals with  HDF5 files"""
    
    def __init__(self, FeatureClass):
        """
        Requires a Feature Class to intialize. Will search for table in the 
        data\features\feature_tables directory. If it does not find the table
        it will create a table.
        """
        self.Feature = FeatureClass
        self.FeatureClass = FeatureClass()
        if not os.path.exists(self.FeatureClass.path):   #creates a table if it cannot find one
            self.create() #creates the table
            self.index() #indexes the table as commanded in the feature modules
        
    def create(self):
        """
        Creates a feature.h5 file given in the feature class
        """
        self.FeatureClass.initalizeTable()
        with Locks(None, self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'a', title=self.FeatureClass.name)  
            table = h5file.createTable('/', 'values', self.FeatureClass.Columns, expectedrows=1000000000)
            #table.attrs.description = self.FeatureClass.description (is explained in the xml output)
            table.flush()       
            h5file.close()

    def append(self, uri, ID):
        """
        Calls the feature class to calculate feature and then appends the feature
        to the feature.h5 file all given by the feature class
        """
        self.FeatureClass.appendTable(uri, ID) #calculates the features
        with Locks(None, self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'a', title=self.FeatureClass.name)
            table=h5file.root.values
            r = table.row
            for row in self.FeatureClass.temptable:
                for keys in table.colnames: 
                    r[keys] = row[keys]
                r.append()
            table.flush()
            h5file.close()
            
    def index(self):
        """
        Calls the feature class to index the table as specified in the class.
        Disclaimer: 
        Doesnt work right now :/
        """
        with Locks(None, self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'a', title=self.FeatureClass.name)
            table=h5file.root.values
            self.FeatureClass.indexTable(table)
            h5file.close()

    def queryTable(self, query, name):
        """
        Reads a table from feature.h5 file and returns a query
        
        input
        -----
        query : pytables query format (type - string)
            exmaple: '(column1 == 'hello')&&(column2 >12)'
        name  : the name of the column one want to find the value for (type - string)
        
        output
        ------
        value 

        """
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            log.debug(table)
            log.debug('query: %s'% query)
            log.debug('name: %s'% name)
            value=[row[name] for row in table.where(query)]
            log.debug(value)
            h5file.close()
        return value
    
    def queryTableindex(self, index, field):
        """
        Reads the table index and returns field value with that index (very fast)
        
        input
        -----
        index : index of the row (type - int)
        name  : the name of the column one want to find the value for (type - string)
        
        output
        ------
        value 
        
        """
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            value = table.read(index, field = field)
            h5file.close()
        return value
                
    def returnCol(self, name):
        """Reads a column out of the table"""
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            value = [row[name] for row in table.iterrows()]
            h5file.close()
        return value    
    
    def colnames(self):
        """returns a list of column names"""
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            names=table.colnames
            h5file.close()
        return names
    
    #look into making this more general
    def returndescriptorCol(self, function): 
        """
        Reads the feature column out of the table 
        
        Input
        -----
        function - a function that accepts one value and that value has to be a numpy string
        
        Output
        ------
        results of that function
        """
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            output = function( table.cols.feature )
            h5file.close()
        return output

    
    def collen(self):
        """Returns the number of rows in the table"""
        with Locks(self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'r', title=self.FeatureClass.name)
            table=h5file.root.values
            nrows=table.nrows
            h5file.close()
        return nrows
    
###############################################################
### Feature Query
###############################################################


##class Initalize_Queries():
#
#class Feature_Query():
#    
#    def __init__(self, query_type, feature_modules):
#        self.query_type = query_type
#        self.feature_modules = feature_modules
#        
#    def return_query(self):
#        outputs = {'ANN' : ANN }
#        queryobject = outputs[self.query_type]
#        return queryobject(self.feature_modules)
#
#class ANN():
#    
#    ANN_DIR = os.path.join(FEATURES_STORAGE_FILE_DIR ,'ANN\\') #initalizing the directory
#    name = 'ANN'
#    ObjectType = 'Query'
#    
#    def __init__(self,feature_modules):
#        self.feature_modules = feature_modules
#        self.tree = {};
#        treeList = os.listdir(self.ANN_DIR)
#        for treename in treeList:
#            if treename.endswith('.tree'):
#                with Locks(self.ANN_DIR + treename): #read lock
#                    self.tree[treename[0:-5]]= ann.kd_tree(self.ANN_DIR + treename, import_kd_tree = True) #initializing all the trees
#                    
#    def index_tree(self, feature_type):
#        """Indexes tree of a specific descriptor table"""
#        feature_module = self.feature_modules.returnfeature(feature_type)
#        Table = HDF5Table(feature_module) #initalizing table
#        if Table.collen()>1:
#            
#            tree = Table.returndescriptorCol(ann.kd_tree)
#            
#            with Locks(None,self.ANN_DIR+feature_type+'.tree'):    
#                tree.save_kd_tree(self.ANN_DIR+feature_type+'.tree')   #saving tree to file
#            
#            self.tree[feature_type] = tree
#             
#            log.debug('saving tree was successful @ %s'% self.ANN_DIR+feature_type+'.tree')
#            return 1
#        else:
#            log.debug('saving tree was NOT successful') #500 Internal Server Error
#            return 0
#    
#    def query_tree(self, feature_type, discriptor, uri, limit ):
#        """searches query tree for nearest neighboring descriptors
#        returns a uri of the image with those descriptors"""
#        feature_module = self.feature_modules.returnfeature(feature_type)
#        Table = FeatureTable( HDF5Table(feature_module) )#initalizing table
#        vectors, dimensions = discriptor.shape
#        if os.path.exists(self.ANN_DIR+feature_type+'.tree'):
#            
#            Anntree=self.tree[feature_type]  #importing kd_tree, import tree at start of the server
#            
#            QueryObject=[]
#            
#            for i in range(0,int(vectors)):
#                total_nearestdescritpors=[]
#                
#                test = np.asarray([discriptor[i,:]], dtype='d', order='C')
#                nQPoints, dimension = test.shape
#                
#                searchtime=time.time()
#                idx, distance = Anntree.search( [discriptor[i,:]], k=limit)
#                log.debug('ann search: %s' % str(time.time()-searchtime))
#                
#                tabletime=time.time()
#                for j in range(0,len(idx[0])):
#                    total_nearestdescritpors.append(Table.return_FeatureObject( index = idx[0][j], short = 1)[0])
#                log.debug('hdf5 table search: %s' % str(time.time()-searchtime))
#                QueryObject.append( self.CreateQueryObject(total_nearestdescritpors, uri, feature_type,[]) )
#
#            return QueryObject
#        else:
#            abort(404, 'tree for feature type: '+feature_type)
#            log.debug('No Tree exists') #404 Not Found
#    
#    def setattributes(self, value, parameter, uri):
#        """creates an object with query outputs"""
#        self.feature = value
#        self.value = value
#        
#        self.parameter = parameter
#        self.uri = uri #image being queried
#        return
#    
#    class CreateQueryObject():
#        
#        def __init__(self, featureObject, uri, feature_type, parameter ):
#            self.query_type ='ANN'
#            self.name = 'ANN'
#            self.ObjectType = 'Query'
#            self.parameter_info = []
#            self.feature_type = feature_type
#            self.parameter = parameter
#            self.featureObject = featureObject
#            self.value = featureObject
#            self.uri = uri
    

###############################################################
# Features Outputs 
###############################################################

class Features_Outputs():
    """Formats the output"""
    def __init__(self , resource, **kw): 
        """ initializing output """
        self.resource = resource
    
    def return_output(self,output_type):
        """ Returns an output function"""
        outputs={'xml'  : self.xml,
                 'none' : self.No_Output,
                 'numpy': self.Numpy_Output,
                 'csv' : self.csv,
                 'bin' : self.bin}
        
        try:
            function = outputs[output_type]
            return function()
        except KeyError:
            abort(404, 'Output Type:'+output_type+' not found')

    #-------------------------------------------------------------
    # Formatters - No Ouptut 
    #-------------------------------------------------------------             
    def No_Output(self):
        response.headers['Content-Type'] = 'text'
        return

    #-------------------------------------------------------------
    # Formatters - Numpy_Output
    #-------------------------------------------------------------  
    def Numpy_Output(self): 
        """
        returns numpy array from tables
        only works for feature and only use for functions in this service or on the system
        """
        
        feature = []
        #parameter = []
        #check for feature class type
               
        for item in self.resource:
            #if isinstance(self.resource, extraction_library.Feature.Feature):  
                    #parameter.append( item.parameter)
            feature.append( item.value)
            #else:
            #    abort(500, 'Numpy only works on features for now and not querys')
        return np.array(feature)#, np.array(parameter) 
    
    #-------------------------------------------------------------
    # Formatters - XML
    # MIME types: 
    #   text/xml
    #-------------------------------------------------------------   
    def xml(self): 
        """Drafts the xml output"""
        resource_element = etree.Element('resource')
        self.xml_return_object( self.resource , resource_element )
        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(resource_element)
        
    def xml_return_object(self,ObjectList, element):
        """
        Formats query and feature objects for xml
        Iterates through nested resource objects
        """
        for resource in ObjectList:
            xml_attributes = {'type':str(resource.name),'name':str(resource.uri)}
            subelement = etree.SubElement( element, resource.ObjectType , xml_attributes)
                
            #parameters
            if resource.parameter_info and resource.parameter!=[]:
                param={}
                for i,item in enumerate(resource.parameter_info):
                    param[str(item)] = str('%g'% resource.parameter[i])
                parameters=etree.SubElement(subelement, 'parameters', param)
            
            #value
            if resource.value!=[]:
                if isinstance(resource.value,np.ndarray):
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g'%item for item in resource.value) 
                else:
                    self.xml_return_object(resource.value, subelement) #allows for nexted objects in value
        
    #-------------------------------------------------------------
    # Formatters - CSV 
    # MIME types: 
    #   text/csv 
    #   text/comma-separated-values
    #-------------------------------------------------------------   
    def csv(self):
        """Drafts the csv output (only works for feature objects)"""
        ## plan to impliment for query and include parameters
        import csv
        import StringIO

        f = StringIO.StringIO()
        writer = csv.writer(f)
        titles = ['Feature Number','Feature_Type','Name','Value']
        writer.writerow(titles)
        for idx,item in enumerate(self.resource):
            if isinstance(item, extraction_library.Feature.Feature):
                #if isinstance(item.feature,np.ndarray):
                value_string = ",".join('%g'%i for i in item.value)
                line = [idx,item.name,item.uri,value_string]
                writer.writerow(line)
            else:
                abort(500, 'csv only works on features for now and not querys')
        
        #creating a file name
        filename = 'feature.csv' #think of how to name the files
        try:
            disposition = 'filename="%s"'% filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition #sets the file name of the csv file
        response.headers['Content-Type'] = 'text/csv' #setting the browser to save csv file
    
        return f.getvalue()

            
    #-------------------------------------------------------------
    # Formatters - Binary 
    # MIME types: 
    #   text 
    #-------------------------------------------------------------   
    def bin(self):
        """Drafts the binary output (only works for feature objects)"""
        """return headered with [store type : len of feature : feature]/n"""
        import StringIO
        import struct
        
        f = StringIO.StringIO()
    
        for item in self.resource:
            if isinstance(self.resource, extraction_library.Feature.Feature): #test for Feature objects
                vector = ''
                vector+=struct.pack('<2s','<d')  #type stored
                vector+=struct.pack('<I',len(item.value)) 
                vector+=''.join([struct.pack('<d',i) for i in item.value])
                vector+='\n'
                f.write(vector)
            else:
                abort(500, 'bin only works on features for now and not querys')
                
        #creating a file name
        filename = 'feature.bin' #think of how to name the files
        try:
            disposition = 'filename="%s"'% filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition #sets the file name of the csv file
        response.headers['Content-Type'] = 'text/bin' #setting the browser to save bin file    
            
        return f.getvalue()
        
 
###################################################################
### Feature Service Controller
###################################################################

class featuresController(ServiceController):

    service_type = "features"

    def __init__(self, server_url):
        super(featuresController, self).__init__(server_url)
        self.baseurl=server_url
        
        log.info('importing features')
        self.feature_modules = Feature_Modules() #initalizing all the feature modules
        
#        log.info ("initializing Trees")
#        self.ANN = Feature_Query('ANN', self.feature_modules).return_query() #may need to create more genericlly to allow for other query types
#        log.info ("Done initializing Trees Feature Server is ready to go")        
    
    ###################################################################
    ### Feature Service
    ###################################################################
    
    @expose()
    def get(self, feature_type, output_type='xml', **kw):
        """Retreives a feature either stored in pytables or calculates it"""
        args={'uri':'','short':0} #for all that remain empty get will return nothing
        for arg in kw: #needs to be fixed
            if arg in args:
                args[arg] = kw[arg]
        for arg in args:
            if not arg in args:
                return
            
        response.headers['Content-Type'] = 'text'
        uri = args['uri']
        uri =uri.rstrip('\n') #there is a newline at the end of uri collected with **kwarg
        log.debug('uri: %s'%uri)
        ID=IDTable().returnID(uri) #find ID
        feature_module = self.feature_modules.returnfeature(feature_type)
        Table = FeatureTable( HDF5Table(feature_module) ) #initalizing table
        featureObject = Table.return_FeatureObject( uri = uri, id = ID, short = args['short'])  #searching for feature object in table if not found will calculate feature
        log.debug('calculated features')
        return Features_Outputs( featureObject ).return_output(output_type)
    
    @expose(content_type="text/xml") #not intended to be used, main purpose is debug
    def indexFeatureTable(self, feature_type, output_type = 'xml'):
        feature_module = self.feature_modules.returnfeature(feature_type)
        HDF5Table(feature_module).index()
        resource = etree.Element('resource', status = 'FINISHED INDEXING FEATURE TABLE')
        feature=etree.SubElement( resource, 'FeatureType', featuretype = str(feature_type))
        return etree.tostring(resource)

    @expose(content_type="text/xml")
    def tablelen(self, feature_type):
        """
        Finding the amount of vectors in a table
        (for debugging purposes)
        """
        feature_module = self.feature_modules.returnfeature(feature_type)
        Table = HDF5Table(feature_module) #initalizing table
        resource = etree.Element('resource', feature = feature_type, table_length = str(Table.collen()))
        return etree.tostring(resource)
    
    @expose(content_type="text/xml")
    def featurelen(self,feature_type):
        feature_module = self.feature_modules.returnfeature(feature_type)
        resource = etree.Element('resource', feature = feature_type, table_length = str(feature_module.length))
        return etree.tostring(resource)

    ###################################################################
    ### Query Service
    ###################################################################

#    @expose(content_type="text/xml")
#    def index(self,query_type, feature_type, output_type='xml'): #may move to a query server
#        """indexes the features in the pytables for query type index"""
#        self.ANN.index_tree(feature_type) #index tree
#        resource = etree.Element('resource', status = 'FINISHED')
#        feature=etree.SubElement( resource, 'QueryType', featuretype = str(query_type))
#        feature=etree.SubElement( resource, 'FeatureType', featuretype = str(feature_type))
#        return etree.tostring(resource)
        
#    @expose(content_type="text/xml")
#    def query(self, query_type, feature_type, output_type='xml', **kw): #may move to a query server
#        """Given a vector it calculates the nearest neighbor to the vector"""
#        
#        args={'uri':'','limit':3,'descriptorlimit':10} #for all that remain empty the query will return nothing
#        for arg in kw:
#            if arg in args:
#                args[arg] = kw[arg]
#        for arg in args:
#            if not args[arg]:
#                return 
#
#        uri = args['uri']
#        feature = self.get(feature_type,'numpy',uri=uri) #returning numpy array of feature
#        vectors, dimensions = feature.shape
#        
#        if vectors>args['descriptorlimit']:
#            vectors = args['descriptorlimit']
#        querytime = time.time()
#        queryObject  = self.ANN.query_tree(feature_type , feature[0:int(vectors),:], uri, args['limit']) #querying feature
#        log.debug('querying time: %s'% str(time.time()-querytime)) 
#         #returning output
#        return Features_Outputs(queryObject).return_output(output_type)
    
    ###################################################################
    ### Documentation
    ###################################################################
    
    @expose(content_type="text/xml")
    def docs(self, *arg):  
        """Ouputs documentation"""
        #Without any import 
        if not arg:
            resource = etree.Element('resource', uri = self.baseurl+'/doc')
            resource.attrib['description'] = 'List of working feature extractors'
            for featuretype in self.feature_modules.returnfeaturelist():
                feature_module = self.feature_modules.returnfeature(featuretype)
                feature=etree.SubElement( resource, 'feature', name = featuretype )
                feature.attrib['description'] = str(feature_module.description)
            return etree.tostring(resource)
        #with an extractor input
        else:
            if len(arg)>1:
                abort(500, 'too many inputs')
            else:
                feature_module = self.feature_modules.returnfeature(arg[0])
                Table = HDF5Table(feature_module)
                feature_module = feature_module()  
                
                xml_attributes = {'file':str(feature_module.file),
                                  'description':str(feature_module.description),
                                  'feature_length':str(feature_module.length),
                                  'parameter_info':str(feature_module.parameter_info),
                                  'table_length':str(Table.collen())} 
                 
                resource = etree.Element('resource', uri = self.baseurl+'/feature'+'/'+str(arg[0]))
                feature=etree.SubElement( resource, 'feature', name = str(feature_module.name))
                for key,value in xml_attributes.iteritems():
                    attrib={key:value}
                    info=etree.SubElement(feature,'info',attrib)   
                return etree.tostring(resource)
    
    
#######################################################################
### Initializing Service
#######################################################################    

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.info ("initialize " + uri)
    
    service =  featuresController(uri)
    #directory.register_service ('features', service)

    return service


__controller__ =  featuresController
