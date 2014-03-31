#!/usr/bin/python 

"""
----------
setup.py 
----------

A script to create h5 file that stores features
to run the test script against

"""
__module__    = "setup"
__author__    = "Dmitry Fedorov & Chris Wheat"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


import tables
import lxml
from lxml import etree
import numpy as np
import os
import ConfigParser
import pdb
from FeatureTestModule import Feature_List
from run_test import FeatureServiceTestBase, setUpTest
from run_test import bisque_archive_1, mask_1, bisque_archive_2, mask_2, bisque_archive_3, mask_3, bisque_archive_4, mask_4
from bqapi.comm import BQSession, BQCommError # local

if __name__ == '__main__':

    setUpTest()
    
    FeatureServiceTestBase.session = BQSession().init_local( FeatureServiceTestBase.user, FeatureServiceTestBase.pswd, bisque_root=FeatureServiceTestBase.root, create_mex = True)
    
    FeatureServiceTestBase.resource_list = []
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_1, mask_1))
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_2, mask_2))
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_3, mask_3))
    FeatureServiceTestBase.resource_list.append( FeatureServiceTestBase.return_archive_info( bisque_archive_4, mask_4))    

    headers = FeatureServiceTestBase.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})

    feature_list = Feature_List().get_List('all')
    
    class Columns(tables.IsDescription):
        feature_name  = tables.StringCol(50,pos=1)
    
    for r in FeatureServiceTestBase.resource_list:
        if os.path.exists('features/'+r['filename'] + '.h5'):
            print 'features/'+r['filename']+'.h5'+' was found to already exist'
            print 'removing previous file'
            os.remove('features/'+r['filename']+ '.h5')
        h5file = tables.open_file( 'features/'+r['filename'] + '.h5', 'w')
        
        for feature_test.name in feature_list:

            #create command
            feature_info = Feature_List().feature_list[feature_name]()
            uri = FeatureServiceTestBase.root+'/features/'+feature_name+'/xml?'
            query = []
            
            for i in feature_info.input_type:
                query += [i+'='+r[i]]
            
            query= '&'.join(query)
            command = uri + query
            
            vlarray = h5file.create_vlarray(h5file.root, feature_name, tables.Float64Atom(), filters=tables.Filters(1))
            
            #send request
            try:
                print 'Making request at: %s'% command
                header, content = FeatureServiceTestBase.session.c.http.request(command, headers = headers)
            except BQCommError:
                print 'Error Occured'
                
            #parse return request
            try:
                content = etree.fromstring( content)
                features = content.xpath('feature/value')
            except:
                features = []

            print 'Storing: %s feature vectors'%feature_name     
                   
            #store features in table
            feature_array = []
            for f in features:
                feature_array.append( f.text.split() )
                
            feature_array = np.array( feature_array )
                
            
            vlarray.flavor = 'python'
            if len(feature_array) == 0:
                vlarray.append(0) #dumby value if the feature server fails to calculate
            for array in feature_array:
                vlarray.append(array)
            h5file.flush()
        h5file.close()
            
            
    bisque_archive_1_uri = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[0]['image_xml'])
    mask_1_uri           = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[0]['mask_xml'])
    bisque_archive_2_uri = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[1]['image_xml'])
    mask_2_uri           = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[1]['mask_xml'])
    bisque_archive_3_uri = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[2]['image_xml'])
    mask_3_uri           = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[2]['mask_xml'])
    bisque_archive_4_uri = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[3]['image_xml'])
    mask_4_uri           = FeatureServiceTestBase.delete_resource( FeatureServiceTestBase.resource_list[3]['mask_xml'])
    
    FeatureServiceTestBase.cleanup_tests_dir()
    FeatureServiceTestBase.session.finish_mex()
    
    