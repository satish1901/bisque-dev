# -*- mode: python -*-
"""Main server for features
"""

__module__ = "features"
__author__ = "Dmitry Fedorov, Kris Kvilekval, Carlos Torres and Chris Wheat"
__version__ = "0.1"
__revision__ = "$Rev$"
__date__ = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os
import io
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
from Feature import type_check
# query is commented out
# querylibraries
# import Query_Library.ANN.ann as ann

log = logging.getLogger("bq.features")

# FUTURE:
#    Key point and region selection with gobjects (may need to api fixes to fit together everything wait on opinions)* everything will be recieving a unique
#    add private and public access (all images must be public)
#    add callback to getting feature requests

# Feature Library maintenance
#    add gist
#    add vignish's features
#    look into nd features

# Research
#    Dynamicly adding new features to the service



# directories
from .var import FEATURES_TABLES_FILE_DIR, FEATURES_TEMP_IMAGE_DIR, EXTRACTOR_DIR, FEATURES_TABLES_WORK_DIR

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
        extractors = [name for module_loader, name, ispkg in pkgutil.iter_modules([EXTRACTOR_DIR]) if ispkg]
        for module in extractors:
            try:
                extractor = importlib.import_module('bq.features.controllers.extractors.' + module + '.extractor')  # the module needs to have a file named
                for n, item in inspect.getmembers(extractor):  # extractor.py to import correctly
                    if inspect.isclass(item) and issubclass(item, Feature.Feature):
                        log.debug('Imported Feature: %s' % item.name)
                        item.library = module
                        self[item.name] = item
            except StandardError, err:  # need to pick a narrower error band but not quite sure right now
                log.exception('Failed Imported Feature: %s\n' % module)  # failed to import feature

    def __missing__(self, feature_type):
        log.debug('feature type:' + feature_type + ' not found')
        abort(404, 'feature type:' + feature_type + ' not found')



class Rows(object):
    """
        Generates rows to be placed into the tables
    """
    def __init__(self, feature):
        self.feature_queue = {}
        self.feature = feature
    
    # def __repr__(self):
    #    return 'Descritpor Generator: Feature: %s List Length: %s'%(self.feature.name, len(feature_list))
    
    def push(self, **resource):
        """
            creates a list to append to the feature table
            if feature calculation was a successs return true 
            otherwise return false
        """
        try:
            log.info('Calculate Feature')
            output = self.feature.calculate(resource)  # finds the feature

            # log.debug('output: %s'% str(self.feature.localfile(output[0][0])))
            if self.feature.localfile(output[0][0]) in self.feature_queue:  # checking the first few element on the hash
                self.feature_queue[self.feature.localfile(output[0][0])].put(output)  # place the output in the queue
            else:
                self.feature_queue[self.feature.localfile(output[0][0])] = Queue.Queue()  # build queue since none were found
                self.feature_queue[self.feature.localfile(output[0][0])].put(output)

            return True
                
        except StandardError, err:
            # creating a list of uri were the error occured
            resource_string = ''
            for r in resource.keys():
                resource_string += r + ' : ' + resource[r] + ', '
            else:
                resource_string = resource_string[:-2]
                
            log.exception('Calculation Error: URI:%s  %s Feature failed to be calculated' % (resource_string, self.feature.name))
            return False



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
        hash = self.feature.returnhash(**resource)  # get hash from features
        log.info('Calculated Hash')
        output = [hash]
        for r in self.feature.resource:
            output += [r + '=' + resource[r]]  # append the uris
        if self.feature.localfile(hash) in self.feature_queue:  # checking the first few element on the hash
            self.feature_queue[self.ID.localfile(output[0][0])].put(output)  # place the output in the queue
        else:
            self.feature_queue[self.ID.localfile(hash)] = Queue.Queue()  # build queue since none were found
            self.feature_queue[self.ID.localfile(hash)].put(output)
            
        return True
    

class UncachedRows(Rows):
    """
        Generates rows to be placed into the uncached tables
    """
    def push(self, **resource):
        """
            creates a list to append to the feature table
            if feature calculation was a successs return true 
            otherwise return false
        """
        try:
            output = self.feature.calculate(resource)
            log.info('Calculated Feature')
            if 'feature' in self.feature_queue:  # feature is used to maintain the structure
                self.feature_queue['feature'].put(output)  # the row is pushed into the queue
            else:  # creates a queue if no queue is found
                self.feature_queue['feature'] = Queue.Queue()
                self.feature_queue['feature'].put(output)
                
            return True
        except StandardError, err:
            # creating a list of uri were the error occured
            resource_string = ''
            for r in resource.keys():
                resource_string += r + ' : ' + resource[r] + ', '
            else:
                resource_string = resource_string[:-2]
                
            log.exception('Calculation Error: %s  %s feature failed to be calculated' % (resource_string, self.feature.name))
            return False


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
        if not os.path.exists(self.feature.path):  # creates a table if it cannot find one
            _mkdir(self.feature.path)

    
    def isin(self, hash):
        """
            queries the table to see if element is in the table
        """
        filename = self.feature.localfile(hash)
        query = 'idnumber=="%s"' % str(hash)
        
        if not os.path.exists(filename):
            self.feature.createtable(filename)  # creates the table
            
        with Locks(filename):
            with tables.openFile(filename, 'r', title=self.feature.name) as h5file:
                table = h5file.root.values
                index = table.getWhereList(query)
        return len(index) > 0
    
    def store(self, rowgenorator):
        """
            store elements to tables
        """
        for filename in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[filename]

            if not os.path.exists(filename):
                self.feature.createtable(filename)  # creates the table
                
            with Locks(None, filename):
                with tables.openFile(filename, 'a', title=self.feature.name) as h5file:
                    table = h5file.root.values
                    
                    while not queue.empty():
                        row = queue.get()
                        query = 'idnumber=="%s"' % str(row[0][0])  # queries the hash to see if a feature has been
                        #log.debug('query: %s' % query)
                        index = table.getWhereList(query)  # appended already
                        if len(index) == 0: 
                            table.append(row)
                    table.flush()
        return
    
    def get(self, hash):
        """
            query for elements and return results
        """
        filename = self.feature.localfile(hash)
        query = 'idnumber=="%s"' % str(hash)
        
        if not os.path.exists(filename):
            self.feature.createtable(filename)  # creates the table
        
        with Locks(filename):
            with tables.openFile(filename, 'r', title=self.feature.name) as h5file:
                table = h5file.root.values
                index = table.getWhereList(query)
                log.debug('index: %s' % str(index))
                if index.size == 0:
                    i = None
                else:
                    i = table[index]
        return i
    
    def copy(self):
        pass
        
    def remove(self):
        pass
    
    def delete(self):
        pass
    
    def __len__(self):
        """
            opens each table in a particular feature directory and sums up the length of all the features
            (note: take a noticable amount of time)
        """
        import glob
        feature_tables = glob.glob(os.path.join(self.feature.path, '*.h5'))
        log.debug('feature table list %s' % str(os.path.join(self.feature.path, '*.h5')))
        l = 0
        for filename in feature_tables:
            with Locks(filename):
                with tables.openFile(filename, 'r', title=self.feature.name) as h5file:
                    l += len(h5file.root.values)
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
        # self.feature = feature
        
        if not os.path.exists(self.ID.path):  # creates a table if it cannot find one
            _mkdir(self.ID.path)


    def isin(self, hash):
        """
            queries the table to see if element is in the table
        """
        # log.debug('hash: %s'%hash)
        filename = self.ID.localfile(hash)
        query = 'idnumber=="%s"' % str(hash)
        
        if not os.path.exists(filename):
            self.ID.createtable(filename)  # creates the table
            
        with Locks(filename):
            with tables.openFile(filename, 'r', title = self.ID.name) as h5file:
                table = h5file.root.values
                index = table.getWhereList(query)
        return len(index) > 0

    def store(self, rowgenorator):
        """
            store elements to tables
        """
        for filename in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[filename]
    
            if not os.path.exists(filename):
                self.ID.createtable(filename)  # creates the table
                
            with Locks(None, filename):
                with tables.openFile(filename, 'a', title=self.ID.name) as h5file:
                    
                    
                    table = h5file.root.values
                    url_vlarray = h5file.root.URI  # finding the variable length array
                    while not queue.empty():
                        row = queue.get()
                        query = 'idnumber=="%s"' % str(row[0])  # queries the hash to see if a feature has been appended already
                        index = table.getWhereList(query)
                        if len(index) == 0:
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
        self.path = os.path.join(FEATURES_TABLES_WORK_DIR, self.element_list.feature.name)
        if not os.path.exists(self.path):  # creates a table if it cannot find one
            _mkdir(self.path)


    def store(self, rowgenorator, filename):
        """
            store row elements to an output table
        """
        for name in rowgenorator.feature_queue.keys():
            queue = rowgenorator.feature_queue[name]

            if not os.path.exists(filename):
                self.feature.outputTable(filename)  # creates the table
            
            # appends elements to the table
            with Locks(None, filename):
                with tables.openFile(filename, 'a', title=self.feature.name) as h5file:
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

class FeatureElements(object):    
    """
        list of all unique elements and their hashes
        sorted by hashes
    """
    
    def __init__(self, feature_archieve, feature_name):
        self.uri_hash_list = []  #list of the resource uris hashed
        self.element_dict = {} #a dictionary with keys as the hash of the resource uris and values as elements
        self.feature_name = feature_name
        self.feature_archieve = feature_archieve
        self.feature = feature_archieve[feature_name]
        
    def hash(self):
        """
            Hashes the list of hashed ordered elements
        """
        hash = ''.join([e[0] for e in self.uri_hash_list])
        hash = uuid.uuid5(uuid.NAMESPACE_URL, hash)
        return hash.hex
    
    def append(self, input_dict):
        """
            appends to element lists and orders the list by hash
            on the first append the types are checked
            
            input_dict : dictionary where the keys are the input types and the values are the uris
        """
        
        # checking type
        if self.uri_hash_list == []:  # check on the first entry
            input_dict, self.feature_name = type_check(input_dict , self.feature_name, self.feature_archieve)  # separates options from resources
            self.feature = self.feature_archieve[self.feature_name]  # reassign new feature
        else:  # check if the types match the original feature
            input_dict, new_feature_name = type_check(input_dict , self.feature_name, self.feature_archieve)  # separates options from resources
            if new_feature_name != self.feature_name:
                log.debug('Argument Error: types are not consistance')
                abort(400, 'Argument Error: types are not consistance')
                             
        if Feature.mex_validation(**input_dict):
            uri_hash = self.feature().returnhash(**input_dict)
            if uri_hash not in self.element_dict:
                self.element_dict[uri_hash] = input_dict
                self.uri_hash_list.append(uri_hash)
                self.uri_hash_list.sort()
        return  # returns options
    
    def remove(self, input_dict):
        """
            Removes the given element from the uri hash list and the element dictionary
        """
        uri_hash = self.feature().returnhash(**input_dict)
        del self.element_dict[uri_hash]
        self.uri_hash_list.remove(uri_hash)
    
    def get(self,hash):
        """ get with hash name """
        if hash in self.uri_hash_list:
            return (hash, self.element_dict[hash])
        else:
            return 
    
    def __getitem__(self, index):
        """ get with index """
        return (self.uri_hash_list[index], self.element_dict[self.uri_hash_list[index]])

    def __len__(self):
        return len(self.uri_hash_list)
    

class Request(object):
    """
        Processes and stores the inputs of a request
    """
    def __init__(self, feature_archieve, feature_request_uri, kw, feature_name, format='xml', operation=None):
        """
        """
        self.feature_request_uri = feature_request_uri
        self.options = {  
                           'callback': None,
                           'limit'   : None,
                           # 'store'   : False,
                           'recalc'  : False,
                         }
        
        # check kw arg values
        for i in kw.keys():
            if i in self.options:
                self.options[i] = kw[i]
                del kw[i] #removes options from the kw list to not interfere with error checking when reading in the resources
                          #kw is a dictionary where the keys are the input types and the values are the uris

        
        # feature assignment
        self.feature_name = feature_name  
        self.ElementList = FeatureElements(feature_archieve, feature_name)
        
        # check if proper format
        self.format = format
        self.Formats = Outputs()[self.format]
        
        # assign inputs
        self.method = request.method
        self.content_type = request.headers['Content-type']

        # validating request
        if self.method == 'POST' and 1 > request.headers['Content-type'].count('xml/text'):
            try:  # parse the resquest
                log.debug('request :%s' % request.body)
                self.body = etree.fromstring(request.body)
                if self.body.tag != 'dataset':
                    abort(400, 'Document Error: Only excepts datasets')
                
                
                # iterating through elements in the dataset parsing and adding to ElementList
                for value in self.body.xpath('value[@type="query"]'):
                    
                    query = value.text
                    query = query.decode("utf8")
                    log.debug('query: %s' % query)
                    query = query.split('&')
                    element = {}
                    for q in query:
                        q = q.split('=')
                        element[q[0]] = q[1].replace('"', '')
                    
                    log.debug('Resource: %s' % element)
                    self.ElementList.append(element)
            except:
                log.exception('Request Error: Xml document is malformed')
                abort(400, 'Xml document is malformed')
                
        elif self.method == 'GET':
            self.body = None
            kw = self.ElementList.append(kw) #kw is a dictionary where the keys are the input types and the values are the uris
        else:
            log.debug('Request Error: http request was not formed correctly')
            abort(400, 'http request was not formed correctly')
        

        

        

    def proccess(self):
        """
            Proccess request provided to the Feature Server
            (main loop of calculating features)
        """
        
        # check work dir for the output
        filename = self.ElementList.hash() + '.h5'
        
        self.filename = os.path.join(self.ElementList.feature.name, filename)
        self.filename = os.path.join(FEATURES_TABLES_WORK_DIR, filename)
        
        #initalizes workdir dir if it doesnt exist
        feature_workdir= os.path.join(FEATURES_TABLES_WORK_DIR, self.ElementList.feature.name)
        if not os.path.exists(feature_workdir):
            _mkdir(feature_workdir)
        
        #checking for cached output in the workdir, if not found starts to calculate features
        if not os.path.exists(self.filename):
            if self.ElementList.feature.cache: #checks if the feature caches

                # finding features
                FeatureTable = Tables(self.ElementList.feature())
                element_list_in_table = []
                
                for i, uri_hash in enumerate(self.ElementList.uri_hash_list):
                    contains_uri_hash = FeatureTable.isin(uri_hash)
                    
                    if contains_uri_hash:
                        log.info("Returning Resource: %s from the feature table"%self.ElementList.element_dict[uri_hash])
                        
                    else:
                        log.info("Resource: %s was not found in the feature table"%self.ElementList.element_dict[uri_hash])
                        
                    element_list_in_table.append(contains_uri_hash) #create a binary list confirming if an element is in the table
                
                # store features
                FeatureRows = Rows(self.ElementList.feature())
                #log.debug('In Feature Table List: %s' % element_list_in_table)
                frozen_uri_hash_list = self.ElementList.uri_hash_list[:]
                for i, element_bool in enumerate(element_list_in_table):
                    if not element_bool:
                        
                        # pushes to the table list unless feature failed to be calculated
                        # then the element is removed from the element list
                        resource_uris_dict = self.ElementList.get(frozen_uri_hash_list[i])[1]
                        
                        #checks to see if the feature calculation succeeded, if error 
                        #then the resource is removed from the element list
                        if not FeatureRows.push(**resource_uris_dict): 
                            self.ElementList.remove(resource_uris_dict)
                            
                FeatureTable.store(FeatureRows) #addes all the features to the h5 tables

                # store in id table after just in case some features fail so their ids are not stored
                HashTable = IDTables()
                
                # finding hashes
                element_list_in_table = []
                for i, uri_hash in enumerate(self.ElementList.uri_hash_list): 
                    contains_uri_hash = FeatureTable.isin(uri_hash)
                    if contains_uri_hash:
                        log.info("Returning Resource: %s from the uri table"%self.ElementList.element_dict[uri_hash])
                    else:
                        log.info("Resource: %s was not found in the uri table"%self.ElementList.element_dict[uri_hash])
                    element_list_in_table.append(contains_uri_hash)
    
                # store hashes
                HashRows = IDRows(self.ElementList.feature())
                #log.debug('In Hash Table List: %s' % element_list_in_table)
                for i, element_bool in enumerate(element_list_in_table):
                    if not element_bool:
                        HashRows.push(**self.ElementList[i][1])
                HashTable.store(HashRows)
    
            else: #creating table for uncached features

                if len(self.ElementList)<1: #if list is empty no table is created
                    FeatureTable = UncachedTable(self.ElementList.feature())
                    
                    
                    # store features in an unindexed table in the workdir
                    FeatureRows = UncachedRows(self.feature())
                    frozen_uri_hash_list = self.ElementList.uri_hash_list[:]
                    for i, uri_hash in enumerate(frozen_uri_hash_list):
                        # pushes to the table list unless feature failed to be calculated
                        # then the element is removed from the element list
                        
                        resource_uris_dict = self.ElementList.get(uri_hash)[1]
                        
                        if not FeatureRows.push(resource_uris_dict):
                            self.ElementList.remove(resource_uris_dict)
                    FeatureTable.store(FeatureRows, self.filename)
        else:
            log.info('Getting request from the workdir')
            
        return
    
    def response(self):
        """
        Builds response
        """
        if len(self.ElementList)<1:
            
            Table = Tables(self.ElementList.feature())
            self.Formats = Outputs()['none'] #return nothing since nothing was found in the element_list
            log.debug('No valid element was found in the element tree') #either a failure to calculate a feature occured or user did not have access to resource
            log.info('Returning with response type as: none')            
            return self.Formats(self.ElementList.feature(),self.feature_request_uri).return_output(Table, self.ElementList)
        
        elif self.ElementList.feature.cache and not os.path.exists(self.filename):  # queries for results in the feature tables
            
            Table = Tables(self.ElementList.feature())
            log.info('Returning with response type as: %s'%self.format)
            return self.Formats(self.ElementList.feature(),self.feature_request_uri).return_output(Table, self.ElementList)
        
        else:  # returns unindexed table from the workdir

            Table = UncachedTable(self.ElementList.feature())
            log.info('Returning with response type as: %s'%self.format)
            return self.Formats(self.ElementList.feature(),self.feature_request_uri).return_from_workdir(Table, self.filename, self.ElementList)

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
    
    def __init__(self, feature, feature_request_uri, **kw):
        self.feature = feature
        self.feature_request_uri = feature_request_uri
    
    def return_output(self, table, element_list, **kw):
        pass
    
    def return_from_workdir(self, table, filename, **kw):
        pass
    

#-------------------------------------------------------------
# Formatters - XML
# MIME types: 
#   text/xml
#-------------------------------------------------------------
class Xml(Format):
    """
        returns in xml
    """
    name = 'XML'
    limit = 1000  # nodes
    description = 'Extensible Markup Language'
    
    def return_output(self, table, element_list, **kw):
        """Drafts the xml output"""
        
        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        nodes = 0
        
        for i, uri_hash in enumerate(element_list.uri_hash_list):
            rows = table.get(uri_hash)
            if rows != None:  # a feature was found for the query
                resource = element_list[i][1]
                    
                for r in rows:
                    subelement = etree.SubElement(element, 'feature' , resource , type=str(self.feature.name))
                    
                    if self.feature.parameter:
                        parameters = {}
                        # creates list of parameters to append to the xml
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name])
                        etree.SubElement(subelement, 'parameters', parameters)
                        
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g' % item for item in r['feature'])  # writes the feature vector to the xml
                    nodes += 1
                    # break out when there are too many nodes
                    if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
                        break
                        
#                else: #the user did not have access to the element the feature is being calculated on
#                    subelement = etree.SubElement( 
#                                              element, 'feature' ,
#                                              resource,
#                                              type = str(self.feature.name),
#                                              error = '403 Forbidden: The current user does not have access to this feature'
#                                          )  
                    if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
                        break                        
            else:  # no feature was found from the query, adds an error message to the xml
                subelement = etree.SubElement(
                                                  element, 'feature' ,
                                                  resource,
                                                  type=str(self.feature.name),
                                                  error='404 Not Found: The feature was not found in the table. Check feature logs for traceback'
                                              )            
            if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
                break

        return etree.tostring(element)

    # not working
    def return_from_workdir(self, table, filename, **kw):
        """Drafts the xml output for uncached tables"""
        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        nodes = 0
        
        with Locks(filename):
            with tables.openFile(filename, 'r', title=self.feature.name) as h5file:  # opens table
                Table = h5file.root.values
                
                # reads through each line in the table and writes an xml node for it
                for i, r in enumerate(Table): 
                    resource = {}  # creating a resource dictionary to story all the uris
                    for res in self.feature.resource:
                        resource[res] = r[res]

                    subelement = etree.SubElement(element, 'feature' , resource, type=str(self.feature.name))
                    
                    if self.feature.parameter:
                        parameters = {}
                        
                        # creates list of parameters to append to the xml node
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name]) 
                        etree.SubElement(subelement, 'parameters', parameters)
                    
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g' % item for item in r['feature'])  # writes the feature vector to the xml
                    nodes += 1
                    
                    # break out when there are too many nodes
                    if nodes > self.limit:
                        break               
                
        return etree.tostring(element)

#-------------------------------------------------------------
# Formatters - CSV 
# MIME types: 
#   text/csv 
#   text/comma-separated-values
#------------------------------------------------------------- 
class Csv(Format):
    """
        returns in csv
    """
    name = 'CSV'
    description = 'Returns csv file format with columns as resource ... | feature | feature attributes...'
    
    def return_output(self, table, element_list, **kw):
        """Drafts the csv output"""
        # # plan to impliment for query and include parameters
        
        import csv
        import StringIO
        f = StringIO.StringIO()
        writer = csv.writer(f)
        resource_names = self.feature.resource
        parameter_names = self.feature.parameter
        
        # creates a title row and writes it to the document
        titles = ['index', 'feature type'] + resource_names + ['descriptor'] + parameter_names
        writer.writerow(titles)
        
        
        for idx, uri_hash in enumerate(element_list.uri_hash_list):
            
            resource = element_list[idx][1]
            
            rows = table.get(uri_hash)
            
            if rows != None:  # check to see if nothing is return from the tables
                
                for r in rows:
                    value_string = ",".join('%g' % i for i in r['feature'])  # parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names] 
                    parameter = []
                    parameter = [r[pn] for pn in parameter_names]
                    line = [idx, self.feature.name] + resource_uri + [value_string] + parameter
                    writer.writerow(line)  # write line to the document
                    
            else:  # if nothing is return from the tables enter Nan into each vector element
                value_string = ",".join(['Nan' for i in range(self.feature.length)])
                resource_uri = [resource[rn] for rn in resource_names]
                line = [idx, self.feature.name] + resource_uri + [value_string]  # appends all the row elements
                writer.writerow(line)  # write line to the document
        
        # creating a file name
        filename = 'feature.csv'  # think of how to name the files
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition  # sets the file name of the csv file
        response.headers['Content-Type'] = 'text/csv'  # setting the browser to save csv file
    
        return f.getvalue()
    
    def return_from_workdir(self, table, filename, **kw):
        """
            returns csv for features without cache
        """
        import csv
        import StringIO
        f = StringIO.StringIO()
        writer = csv.writer(f)
        resource_names = self.feature.resource
        parameter_names = self.feature.parameter
        
        # creates a title row and writes it to the document
        titles = ['index', 'feature type'] + resource_names + ['descriptor'] + parameter_names
        writer.writerow(titles)
        with Locks(filename):
            with tables.openFile(filename, 'r', title=self.feature.name) as h5file:  # opens table
                Table = h5file.root.values  
                for i, r in enumerate(Table):
                    
                    resource = {}  # creating a resource dictionary to story all the uris
                    for res in self.feature.resource:
                        resource[res] = r[res]
                        
                    value_string = ",".join('%g' % i for i in r['feature'])  # parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names]
                    parameter = [r[pn] for pn in parameter_names]
                    line = [idx, self.feature.name] + resource_uri + [value_string] + parameter  # appends all the row elements
                    writer.writerow(line)  # writes line to the document
            
        # creating a file name
        filename = 'feature.csv'  # think of how to name the files
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition  # sets the file name of the csv file
        response.headers['Content-Type'] = 'text/csv'  # setting the browser to save csv file
    
        return f.getvalue()
    
#-------------------------------------------------------------
# Formatters - Binary 
# MIME types: 
#   text 
#------------------------------------------------------------- 
# class Binary(Format):
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


#-------------------------------------------------------------
# Formatters - Hierarchical Data Format 5
# MIME types: 
#   text 
#-------------------------------------------------------------
class Hdf(Format):
    
    name = 'HDF'
    description = 'Returns HDF5 file with columns as resource ... | feature | feature attributes...'
     
    def return_output(self, table, element_list, **kw):
        """
        Returns a newly formed hdf5 table
        
        All HDF files are saved in the work dir of the feature service
        """

        
        # creating a file name
        name = element_list.hash() + '.h5'
        filename = os.path.join(element_list.feature.name, name)
        filename = os.path.join(FEATURES_TABLES_WORK_DIR, filename)
        
        self.feature.outputTable(filename)  # create new table in workdir

        with Locks(None, filename):
            with tables.openFile(filename, 'a', title=self.name) as h5file:  # open table
                # writing to table
                outtable = h5file.root.values
                for i, uri_hash in enumerate(element_list.uri_hash_list):
                    rows = table.get(uri_hash)
                    for r in rows:  # taking rows out of one and placing them into the rows of the output table
                        row = ()
                        for e in self.feature.resource:  # adding input reasource uris
                            row += tuple([element_list[i][1][e]])
                        row += tuple([r['feature']])
                        for p in self.feature.parameter:
                            row += tuple([r[p]])
                            # log.debug('row: %s' % str(row))
                        outtable.append([row]) 
                    outtable.flush()
        
        #
        f = io.FileIO(filename)
        try:
            disposition = 'filename="%s"' % name.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (name.encode('utf8'), name.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition
        response.headers['Content-Type'] = 'application/hdf5'  # setting the browser to save hdf5 file
        return f.read()
    
    
    def return_from_workdir(self, table, filename, **kw):
        # since the uncached table is already saved in the workdir the file is just
        # returned
        f = io.FileIO(filename)
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8')) 
            
        response.headers['Content-Disposition'] = disposition
        response.headers['Content-Type'] = 'application/hdf5'  # setting the browser to save hdf5 file
        return f.read()              
     
#-------------------------------------------------------------
# Formatters - No Ouptut 
# MIME types: 
#   text/xml
#-------------------------------------------------------------
class NoOutput(Format):
    name = 'No Output'
    
  
# class Numpy(Format):
#    def __init__(self, *args, **kw):
#        pass
#    
#    def return_output(self):
#        pass
#
#

#-------------------------------------------------------------
# Formatters - Local Path
# MIME types: 
#   text/xml
#-------------------------------------------------------------
class LocalPath(Format):
    """
        
    """

    name = 'localpath'
    description = 'Returns location of the file along with the location of the feature in the table'
    
    def return_output(self, table, element_list, **kw):
        """
            
        """

        response.headers['Content-Type'] = 'text/xml'
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        file_path = {}
        for i, uri_hash in enumerate(element_list.uri_hash_list):
            local_file = self.feature.localfile(uri_hash)
            if local_file not in file_path :
                file_path[local_file] = etree.SubElement(element, 'hdf', src='file:'+local_file)
            
            etree.SubElement(file_path[local_file],'row', idnumber=uri_hash)
                       
        return etree.tostring( element)


    def return_from_workdir(self, table, filename, **kw):
        """
        Reading hdf5 from wordir and returning it in the 
        local path format
        """
        element_list = kw['element_list']
        response.headers['Content-Type'] = 'text/xml' 
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        file_paths = {}
        for i, uri_hash in enumerate( element_list.uri_hash_list):
            local_file = self.feature.localfile( uri_hash)
            if local_file not in file_path :
                file_path[local_file] = etree.SubElement(element, 'hdf', src='file:'+local_file)
            
            etree.SubElement( file_path[local_file], 'row', idnumber = uri_hash)
                       
        return etree.tostring( element)
   

class Outputs(dict):
    """
        Reads the hdf5 tables and returns features in 
        correct format
    """
    def __init__(self):
        self['xml'] = Xml
        self['csv'] = Csv
        # self['bin'] = Binary
        self['hdf'] = Hdf
        self['none'] = NoOutput
        self['localpath'] = LocalPath
    
    def __missing__(self, format):
        log.debug('format type: ' + format + ' not found')
        abort(404, 'Format type: %s not found' % format)  # if element type is not found
    

###################################################################
# ##  Documentation
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
        resource = etree.Element('resource', uri=str(request.url))
        command = etree.SubElement(resource, 'command', name='/*feature name*', type='string', value='Documentation of specific feature')
        command = etree.SubElement(resource, 'command', name='/list', type='string', value='List of features')
        command = etree.SubElement(resource, 'command', name='/format', type='string', value='List of formats')
        command = etree.SubElement(resource, 'command', name='/format/*format name*', type='string', value='Documentation of specific format')
        command = etree.SubElement(resource, 'command', name='/*feature name*?uri=http://...', type='string', value='Returns feature in format set to xml')
        command = etree.SubElement(resource, 'command', name='/*feature name*/*format name*?*resource type*=http://...(&*resource type*=http://...)', type='string', value='Returns feature in format specified')
        command = etree.SubElement(resource, 'attribute', name='resource', value='The name of the resource depends on the requested feature')
        return etree.tostring(resource)


    def feature_list(self, feature_archieve):
        """
            Returns xml of given feature
        """
        response.headers['Content-Type'] = 'text/xml' 
        resource = etree.Element('resource', uri=str(request.url))  # self.baseurl+'/doc')
        resource.attrib['description'] = 'List of working feature extractors'
        feature_library = {}
        for featuretype in feature_archieve.keys():
            feature_module = feature_archieve[featuretype]
            # log.debug('feature_module: %s'%feature_module.child_feature)
            
            if feature_module.library not in feature_library:
                feature_library[feature_module.library] = etree.SubElement(resource, 'library', name=feature_module.library)
                
            # if feature_modele.parent_feature 
            
            feature = etree.SubElement(
                                      feature_library[feature_module.library],
                                      'feature',
                                      name=featuretype,
                                      permission="Published",
                                      uri='features/list/' + featuretype 
                                    )
            
        return etree.tostring(resource)

       
    def feature(self, feature_name, feature_archieve):
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
                          #'table_length':str(len(Table)) this request takes a very long time in the current state
                         }
        if len(feature_module.parameter) > 0:
            xml_attributes['parameters'] = ','.join(feature_module.parameter)
         
        resource = etree.Element('resource', uri=str(request.url))
        feature = etree.SubElement(resource, 'feature', name=str(feature_module.name))
        for key, value in xml_attributes.iteritems():
            attrib = {key:value}
            info = etree.SubElement(feature, 'info', **attrib)
        return etree.tostring(resource)
    

        return etree.tostring(resource)
    
    def format_list(self):
        """
            Returns List of Formats
        """
        response.headers['Content-Type'] = 'text/xml' 
        resource = etree.Element('resource', uri=str(request.url))
        resource.attrib['description'] = 'List of Return Formats'
        format_archieve = Outputs()
        log.debug('format_achieve: %s' % format_archieve)
        for format_name in format_archieve.keys():
            format = format_archieve[format_name]
            feature = etree.SubElement(resource,
                                      'format',
                                      name=format_name,
                                      permission="Published",
                                      uri='format/' + format_name)
        response.headers['Content-Type'] = 'text/xml' 
        return etree.tostring(resource)

    def format(self, format_name):
        """
            Returns documentation about format
        """
        response.headers['Content-Type'] = 'text/xml'
        format_archieve = Outputs()
        format = format_archieve[format_name]
         
        xml_attributes = {
                          'Name':str(format.name),
                          'Description':str(format.description),
                          'Limit':str(format.limit)
                          }
         
        resource = etree.Element('resource', uri=str(request.url))
        feature = etree.SubElement(resource, 'format', name=str(format.name))
        for key, value in xml_attributes.iteritems():
            attrib = {key:value}
            info = etree.SubElement(feature, 'info', attrib)
        return etree.tostring(resource)
        
###################################################################
# ## Feature Service Controller
###################################################################

class featuresController(ServiceController):

    service_type = "features"

    def __init__(self, server_url):
        super(featuresController, self).__init__(server_url)
        self.baseurl = server_url
        _mkdir(FEATURES_TABLES_FILE_DIR)
        _mkdir(FEATURES_TEMP_IMAGE_DIR)
        log.info('importing features')

        self.feature_archieve = Feature_Archieve()  # initalizing all the feature classes     
        
    
    ###################################################################
    # ## Feature Service Entry Points
    ###################################################################
    @expose(content_type='text/xml')
    def _default(self, *args, **kw):
        """
        Entry point for features calculation and command and feature documentation
        """
        # documentation
        if not args:
            return FeatureDoc().feature_server()  #print documentation

        elif len(args) == 1 and (request.method != 'POST') and not kw:
            return FeatureDoc().feature(args[0], self.feature_archieve)
                    
        # calculating features
        elif len(args) <= 2:
            Feature_Request = Request(self.feature_archieve, request.url, kw, *args)
            Feature_Request.proccess()
            output = Feature_Request.response()

            log.debug('Content-Type: %s' % str(response.headers['Content-Type']))
            return output
        
        else: 
            log.debug('Malformed Request: Not a valid features request')
            abort(400, 'Malformed Request: Not a valid features request')
            
    @expose()
    def formats(self, *args):
        """
            entry point for format documetation
        """
        if len(args) < 1:
            return FeatureDoc().format_list()
        elif len(args) < 2:
            return FeatureDoc().format(args[0])
        else:
            log.debug('Malformed Request: Not a valid features request')
            abort(400, 'Malformed Request: Not a valid features request')            
    
    @expose(content_type='text/xml')   
    def list(self):
        """
            entry point for list of features
        """
        return FeatureDoc().feature_list(self.feature_archieve)
    
#    def diagnostic(self, *arg, **kw):
#        """
#            Calls tests suite for feature service
#        """
#        pass
    
    def local(self):
        """
            Local entry point for feature calculations
        """
        pass
    
    
    

    
#######################################################################
# ## Initializing Service
#######################################################################    

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.info ("initialize " + uri)
    service = featuresController(uri)
    # directory.register_service ('features', service)

    return service

# def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("features")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'features', 'public'))]

__controller__ = featuresController
