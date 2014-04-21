# -*- mode: python -*-
""" Test library
"""
import tables
import logging
from pylons.controllers.util import abort
from bq.image_service.controllers.locks import Locks
from bq.features.controllers.Feature import calc_wrapper, ImageImport #import base class
from bq.features.controllers import Feature


log = logging.getLogger("bq.features")

class TestFeature(Feature.BaseFeature):
    """
        Test Feature
        This extractor is completely useless to calculate any 
        useful feature. 
        Purpose: to test the reliability of the feature service
    """
    #parameters
    name = 'TestFeature'
    description = """Dummy Test Feature Extractor (test feature) Calculates random numbers for features"""
    length = 64
    feature_format = 'int32'
    
    #cache = False
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Calculates features for DTFE"""
        
        #initalizing
        image_uri = resource['image']
        descriptor = [x for x in range(64)]
                
        #initalizing rows for the table
        return [descriptor]
        
        
class TestFeatureUncached(Feature.BaseFeature):
    """
        Test Feature Uncahced
        This extractor is completely useless to calculate any 
        useful feature. 
        Purpose: to test the reliability of the feature service
    """
    #parameters
    name = 'TestFeatureUncached'
    description = """Feature Test Uncached returns a very predicable vector"""
    length = 64
    feature_format = 'int32'
    cache = False
    
    @calc_wrapper
    def calculate(self, **resource):
        """ Calculates features for DTFE"""
        
        #initalizing
        image_uri = resource['image']
        descriptor = [x for x in range(64)]
                
        #initalizing rows for the table
        return [descriptor]
    
#class TestFeatureParameters(BaseFeature):
#    """
#        Test Feature parameters
#        This extractor is completely useless to calculate any 
#        useful feature. 
#        Purpose: to test the reliability of the feature service        
#    """
#    #parameters
#    name = 'TestFeatureUncached'
#    description = """Feature Test Uncached returns a very predicable vector"""
#    length = 64
#    feature_format = 'int32'
#    cache = False
#    
#    @calc_wrapper
#    def calculate(self, **resource):
#        """ Calculates features for DTFE"""
#        
#        #initalizing
#        image_uri = resource['image']
#        descriptor = [x for x in range(64)]
#                
#        #initalizing rows for the table
#        return [descriptor]    
#        

#class TestFeatureVaryingInputs(BaseFeature):
#    """
#        Test Feature parameters
#        This extractor is completely useless to calculate any 
#        useful feature. 
#        Purpose: to test the reliability of the feature service        
#    """
#    #parameters
#    name = 'TestFeatureVaryingInputs'
#    description = """Feature Test Uncached returns a very predicable vector"""
#    length = 64
#    feature_format = 'int32'
#    cache = False
#    
#    @calc_wrapper
#    def calculate(self, **resource):
#        """ Calculates features for DTFE"""
#        
#        #initalizing
#        image_uri = resource['image']
#        descriptor = [x for x in range(64)]
#                
#        #initalizing rows for the table
#        return [descriptor]    
#        

        
        
