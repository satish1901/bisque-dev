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
import uuid
import threading
import httplib2
import Queue

from pylons.i18n import ugettext as _, lazy_ugettext as l_ 
from pylons.controllers.util import abort
from tg import expose, flash, config, response, request
from repoze.what import predicates 
from bq.core.service import ServiceController

from lxml import etree
import lxml
from datetime import datetime, timedelta
import urllib
import time

from repoze.what.predicates import is_user, not_anonymous

import bq
from bq.util.paths import data_path
from bq.client_service.controllers import aggregate_service
from bq import data_service
from bq.image_service.controllers.locks import Locks
from bq.api.comm import BQServer
from bq.util.mkdir import _mkdir
import traceback
from ID import ID
import Feature

#query is commented out
#querylibraries
#import Query_Library.ANN.ann as ann

log = logging.getLogger("bq.features")

#FUTURE:
#    Key point and region selection with gobjects (may need to api fixes to fit together everything wait on opinions)* everything will be recieving a unique
#    add private and public access (all images must be public)
#    add callback to getting feature requests

#Feature Library maintenance
#    add gist
#    add vignish's features
#    look into nd features

#Research
#    Dynamicly adding new features to the service



#directories
from .var import FEATURES_TABLES_FILE_DIR,FEATURES_TEMP_IMAGE_DIR,EXTRACTOR_DIR,FEATURES_TABLES_WORK_DIR

class Feature_Archieve(dict):
    """
        List of included descriptors:
        SURF, ORB, SIFT, HTD, EHD, CLD, CSD, SCD, DCD
        FREAK, BRISK, TAS, PFTAS, ZM, HAR, ShCoD, FFTSD
        RSD, many more...
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
            except StandardError, err: #need to pick a narrower error band but not quite sure right now
                log.exception('Failed Imported Feature: %s\n'%module) #failed to import feature 

    def __missing__(self, feature_type):
        log.debug('feature type:'+feature_type+' not found')
        abort(404,'feature type:'+feature_type+' not found')



class Rows(object):
    """
    Generates rows to be placed into the tables
    """
    def __init__(self, feature):
        self.feature_queue = {}
        self.feature = feature
    
    #def __repr__(self):
    #    return 'Descritpor Generator: Feature: %s List Length: %s'%(self.feature.name, len(feature_list))
    
    def push(self, **resource):
        """
        Calculates features and organizes them into rows to be correctly placed
        into the tables 
        """
        try:
            output = self.feature.calculate(resource) #finds the feature
            log.debug('output: %s'% str(self.feature.localfile(output[0][0])))
            if self.feature.localfile(output[0][0]) in self.feature_queue: # checking the first few element on the hash
                self.feature_queue[self.feature.localfile(output[0][0])].put(output) #place the output in the queue
            else:
                self.feature_queue[self.feature.localfile(output[0][0])] = Queue.Queue() #build queue since none were found
                self.feature_queue[self.feature.localfile(output[0][0])].put(output)
                
        except StandardError, err:
            #creating a list of uri were the error occured
            resource_string=''
            for r in resource.keys():
                resource_string+=r+' : '+resource[r]+', '
            else:
                resource_string=resource_string[:-2]
                
            log.exception('Calculation Error: URI:%s  %s Feature failed to be calculated'%(resource_string,self.feature.name))

class IDRows(Rows):
    """
    Generates rows to be placed into the ID tables
    """
    def __init__(self, feature):
        self.feature_queue = {}
        self.ID = ID()
        self.feature = feature
    
    def push(self, **resource):
        """
            creates the rows to store urls with there ids in the idtable
        """
        hash = self.feature.returnhash(**resource) #get hash from features
        output = [hash]
        for r in self.feature.resource:
            output += [r+'='+resource[r]] #append the uris
        if self.feature.localfile(hash) in self.feature_queue: # checking the first few element on the hash
            self.feature_queue[self.ID.localfile(output[0][0])].put(output) #place the output in the queue
        else:
            self.feature_queue[self.ID.localfile(hash)] = Queue.Queue() #build queue since none were found
            self.feature_queue[self.ID.localfile(hash)].put(output)        
        pass
    

class UncachedRows(Rows):
    """
        Generates rows to be placed into the uncached tables
    """
    def push(self, **resource):
        try:
            output = self.feature.calculate(resource)
            if 'feature' in self.feature_queue: #feature is used to maintain the structure
                self.feature_queue['feature'].put(output) #the row is pushed into the queue
            else: #creates a queue if no queue is found
                self.feature_queue['feature'] = Queue.Queue()
                self.feature_queue['feature'].put(output)
        except StandardError, err:
            #creating a list of uri were the error occured
            resource_string=''
            for r in resource.keys():
                resource_string+=r+' : '+resource[r]+', '
            else:
                resource_string=resource_string[:-2]
                
            log.exception('Calculation Error: %s  %s feature failed to be calculated'%(resource_string,self.feature.name))

class Tables(object):
    """
        Creates table to store features
    """
    
    def __init__(self, feature):
        """
            Requires a Feature Class to intialize. Will search for table in the 
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.feature = feature
        if not os.path.exists(self.feature.path):   #creates a table if it cannot find one
            _mkdir(self.feature.path)

    
    def isin(self, hash):
        """
            queries the table to see if element is in the table
        """
        filename = self.feature.localfile(hash)
        query='idnumber=="%s"'% str(hash)
        
        if not os.path.exists(filename):
            self.feature.createtable(filename) #creates the table
            
        with Locks(filename):
            with tables.openFile(filename,'r', title=self.feature.name) as h5file:
                table = h5file.root.values
                index = table.getWhereList(query)
        return len(index)>0
    
    def store(self, rowgenorator):
        """
            store elements to tables
        """
        for filename in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[filename]

            if not os.path.exists(filename):
                self.feature.createtable(filename) #creates the table
                
            with Locks(None, filename):
                with tables.openFile(filename,'a', title=self.feature.name) as h5file:
                    table = h5file.root.values
                    
                    while not queue.empty():
                        row=queue.get()
                        query='idnumber=="%s"'% str(row[0][0]) #queries the hash to see if a feature has been
                        log.debug('query: %s'%query)
                        index = table.getWhereList(query)   #appended already
                        if len(index)==0: 
                            table.append(row)
                    table.flush()
        return
    
    def get(self, hash):
        """
            query for elements and return results
        """
        filename = self.feature.localfile(hash)
        query='idnumber=="%s"'% str(hash)
        
        if not os.path.exists(filename):
            self.feature.createtable(filename) #creates the table
        
        with Locks(filename):
            with tables.openFile(filename,'r', title=self.feature.name) as h5file:
                table=h5file.root.values
                index = table.getWhereList(query)
                log.debug('index: %s'%str(index))
                if index.size==0:
                    i = None
                else:
                    i=table[index]
        return i
    
    def copy(self):
        pass
        
    def remove(self):
        pass
    
    def delete(self):
        pass
    
    def __len__(self):
        import glob
        feature_tables=glob.glob(os.path.join( self.feature.path,'*.h5' ))
        log.debug('feature table list %s'%str(os.path.join(self.feature.path,'*.h5')))
        l=0
        for filename in feature_tables:
            with Locks(filename):
                with tables.openFile(filename,'r', title=self.feature.name) as h5file:
                    l+=len(h5file.root.values)
        return l


class IDTables(Tables):
    """
        a subclass of tables but operates only on the ID table
    """

    def __init__(self):
        """
            Requires a Feature Class to intialize. Will search for table in the 
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.ID = ID()
        #self.feature = feature
        
        if not os.path.exists(self.ID.path):   #creates a table if it cannot find one
            _mkdir(self.ID.path)


    def isin(self, hash):
        """
            queries the table to see if element is in the table
        """
        #log.debug('hash: %s'%hash)
        filename = self.ID.localfile(hash)
        query='idnumber=="%s"'% str(hash)
        
        if not os.path.exists(filename):
            self.ID.createtable(filename) #creates the table
            
        with Locks(filename):
            with tables.openFile(filename,'r', title=self.ID.name) as h5file:
                table = h5file.root.values
                index = table.getWhereList(query)
        return len(index)>0

    def store(self, rowgenorator):
        """
            store elements to tables
        """
        for filename in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[filename]
    
            if not os.path.exists(filename):
                self.ID.createtable(filename) #creates the table
                
            with Locks(None, filename):
                with tables.openFile(filename,'a', title=self.ID.name) as h5file:
                    
                    
                    table = h5file.root.values
                    url_vlarray = h5file.root.URI #finding the variable length array
                    while not queue.empty():
                        row=queue.get()
                        query='idnumber=="%s"'% str(row[0]) #queries the hash to see if a feature has been
                        index = table.getWhereList(query)   #appended already
                        if len(index)==0:
                            table.append((row[0]))
                            url_vlarray.append(row[1:])
                        
                    table.flush()
        return

class UncachedTable(Tables):
    """
    Places a table into the workdir without index
    """
    
    def __init__(self, feature):
        """
            Requires a Feature Class to intialize. Will search for table in the 
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.feature = feature
        if not os.path.exists(FEATURES_TABLES_WORK_DIR):   #creates a table if it cannot find one
            _mkdir(FEATURES_TABLES_WORK_DIR)


    def store(self, rowgenorator, filename):
        """
            store row elements to an output table
        """
        filename = os.path.join(FEATURES_TABLES_WORK_DIR,filename)
        for name in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[name]

            if not os.path.exists(filename):
                self.feature.outputTable(filename) #creates the table
            
            #appends elements to the table
            with Locks(None, filename):
                with tables.openFile(filename,'a', title=self.feature.name) as h5file:
                    table = h5file.root.values
                    while not queue.empty():
                        table.append(queue.get())
                    table.flush()
        return

    def isin(self, hash):
        pass

    def get(self, hash):
        pass

    def __len__(self):
        pass
    
###############################################################
# Features Inputs
###############################################################

class Request(object):
    """
        Processes and stores the inputs of a request
        and deals with exceptions
    """


    def __init__(self, feature_archieve, feature_name, format='xml',**kw):
        
        self.options =  {  
                           'callback': None,
                           'limit'   : None,
                           'store'   : False,
                           'calc'    : True,
                        }
        

        #feature assignment
        self.feature_name = feature_name
        self.feature = feature_archieve[feature_name]    
        
        # check kw arg values
        for i in kw.keys():
            if i in self.options:
                self.options[i] = kw[i]
            #else:
            #    log.debug('Argument Error: "%s" is not a valid argument'%i)
            #    abort(404,'Argument Error: "%s" is not a valid argument'%i)
        
        #check if proper format
        self.format = format
        self.Formats = Outputs()[self.format]
        
        #assign inputs
        self.method = request.method
        self.content_type = request.headers['Content-type']
        
        #validating request
        if self.method =='POST' and 1>request.headers['Content-type'].count('xml/text'):
            try: #parse the resquest
                log.debug('request :%s' %request.body)
                self.body = etree.fromstring(request.body)
                if self.body.tag!='dataset':
                    abort(400, 'Document Error: Only excepts datasets')
                self.element_list=[]
                for value in self.body.xpath('value[@type="query"]'):
                    query = value.text
                    query = query.split('&')
                    element = {}
                    for q in query:
                        q = q.split('=')
                        element[q[0]] = q[1].replace('"','')
                    element = self.feature().typecheck(**element)
                    log.debug('element %s'% element)
                    self.element_list.append(element)
            except:
                log.exception('Request Error: Xml document is malformed')
                abort(400, 'Xml document is malformed')
                
        elif self.method =='GET':
            resource = self.feature().typecheck(**kw)
            self.body = None
            self.element_list = [resource]
                         
        else:
            log.debug('Request Error: http request was not formed correctly')
            abort(400, 'http request was not formed correctly')
    
    def proccess(self):
        """
        Proccess request provided to the Feature Server
        (main loop of calculating features)
        """
        if self.feature.cache:
            if self.options['calc']: #no features will be calculated if true
                
                HashTable = IDTables()
                
                #finding hashes
                elementlistintable=[]
                for i,element in enumerate(self.element_list):
                    uri_hash = self.feature().returnhash(**element)    
                    elementlistintable.append(HashTable.isin(uri_hash))
    
                #store hashes
                HashRows=IDRows(self.feature())
                log.debug('In Hash Table List: %s'%elementlistintable)
                for i, element_bool in enumerate(elementlistintable):
                    if not element_bool:
                        HashRows.push(**self.element_list[i])
                HashTable.store(HashRows)
    
                #finding features
                FeatureTable = Tables(self.feature())
                
                elementlistintable = []
                log.debug('element_list: %s'% self.element_list)
                for i,element in enumerate(self.element_list):
                    uri_hash = self.feature().returnhash(**element)
                    elementlistintable.append(FeatureTable.isin(uri_hash))
                
                #store features
                FeatureRows = Rows(self.feature())
                log.debug('In Feature Table List: %s'%elementlistintable)
                for i, element_bool in enumerate(elementlistintable):
                    if not element_bool:
                        FeatureRows.push(**self.element_list[i])
                FeatureTable.store(FeatureRows)

        else:
            #creating name for uncached table
            name = self.feature.name+str(time.time())
            self.uncachedTableName = self.feature().returnhash(name)+'.h5'
            FeatureTable = UncachedTable(self.feature())
            
            log.debug('element_list: %s'% self.element_list)
            
            #store features in an unindexed table in the workdir
            FeatureRows = UncachedRows(self.feature())
            for i, element_bool in enumerate(self.element_list):
                FeatureRows.push(self.element_list[i])
            FeatureTable.store(FeatureRows, self.uncachedTableName)
          
        return
    
    def response(self):
        """
        Builds response
        """
        if self.feature.cache: #queries for results in the feature tables
            Table = Tables(self.feature())
            return self.Formats(self.feature()).return_output(Table, self.element_list)
        
        else: #builds output from the unindexed table built in the workdir
            Table = UncachedTable(self.feature())
            return self.Formats(self.feature()).return_output_uncached(Table, self.uncachedTableName)

###############################################################
# Features Outputs 
###############################################################

class Format(object):
    """
        Base Class of formats for output
    """
    name = 'Format'
    limit = 'Unlimited'
    description = 'Discription of the Format'
    
    def __init__(self, feature, **kw):
        self.feature = feature
    
    def return_output(self,table, element_list):
        pass
    
    def return_output_uncached(self, table, filename):
        pass
    
    def store(self):
        pass


class Xml(Format):
    """
        returns in xml
    """
    name = 'XML'
    limit = 1000 #nodes
    description = 'Extensible Markup Language'
    
    def return_output(self,  table, element_list):
        """Drafts the xml output"""
        
        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource')
        nodes = 0
        
        for i,resource in enumerate(element_list):
            uri_hash =self.feature.returnhash(**resource)
            rows = table.get(uri_hash)
            if rows!=None: #a feature was found for the query
                for r in rows:
                    subelement = etree.SubElement( element, 'feature' , resource ,type = str(self.feature.name))
                    
                    if self.feature.parameter:
                        parameters = {}
                        
                        #creates list of parameters to append to the xml
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name]) 
                        etree.SubElement(subelement, 'parameters', parameters)
                        
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g'%item for item in r['feature']) #writes the feature vector to the xml
                    nodes+=1
                    #break out when there are too many nodes
                    if nodes>self.limit: #checks to see if the number of lines has surpassed the limit
                        break
            else: #not feature was found for the query, adds an error message to the xml
                subelement = etree.SubElement( 
                                                  element, 'feature' ,
                                                  resource,
                                                  type = str(self.feature.name),
                                                  value = 'Return Error: Feature was not found in the table'
                                              )            
            if nodes>self.limit: #checks to see if the number of lines has surpassed the limit
                break

        return etree.tostring(element)

    def return_output_uncached(self, table, filename):
        """Drafts the xml output for uncached tables"""
        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource')
        nodes = 0
                
        filename = os.path.join(FEATURES_TABLES_WORK_DIR,filename)
        with Locks(filename):
            with tables.openFile(filename,'r', title=self.feature.name) as h5file: #opens table
                Table = h5file.root.values
                
                #reads through each line in the table and writes an xml node for it
                for i, r in enumerate(Table): 
                    
                    subelement = etree.SubElement( element, 'feature' , type = str(self.feature.name), name = r['uri'])
                    
                    if self.feature.parameter:
                        parameters = {}
                        
                        #creates list of parameters to append to the xml node
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name]) 
                        etree.SubElement(subelement, 'parameters', parameters)
                    
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g'%item for item in r['feature']) #writes the feature vector to the xml
                    nodes+=1
                    
                    #break out when there are too many nodes
                    if nodes>self.limit:
                        break               
                
        return etree.tostring(element)


class Csv(Format):
    """
        returns in csv
    """
    name = 'CSV'
    
    def return_output(self, table, element_list, **kw):
        """Drafts the csv output"""
        ## plan to impliment for query and include parameters
        
        import csv
        import StringIO
        f = StringIO.StringIO()
        writer = csv.writer(f)
        resource_names = self.feature.resource
        parameter_names = self.feature.parameter
        
        #creates a title row and writes it to the document
        titles = ['index','feature type']+resource_names+['descriptor']+parameter_names
        writer.writerow(titles)
        
        
        for idx,resource in enumerate(element_list):
            uri_hash = self.feature.returnhash(**resource)
            rows = table.get(uri_hash)
            
            if rows!=None: #check to see if nothing is return from the tables
                
                for r in rows:
                    value_string = ",".join('%g'%i for i in r['feature']) #parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names] 
                    parameter = [r[pn] for pn in parameter_names]
                    line = [idx,self.feature.name]+resource_uri+[value_string]+parameter
                    writer.writerow(line) #write line to the document
                    
            else: #if nothing is return from the tables enter Nan into each vector element
                value_string = ",".join(['Nan' for i in range(feature.length)])
                resource_uri = [resource[rn] for rn in resource_names]
                line = [idx,self.feature.name]+resource_uri+[value_string] #appends all the row elements
                writer.writerow(line) #write line to the document
        
        #creating a file name
        filename = 'feature.csv' #think of how to name the files
        try:
            disposition = 'filename="%s"'% filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition #sets the file name of the csv file
        response.headers['Content-Type'] = 'text/csv' #setting the browser to save csv file
    
        return f.getvalue()
    
    def return_output_uncached(self, table, filename):
        """
            returns csv for features without cache
        """
        import csv
        import StringIO
        f = StringIO.StringIO()
        writer = csv.writer(f)
        resource_names = self.feature.resource
        parameter_names = self.feature.parameter
        
        #creates a title row and writes it to the document
        titles = ['index','feature type']+resource_names+['descriptor']+parameter_names
        writer.writerow(titles)
                
        filename = os.path.join(FEATURES_TABLES_WORK_DIR,filename)
        with Locks(filename):
            with tables.openFile(filename,'r', title=self.feature.name) as h5file: #opens table
                Table = h5file.root.values  
                for i, r in enumerate(Table):
                    value_string = ",".join('%g'%i for i in r['feature']) #parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names]
                    parameter = [r[pn] for pn in parameter_names]
                    line = [idx,self.feature.name]+resource_uri+[value_string]+parameter #appends all the row elements
                    writer.writerow(line) #writes line to the document
            
        #creating a file name
        filename = 'feature.csv' #think of how to name the files
        try:
            disposition = 'filename="%s"'% filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition #sets the file name of the csv file
        response.headers['Content-Type'] = 'text/csv' #setting the browser to save csv file
    
        return f.getvalue()
    
#class Binary(Format):
#    
#    def return_output(self):
#        """Drafts the binary output (only works for feature objects)"""
#        """return headered with [store type : len of feature : feature]/n"""
#        import StringIO
#        import struct
#        
#        f = StringIO.StringIO()
#    
#        for item in self.resource:
#            vector = ''
#            vector+=struct.pack('<2s','<d')  #type stored
#            vector+=struct.pack('<I',len(item.value)) 
#            vector+=''.join([struct.pack('<d',i) for i in item['features']])
#            vector+='\n'
#            f.write(vector)
#                
#        #creating a file name
#        filename = 'feature.bin' #think of how to name the files
#        try:
#            disposition = 'filename="%s"'% filename.encode('ascii')
#        except UnicodeEncodeError:
#            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8')) 
#            
#        response.headers['Content-Disposition'] = disposition #sets the file name of the csv file
#        response.headers['Content-Type'] = 'text/bin' #setting the browser to save bin file
#            
#        return f.getvalue()


class Hdf(Format):
    
    name = 'HDF'
     
    def return_output(self,  table, element_list, **kw):
        """
        Returns a newly formed hdf5 table
        
        All HDF files are saved in the work dir of the feature service
        """
        import io
        
        #creating a file name
        name = self.feature.name+str(time.time())
        name_hash = uuid.uuid5(uuid.NAMESPACE_URL, str(name))
        name = name_hash.hex+'.h5'
        filename = os.path.join(FEATURES_TABLES_WORK_DIR,name)
        
        self.feature.outputTable(filename) #create new table in workdir

        with Locks(None, filename):
            with tables.openFile(filename,'a', title=self.name) as h5file: #open table
                #writing to table      
                outtable=h5file.root.values
                for i,element in enumerate(element_list):
                    uri_hash = self.feature.returnhash(**element)
                    rows = table.get(uri_hash)
                    for r in rows: #taking rows out of one and placing them into the rows of the output table
                        row=()
                        for e in self.feature.resource:
                            row+=tuple([element[e]])
                        row += tuple([r['feature']])
                        for p in self.feature.parameter:
                            row += tuple([r[p]])
                            log.debug('row: %s' % str(row))
                        outtable.append([row]) 
                outtable.flush()
        
        #
        f = io.FileIO(filename)
        try:
            disposition = 'filename="%s"'% name.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'% (name.encode('utf8'), name.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition
        response.headers['Content-Type'] = 'application/hdf5' #setting the browser to save hdf5 file
        return f.read()
    
    
    def return_output_uncached(self, table, filename):
        #since the uncached table is already saved in the workdir the file is just
        #returned
        filename = os.path.join(FEATURES_TABLES_WORK_DIR,filename)
        f = io.FileIO(filename)
        try:
            disposition = 'filename="%s"'% filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'% (filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition
        response.headers['Content-Type'] = 'application/hdf5' #setting the browser to save hdf5 file
        return f.read()              
    
    def returnHDF(self, filename):
        pass


class NoOutput(Format):
    name = 'No Output'
    
    def return_output(self,  table, element_list, **kw):
        return
    
    def return_output_uncached(self, table, filename):
        return
  
#class Numpy(Format):
#    def __init__(self, *args, **kw):
#        pass
#    
#    def return_output(self):
#        pass
#
#
#class Local(Format):
#    def __init__(self, *args, **kw):
#        pass
#    
#    def return_output(self):
#        pass

class Outputs(dict):
    """
        Reads the hdf5 tables and returns features in 
        correct format
    """
    def __init__(self):
        self['xml'] = Xml
        self['csv'] = Csv
        #self['bin'] = Binary
        self['hdf'] = Hdf
        self['none'] = NoOutput
    
    def __missing__(self, format):
        log.debug('format type:'+format+' not found')
        abort(404,'Format type: %s not found'% format) #if element type is not found
    

    
        
###################################################################
###  Documentation
###################################################################

class FeatureDoc():
    """
    Feature Documentation Class is to organize the documention for
    the feature server 
    (it will always output in xml)
    """ 
    def __init__(self):
        pass
    
    def feature_server(self):
        """
        Returns xml of the commands allowed on the feature server
        """
        response.headers['Content-Type'] = 'text/xml'
        resource = etree.Element('resource', uri = str(request.url))
        command=etree.SubElement( resource, 'command', name = '/*feature name*', type = 'string', value='Documentation of specific feature')
        command=etree.SubElement( resource, 'command', name = '/list', type = 'string', value='List of features')
        command=etree.SubElement( resource, 'command', name = '/format', type = 'string', value='List of formats')
        command=etree.SubElement( resource, 'command', name = '/format/*format name*', type = 'string', value='Documentation of specific format')
        command=etree.SubElement( resource, 'command', name = '/*feature name*?uri=http://...', type = 'string', value='Returns feature in format set to xml')
        command=etree.SubElement( resource, 'command', name = '/*feature name*/*format name*?*resource type*=http://...(&*resource type*=http://...)', type = 'string', value='Returns feature in format specified')
        command=etree.SubElement( resource, 'attribute', name = 'resource', value='The name of the resource depends on the requested feature')
        return etree.tostring(resource)


    def feature_list(self, feature_archieve):  
        """
        Returns xml of given feature
        """
        response.headers['Content-Type'] = 'text/xml' 
        resource = etree.Element('resource', uri = str(request.url))#self.baseurl+'/doc')
        resource.attrib['description'] = 'List of working feature extractors'
        for featuretype in feature_archieve.keys():
            feature_module = feature_archieve[featuretype]
            feature=etree.SubElement( resource, 
                                      'feature', 
                                      name = featuretype, 
                                      permission="Published",
                                      uri = 'features/list/'+featuretype )
        return etree.tostring(resource)

       
    def feature(self,feature_name,feature_archieve):
        """
        Returns xml of information about the features
        """
        response.headers['Content-Type'] = 'text/xml'
        feature_module = feature_archieve[feature_name]
        feature_module = feature_module() 
        Table = Tables(feature_module)
         
        
        xml_attributes = {
                          'description':str(feature_module.description),
                          'feature_length':str(feature_module.length),
                          'required_resources': ','.join(feature_module.resource),
                          'cache': str(feature_module.cache),
                          'table_length':str(len(Table))
                         }
        if len(feature_module.parameter)>0:
            xml_attributes['parameters'] = ','.join(feature_module.parameter)
         
        resource = etree.Element('resource', uri = str(request.url))
        feature=etree.SubElement( resource, 'feature', name = str(feature_module.name))
        for key,value in xml_attributes.iteritems():
            attrib={key:value}
            info=etree.SubElement(feature,'info',**attrib)
        return etree.tostring(resource)
    

        return etree.tostring(resource)
    
    def format_list(self):
        """
            Returns List of Formats
        """
        response.headers['Content-Type'] = 'text/xml' 
        resource = etree.Element('resource', uri = str(request.url)) 
        resource.attrib['description'] = 'List of Return Formats'
        format_archieve = Outputs()
        log.debug('format_achieve: %s'%format_archieve)
        for format_name in format_archieve.keys():
            format = format_archieve[format_name]
            feature=etree.SubElement( resource, 
                                      'format', 
                                      name = format_name, 
                                      permission = "Published",
                                      uri = 'format/'+format_name )
        response.headers['Content-Type'] = 'text/xml' 
        return etree.tostring(resource)

    def format(self,format_name):
        """
            Returns documentation about format
        """
        response.headers['Content-Type'] = 'text/xml'
        format_archieve = Outputs()
        format = format_archieve[format_name]
         
        xml_attributes = {'Name':str(format.name),
                          'Description':str(format.description),
                          'Limit':str(format.limit)
                          }
         
        resource = etree.Element('resource', uri = str(request.url))
        feature=etree.SubElement( resource, 'format', name = str(format.name))
        for key,value in xml_attributes.iteritems():
            attrib={key:value}
            info=etree.SubElement(feature,'info',attrib)
        return etree.tostring(resource)
        
###################################################################
### Feature Service Controller
###################################################################

class featuresController(ServiceController):

    service_type = "features"

    def __init__(self, server_url):
        super(featuresController, self).__init__(server_url)
        self.baseurl = server_url
        _mkdir(FEATURES_TABLES_FILE_DIR)
        _mkdir(FEATURES_TEMP_IMAGE_DIR) 
        log.info('importing features')
        self.feature_archieve = Feature_Archieve() #initalizing all the feature classes     
    
    
    ###################################################################
    ### Feature Service Entry Points
    ###################################################################
    @expose()
    def _default(self, *args, **kw):
        """
        Entry point for features calculation and command and feature documentation
        """
        #documentation
        if not args:
            return FeatureDoc().feature_server() #print documentation

        elif len(args)==1 and (request.method!='POST') and not kw:
            return FeatureDoc().feature(args[0],self.feature_archieve)
                    
        #calculating features
        elif len(args)<=2:
            log.debug('Request: %s'%request.method)
            Feature_Request = Request(self.feature_archieve,*args,**kw)
            Feature_Request.proccess()
            return Feature_Request.response()
        
        else: 
            log.debug('Malformed Request: Not a valid uri request')
            abort(400,'Malformed Request: Not a valid uri request')
            
    @expose()        
    def formats(self, *args):
        """
            entry point for format documetation
        """
        if len(args)<1:
            return FeatureDoc().format_list()
        elif len(args)<2:
            return FeatureDoc().format(args[0])
    
    @expose()    
    def list(self):
        """
            entry point for list of features
        """
        return FeatureDoc().feature_list(self.feature_archieve)
    
    def diagnostic(self, *arg, **kw):
        """
            Calls tests suite for feature service
        """
        pass
    
    def local(self):
        """
            Local entry point for feature calculations
        """
        pass
    
    
    

    
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

#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("features")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'features', 'public'))]

__controller__ =  featuresController
