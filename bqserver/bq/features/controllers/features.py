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

from numpy.lib.recfunctions import append_fields

from pylons.i18n import ugettext as _, lazy_ugettext as l_ 
from pylons.controllers.util import abort
from tg import expose, flash, config, response
from repoze.what import predicates 
from bq.core.service import ServiceController

from lxml import etree
import lxml
from datetime import datetime, timedelta
import urllib

from repoze.what.predicates import is_user, not_anonymous

import bq
from bq.util.paths import data_path
from bq.client_service.controllers import aggregate_service
from bq import data_service
from bq.image_service.controllers.locks import Locks
from bq.api.comm import BQServer
from bq.util.mkdir import _mkdir

import Feature

#query is commented out
#querylibraries
#import Query_Library.ANN.ann as ann

log = logging.getLogger("bq.features")

#FUTURE:
#    Key point and region selection with gobjects (may need to api fixes to fit together everything wait on opinions)* everything will be recieving a unique
#    add private and public access (all images must be public)
#    package server for first release (better way of packaging libraries)

#bisque API
#    adding importing 3D 4D and 5D images for higher dimensional feature analysis (api limitation)
#    import images as numpy arrays

#Feature Library maintenance
#    create a VRL descriptor library wrapping C code (if i finish everything else)
#    add gist
#    look into nd features
#    DOCUMENTATION!!! (it never ends)

#Query
#    Adding nearest nearbor search with libspacial
#    Figure out index to work with deletes so that if a delete happens the index isnt thrown off
#    integrate the hdf5 into the libspaical so index files do not store too much feature info

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
FEATURES_CONTOLLERS_DIR = bq.features.controllers.__path__[0]
EXTRACTOR_DIR = os.path.join(FEATURES_CONTOLLERS_DIR,'extractors')

#################################################################
###  descriptor tables
#################################################################

class Feature_Achieve(dict):
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
        extractors=[name for module_loader, name, ispkg in pkgutil.iter_modules([EXTRACTOR_DIR]) if ispkg]
        for module in extractors:
            try:
                extractor = importlib.import_module('bq.features.controllers.extractors.'+module+'.extractor') # the module needs to have a file named
                for n,item in inspect.getmembers(extractor):                                                   # extractor.py to import correctly
                    if inspect.isclass(item) and issubclass(item, Feature.Feature):
                        log.debug('Imported Feature: %s'%item.name)
                        self[item.name] = item
            except Exception,e:                                   #feature failed to import
                log.debug('Failed Imported Feature: %s'%module)
                traceback.print_exc()

    def __missing__(self, feature_type):
        abort(404,'feature type:'+feature_type+' not found')


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
        value = self.Table.query(query)
        log.debug(value)
        if len(value)>1:
            abort(500, 'ERROR: Too many values returned from the IDTable')
            
        elif len(value)<1:
            self.Table.append(uri,'dumbnumber')
            value = self.Table.query(query)
            value=value['idnumber']
            #value = self.Table.FeatureClass.temptable[0]['idnumber']
        else:
            value = value['idnumber']
        return value[0]
    
    def returnURI(self, id):
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
        value = self.Table['uri'][id]
        value = value[0].strip()
        return value
    
    def deleteURI(self,uri):
        """
        Deletes URI and ID from the table
        """
        query = 'uri=="%s"'% str(uri)
        self.Table.delete(query)
        
    def deleteTable(self):
        """
        Delete the IDTable
        """
        self.Table.delete()
        
########################################################
###   Feature List
########################################################

class FeatureList(object):
    
    def __init__(self, FeatureClass):
        self.FeatureClass = FeatureClass() #saving HDRFTable object
        self.Table = HDF5Table(FeatureClass)
        self.f_list=np.array([])
    
    def __len__(self):
        return len(self.f_list)
    
    def __getitem__(self,i):
        return self.f_list[i]
    
    def __getslice__(self,i,j):
        return self.f_list[i:j]
    
    def __iter__(self):
        return iter(self.f_list)
    
    def iappend(self,index):
        """
        appends to the list a feature info and feature called with the index from the table
        """
        id = IDTable().returnURI( feature_attributes['idnumber'] ) 
        row=self.HDF5_Table[index]
        r=append_fields(row,'id',np.array([id]),'i4',usemask=False)
        if self.f_list.size<1:
            self.f_list = r
        self.f_list = np.append(self.f_list,r,axis=0)
        return
    
    def uappend(self,uri,id):
        """
        appends to the list the feature info and feature requiring a uri and id 
        """
        query = 'idnumber=="%s"' %id
        row=self.Table.query(query)
        if row.size<1: #nothing matched from the table
            self.Table.append(uri, id) #add feature to the table and requery
            row=self.Table.query(query)
        for r in row:
            r=append_fields(r,'uri',np.array([uri]),'|S200',usemask=False)
            if self.f_list.size<1:
                self.f_list = r
            self.f_list = np.append(self.f_list,r,axis=0)
        return
    
    def fappend(self,feature):
        """
        appends to the list the feature info and feature using the feature vector
        """
        pass




#################################################################
### HDF5 Tables
#################################################################

class HDF5Table(object):
    """ Class that deals with  HDF5 files"""
    
    def __init__(self, FeatureClass):
        """
            Requires a Feature Class to intialize. Will search for table in the 
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.FeatureClass = FeatureClass()
        if not os.path.exists(self.FeatureClass.path):   #creates a table if it cannot find one
            self.create() #creates the table
            self.index() #indexes the table as commanded in the feature modules

    def __getitem__(self, index):
        """
            Reads the table index and returns field value with that index (very fast)
            
            input
            -----
            index : index of the row (type - int)
            
            output
            ------
            row
            
            option
            ------
            row['field']
        
        """
        with Locks( self.FeatureClass.path ):
            h5file = tables.openFile( self.FeatureClass.path ,'r', title=self.FeatureClass.name)
            table = h5file.root.values
            value = table.read(index)
            h5file.close()
        return value 

        
    def create(self):
        """
            Creates a feature.h5 file given in the feature class
        """
        self.FeatureClass.initalizeTable()
        with Locks(None, self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'a', title=self.FeatureClass.name)  
            table = h5file.createTable('/', 'values', self.FeatureClass.Columns, expectedrows=1000000000)
            table.flush()       
            h5file.close()

      

    def append(self, uri, id):
        """
            Calls the feature class to calculate feature and then appends the feature
            to the feature.h5 file all given by the feature class
        """
        self.FeatureClass.appendTable(uri, id) #calculates the features
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
 
    def delete(self,query=None):
        """
            Deletes feature with query is given the table is deleted and a new tables
            is initalized in its place
        """
        if not query:
            with Locks(None, self.FeatureClass.path):
                os.remove(self.FeatureClass.path)
                self.create()
                self.index()
        else:
            with Locks(None, self.FeatureClass.path):
                index = table.getWhereList(query)
                for i in index:
                    table.removeRows(i) #not sure if this works
 
    def query(self, query):
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
            q=table.getWhereList(query)
            value=np.array([])
            if q.size<1:
                pass
            else:
                for i in q:
                    if value.size<1:
                        value=table.read(i)
                    else:
                        value=np.append(value,table.read(i),axis=0)
            h5file.close()
        return value 
            
    def index(self):
        """
            Calls the feature class to index the table as specified in the class.
            Disclaimer: 
            Requires monkey patch to work
        """
        with Locks(None, self.FeatureClass.path):
            h5file=tables.openFile(self.FeatureClass.path,'a', title=self.FeatureClass.name)
            table=h5file.root.values
            self.FeatureClass.indexTable(table)
            h5file.close()
        
    def returnCol(self, name):
        """Reads a column out of the table"""
        with Locks( self.FeatureClass.path ):
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
    
    #for querying the tables
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

    
    def __len__(self):
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
                 'numpy': self.Numpy,
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
    def Numpy(self): 
        """
        returns numpy array from tables
        only works for feature and only use for functions in this service or on the system
        """
        feature = []
        for item in self.resource:
            feature.append( item['feature'])
        return np.array(feature)#, np.array(parameter) 
    
    #-------------------------------------------------------------
    # Formatters - XML
    # MIME types: 
    #   text/xml
    #-------------------------------------------------------------
    def xml(self): 
        """Drafts the xml output"""
        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource')
        for res in self.resource:
            subelement = etree.SubElement( element, 'feature' , type = str(self.resource.FeatureClass.name), name = str(res['uri']))
            #values
            if res['feature'].size>1:
                value = etree.SubElement(subelement, 'value')
                value.text = " ".join('%g'%item for item in res['feature'])
            
            #parameter
            if res['parameter'].size>1:
                p={} #parameters
                for i,name in enumerate(self.resource.FeatureClass.parameter_info):
                    p[str(name)] = str('%g'% res['parameter'][i])
                parameters=etree.SubElement(subelement, 'parameter', p)    
        
        return etree.tostring(element)
        
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
                #if isinstance(item.feature,np.ndarray):
                value_string = ",".join('%g'%i for i in item['features'])
                line = [idx,item.name,item.uri,value_string]
                writer.writerow(line)
        
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
            vector = ''
            vector+=struct.pack('<2s','<d')  #type stored
            vector+=struct.pack('<I',len(item.value)) 
            vector+=''.join([struct.pack('<d',i) for i in item['features']])
            vector+='\n'
            f.write(vector)
                
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
        self.fullurl=ServiceController
        _mkdir(FEATURES_TABLES_FILE_DIR)
        _mkdir(FEATURES_TEMP_IMAGE_DIR) 
        log.info('importing features')
        self.feature_achieve = Feature_Achieve() #initalizing all the feature classes
        
#        log.info ("initializing Trees")
#        self.ANN = Feature_Query('ANN', self.feature_modules).return_query() #may need to create more genericlly to allow for other query types
#        log.info ("Done initializing Trees Feature Server is ready to go")        
    
    ###################################################################
    ### Feature Service
    ###################################################################
    @expose(content_type="text/xml")
    def _default(self, *path, **kw):
        """
        default page on feature server
        """
        resource = etree.Element('resource')
        command=etree.SubElement( resource, 'command', name = 'get', type = 'string', value='fetches feature')
        command=etree.SubElement( resource, 'command', name = 'docs', type = 'string', value='returns documentation')
        return etree.tostring(resource)
    
    @expose()
    def get(self, feature_type, output_type='xml', **kw):
        """
        Retreives a feature either stored in pytables or calculates it
        """
        args={'uri':''} #for all that remain empty get will return nothing
        for arg in kw: #needs to be fixed
            if arg in args:
                args[arg] = kw[arg]
        for arg in args:
            if not arg in args:
                return 
            
        #response.headers['Content-Type'] = 'text'
        uri = args['uri'].rstrip('\n') #there is a newline at the end of uri collected with **kwarg
        id=IDTable().returnID(uri) #find ID
        Feature_Class = self.feature_achieve[feature_type]
        F_list = FeatureList(Feature_Class)
        F_list.uappend(uri,id) #searching for feature object in table if not found will calculate feature
        return Features_Outputs( F_list ).return_output(output_type)
    
    @expose()
    def delete(self,feature_type=None, **kw):
        """
        Delete features from the table or tables themselves
        """
        
        if not not_anonymous:
            abort(401)
        elif not is_user('admin'):
            abort(403)
        else:
            if not kw[uri] and not feature_type:
                #mass deletion
                #delete id
                IDTable().deleteTable()
                #delete feature tables
                for feature_type in feature_achieve.keys():
                    Table=HDF5Table(feature_achieve[feature_type])
                    Table.delete()
            elif not kw[uri]:
                #deletes one table
                FeatureClass = feature_achieve[feature_type]
                Table=HDF5Table(FeatureClass)
                Table.delete()
            elif not feature_type:
                kw[uri]
                #delete from id tables
                ID=IDTable()
                id=ID.returnID(uri)
                ID.deleteURI(uri)
                #delete from feature tables
                for feature_type in feature_achieve.keys():
                    Table=HDF5Table(feature_achieve[feature_type])
                    query='idnumber==%s' %id
                    Table.delete(query)
            else:
                #delete feature from table
                id=IDTable().returnID(uri)
                Table=HDF5Table(feature_achieve[feature_type])
                query='idnumber==%s' %id
                Table.delete(query)
        
#    def index(self, feature_type, output_type = 'xml'):
#        feature_module = self.feature_modules.returnfeature(feature_type)
#        HDF5Table(feature_module).index()
#        resource = etree.Element('resource', status = 'FINISHED INDEXING FEATURE TABLE')
#        feature=etree.SubElement( resource, 'FeatureType', featuretype = str(feature_type))
#        return etree.tostring(resource)


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
        """
        Ouputs documentation
        """
        #Without any import 
        if not arg:
            resource = etree.Element('resource', uri = self.baseurl+'/doc')
            resource.attrib['description'] = 'List of working feature extractors'
            for featuretype in self.feature_achieve.keys():
                feature_module = self.feature_achieve[featuretype]
                feature=etree.SubElement( resource, 'feature', name = featuretype )
                feature.attrib['description'] = str(feature_module.description)
            return etree.tostring(resource)
        #with an extractor input
        else:
            if len(arg)>1:
                abort(500, 'too many inputs')
            else:
                feature_module = self.feature_achieve[arg[0]]
                Table = HDF5Table(feature_module)
                feature_module = feature_module()  
                
                xml_attributes = {'file':str(feature_module.file),
                                  'description':str(feature_module.description),
                                  'feature_length':str(feature_module.length),
                                  'parameter_info':str(feature_module.parameter_info),
                                  'table_length':str(len(Table))} 
                 
                resource = etree.Element('resource', uri = self.baseurl+'/docs'+'/'+str(arg[0]))
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
