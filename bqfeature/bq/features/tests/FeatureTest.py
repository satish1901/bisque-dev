import nose
import unittest
import TestGlobals 
import numpy as np
import tables
from lxml import etree
from unittest import TestCase
from nose.tools import assert_equals
import tempfile
import tables
import re
import os
import pdb
import csv
from nose.plugins.attrib import attr       
from FeatureTestAsserts import isEqualXMLElement,isCSVEqual,isHDFEqual


def set_docstring(value):
    def dec(obj):
        obj.__doc__ = value
        return obj
    return dec


class FeatureBase(object):
    
    name = ''
    family_name = ''
    input_resource = ['image']
    parameters = []
    
    #seen as an indiviual test module
    #XML

    def constuct_xml_response(self,uri,resource_list):
        """
            contructs the ideal xml response
        
            input
            @uri(str) - request uri to the feature
            @resource(list) - list of resources to look up in the stored feature tables
            
            output
            @resource(etree) - the ideal request for the feature server response
        """
        resource = etree.Element('resource', uri=str(uri))
        for r in resource_list:
            
            with tables.open_file(os.path.join(TestGlobals.LOCAL_FEATURES_STORE,r['feature_filename']),'r') as h5file:
                group = getattr(h5file.root, self.name)
                feature_array_list = getattr(group, 'feature')
                
                for idx,feature_array in enumerate(feature_array_list):
                    inputs = {}
                    
                    for i in self.input_resource:
                        inputs[i] = r[i]
                    feature = etree.SubElement(resource, 'feature', inputs, type = self.name)
                    
                    if self.parameters:
                        parameters = {}
                        
                        for p in self.parameters:
                            etree.SubElement(feature, 'tag', name=p, value=str(str(getattr(group, p)[idx][0])))

#                            parameters[p] = str(getattr(group, p)[idx][0])
#                        etree.SubElement(feature, 'parameters', parameters)
                    value = etree.SubElement(feature, 'tag', name= 'feature', value= ",".join('%g'%item for item in feature_array))
#                    value=etree.SubElement(feature,'value')
#                    value.text = " ".join('%g' % item for item in feature_array)

        return resource
    
    
    def construct_csv_response(self,resource_list):
        """
            contructs the ideal xml response
        
            input
            @resource(list) - list of resources to look up in the stored feature tables
            
            output
            @resource(str) - the ideal csv request for the feature server response 
            
        """
        import csv
        import StringIO
        f = StringIO.StringIO()
        writer = csv.writer(f)
        titles = ['index', 'feature type'] + self.input_resource + ['feature'] + self.parameters + ['response code','error message']  #+ parameter_names
        writer.writerow(titles)
        line_idx = 0
        for r in resource_list:
            with tables.open_file(os.path.join(TestGlobals.LOCAL_FEATURES_STORE,r['feature_filename']),'r')  as h5file:
                group = getattr(h5file.root, self.name)
                feature_array_list = getattr(group, 'feature')
                for idx,feature_array in enumerate(feature_array_list):
                    inputs = [] #list of input resource uris
                    for i in self.input_resource:
                        inputs.append(r[i])
                    
                    feature_array = ','.join('%g' % item for item in feature_array)
                    
                    parameter_array = []
                    for p in self.parameters:
                        parameter_array.append(getattr(group, p)[idx][0])
                    
                    line = [line_idx, self.name] + inputs + ['%s'%feature_array] + parameter_array + ['200','none'] 
                    line_idx+=1

                    writer.writerow(line)
        return f.getvalue()


    def def_hdf_column(self):
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=0)
            feature_type  = tables.StringCol(20, pos=1)
            feature       = tables.Float32Col(shape=(self.length), pos=2)
        return Columns    
    
    
    def construct_hdf_response(self,resource_list):
        """
            contructs the ideal hdf response
        
            input
            @resource(list) - list of resources to look up in the stored feature tables
            
            output
            @resource(str) - the path to the ideal hdf table
        """
        f = tempfile.NamedTemporaryFile(dir=TestGlobals.TEMP_DIR, prefix='feature_', delete=False) 
        with tables.open_file(f.name,'a') as h5file_ideal:
            table = h5file_ideal.createTable('/', 'values', self.def_hdf_column(), expectedrows=100)
            
            for r in resource_list:
                with tables.open_file(os.path.join(TestGlobals.LOCAL_FEATURES_STORE,r['feature_filename']),'r') as h5file_feature:
                    group = getattr(h5file_feature.root, self.name)
                    feature_array_list = getattr(group, 'feature')
                    for idx,feature_array in enumerate(feature_array_list):
                        row = ()
                        for i in self.input_resource:
                            row += tuple([r[i]])
                        row += tuple([self.name])
                        row += tuple([feature_array])
                        for p in self.parameters:
                            row += tuple(getattr(group, p)[idx])
                        table.append([row])
            table.flush()
        return f.name


    def make_GET_request(self,response_type):
        
        uri = TestGlobals.ROOT+'/features/'+self.name+'/'+response_type+'?'
        query = []
        for i in self.input_resource:
            query += [i+'='+TestGlobals.RESOURCE_LIST[0][i]]
        query= '&'.join(query)
        command = uri + query
        return command

   
    def make_POST_request(self,response_type):
        
        command = TestGlobals.ROOT+'/features/'+self.name+'/'+response_type
        resource = etree.Element('resource')
        for r in TestGlobals.RESOURCE_LIST:
            query = {}
            for i in self.input_resource:
                query[i]=r[i]            
            value = etree.SubElement(resource,'feature',**query)
#            query = []
#            for i in self.input_resource:
#                query+=[i+'='+r[i]]
#            query= '&'.join(query)
#            value.text = query
        body = etree.tostring(resource)
        return command, body
    

    #@attr('xml')
    @attr(speed='slow')
    def test_GET_xmlresponse(self):
        
        response_code = 200
        response_type = 'xml'
        method = 'GET'

        #make request
        command= self.make_GET_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = TestGlobals.SESSION.c.http.request(command, headers = headers, method = method)

        etree_content_test = etree.XML(content)
        resource_list = [TestGlobals.RESOURCE_LIST[0]]
        etree_content_ideal = self.constuct_xml_response(command,resource_list)
        
        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isEqualXMLElement(etree_content_ideal,etree_content_test)
            
        
        #running tests
        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code
        
        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body

    test_GET_xmlresponse.method = 'GET'

    #attr('csv')
    #@attr('GET')     
    def test_GET_csvresponse(self):
    
        response_code = 200
        response_type = 'csv'
        method = 'GET'

        #make request
        command= self.make_GET_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = TestGlobals.SESSION.c.http.request(command, headers = headers, method = method)
        resource_list = [TestGlobals.RESOURCE_LIST[0]]
        csv_content_ideal = self.construct_csv_response(resource_list)

        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isCSVEqual(csv_content_ideal,content)

        
        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code
        

        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body


    @attr('hdf')
    @attr('GET')
    def test_GET_hdfresponse(self):
        import os 
        if not os.path.isdir(TestGlobals.TEMP_DIR):
            os.mkdir(TestGlobals.TEMP_DIR)
                
        response_code = 200
        response_type = 'hdf'
        method = 'GET'

        #make request
        command= self.make_GET_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'application/hdf5', 'Accept':'application/hdf5'})
        header, content = TestGlobals.SESSION.c.http.request(command, headers = headers, method = method)
        
        with tempfile.NamedTemporaryFile(dir=TestGlobals.TEMP_DIR, prefix='feature_', delete=False) as f:
            f.write(content)
            path = f.name
        resource_list = [TestGlobals.RESOURCE_LIST[0]]
        hdf_content_ideal_path = self.construct_hdf_response(resource_list)

        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isHDFEqual(hdf_content_ideal_path,path)

        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code        

        
        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body
        #clean up
        #os.remove(path)  

    @attr('xml')
    @attr('POST')
    def test_POST_xmlresponse(self):

        response_code = 200
        response_type = 'xml'
        method = 'POST'
        
        #make request
        command, body = self.make_POST_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = TestGlobals.SESSION.c.http.request(command, body=body , headers = headers, method = method)
        etree_content = etree.XML(content) #parse xml

        etree_content_test = etree.XML(content)
        resource_list = TestGlobals.RESOURCE_LIST
        etree_content_ideal = self.constuct_xml_response(command,resource_list)
         

        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isEqualXMLElement(etree_content_ideal,etree_content_test)

        
        #running tests
        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code
        
        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body


    @attr('csv')
    @attr('POST')   
    def test_POST_csvresponse(self):
    
        response_code = 200
        response_type = 'csv'
        method = 'POST'
        
        #make request
        command, body = self.make_POST_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = TestGlobals.SESSION.c.http.request(command, headers = headers, body=body, method = method)
        resource_list = TestGlobals.RESOURCE_LIST
        csv_content_ideal = self.construct_csv_response(resource_list)

        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isCSVEqual(csv_content_ideal,content)
        
            
        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code
        

        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body


    @attr('hdf')
    @attr('POST')
    def test_POST_hdfresponse(self):
        import os 
        if not os.path.isdir(TestGlobals.TEMP_DIR):
            os.mkdir(TestGlobals.TEMP_DIR)
        response_code = 200
        response_type = 'hdf'
        method = 'POST'

        #make request
        command, body = self.make_POST_request(response_type)
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = TestGlobals.SESSION.c.http.request(command, headers = headers, body=body, method = method)
        with tempfile.NamedTemporaryFile(dir='Temp', prefix='feature_', delete=False) as f:
            f.write(content)
            path = f.name
        resource_list = TestGlobals.RESOURCE_LIST
        hdf_content_ideal_path = self.construct_hdf_response(resource_list)

        def test_header_response_code():
            assert header['status'] == str(response_code) , "%r != %r" % (header['status'], str(response_code))

        def test_response_body():
            isHDFEqual(hdf_content_ideal_path,path)

        test_header_response_code.description = '%s Feature: %s Format Type: %s Check header response code'%( method, self.name, response_type)
        yield test_header_response_code        

        
        test_response_body.description = '%s Feature: %s Format Type: %s Check body response'%( method, self.name, response_type)
        yield test_response_body



