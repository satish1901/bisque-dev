#from bq.api.bqclass import fromXml # bisque
#from bq.api.comm import BQSession, BQCommError # bisque
#from bq.api.util import save_blob # bisque
import urllib
import zipfile
from FeatureTest import FeatureBase
from RequestTest import RequestBase
from bqapi.comm import BQSession, BQCommError
from lxml import etree
import getpass
import argparse
import time
import posixpath
import ConfigParser
import os
import glob
from subprocess import Popen, call, PIPE
import ntpath
import logging as log
from unittest import TestCase
import time
import tables
import pdb
#from TestGlobals import check_for_file, fetch_file, delete_resource, cleanup_dir
from TestGlobals import LOCAL_FEATURES_STORE#,TEST_TYPE
from nose.plugins.attrib import attr  
from utils import check_for_file, fetch_file, resource_info, delete_resource, cleanup_dir
#clearing logs
#with open('test.log', 'w'): pass


#log.basicConfig(filename='test.log',level=log.DEBUG)


import TestGlobals



def setUpModule():
    """
        Initalizes the bisque to run tests
        (moved to the TestGlobals module so that everything is initalized before nose startes)
    """    
    #importing pre-calculated features on images
    check_for_file( TestGlobals.FEATURE_1, TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    fetch_file( TestGlobals.FEATURE_1, local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    check_for_file( TestGlobals.FEATURE_2, TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    fetch_file( TestGlobals.FEATURE_2, local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    check_for_file( TestGlobals.FEATURE_3, TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    fetch_file( TestGlobals.FEATURE_3, local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    check_for_file( TestGlobals.FEATURE_4, TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
    fetch_file( TestGlobals.FEATURE_4, local_dir=TestGlobals.LOCAL_FEATURES_STORE) 

    #assigns the create session to global
    TestGlobals.SESSION = BQSession().init_local( TestGlobals.USER, TestGlobals.PWD, bisque_root = TestGlobals.ROOT, create_mex = True)
    
    #importing resources
    RESOURCE_LIST = []
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_1, TestGlobals.MASK_1, TestGlobals.FEATURE_1) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_2, TestGlobals.MASK_2, TestGlobals.FEATURE_2) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_3, TestGlobals.MASK_3, TestGlobals.FEATURE_3) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_4, TestGlobals.MASK_4, TestGlobals.FEATURE_4) )
    TestGlobals.RESOURCE_LIST = RESOURCE_LIST


def tearDownModule():
    
    bisque_archive_1_uri = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[0]['image_xml'])
    mask_1_uri           = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[0]['mask_xml'])
    bisque_archive_2_uri = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[1]['image_xml'])
    mask_2_uri           = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[1]['mask_xml'])
    bisque_archive_3_uri = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[2]['image_xml'])
    mask_3_uri           = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[2]['mask_xml'])
    bisque_archive_4_uri = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[3]['image_xml'])
    mask_4_uri           = delete_resource(TestGlobals.SESSION, TestGlobals.RESOURCE_LIST[3]['mask_xml'])
    
    cleanup_dir()
    TestGlobals.SESSION.finish_mex()
    



########################################
###         documentation
#######################################
class TestFeatureMain(RequestBase):

    name = 'feature_main'
    #request = TestGlobals.ROOT+'/features'
    response_code = '200'
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features'
    
class TestFeatureList(RequestBase):

    name = 'feature_list' 
    #request = TestGlobals.ROOT+'/features/list'
    response_code = '200'  
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/list'
    
class TestFormats(RequestBase):
  
    name = 'formats' 
    #request = TestGlobals.ROOT+'/features/formats'
    response_code = '200'
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/formats'
               
#######################################
###      Feature Functionality
#######################################
class TestFeature(RequestBase):
    """
        Testing on a Test Features
    """
    name = 'feature' 
    #request = TestGlobals.ROOT+'/features/TestFeature'
    response_code = '200'
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature'

class TestFeatureCached(RequestBase):
    """
        Testing on a Cached Test Features
    """
    name = 'feature_cached' 
    #request = TestGlobals.ROOT+'/features/TestFeature'
    response_code = '200'
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature' 

############################################
###     Malformed Requests
############################################
class TestMultibleSameElementTypes(RequestBase):
    
    name = 'multible_same_element_types' 
    #request = TestGlobals.ROOT+'/features/TestFeature/none?'+TestGlobals.RESOURCE_LIST[0]['image']+'&'+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '400'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature/none?'+TestGlobals.RESOURCE_LIST[0]['image']+'&'+TestGlobals.RESOURCE_LIST[0]['image']

class TestNonlistedFeature(RequestBase):
    
    name = 'nonlisted_feature' 
    #request = TestGlobals.ROOT+'/features/asdf/none?'+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '404'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/asdf/none?'+TestGlobals.RESOURCE_LIST[0]['image']     
        
class TestNonlistedFormat(RequestBase):
    
    name = 'nonlisted_format' 
    #request = TestGlobals.ROOT+'/features/TestFeature/sadf?image='+TestGlobals.RESOURCE_LIST[0]['image'] 
    response_code = '404'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature/sadf?image='+TestGlobals.RESOURCE_LIST[0]['image'] 
        
class TestIncorrectResourceInputType(RequestBase):
    
    name = 'incorrect_resource_input_type'
    #request = TestGlobals.ROOT+'/features/TestFeature/none?stuff='+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '400'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature/none?stuff='+TestGlobals.RESOURCE_LIST[0]['image']

class TestResourceTypeNotFound(RequestBase):

    name = 'resource_type_not_found'
    #request = TestGlobals.ROOT+'/features/TestFeature/xml?image='+TestGlobals.ROOT+'/image_service/image/notaresource"'  
    response_code = '200'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature/xml?image='+TestGlobals.ROOT+'/image_service/image/notaresource"'  

class TestDocumentationIncorrectFeature(RequestBase):
    
    name = 'documentation_of_incorrect_feature'
    #request = TestGlobals.ROOT+'/features/asdf'  
    response_code = '404'
    
    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/asdf'  

class TestDocumentationIncorrectFormat(RequestBase):
    
    name = 'documentation_of_incorrect_format'
    #request = TestGlobals.ROOT+'/features/format/asdf'  
    response_code = '404'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/format/asdf'  

class TestPostWithoutABody(RequestBase):
    name = 'post_without_a_body'
    #request = TestGlobals.ROOT+'/features/TestFeature/xml'
    response_code = '400'
    method = 'POST'

    def write_request(self): 
        self.request = TestGlobals.ROOT+'/features/TestFeature/xml'

##################################
###     VRL Features
##################################
class TestHTD(FeatureBase):
    name = 'HTD'
    family_name = 'VRL'
    length = 48
    

class TestEHD(FeatureBase):
    name = 'EHD'
    family_name = 'VRL'
    length = 80
    
    
class TestmHTD(FeatureBase):
    name = 'mHTD'
    family_name = 'VRL'
    length = 48
    input_resource = ['image','mask']
    parameters = ['label']
    
    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            mask         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Float32Col(shape=(self.length), pos=3)
            label         = tables.Float32Col(pos=4)
        return Columns    
    
    
###################################
#### MPEG7Flex Features
###################################
class TestCLD(FeatureBase):
    name = 'CLD'
    family_name = 'MPEG7Flex'
    length = 120
    
class TestCSD(FeatureBase):
    name = 'CSD'
    family_name = 'MPEG7Flex'
    length = 64
    
class TestSCD(FeatureBase):
    name = 'SCD'
    family_name = 'MPEG7Flex'
    length = 256
    
class TestDCD(FeatureBase):
    name = 'DCD'
    family_name = 'MPEG7Flex'
    length = 100
    
class TestHTD2(FeatureBase):
    name = 'HTD2'
    family_name = 'MPEG7Flex'
    length = 62
    
class TestEHD2(FeatureBase):
    name = 'EHD2'
    family_name = 'MPEG7Flex'
    length = 80


class TestRSD(FeatureBase):
    name = 'RSD'
    family_name = 'MPEG7Flex'
    length = 35

class TestmCLD(FeatureBase):
    name = 'mCLD'
    family_name = 'MPEG7Flex'
    length = 120
    input_resource = ['image','mask']
    parameters = ['label']

    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            mask         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Float32Col(shape=(self.length), pos=3)
            label         = tables.Float32Col(pos=4)
        return Columns
    
class TestmCSD(FeatureBase):
    name = 'mCSD'
    family_name = 'MPEG7Flex'
    length = 64
    input_resource = ['image','mask']
    parameters = ['label']

    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            mask         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Float32Col(shape=(self.length), pos=3)
            label         = tables.Float32Col(pos=4)
        return Columns
  
    
class TestmDCD(FeatureBase):
    name = 'mDCD'
    family_name = 'MPEG7Flex'
    length = 100
    input_resource = ['image','mask']     
    parameters = ['label']
    
    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            mask         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Float32Col(shape=(self.length), pos=3)
            label         = tables.Float32Col(pos=4)
        return Columns
    

class TestmRSD(FeatureBase):
    name = 'mRSD'
    family_name = 'MPEG7Flex'
    length = 35
    input_resource = ['image','mask']
    parameters = ['label']
    
    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            mask         = tables.StringCol(2000,pos=1)
            feature_type  = tables.StringCol(20, pos=2)
            feature       = tables.Float32Col(shape=(self.length), pos=3)
            label         = tables.Float32Col(pos=4)
        return Columns
    
    
###################################
#### WNDCharm Features
###################################
class TestChebishev_Statistics(FeatureBase):
    name = 'Chebishev_Statistics'
    family_name = 'WNDCharm'
    length = 32
    
class TestChebyshev_Fourier_Transform(FeatureBase):
    name = 'Chebyshev_Fourier_Transform'
    family_name = 'WNDCharm'
    length = 32
    
class TestColor_Histogram(FeatureBase):
    name = 'Color_Histogram'
    family_name = 'WNDCharm'
    length = 20

class TestComb_Moments(FeatureBase):
    name = 'Comb_Moments'
    family_name = 'WNDCharm'
    length = 48
    
#only fails on hdf
class TestEdge_Features(FeatureBase):
    name = 'Edge_Features'
    family_name = 'WNDCharm'
    length = 28
    
class TestFractal_Features(FeatureBase):
    name = 'Fractal_Features'
    family_name = 'WNDCharm'
    length = 20
    
class TestGini_Coefficient(FeatureBase):
    name = 'Gini_Coefficient'
    family_name = 'WNDCharm'
    length = 1
    
class TestGabor_Textures(FeatureBase):
    name = 'Gabor_Textures'
    family_name = 'WNDCharm'
    length = 7

class TestHaralick_Textures(FeatureBase):
    name = 'Haralick_Textures'
    family_name = 'WNDCharm'
    length = 28
    
class TestMultiscale_Historgram(FeatureBase):
    name = 'Multiscale_Historgram'
    family_name = 'WNDCharm'
    length = 24

class TestObject_Feature(FeatureBase):
    name = 'Object_Feature'
    family_name = 'WNDCharm'
    length = 34

class TestInverse_Object_Features(FeatureBase):
    name = 'Inverse_Object_Features'
    family_name = 'WNDCharm'
    length = 34

class TestPixel_Intensity_Statistics(FeatureBase):
    name = 'Pixel_Intensity_Statistics'
    family_name = 'WNDCharm'
    length = 5
    
class TestRadon_Coefficients(FeatureBase):
    name = 'Radon_Coefficients'
    family_name = 'WNDCharm'
    length = 12
    
class TestTamura_Textures(FeatureBase):
    name = 'Tamura_Textures'
    family_name = 'WNDCharm'
    length = 6
    
class TestZernike_Coefficients(FeatureBase):
    name = 'Zernike_Coefficients'
    family_name = 'WNDCharm'
    length = 72



############################################
### OpenCV Features
############################################
class TestBRISK(FeatureBase):
    name = 'BRISK'
    family_name = 'OpenCV'
    length = 64
    parameters = ['x','y','response','size','angle','octave']
    
    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            feature_type  = tables.StringCol(20, pos=1)
            feature       = tables.Float32Col(shape=(self.length), pos=2)
            x         = tables.Float32Col(pos=4)
            y         = tables.Float32Col(pos=5)
            response  = tables.Float32Col(pos=6)
            size      = tables.Float32Col(pos=7)
            angle     = tables.Float32Col(pos=8)
            octave    = tables.Float32Col(pos=9)            
        return Columns     

    
class TestORB(FeatureBase):
    name = 'ORB'
    family_name = 'OpenCV'
    length = 32
    parameters = ['x','y','response','size','angle','octave']
    
    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            feature_type  = tables.StringCol(20, pos=1)
            feature       = tables.Float32Col(shape=(self.length), pos=2)
            x         = tables.Float32Col(pos=4)
            y         = tables.Float32Col(pos=5)
            response  = tables.Float32Col(pos=6)
            size      = tables.Float32Col(pos=7)
            angle     = tables.Float32Col(pos=8)
            octave    = tables.Float32Col(pos=9)
        return Columns     

    
class TestSIFT(FeatureBase):
    name = 'SIFT'
    family_name = 'OpenCV'
    length = 128
    parameters = ['x','y','response','size','angle','octave']  

    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            feature_type  = tables.StringCol(20, pos=1)
            feature       = tables.Float32Col(shape=(self.length), pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
        return Columns 

    
class TestSURF(FeatureBase):
    name = 'SURF'
    family_name = 'OpenCV'
    length = 64
    parameters = ['x','y','laplacian','size','direction','hessian'] 

    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            feature_type  = tables.StringCol(20, pos=1)
            feature       = tables.Float32Col(shape=(self.length), pos=2)
            x         = tables.Float32Col(pos=4)
            y         = tables.Float32Col(pos=5)
            laplacian = tables.Float32Col(pos=6)
            size      = tables.Float32Col(pos=7)
            direction = tables.Float32Col(pos=8)
            hessian   = tables.Float32Col(pos=9)
        return Columns 

#############################################
#### Mahotas Features
#############################################
class TestLBP(FeatureBase):
    name = 'LBP'
    family_name = 'Mahotas'
    length = 8
    
    
class TestPFTAS(FeatureBase):
    name = 'PFTAS'
    family_name = 'Mahotas'
    length = 54
    
class TestPFTASColored(FeatureBase):
    name = 'PFTASColored'
    family_name = 'Mahotas'
    length = 162

class TestTAS(FeatureBase):
    name = 'TAS'
    family_name = 'Mahotas'
    length = 54
    
class TestTASColored(FeatureBase):
    name = 'TASColored'
    family_name = 'Mahotas'
    length = 162    
    
class TestZM(FeatureBase):
    name = 'ZM'
    family_name = 'Mahotas'
    length = 25


class TestHARColored(FeatureBase):
    name = 'HARColored'
    family_name = 'Mahotas'
    length = 169

class TestHAR(FeatureBase):
    name = 'HAR'
    family_name = 'Mahotas'
    length = 52
    
    
#class FFTSD(FeatureBase):
#    name = 'FFTSD'
#    family_name = 'MyFeatures'
#    length = 500
#    input_resource = ['polygon']    


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__])
    
    
