#!/usr/bin/python 

""" Feature service testing framework
"""

__module__    = "run_tests"
__author__    = "Dmitry Fedorov & Chris Wheat"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


import sys
if sys.version_info  < ( 2, 7 ):
    import unittest2 as unittest
else:
    import unittest

from lxml import etree
import getpass
import argparse
import time
import posixpath
import ConfigParser
import os
from subprocess import Popen, call, PIPE
import ntpath
import logging as log

#from bq.api.bqclass import fromXml # bisque
#from bq.api.comm import BQSession, BQCommError # bisque
#from bq.api.util import save_blob # bisque
from bqapi.bqclass import fromXml # local
from bqapi.comm import BQSession, BQCommError # local
from bqapi.util import save_blob # local

import time 
import pdb
#clearing logs
with open('test.log', 'w'):
    pass

log.basicConfig(filename='test.log',level=log.DEBUG)


FEATURES = 'features'

url_file_store       = 'http://hammer.ece.ucsb.edu/~bisque/test_data/images/' 
local_store_images   = 'images'
local_features_store = 'features'
local_store_tests    = 'tests'

service_data         = 'data_service'
service_image        = 'image_service'
resource_image       = 'image'
features             = 'features'

#imported files
bisque_archive_1     = 'image_08093.tar'
mask_1               = 'mask_8093.jpg'
bisque_archive_2     = 'image_08089.tar'
mask_2               = 'mask_8089.jpg'
bisque_archive_3     = 'image_08069.tar'
mask_3               = 'mask_8069.jpg'
bisque_archive_4     = 'image_08043.tar'
mask_4               = 'mask_8043.jpg'



###############################################################
# response check
###############################################################
        
class TestStatus():
    """
        Constructs full error message for unittest
    """
    def __init__(self):
        self.error_messages = []
        
    def not_equal(self,log_message):
        log.info(log_message)
        self.error_messages.append(log_message)
        
    def equal(self,log_message):
        log.info(log_message)
        
    def return_error(self):
        error_messages = ''
        if len(self.error_messages)>1:
            for em in self.error_messages:
                error_messages =  '%s; Check log for the full list'%str(em)
                raise ResponseCheckError(error_messages)
            
        elif len(self.error_messages)==1:
            for em in self.error_messages:
                error_messages =  '%s'%str(em)            
                raise ResponseCheckError(error_messages)                

        else:
            #no errors listed
            return


class ResponseCheckError(Exception):
    """
    """
    def __init__(self, value):
        self.value = value
    def __str__(self): 
        return repr(self.value)        


##################################################################
# FeatureServiceTestBase
##################################################################
class FeatureServiceTestBase(unittest.TestCase):
    """
        Test feature service operations
    """
    
#test_type_bool = True
    time_trial = False

#test initalization
    @classmethod
    def ensure_bisque_file(self, filename,achieve=False, local_dir='.'):
        """
            Checks for test files stored locally
            If not found fetches the files from a store
        """
        path = self.fetch_file(filename,local_dir)
        if achieve:
            return self.upload_achieve_file(path)
        else:
            return self.upload_new_file(path)
    
    @classmethod
    def fetch_file(self, filename, local_dir='.'):
        """
            fetches files from a store as keeps them locally
        """
        url = posixpath.join(url_file_store, filename)
        path = os.path.join(local_dir, filename)
        if not os.path.exists(path):
            urllib.urlretrieve(url, path)
        return path

    @classmethod
    def upload_new_file(self, path):
        """
            uploads files to bisque server
        """
        r = save_blob(self.session,  path)
        print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
        return r

    @classmethod    
    def upload_achieve_file(self, path):
        """
            upload bisque archive files
        """
        filename = ntpath.basename(path)
        resource = etree.Element('resource', image = filename)
        tag = etree.SubElement(resource,'tag', name = 'ingest')
        etree.SubElement(tag,'tag', name = 'type', value = 'zip-bisque')
        r = save_blob(self.session,  path, resource = resource)
        print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
        return r

    @classmethod
    def return_archive_info(self, bisque_archive, mask):
        bisque_archive_data_xml_top    = self.ensure_bisque_file(bisque_archive,achieve=True,local_dir=local_store_images)
        bisque_archive_image_uri       = self.root+'/image_service/image/'+bisque_archive_data_xml_top.attrib['resource_uniq']
        mask_xml_top                   = self.ensure_bisque_file(mask,local_dir=local_store_images)
        
        bisque_archive_xml         = self.session.fetchxml(bisque_archive_data_xml_top.attrib['uri']+'?view=deep')
        polygon_xml                = bisque_archive_xml.xpath('//polygon')
        bisque_archive_polygon     = polygon_xml[0].attrib['uri']                

        return ({
                 'filename'      : bisque_archive,
                 'mask_filename' : mask,
                 'image'         : self.root+'/image_service/image/'+bisque_archive_data_xml_top.attrib['resource_uniq'],
                 'image_xml'     : bisque_archive_data_xml_top,
                 'mask'          : self.root+'/image_service/image/'+mask_xml_top.attrib['resource_uniq'],
                 'mask_xml'      : mask_xml_top,
                 'polygon'       : bisque_archive_polygon   
                 })

#test breakdown
    @classmethod
    def delete_resource(self, r):
        """
            remove uploaded resource from bisque server
        """
        url = r.get('uri')
        print 'Deleting id: %s url: %s'%(r.get('resource_uniq'), url)
        self.session.postxml(url, etree.Element ('resource') , method='DELETE')



    @classmethod
    def cleanup_tests_dir(self):
        """
            Removes files downloaded into the local store
        """
        print 'Cleaning-up %s'%local_store_tests
        for root, dirs, files in os.walk(local_store_tests, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))



#Tests
    @classmethod
    def validate_request(self, commands, content_type, headers_required, content_required):
        """
            makes a request to the bisque server and checks the returned content
        """
        headers = self.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        
        start = time.time()
        header, content = self.session.c.http.request(commands, headers = headers)
        end = time.time()
        
        if self.time_trial:
            log.info('=========== Time Results ===========')
            log.info('Elapsed Time: %s sec'%(end-start))
        
        log.info('=========== Test Results ===========')
        RC = ResponseCheck()
        RC.check_header( headers_required, header) #check to see if the resulting response code is valid
        RC.check_response(content_type, content_required, content)
        RC.return_check() #returns the error message for unittest





##################################################################
# Request initalization 
##################################################################

class RequestTest(FeatureServiceTestBase):
    """
        Request Class
        The class all the test will be applied to
    """
    pass


def initialize_request_test():
    """
        
    """
    from RequestTestModule import request_test_generator, RequestList
    resquest_set = RequestList().get_List(['all'])
    for r in resquest_set:
        test_name = 'test_%s' % (r.name)
        log.debug('Initalizing request test: %s'%test_name)
        test = request_test_generator(r.name,r,['xml'])
        setattr( RequestTest, test_name, test) #normal run
#        pdb.set_trace()        


##################################################################
# Feature initalization
##################################################################

class FeatureTest(FeatureServiceTestBase):
    """
        Feature Test Class
        The class all the test will be applied to
    """
    pass

def initialize_feature_test(feature_groups,formats):
    """
    """
    from FeatureTestModule import feature_test_generator,FeatureList
    feature_set = FeatureList().get_List(feature_groups)
    for f in feature_set:
        test_name = 'test_%s' % (f.name)
        log.debug('Initalizing feature test: %s'%test_name)
        test = feature_test_generator(f.name , f, formats)
        setattr( FeatureTest, test_name, test) #normal run
        #setattr(FeatureTestCached, test_name, test) #cached run
        
        
##################################################################
# module setup and teardown
##################################################################

def setUpTest():
    """
        Initalizes all the Tests
    """
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    
    #login
    FeatureServiceTestBase.root = config.get('Host', 'root') or 'localhost:8080'
    FeatureServiceTestBase.user = config.get('Host', 'user') or 'test'
    FeatureServiceTestBase.pswd = config.get('Host', 'password') or 'test'
  
    #test options
    test_type = config.get('TestOptions', 'test_type') or 'all'
    FeatureServiceTestBase.test_type = test_type.replace(' ','').split(',')
    

    if 'features' in FeatureServiceTestBase.test_type or 'all' in FeatureServiceTestBase.test_type:
        #importing pre-calculated features on images
        FeatureServiceTestBase.fetch_file(bisque_archive_1+'.h5',local_dir=local_features_store)
        FeatureServiceTestBase.fetch_file(bisque_archive_2+'.h5',local_dir=local_features_store)
        FeatureServiceTestBase.fetch_file(bisque_archive_3+'.h5',local_dir=local_features_store)
        FeatureServiceTestBase.fetch_file(bisque_archive_4+'.h5',local_dir=local_features_store)        

        
        #test feature options
        test_features = config.get('TestOptions', 'test_features') or 'all'
        FeatureServiceTestBase.test_features = test_features.replace(' ','').split(',')     
        
        format_types = config.get('TestOptions', 'format_types') or 'all'
        FeatureServiceTestBase.test_features_formats = format_types.replace(' ','').split(',')          
        
        time_trial = config.get('TestOptions','time_trail') or 'False'
#        pdb.set_trace()
        if time_trial == 'True':
            FeatureServiceTestBase.time_trial = True
        elif time_trial == 'False':
            FeatureServiceTestBase.time_trial = False
        else:
            FeatureServiceTestBase.time_trial = False #defaults false if input is incorrect
    
        # download and upload test images and get their IDs
        # setup what test to be added to the test module
        initialize_feature_test(FeatureServiceTestBase.test_features, FeatureServiceTestBase.test_features_formats)
        
    if 'commands' in FeatureServiceTestBase.test_type or 'all' in FeatureServiceTestBase.test_type:
        initialize_request_test()
#        pdb.set_trace()

        
#    InitalizeRequestTest()


def setUpModule():
    """
        Initalizes the bisque to run tests
    """

    FeatureServiceTestBase.session = BQSession().init_local( FeatureServiceTestBase.user, FeatureServiceTestBase.pswd, bisque_root=FeatureServiceTestBase.root, create_mex = True)
    FeatureServiceTestBase.resource_list = []
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_1, mask_1) )
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_2, mask_2) )
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_3, mask_3) )
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_4, mask_4) )   




def tearDownModule():
    
    bisque_archive_1_uri = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[0]['image_xml'])
    mask_1_uri           = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[0]['mask_xml'])
    bisque_archive_2_uri = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[1]['image_xml'])
    mask_2_uri           = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[1]['mask_xml'])
    bisque_archive_3_uri = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[2]['image_xml'])
    mask_3_uri           = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[2]['mask_xml'])
    bisque_archive_4_uri = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[3]['image_xml'])
    mask_4_uri           = FeatureServiceTestBase.delete_resource(FeatureServiceTestBase.resource_list[3]['mask_xml'])
    
    FeatureServiceTestBase.cleanup_tests_dir()
    FeatureServiceTestBase.session.finish_mex()




if __name__=='__main__':
#    
    setUpTest()
    unittest.main(verbosity=2)







    
           
