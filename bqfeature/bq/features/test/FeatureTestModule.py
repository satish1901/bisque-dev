#!/usr/bin/python

""" List of features
"""

import pdb
from run_test import TestStatus,log
from lxml import etree
import time
import tables
import numpy as np


def feature_test_generator(feature_name, feature_test, formats):

    def test(self):
        """
            generates feature tests
        """
#        pdb.set_trace()
        for f in formats:

            feature_test(self).run_tests(f)


    return test


####################################################
### Feature List Class
####################################################

class FeatureList(object):
    """

    """
    def __init__(self):

        #construct feature list
        self.feature_map = {'all': []}
        for feature_test in FeatureTests.__subclasses__():

            #for each feature
            self.feature_map[feature_test.name] = [feature_test]

            #for each family
            if feature_test.family_name in self.feature_map:
                self.feature_map[feature_test.name].append(feature_test)
            else:
                self.feature_map[feature_test.name] = [feature_test]

            self.feature_map['all'].append(feature_test)

    def get_List(self,feature_name_list):
        """
        give it a list of all, feature_groups and/or specific feature names and it will return
        a list of object with information about such features
        """
        feature_set = set()
        try:
            for feature_name in feature_name_list:
                for feature_test in self.feature_map[feature_name]:
                    feature_set.add(feature_test)

        except KeyError:
            feature_set = set()

        return feature_set


def test(format = None):
    """
        wrapper function to filter out content type outputs requested
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
### Feature Tests Parent Class
####################################################

class FeatureTests(object):
    name = ''
    input_type = ['image']
    format = None
    family_name = 'all'

    def __init__(self, feature_service_test_base):
        self.feature_service_test_base = feature_service_test_base
        self.TestStatus = TestStatus()

#        self.header_required['status'] = '200'
#        self.content_required['feature'] = {'type': self.name}

    @test()
    def test_header(self):
        #check headers status
        if self.header['status'] == '200':
            self.TestStatus.equal('Success!: Header Attribute: status ==> required: %s == test: %s'%(self.header['status'],'200'))
        else:
            self.TestStatus.not_equal('Failure!: Header Attribute: status ==> required: %s != test: %s'%(self.header['status'],'200'))


    @test('xml')
    def test_content_xml(self):
        try:
            xml_test = etree.XML(self.content)
        except: #did not return xml
            self.TestStatus.not_equal('Did not return xml')
            return

        value = xml_test.xpath('//feature[@type]')
        if value[0].attrib['type'] == self.name:
            self.TestStatus.equal('Success!: XML Attribute: type ==> required: %s == test: %s'%(value[0],self.name))
        else:
            self.TestStatus.not_equal('Failure!: XML Attribute: type ==> required: %s != test: %s'%(value[0],self.name))

    @test('xml')
    def test_feature_vectors_xml(self):
        try:
            xml_test = etree.XML(self.content)
        except: #did not return xml
            self.TestStatus.not_equal('Did not return xml')
            return

        value = xml_test.xpath('//feature/value')
        feature_array = np.array(value[0].text.split()).astype('float')
        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
        root = h5file.root
        vl_array = getattr(root, self.name)[0]
        try:
            np.testing.assert_array_almost_equal(vl_array,feature_array, 4)
            self.TestStatus.equal('Success!: XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
        except AssertionError:
            self.TestStatus.not_equal('Failure!: XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))


#    @test('csv')
#    def test_csv(self):
#

    def run_tests(self, format):

        self.format = format
        uri = self.feature_service_test_base.root+'/features/'+self.name+'/'+format+'?'
        query = []
        for i in self.input_type:
            query += [i+'='+self.feature_service_test_base.resource_list[0][i]]

        query= '&'.join(query)
        command = uri + query

        log.info('============ Test Info =============')
        log.info('Test Name: %s'%self.feature_service_test_base._testMethodName)
        log.info('Requested URI: %s'%command)
        log.info('Request Method: %s'%'GET')

        headers = self.feature_service_test_base.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        start = time.time()
        self.header, self.content = self.feature_service_test_base.session.c.http.request(command, headers = headers)
        end = time.time()
        if self.feature_service_test_base.time_trial:
            log.info('=========== Time Results ===========')
            log.info('Elapsed Time: %s sec'%(end-start))

        log.info('=========== Test Results ===========')

        test_list = []

        for test_func in (getattr(self,name) for name in dir(self) if name.startswith('test_')):
            test_func()

        self.TestStatus.return_error()
        return


####################################################
### Feature Tests Child Class
####################################################

class HTD(FeatureTests):
    name = 'HTD'
    family_name = 'VRL'

    def __init__(self, feature_service_test_base):
        super(HTD, self).__init__(feature_service_test_base)


class EHD(FeatureTests):
    name = 'EHD'
    family_name = 'VRL'

    def __init__(self, feature_service_test_base):
        super(EHD, self).__init__(feature_service_test_base)


class mHTD(FeatureTests):
    name = 'mHTD'
    family_name = 'VRL'
    input_type = ['image','mask']

    def __init__(self, feature_service_test_base):
        super(mHTD, self).__init__(feature_service_test_base)


    @test('xml')
    def test_feature_vectors_xml(self): #need to think more on how the results should be generated
        pass
#        xml_test = etree.XML(self.content)
#        value = xml_test.xpath('//feature/value')
#        feature_array = np.array(value[0].text.split()).astype('float')
#        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
#        root = h5file.root
#        vl_array = getattr(root, self.name)[0]
#        if np.array_equal(vl_array,feature_array):
#            log.info('XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
#        else:
#            log.info('XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))

class CLD(FeatureTests):
    name = 'CLD'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(CLD, self).__init__(feature_service_test_base)



class CSD(FeatureTests):
    name = 'CSD'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(CSD, self).__init__(feature_service_test_base)




class SCD(FeatureTests):
    name = 'SCD'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(SCD, self).__init__(feature_service_test_base)



class DCD(FeatureTests):
    name = 'DCD'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(DCD, self).__init__(feature_service_test_base)



class HTD2(FeatureTests):
    name = 'HTD2'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(HTD2, self).__init__(feature_service_test_base)



class EHD2(FeatureTests):
    name = 'EHD2'
    family_name = 'MPEG7Flex'

    def __init__(self, feature_service_test_base):
        super(EHD2, self).__init__(feature_service_test_base)



class pRSD(FeatureTests):
    name = 'pRSD'
    family_name = 'MPEG7Flex'
    input_type = ['image','polygon']

    def __init__(self, feature_service_test_base):
        super(RSD, self).__init__(feature_service_test_base)


class Chebishev_Statistics(FeatureTests):
    name = 'Chebishev_Statistics'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Chebishev_Statistics, self).__init__(feature_service_test_base)


class Chebyshev_Fourier_Transform(FeatureTests):
    name = 'Chebyshev_Fourier_Transform'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Chebyshev_Fourier_Transform, self).__init__(feature_service_test_base)


class Color_Histogram(FeatureTests):
    name = 'Color_Histogram'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Color_Histogram, self).__init__(feature_service_test_base)


class Comb_Moments(FeatureTests):
    name = 'Comb_Moments'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Comb_Moments, self).__init__(feature_service_test_base)


class Edge_Features(FeatureTests):
    name = 'Edge_Features'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Edge_Features, self).__init__(feature_service_test_base)


class Fractal_Features(FeatureTests):
    name = 'Fractal_Features'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Fractal_Features, self).__init__(feature_service_test_base)



class Gini_Coefficient(FeatureTests):
    name = 'Gini_Coefficient'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Gini_Coefficient, self).__init__(feature_service_test_base)


class Gabor_Textures(FeatureTests):
    name = 'Gabor_Textures'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Gabor_Textures, self).__init__(feature_service_test_base)


class Haralick_Textures(FeatureTests):
    name = 'Haralick_Textures'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Haralick_Textures, self).__init__(feature_service_test_base)


class Multiscale_Historgram(FeatureTests):
    name = 'Multiscale_Historgram'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Multiscale_Historgram, self).__init__(feature_service_test_base)



class Object_Feature(FeatureTests):
    name = 'Object_Feature'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Object_Feature, self).__init__(feature_service_test_base)


class Inverse_Object_Features(FeatureTests):
    name = 'Inverse_Object_Features'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Inverse_Object_Features, self).__init__(feature_service_test_base)


class Pixel_Intensity_Statistics(FeatureTests):
    name = 'Pixel_Intensity_Statistics'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Pixel_Intensity_Statistics, self).__init__(feature_service_test_base)



class Radon_Coefficients(FeatureTests):
    name = 'Radon_Coefficients'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Radon_Coefficients, self).__init__(feature_service_test_base)


class Tamura_Textures(FeatureTests):
    name = 'Tamura_Textures'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Tamura_Textures, self).__init__(feature_service_test_base)


class Zernike_Coefficients(FeatureTests):
    name = 'Zernike_Coefficients'
    family_name = 'WNDCharm'

    def __init__(self, feature_service_test_base):
        super(Zernike_Coefficients, self).__init__(feature_service_test_base)


class BRISK(FeatureTests):
    name = 'BRISK'
    family_name = 'OpenCV'

    def __init__(self, feature_service_test_base):
        super(BRISK, self).__init__(feature_service_test_base)

    @test('xml')
    def test_feature_vectors_xml(self):
        pass
#        xml_test = etree.XML(self.content)
#        value = xml_test.xpath('//feature/value')
#        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
#        root = h5file.root
#        for i,v in  enumerate(value):
#            feature_array = np.array(value[0].text.split()).astype('float')
#            vl_array = getattr(root, self.name)[0]
#
#            if np.array_equal(vl_array,feature_array):
#                log.info('XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
#            else:
#                log.info('XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))



class ORB(FeatureTests):
    name = 'ORB'
    family_name = 'OpenCV'

    def __init__(self, feature_service_test_base):
        super(ORB, self).__init__(feature_service_test_base)


    @test('xml')
    def test_feature_vectors_xml(self):
        pass
#        xml_test = etree.XML(self.content)
#        value = xml_test.xpath('//feature/value')
#        feature_array = np.array(value[0].text.split()).astype('float')
#        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
#        root = h5file.root
#        vl_array = getattr(root, self.name)[0]
#        if np.array_equal(vl_array,feature_array):
#            log.info('XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
#        else:
#            log.info('XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))

class SIFT(FeatureTests):
    name = 'SIFT'
    family_name = 'OpenCV'

    def __init__(self, feature_service_test_base):
        super(SIFT, self).__init__(feature_service_test_base)


    @test('xml')
    def test_feature_vectors_xml(self):
        pass
#        xml_test = etree.XML(self.content)
#        value = xml_test.xpath('//feature/value')
#        feature_array = np.array(value[0].text.split()).astype('float')
#        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
#        root = h5file.root
#        vl_array = getattr(root, self.name)[0]
#        if np.array_equal(vl_array,feature_array):
#            log.info('XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
#        else:
#            log.info('XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))


class SURF(FeatureTests):
    name = 'SURF'
    family_name = 'OpenCV'

    def __init__(self, feature_service_test_base):
        super(SURF, self).__init__(feature_service_test_base)

    @test('xml')
    def test_feature_vectors_xml(self):
        pass
#    @test('xml')
#    def test_feature_vectors_xml(self):
#        xml_test = etree.XML(self.content)
#        value = xml_test.xpath('//feature/value')
#        feature_array = np.array(value[0].text.split()).astype('float')
#        h5file = tables.open_file('features/'+self.feature_service_test_base.resource_list[0]['filename']+'.h5','r')
#        root = h5file.root
#        vl_array = getattr(root, self.name)[0]
#        if np.array_equal(vl_array,feature_array):
#            log.info('XML Attribute: feature/value ==> required: %s == test: %s'%(vl_array,feature_array))
#        else:
#            log.info('XML Attribute: feature/value ==> required: %s != test: %s'%(vl_array,feature_array))


class LBP(FeatureTests):
    name = 'LBP'
    family_name = 'OpenCV'

    def __init__(self, feature_service_test_base):
        super(LBP, self).__init__(feature_service_test_base)


class PFTAS(FeatureTests):
    name = 'PFTAS'
    family_name = 'Mahotas'

    def __init__(self, feature_service_test_base):
        super(PFTAS, self).__init__(feature_service_test_base)


class TAS(FeatureTests):
    name = 'TAS'
    family_name = 'Mahotas'

    def __init__(self, feature_service_test_base):
        super(TAS, self).__init__(feature_service_test_base)


class ZM(FeatureTests):
    name = 'ZM'
    family_name = 'Mahotas'

    def __init__(self, feature_service_test_base):
        super(ZM, self).__init__(feature_service_test_base)


class FFTSD(FeatureTests):
    name = 'FFTSD'
    family_name = 'MyFeatures'
    input_type = ['polygon']

    def __init__(self, feature_service_test_base):
        super(FFTSD, self).__init__(feature_service_test_base)

