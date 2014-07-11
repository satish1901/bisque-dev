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
import run_test
import inspect
from  FeatureTest import FeatureBase
from run_test import tearDownModule
import TestGlobals #setups of the resources in bisque
from bqapi.comm import BQSession, BQCommError
from utils import resource_info
def featureList():
    """
        a Facotry that produces a list of features in the test script
    """
#    import run_test
#    import inspect
#    from  FeatureTest import FeatureBase
    feature_list = {}
    for n, item in inspect.getmembers(run_test):  # extractor.py to import correctly
        if inspect.isclass(item) and issubclass(item, FeatureBase):
            if not item.name == '': #removing base class
                feature_list[item.name] = item    
    return feature_list
    

if __name__ == '__main__':
    

    #assigns the create session to global
    TestGlobals.SESSION = BQSession().init_local( TestGlobals.USER, TestGlobals.PWD, bisque_root = TestGlobals.ROOT, create_mex = True)
    
    #importing resources
    RESOURCE_LIST = []
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_1, TestGlobals.MASK_1, TestGlobals.FEATURE_1) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_2, TestGlobals.MASK_2, TestGlobals.FEATURE_2) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_3, TestGlobals.MASK_3, TestGlobals.FEATURE_3) )
    RESOURCE_LIST.append( resource_info(TestGlobals.SESSION, TestGlobals.BISQUE_ARCHIVE_4, TestGlobals.MASK_4, TestGlobals.FEATURE_4) )
    TestGlobals.RESOURCE_LIST = RESOURCE_LIST
    
    headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})

    feature_list = featureList() #create list of features
    
    #class Columns(tables.IsDescription):
    #    feature_name  = tables.StringCol(50,pos=1)
    
    if not os.path.exists('features'):
        os.mkdir('features')
    
    for resource in TestGlobals.RESOURCE_LIST:
        feature_filename = os.path.join('features','%s'%resource['feature_filename'])
        if os.path.exists(feature_filename):
            print feature_filename +' was found to already exist'
            print 'removing previous file'
            os.remove(feature_filename)
        h5file = tables.open_file(feature_filename, 'w')
        
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
            
            
            if not os.path.isdir( TestGlobals.TEMP_DIR):
                os.mkdir( TestGlobals.TEMP_DIR)
            with tempfile.NamedTemporaryFile( dir = TestGlobals.TEMP_DIR, prefix='feature_', delete=False) as f:
                f.write(content)
                path=f.name


            feature_group = h5file.createGroup( h5file.root,feature_name)
            vlarray = h5file.create_vlarray( feature_group, 'feature', tables.Float64Atom(), filters=tables.Filters(1))
            feature_array = []
            with tables.open_file(path,'r') as response_table:
                table = response_table.root.values
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
            
    tearDownModule()

    
    