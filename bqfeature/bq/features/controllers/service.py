# -*- mode: python -*-
"""Main server for features
"""

__author__ = "Dmitry Fedorov, Kris Kvilekval, Carlos Torres and Chris Wheat"
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
import urllib2
import hashlib

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
from bq.features.controllers.Feature import BaseFeature
# query is commented out
# querylibraries
# import Query_Library.ANN.ann as ann

log = logging.getLogger("bq.features")

# FUTURE:
#    Key point and region selection with gobjects (may need to api fixes to fit together everything wait on opinions)* everything will be recieving a unique
#    add callback to getting feature requests

# Feature Library maintenance
#    add gist
#    add vignish's features
#    look into nd features

# Research
#    Dynamicly adding new features to the service



# directories
from .var import FEATURES_TABLES_FILE_DIR, FEATURES_TEMP_IMAGE_DIR, EXTRACTOR_DIR, FEATURES_TABLES_WORK_DIR


class FeatureExtractionError(Exception):

    def __init__(self, resources, error_code=500, error_message='Internal Server Error'):
        self.error_code = error_code
        self.error_message = error_message
        self.resources = resources


class FeatureServiceError(Exception):
    
    def __init__(self, error_code=500, error_message='Internal Server Error'):
        self.error_code = error_code
        self.error_message = error_message


class Feature_Archive(dict):
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
                    if inspect.isclass(item) and issubclass(item, BaseFeature):
                        log.debug('Imported Feature: %s' % item.name)
                        item.library = module #for the list of features
                        self[item.name] = item
            except StandardError, err:  # need to pick a narrower error band but not quite sure right now
                log.exception('Failed Imported Feature: %s\n' % module)  # failed to import feature

#    def __missing__(self, feature_type):
#        log.debug('feature type:' + feature_type + ' not found')
#        abort(404, 'feature type:' + feature_type + ' not found')


FEATURE_ARCHIVE = Feature_Archive()


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
            raise FeatureExtractionError(resource,500,'Calculation Error: URI:[ %s ]  Feature failed to be calculated'%resource_string)
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
            raise FeatureExtractionError(resource,500,'Calculation Error: URI:[ %s ]  Feature failed to be calculated'%resource_string)

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
                        if len(index) < 1:
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
        """
            remove rows
        """
        pass

    def delete(self):
        """
            delete tables
        """
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
        self.path = os.path.join(FEATURES_TABLES_WORK_DIR, self.feature.name)
        if not os.path.exists(self.path):  # creates a table if it cannot find one
            _mkdir(self.path)


    def store(self, rowgenorator, filename):
        """
            store row elements to an output table
        """
        queue = rowgenorator.feature_queue['feature']

        if not os.path.exists(filename):
            log.info('Writing hdf file into workdir: %s'%filename)
            self.feature.outputTable(filename)  # creates the table
        else:
            FeatureServiceError(500,'File already exists in workdir: %s'%filename)

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

class ResourceList(object):
    """
        list of all unique elements and their hashes
        sorted by hashes
    """

    def __init__(self, feature_request_uri, feature_name, format_name , **kw):
        self.uri_hash_list = []  #list of the resource uris hashed
        self.element_dict = {} #a dictionary with keys as the hash of the resource uris and values as elements
        self.error_list = []
        #self.feature_name = feature_name
        #self.feature_archive = feature_archive

        try:
            self.format = FORMAT_DICT[format_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Format: %s  was not found'%format_name)

        try:
            self.feature = FEATURE_ARCHIVE[feature_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Feature: %s requested was not found'%feature_name)
            
        self.feature_request_uri = feature_request_uri
        
        if 'options' in kw:
            self.options=kw['options']
        else:
            self.options = {}
    
    def workdir_filename(self):
        """
            Returns resource name for the workdir which is an ordered
            list of all the element hashes 
        """
        return os.path.join(FEATURES_TABLES_WORK_DIR,self.feature.name, self.hash() + '.h5' )     
    
    def hash(self):
        """
            Hashes the list of hashed ordered elements
        """
        hash = hashlib.md5()
        for e in self.uri_hash_list:
            hash.update(e)
        return hash.hexdigest()

    def append(self, input_dict):
        """
            appends to element lists and orders the list by hash
            on the first append the types are checked

            input_dict : dictionary where the keys are the input types and the values are the uris
        """
        # checking type
        if not self.uri_hash_list:  # check on the first entry
            input_dict, self.feature_name = input_resource_check(input_dict , self.feature.name)  # separates options from resources
            self.feature = FEATURE_ARCHIVE[self.feature_name]  # reassign new feature
        else:  # check if the types match the original feature
            input_dict, new_feature_name = input_resource_check(input_dict , self.feature.name)  # separates options from resources
            if new_feature_name != self.feature_name:
                log.debug('Argument Error: types are not consistance')
                raise FeatureServiceError(400, 'Argument Error: types are not consistance')
                #abort(400, 'Argument Error: types are not consistance')

        #check if user has access to resource
        if Feature.mex_validation(**input_dict):
            uri_hash = self.feature().returnhash(**input_dict)
            if uri_hash not in self.element_dict:
                self.element_dict[uri_hash] = input_dict
                self.uri_hash_list.append(uri_hash)
                self.uri_hash_list.sort()
                
        #add it to a list of element with errors
        else:
            self.error_list.append(FeatureExtractionError(403, 'User is not authorized to read resource internally: %s', input_dict))
            
        return  # returns options

    def remove(self, input_dict, exc):
        """
            Removes the given element from the uri hash list and the element dictionary 
            and place them in the error list
        """
        uri_hash = self.feature().returnhash(**input_dict)
        del self.element_dict[uri_hash]
        self.uri_hash_list.remove(uri_hash)
        self.error_list.append(exc)
        

    def get(self,hash):
        """ get with hash name, if it doesnt find anything it returns nothing"""
        if hash in self.uri_hash_list:
            return (hash, self.element_dict[hash])
        else:
            return

    def __getitem__(self, index):
        """ get with index """
        return (self.uri_hash_list[index], self.element_dict[self.uri_hash_list[index]])

    def __len__(self):
        return len(self.uri_hash_list)
    
    def __iter__(self): 
        #TODO: make a better iter function
        return iter(self.uri_hash_list)
    
    def error_list(self):
        return error_list


def input_resource_check( resources, feature_name):
    """
        Checks resource type of the input to make sure
        the correct resources have been used, if it can
        find an alternative feature with those inputs
        it will output the name of the new suggested feature
    """
    resource = {}
    feature = FEATURE_ARCHIVE[feature_name]
    if sorted(resources.keys()) == sorted(feature.resource):
        feature_name = feature.name
    else:
        for cf in feature.child_feature:
            if sorted(resources.keys()) == sorted(FEATURE_ARCHIVE[cf].resource):
                log.debug('Reassigning from %s to %s'%(feature_name,cf))
                feature_name = cf
                feature = FEATURE_ARCHIVE[feature_name]
                break
        else:
            log.debug('Argument Error: No resource type(s) that matched the feature')
            raise FeatureServiceError(400, 'Argument Error: No resource type(s) that match the feature')
            #abort(400,'Argument Error: No resource type(s) that matched the feature')

    for resource_name in resources.keys():

        if resource_name not in feature.resource:

            log.debug('Argument Error: %s type was not found'%resource_name)
            raise FeatureServiceError(400, 'Argument Error: %s type was not found'%resource_name)
            #abort(400,'Argument Error: %s type was not found'%resource_name)

        elif type(resources[resource_name]) == list: #to take care of when elements have more then uri attached. not allowed in the features
              #server for now

            log.debug('Argument Error: %s type was found to have more then one URI'%resource_name)
            #abort(400,'Argument Error: %s type was found to have more then one URI'%resource_name)
            raise FeatureServiceError(400,'Argument Error: %s type was found to have more then one URI'%resource_name)
        else:

            resource[resource_name] = urllib2.unquote(resources[resource_name]) #decode url

    return resource ,feature_name


def parse_request(feature_request_uri, feature_name, format_name='xml', method='GET', **kw):
    """
        Parses request and returns a ResourceList
    """
    options = {
                   'callback': None,
                   'limit'   : None,
                   # 'store'   : False,
                   'recalc'  : False,
                }

    # check kw arg values
    for i in kw.keys():
        if i in options: 
            options[i] = kw[i]
            del kw[i] #removes options from the kw list to not interfere with error checking when reading in the resources
                      #kw is a dictionary where the keys are the input types and the values are the uris
    
    resource_list = ResourceList( feature_request_uri, feature_name, format_name, options=options )

    # validating request
    if method == 'POST' and 1 > request.headers['Content-type'].count('xml/text'):
        try:  # parse the resquest
            log.debug('request :%s' % request.body)
            body = etree.fromstring(request.body)
            if body.tag != 'dataset':
                raise FeatureServiceError(400,'Document Error: Only excepts datasets')
                #abort(400, 'Document Error: Only excepts datasets')


            # iterating through elements in the dataset parsing and adding to ElementList
            for value in body.xpath('value[@type="query"]'):
                query = value.text
                query = query.decode("utf8")
                log.debug('query: %s' % query)
                query = query.split('&')
                element = {}
                
                for q in query:
                    q = q.split('=')
                    element[q[0]] = q[1].replace('"', '')

                log.debug('Resource: %s' % element)
                resource_list.append(element)
        except:
            log.exception('Request Error: Xml document is malformed')
            raise FeatureServiceError(400, 'Xml document is malformed')

    elif method == 'GET':
        kw = resource_list.append(kw) #kw is a dictionary where the keys are the input types and the values are the uris
        
    else:
        log.debug('Request Error: http request was not formed correctly')
        raise FeatureServiceError(400, 'http request was not formed correctly')

    return resource_list


def opertions(resource_list):
    """
        calculates features and stores them in the tables
    """
    # check work dir for the output
    workdir_filename = resource_list.workdir_filename()
    
    #initalizes workdir dir if it doesnt exist
    feature_workdir = os.path.join(FEATURES_TABLES_WORK_DIR, resource_list.feature.name)
    if not os.path.exists(feature_workdir):
        _mkdir(feature_workdir)
    
    #checking for cached output in the workdir, if not found starts to calculate features
    if not os.path.exists(workdir_filename):
        if resource_list.feature.cache: #checks if the feature caches

            # finding if features are in the tables
            feature_table = Tables(resource_list.feature())
            feature_rows = Rows(resource_list.feature())
            
            element_list_in_table = []
            for i, uri_hash in enumerate(resource_list):
                if feature_table.isin(uri_hash):
                    log.info("Returning Resource: %s from the feature table"%resource_list.element_dict[uri_hash])

                else:
                    log.info("Resource: %s was not found in the feature table"%resource_list.element_dict[uri_hash])
                    resource_uris_dict = resource_list.get(uri_hash)[1]
                    
                    #checks to see if the feature calculation succeeded, if error
                    #then the resource is removed from the element list
                    try:
                        feature_rows.push(**resource_uris_dict)
                    except FeatureExtractionError as feature_extractor_error: #if error occured the element is moved for the resource list to the error list
                        resource_list.remove(resource_uris_dict,feature_extractor_error)

            # store features
            feature_table.store(feature_rows)

            # store in id table after just in case some features fail so their ids are not stored
            hash_table = IDTables()
            hash_row = IDRows(resource_list.feature())
            
            # finding hashes
            element_list_in_table = []
            for i, uri_hash in enumerate(resource_list):
                if hash_table.isin(uri_hash):
                    log.info("Returning Resource: %s from the uri table"%resource_list.element_dict[uri_hash])
                    
                else:
                    log.info("Resource: %s was not found in the uri table"%resource_list.element_dict[uri_hash])
                    hash_row.push(**resource_list.get(uri_hash)[1])

            # store hashes
            hash_table.store(hash_row)

        else: #creating table for uncached features
            log.info('Calculating on uncached feature')

            if len(resource_list)>0: #if list is empty no table is created
                uncached_feature_table = UncachedTable(resource_list.feature())


                # store features in an unindexed table in the workdir
                uncached_feature_rows = UncachedRows(resource_list.feature())

                for i, uri_hash in enumerate(resource_list):
                    # pushes to the table list unless feature failed to be calculated
                    # then the element is removed from the element list
                    resource_uris_dict = resource_list.get(uri_hash)[1]
                    try:
                        uncached_feature_rows.push(**resource_uris_dict)
                    except FeatureExtractionError as feature_extractor_error: #if error occured the element is moved for the resource list to the error list
                        resource_list.remove(resource_uris_dict,feature_extractor_error)
                
                workdir_filename = resource_list.workdir_filename() #just in case some features failed
                uncached_feature_table.store(uncached_feature_rows, workdir_filename)
    else:
        log.info('Getting request from the workdir at: %s'% workdir_filename)



def format_response(resource_list):
    """
        reads features from the tables and froms a response
    """

    if resource_list.feature.cache and not os.path.exists(resource_list.workdir_filename()):  # queries for results in the feature tables

        feature_table = Tables(resource_list.feature())
        log.info('Returning with response type as: %s'%resource_list.format.name)
        return resource_list.format(resource_list.feature(),resource_list.feature_request_uri).return_from_tables(feature_table, resource_list)

    else:  #returns unindexed table from the workdir

        uncached_feature_table = UncachedTable(resource_list.feature())
        log.info('Returning with response type as: %s'%resource_list.format.name)
        return resource_list.format(resource_list.feature(),resource_list.feature_request_uri).return_from_workdir(uncached_feature_table, resource_list.workdir_filename())




###############################################################
# Features Outputs
###############################################################

class Format(object):
    """
        Base Class of formats for output
    """
    name = 'Format'
    #limit = 'Unlimited'
    description = 'Discription of the Format'
    content_type = 'text/xml'

    def __init__(self, feature, feature_request_uri, **kw):
        self.feature = feature
        self.feature_request_uri = feature_request_uri

    def return_from_tables(self, table, element_list, **kw):
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
    #limit = 1000  # nodes
    description = 'Extensible Markup Language'
    content_type = 'text/xml'

    def return_from_tables(self, table, resource_list, **kw):
        """Drafts the xml output"""
        
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        nodes = 0

        for i, uri_hash in enumerate(resource_list):
            rows = table.get(uri_hash)
            if rows != None:  # a feature was found for the query
                resource = resource_list[i][1]

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
#                    if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
#                        break

#                else: #the user did not have access to the element the feature is being calculated on
#                    subelement = etree.SubElement(
#                                              element, 'feature' ,
#                                              resource,
#                                              type = str(self.feature.name),
#                                              error = '403 Forbidden: The current user does not have access to this feature'
#                                          )
#                    if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
#                        break
            else:  # no feature was found from the query, adds an error message to the xml
                subelement = etree.SubElement(
                                                  element, 'feature' ,
                                                  resource,
                                                  type=str(self.feature.name),
                                                  error='404 Not Found: The feature was not found in the table. Check feature logs for traceback'
                                              )
                
                
            #read through errors
            for i, errors in enumerate(resource_list.error_list):
                subelement = etree.SubElement(
                                                  element, 'feature' ,
                                                  errors.resource,
                                                  type=str(self.feature.name),
                                                  error=errors.error_message
                                              )                
#            if nodes > self.limit:  # checks to see if the number of lines has surpassed the limit
#                break
            
        header = {'content-type': self.content_type}    
        return header, etree.tostring(element)

    # not working
    def return_from_workdir(self, table, filename, **kw):
        """Drafts the xml output for uncached tables"""
        
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

#                    # break out when there are too many nodes
#                    if nodes > self.limit:
#                        break
                    
        header = {'content-type': self.content_type}
        return  header, etree.tostring(element)

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
    content_type = 'text/csv'


    def return_from_tables(self, table, element_list, **kw):
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

        
        header = {
                  'content-type': self.content_type,
                  'Content-Disposition':disposition
                  }
        return header, f.getvalue()

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
                for idx, r in enumerate(Table):

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


        header = {
                  'content-type': self.content_type,
                  'Content-Disposition':disposition    # sets the file name of the csv file
                  }
        return header, f.getvalue()

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
    content_type = 'application/hdf5'

    def return_from_tables(self, table, element_list, **kw):
        """
        Returns a newly formed hdf5 table
        All HDF files are saved in the work dir of the feature service
        """


        # creating a file name
        filename = element_list.workdir_filename()
        path = os.path.join(FEATURES_TABLES_WORK_DIR,element_list.feature.name, filename)

        element_list.feature().outputTable(path)  # create new table in workdir

        with Locks(None, path):
            with tables.openFile(filename, 'a', title=self.name) as h5file:  # open table
                # writing to table
                out_table = h5file.root.values
                for i, uri_hash in enumerate(element_list.uri_hash_list):
                    rows = table.get(uri_hash)
                    for r in rows:  # taking rows out of one and placing them into the rows of the output table
                        row = ()
                        for e in self.feature.resource:  # adding input reasource uris
                            row += tuple([element_list[i][1][e]])
                        row += tuple([element_list.feature.name])
                        row += tuple([r['feature']])
                        for p in self.feature.parameter:
                            row += tuple([r[p]])
                            # log.debug('row: %s' % str(row))
                        out_table.append([row])
                    out_table.flush()

        #convert file to a stream
        f = io.FileIO(path)
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8'))

        header = {
                  'content-type': self.content_type,
                  'Content-Disposition':disposition    # sets the file name of the csv file
                  }
        return header,f.read()


    def return_from_workdir(self, table, filename, **kw):
        # since the uncached table is already saved in the workdir the file is just
        # returned
        f = io.FileIO(filename)
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8'))

        header = {
                  'content-type': self.content_type,
                  'Content-Disposition':disposition    # sets the file name of the csv file
                  }
        return header,f.read()

#-------------------------------------------------------------
# Formatters - No Ouptut
# MIME types:
#   text/xml
#-------------------------------------------------------------
class NoOutput(Format):
    name = 'No Output'


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
    content_type = 'text/xml'

    def return_from_tables(self, table, element_list, **kw):
        """
        """
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        file_path = {}
        for i, uri_hash in enumerate(element_list.uri_hash_list):
            local_file = self.feature.localfile(uri_hash)
            if local_file not in file_path :
                file_path[local_file] = etree.SubElement(element, 'hdf', src='file:'+local_file)

            etree.SubElement(file_path[local_file],'row', idnumber=uri_hash)

        header = {'content-type': self.content_type}
        return  header, etree.tostring(element)


    def return_from_workdir(self, table, filename, **kw):
        """
        Reading hdf5 from wordir and returning it in the
        local path format
        """
        element_list = kw['element_list']
        element = etree.Element('resource', uri=str(self.feature_request_uri))
        file_paths = {}
        for i, uri_hash in enumerate( element_list.uri_hash_list):
            local_file = self.feature.localfile( uri_hash)
            if local_file not in file_path :
                file_path[local_file] = etree.SubElement(element, 'hdf', src='file:'+local_file)

            etree.SubElement( file_path[local_file], 'row', idnumber = uri_hash)

        header = {'content-type': self.content_type}
        return  header, etree.tostring(element)

#-------------------------------------------------------------
# Formatters - Numpy
# Only for internal use
#-------------------------------------------------------------
class ReturnNumpy(Format):
    """
    """
    name = 'numpy'
    description = 'Returns numpy arrays for features'
    content_type = ''    
    def return_from_tables(self, table, element_list, **kw):
        pass
    
    def return_from_workdir(self, table, filename, **kw):
        pass


#
FORMAT_DICT = {
    'xml'      : Xml,
    'csv'      : Csv,
    'hdf'      : Hdf,
    'none'     : NoOutput,
    'localpath': LocalPath
}


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


    def feature_list(self):
        """
            Returns xml of given feature
        """
        #response.headers['Content-Type'] = 'text/xml'
        resource = etree.Element('resource', uri=str(request.url))  # self.baseurl+'/doc')
        resource.attrib['description'] = 'List of working feature extractors'
        feature_library = {}
        for featuretype in FEATURE_ARCHIVE.keys():
            feature_module = FEATURE_ARCHIVE[featuretype]
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


    def feature(self, feature_name):
        """
            Returns xml of information about the features
        """
        #response.headers['Content-Type'] = 'text/xml'
        try:
            feature_module = FEATURE_ARCHIVE[feature_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Feature: %s requested was not found'%feature_name)
        
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
        #response.headers['Content-Type'] = 'text/xml'
        resource = etree.Element('resource', uri=str(request.url))
        resource.attrib['description'] = 'List of Return Formats'
        #log.debug('format_achieve: %s' % FORMAT_DICT)
        for format_name in FORMAT_DICT.keys():
            format = FORMAT_DICT[format_name]
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
        #response.headers['Content-Type'] = 'text/xml'
        try:
            format = FORMAT_DICT[format_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Format: %s  was not found'%format_name)        

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

        self.docs = FeatureDoc()


    ###################################################################
    # ## Feature Service Entry Points
    ###################################################################
    @expose()
    def _default(self, *args, **kw):
        """
        Entry point for features calculation and command and feature documentation
        """
        # documentation
        if not args:
            body = self.docs.feature_server()  #print documentation
            header = {'Content-Type':'text/xml'}
#            content_type = 'text/xml'

        elif len(args) == 1 and (request.method != 'POST') and not kw:
            try:
                body = self.docs.feature(args[0])
                header = {'Content-Type':'text/xml'}
            except FeatureServiceError as e:
                abort(e.error_code, e.error_message)
#            content_type = 'text/xml'

        # calculating features
        elif len(args) <= 2:
            try:
                resource_list = parse_request( request.url, args[0], args[1], request.method, **kw)
                opertions( resource_list)
                header, body = format_response( resource_list)
                #resource_list = Request(request.url, kw, *args)
                #Feature_Request.proccess()
                #output = Feature_Request.response()
            except FeatureServiceError as e:
                abort(e.error_code, e.error_message)

        else:
            log.debug('Malformed Request: Not a valid features request')
            abort(400, 'Malformed Request: Not a valid features request')
        
        
        response.headers.update(header)
        log.debug('Content-Type: %s' % str(response.headers.get ('Content-Type', '')))
        return body

    @expose()
    def formats(self, *args):
        """
            entry point for format documetation
        """
        if len(args) < 1:
            body = self.docs.format_list()
            header = {'Content-Type':'text/xml'}
            
        elif len(args) < 2:
            try:
                body = self.docs.format(args[0])
                header = {'Content-Type':'text/xml'}
            except FeatureServiceError as e:
                abort(e.error_code, e.error_message)            
        else:
            log.debug('Malformed Request: Not a valid features request')
            abort(400, 'Malformed Request: Not a valid features request')
            
        response.headers.update(header)
        return body

    @expose()#content_type='text/xml')
    def list(self):
        """
            entry point for list of features
        """
        header = {'Content-Type':'text/xml'}
        response.headers.update(header)
        return self.docs.feature_list()




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
