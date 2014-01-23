#!/usr/bin/python

import pdb
from run_test import TestStatus,log
from run_test import log
import time

def request_test_generator(request_test_name, request_test, formats):
    
    def test(self):
        """
            generates feature tests
        """
        for f in formats:
            request_test(self).run_tests(f)
            
    return test

####################################################
### Request List Class
####################################################

class RequestList(object):
    """
        
    """
    def __init__(self):

        #construct feature list        
        self.request_map = {'all': []}
        for request_test in RequestTest.__subclasses__():
            
            #for each feature
            self.request_map[request_test.name] = [request_test]
            
            #for all
            self.request_map['all'].append(request_test)
            
    def get_List(self,request_test_list=['all']):
        """
        """
        request_set = set()
        try:
            for request_test_name in request_test_list:
                for request_test in self.request_map[request_test_name]:
                    request_set.add(request_test)
                
        except KeyError:
            request_set = set()
                
        return request_set


def test(format = None):
    """
        wrapper function to decide what content type output to be 
        applied
    """
    
    def wrap(func):      
        def wrapper(self):
            
            if self.format == None:
                return
                
            if format == None or format == self.format:
                func(self)
            else:
                return
            
        return wrapper
    return wrap

####################################################
### Request Tests Parent Class
####################################################

class RequestTest(object):
    
    name = 'request_test'
    
    def __init__(self, feature_service_test_base):
        self.feature_service_test_base = feature_service_test_base
        self.TestStatus = TestStatus()
    
    @test()
    def test_header(self):
        #check headers status
        if self.header['status'] == '200':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'200'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'200'))
 
    @test('xml')
    def test_content(self):
        pass
    
    def run_tests(self, format):
        
        self.format = format

        log.info('============ Test Info =============')
        log.info('Test Name: %s'%self.feature_service_test_base._testMethodName)
        log.info('Requested URI: %s'%self.command)
        log.info('Request Method: %s'%'GET')
        
        headers = self.feature_service_test_base.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        
        start = time.time()
        self.header, self.content = self.feature_service_test_base.session.c.http.request(self.command, headers = headers)
        end = time.time()
        
        if self.feature_service_test_base.time_trial:
            log.info('=========== Time Results ===========')
            log.info('Elapsed Time: %s sec'%(end-start))
        
        log.info('=========== Test Results ===========')
        
        test_list = []
#        pdb.set_trace()
        for test_func in (getattr(self,name) for name in dir(self) if name.startswith('test_')):
#            pdb.set_trace()
            test_func()

        self.TestStatus.return_error()
        return
    
####################################################
### Request Tests Child Class
####################################################  
  
class FeatureMain(RequestTest):
    
    name = 'feature_main' 
           
    def __init__(self, feature_service_test_base):
        super(FeatureMain, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features'
        
class FeatureList(RequestTest):
    
    name = 'feature_list' 
           
    def __init__(self, feature_service_test_base):
        super(FeatureList, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/list'
    
class Formats(RequestTest):
    
    name = 'formats' 
           
    def __init__(self, feature_service_test_base):
        super(Formats, self).__init__(feature_service_test_base)    
        self.command = self.feature_service_test_base.root+'/features/formats'
        
class Feature(RequestTest):
    
    name = 'feature' 
           
    def __init__(self, feature_service_test_base):
        super(Feature, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/DTFE'
    
    
class MultibleSameElementTypes(RequestTest):
    
    name = 'multible_same_element_types' 
           
    def __init__(self, feature_service_test_base):
        super(MultibleSameElementTypes, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/DTFE/none?'+self.feature_service_test_base.resource_list[0]['image']+'&'+self.feature_service_test_base.resource_list[0]['image']

    @test()
    def test_header(self):
        if self.header['status'] == '400':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'400'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'400'))
            

class NonlistedFeature(RequestTest):
    
    name = 'nonlisted_feature' 
           
    def __init__(self, feature_service_test_base):
        super(NonlistedFeature, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/asdf/none?'+self.feature_service_test_base.resource_list[0]['image']  

    @test()
    def test_header(self):
        if self.header['status'] == '404':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'404'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'404'))
        
class NonlistedFormat(RequestTest):
    
    name = 'nonlisted_format' 
           
    def __init__(self, feature_service_test_base):
        super(NonlistedFormat, self).__init__(feature_service_test_base)   
        self.command = self.feature_service_test_base.root+'/features/DTFE/safd?image='+self.feature_service_test_base.resource_list[0]['image'] 

    @test()
    def test_header(self):
        if self.header['status'] == '404':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'404'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'404'))
        
class IncorrectResourceInputType(RequestTest):
    
    name = 'incorrect_resource_input_type' 
           
    def __init__(self, feature_service_test_base):
        super(IncorrectResourceInputType, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/DTFE/none?stuff='+self.feature_service_test_base.resource_list[0]['image']

    @test()
    def test_header(self):
        if self.header['status'] == '400':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'400'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'400'))

class ResourceTypeNotFound(RequestTest):

    name = 'resource_type_not_found' 
           
    def __init__(self, feature_service_test_base):
        super(ResourceTypeNotFound, self).__init__(feature_service_test_base)
        self.command = self.feature_service_test_base.root+'/features/DTFE/xml?image='+self.feature_service_test_base.root+'/image_service/image/notaresource"'

     