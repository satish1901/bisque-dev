#from bqapi.bqclass import fromXml # bisque
#from bqapi.comm import BQSession, BQCommError # bisque
#from bqapi.util import save_blob # bisque
import urllib
import zipfile
from FeatureTest import FeatureBase
from RequestTest import RequestBase
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
from TestGlobals import check_for_file, fetch_file, delete_resource, cleanup_dir
from TestGlobals import LOCAL_FEATURES_STORE,TEST_TYPE
from nose.plugins.attrib import attr
#clearing logs
#with open('test.log', 'w'): pass


#log.basicConfig(filename='test.log',level=log.DEBUG)


import TestGlobals


#url_file_store       = 'http://hammer.ece.ucsb.edu/~bisque/test_data/images/'
url_file_store       = 'http://biodev.ece.ucsb.edu/binaries/download/'
local_store_images   = 'images'
local_features_store = 'features'
local_store_tests    = 'tests'
TEMP                 = 'Temp'

service_data         = 'data_service'
service_image        = 'image_service'
resource_image       = 'image'
features             = 'features'

image_archive_zip    = 'D91AC09AB1A1086F71BF6EC03E518DA3DF701870-feature_test_images.zip'
feature_archive_zip  = '4236628712FCF4543F640513AB9DA9F28616BEC5-feature_test_features.zip'

feature_zip          = 'feature_test_features'
image_zip            = 'feature_test_images'

#imported files
bisque_archive_1     = 'image_08093.tar'
mask_1               = 'mask_8093.jpg'
bisque_archive_2     = 'image_08089.tar'
mask_2               = 'mask_8089.jpg'
bisque_archive_3     = 'image_08069.tar'
mask_3               = 'mask_8069.jpg'
bisque_archive_4     = 'image_08043.tar'
mask_4               = 'mask_8043.jpg'





def setUpModule():
    """
        Initalizes the bisque to run tests
        (moved to the TestGlobals module so that everything is initalized before nose startes)
    """
    if 'features' in TEST_TYPE or 'all' in TEST_TYPE:

        #importing pre-calculated features on images
        TestGlobals.check_for_file(TestGlobals.BISQUE_ARCHIVE_1+'.h5', TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.fetch_file(TestGlobals.BISQUE_ARCHIVE_1+'.h5',local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.check_for_file(TestGlobals.BISQUE_ARCHIVE_2+'.h5', TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.fetch_file(TestGlobals.BISQUE_ARCHIVE_2+'.h5',local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.check_for_file(TestGlobals.BISQUE_ARCHIVE_3+'.h5', TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.fetch_file(TestGlobals.BISQUE_ARCHIVE_3+'.h5',local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.check_for_file(TestGlobals.BISQUE_ARCHIVE_4+'.h5', TestGlobals.FEATURE_ARCHIVE_ZIP,local_dir=TestGlobals.LOCAL_FEATURES_STORE)
        TestGlobals.fetch_file(TestGlobals.BISQUE_ARCHIVE_4+'.h5',local_dir=TestGlobals.LOCAL_FEATURES_STORE)



def tearDownModule():

    bisque_archive_1_uri = delete_resource(TestGlobals.RESOURCE_LIST[0]['image_xml'])
    mask_1_uri           = delete_resource(TestGlobals.RESOURCE_LIST[0]['mask_xml'])
    bisque_archive_2_uri = delete_resource(TestGlobals.RESOURCE_LIST[1]['image_xml'])
    mask_2_uri           = delete_resource(TestGlobals.RESOURCE_LIST[1]['mask_xml'])
    bisque_archive_3_uri = delete_resource(TestGlobals.RESOURCE_LIST[2]['image_xml'])
    mask_3_uri           = delete_resource(TestGlobals.RESOURCE_LIST[2]['mask_xml'])
    bisque_archive_4_uri = delete_resource(TestGlobals.RESOURCE_LIST[3]['image_xml'])
    mask_4_uri           = delete_resource(TestGlobals.RESOURCE_LIST[3]['mask_xml'])

    cleanup_dir()
    TestGlobals.SESSION.finish_mex()

    #remove all files form temp dir

    tempfilelist = glob.glob(os.path.join('Temp','*'))
    for f in tempfilelist:
        try:
            os.remove(f)
        except:
            pass


########################################
###         documentation
#######################################
class TestFeatureMain(RequestBase):

    name = 'feature_main'
    request = TestGlobals.ROOT+'/features'
    response_code = '200'

class TestFeatureList(RequestBase):

    name = 'feature_list'
    request = TestGlobals.ROOT+'/features/list'
    response_code = '200'

class TestFormats(RequestBase):

    name = 'formats'
    request = TestGlobals.ROOT+'/features/formats'
    response_code = '200'

#######################################
###      Feature Functionality
#######################################
class TestFeature(RequestBase):
    """
        Testing on a Test Features
    """
    name = 'feature'
    request = TestGlobals.ROOT+'/features/TestFeature'
    response_code = '200'

class TestFeatureCached(RequestBase):
    """
        Testing on a Cached Test Features
    """
    name = 'feature_cached'
    request = TestGlobals.ROOT+'/features/TestFeature'
    response_code = '200'

############################################
###     Malformed Requests
############################################
class TestMultibleSameElementTypes(RequestBase):

    name = 'multible_same_element_types'
    request = TestGlobals.ROOT+'/features/TestFeature/none?'+TestGlobals.RESOURCE_LIST[0]['image']+'&'+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '400'


class TestNonlistedFeature(RequestBase):

    name = 'nonlisted_feature'
    request = TestGlobals.ROOT+'/features/asdf/none?'+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '404'


class TestNonlistedFormat(RequestBase):

    name = 'nonlisted_format'
    request = TestGlobals.ROOT+'/features/TestFeature/sadf?image='+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '404'


class TestIncorrectResourceInputType(RequestBase):

    name = 'incorrect_resource_input_type'
    request = TestGlobals.ROOT+'/features/TestFeature/none?stuff='+TestGlobals.RESOURCE_LIST[0]['image']
    response_code = '400'


class TestResourceTypeNotFound(RequestBase):

    name = 'resource_type_not_found'
    request = TestGlobals.ROOT+'/features/TestFeature/xml?image='+TestGlobals.ROOT+'/image_service/image/notaresource"'
    response_code = '200'


class TestDocumentationIncorrectFeature(RequestBase):

    name = 'documentation_of_incorrect_feature'
    request = TestGlobals.ROOT+'/features/asdf'
    response_code = '404'


class TestDocumentationIncorrectFormat(RequestBase):

    name = 'documentation_of_incorrect_format'
    request = TestGlobals.ROOT+'/features/format/asdf'
    response_code = '404'

class TestPostWithoutABody(RequestBase):
    name = 'post_without_a_body'
    request = TestGlobals.ROOT+'/features/TestFeature/xml'
    response_code = '400'
    method = 'POST'

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
    length = 162


class TestTAS(FeatureBase):
    name = 'TAS'
    family_name = 'Mahotas'
    length = 162


class TestZM(FeatureBase):
    name = 'ZM'
    family_name = 'Mahotas'
    length = 25


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


