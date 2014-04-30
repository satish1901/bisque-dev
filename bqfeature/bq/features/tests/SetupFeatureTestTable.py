#!/usr/bin/python 

"""
----------
setup.py 
----------

A script to create h5 file that stores features
to run the test script against

All the features are taken from the test classes with FeatureBase in the run test script
The features are stored in the features dir

"""
__module__    = "SetupFeatureTestTable"
__author__    = "Chris Wheat"
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
import tempfile 

def featureList():
    """
        a Facotry that produces a list of features in the test script
    """
    import run_test
    import inspect
    from  FeatureTest import FeatureBase
    feature_list = {}
    for n, item in inspect.getmembers(run_test):  # extractor.py to import correctly
        if inspect.isclass(item) and issubclass(item, FeatureBase):
            if not item.name == '': #removing base class
                feature_list[item.name] = item    
    return feature_list
    

if __name__ == '__main__':


    import TestGlobals #setups of the resources in bisque

    headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})

    feature_list = featureList() #create list of features
    
    #class Columns(tables.IsDescription):
    #    feature_name  = tables.StringCol(50,pos=1)
    
    for resource in TestGlobals.RESOURCE_LIST:
        if os.path.exists('features/'+resource['filename'] + '.h5'):
            print 'features/'+resource['filename']+'.h5'+' was found to already exist'
            print 'removing previous file'
            os.remove(os.path.join('features',resource['filename']+ '.h5'))
        h5file = tables.open_file( os.path.join('features',resource['filename'] + '.h5'), 'w')
        
        for feature_name in feature_list.keys():

            #create command
            feature_info = feature_list[feature_name]
            uri = TestGlobals.ROOT+'/features/'+feature_name+'/hdf?'
            query = []
            

            for i in feature_info.input_resource:
                query += [i+'='+resource[i]]
            
            query= '&'.join(query)
            command = uri + query

                 
            #send request
            try:
                print 'Making request at: %s'% command
                header, content = TestGlobals.SESSION.c.http.request(command, headers = headers)
            except BQCommError:
                print 'Error Occured'
            
            
            if not os.path.isdir(TestGlobals.TEMP):
                os.mkdir(TestGlobals.TEMP)
            with tempfile.NamedTemporaryFile(dir='Temp', prefix='feature_', delete=False) as f:
                f.write(content)
                path=f.name


            feature_group = h5file.createGroup(h5file.root,feature_name)
            vlarray = h5file.create_vlarray(feature_group, 'feature', tables.Float64Atom(), filters=tables.Filters(1))
            feature_array = []
            with tables.open_file(path,'r') as response_table:
                table=response_table.root.values
                for r in table:
                    feature_array.append(r['feature'])
                    
            feature_array = np.array( feature_array )
            vlarray.flavor = 'python'
            if len(feature_array) == 0:
                vlarray.append([0]) #dumby value if the feature server fails to calculate
            for array in feature_array:
                vlarray.append(array)
                            
            for p in feature_info.parameters:
                
                vlarray = h5file.create_vlarray(feature_group, p, tables.Float64Atom(), filters=tables.Filters(1))
                with tables.open_file(path,'r') as response_table:
                    table=response_table.root.values
                    parameter_array = []
                    for r in table:
                        parameter_array.append(r[p])   
                                     
                parameter_array = np.array( parameter_array )
                vlarray.flavor = 'python'    
           
                for array in parameter_array:
                    vlarray.append([array])                 
                        
            h5file.flush()
        h5file.close()
            
            
    bisque_archive_1_uri = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[0]['image_xml'])
    mask_1_uri           = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[0]['mask_xml'])
    bisque_archive_2_uri = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[1]['image_xml'])
    mask_2_uri           = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[1]['mask_xml'])
    bisque_archive_3_uri = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[2]['image_xml'])
    mask_3_uri           = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[2]['mask_xml'])
    bisque_archive_4_uri = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[3]['image_xml'])
    mask_4_uri           = TestGlobals.delete_resource( TestGlobals.RESOURCE_LIST[3]['mask_xml'])
    
    TestGlobals.cleanup_dir()
    TestGlobals.SESSION.finish_mex()
    
    