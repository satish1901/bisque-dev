from lxml import etree
import tables
import numpy as np
import csv
import pdb

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
    
def isEqualXMLElement(element_a,element_b):
    """
        Compares etree elements together
        inputs
        @element_a(etree) - etree element
        @element_b(etree) - etree element
        
        ouput
        asserts
        Compares an element of 2 xml etree structures
        
        #wanted to log results and keep track of all failres
    """
    assert element_a.tag == element_b.tag, '%s != %s'%(element_a.tag,element_b.tag)
    
    for name in element_b.attrib:
        if name not in element_a.attrib:
            assert 0, 'Element B has an attribute element A is missing: %s'%name    
    
    for name, value in element_a.attrib.items():
        if is_number(element_b.attrib.get(name)) and is_number(value):
            np.testing.assert_approx_equal(float(element_b.attrib.get(name)),float(value), 6)
        else:
            assert element_b.attrib.get(name) == value, 'Attribute of element A %s != attribute of element B %s' % (value,element_b.attrib.get(name))
    

    
    #compare feature vectors
    if element_a.tag =='value':
        element_a_array = np.array(element_a.text.split()).astype('float')
        element_b_array = np.array(element_b.text.split()).astype('float')
        np.testing.assert_almost_equal(element_a_array,element_b_array, 4)
    else:    
        assert element_a.text==element_b.text,'Text: %s != %s'%(element_a.text,element_b.text)
    
    subelement_a = element_a.getchildren()
    subelement_b = element_b.getchildren()
    assert len(subelement_a)==len(subelement_b),'%s != %s'%(len(subelement_a),len(subelement_b))
    
    for subele_a,subele_b in zip(sorted(subelement_a, key=lambda x:x.attrib.get('image')),sorted(subelement_b, key=lambda x:x.attrib.get('image'))):
        isEqualXMLElement(subele_a,subele_b)

    assert 1


def isCSVEqual(doc_a,doc_b):
    """
        Compares csv files together
        inputs
        @element_a(etree) - etree element
        @element_b(etree) - etree element
        
        ouput
        asserts
        Compares an element of 2 xml etree structures
        
        #TODO
        #wanted to log results and keep track of all failures
        #compare the elements together 
        #need to make it work for many different kind of inputs
        #only sorts on image right now
    """
    parsed_csv_a = list(csv.reader( doc_a.splitlines(), delimiter=',', quotechar='"'))
    parsed_csv_b = list(csv.reader( doc_b.splitlines(), delimiter=',', quotechar='"'))
    
    #check to see if the same length
    assert len(parsed_csv_a)==len(parsed_csv_b), '%s!=%s'%(len(parsed_csv_a),len(parsed_csv_b))
    
    #check if titles are the same
    assert parsed_csv_a[0]==parsed_csv_b[0], '%s != %s'%( '%s...'%parsed_csv_a[0][:30] if len(parsed_csv_a[0])>30 else parsed_csv_a[0],
                                                          '%s...'%parsed_csv_b[0][:30] if len(parsed_csv_b[0])>30 else parsed_csv_b[0])

    #sorting based on the resource uris
    sorted_csv_rows_a = sorted(parsed_csv_a[1:],key=lambda x:x[2])
    sorted_csv_rows_b = sorted(parsed_csv_b[1:],key=lambda x:x[2])

    for row_a,row_b in zip(sorted_csv_rows_a,sorted_csv_rows_b):
        assert len(row_a)==len(row_b), '%s!=%s'%(len(row_a),len(row_b))
        for ncol in range(1,len(row_a)):
            if parsed_csv_a[0][ncol]=='descriptor':
                element_a_array = np.array(row_a[ncol].split(',')).astype('float')
                element_b_array = np.array(row_b[ncol].split(',')).astype('float')
                np.testing.assert_array_almost_equal(element_a_array,element_b_array, decimal=4)  
            elif is_number(row_a[ncol]) and is_number(row_b[ncol]):
                np.testing.assert_approx_equal(float(row_a[ncol]),float(row_b[ncol]), 6)
            else:
                assert row_a[ncol]==row_b[ncol], '%s != %s'%( '%s...'%row_a[ncol][:30] if len(row_a[ncol])>30 else row_a[ncol],
                                                              '%s...'%row_b[ncol][:30] if len(row_b[ncol])>30 else row_b[ncol])
    
    assert 1


def isHDFEqual(path_hdf_a,path_hdf_b):
    """
        Compares csv files together
        
        inputs
        @path_hdf_a(str) - path to the hdf file being compared
        @path_hdf_b(str) - path to the hdf file being compared
        
        ouput
        asserts
        Compares hdf5 tables
        
        #TODO
        #wanted to log results and keep track of all failures
        #compare the elements together
    """

    with tables.open_file(path_hdf_a,'r') as h5file_a:
        with tables.open_file(path_hdf_b,'r') as h5file_b:
           table_a = h5file_a.root.values
           table_b = h5file_b.root.values
           
           assert set(table_a.colnames)==set(table_b.colnames), '%s!=%s'%(table_a.colnames,table_b.colnames)
           
           sorted_resource_a = sorted(zip(range(len(table_a)),table_a[:]['image']), key=lambda x:x[1:])
           sorted_resource_b = sorted(zip(range(len(table_b)),table_b[:]['image']), key=lambda x:x[1:])

           for idx_a,idx_b in zip(zip(*sorted_resource_a)[0],zip(*sorted_resource_b)[0]):
               for colname in table_a.colnames:
                   if colname == 'feature':
                       np.testing.assert_array_almost_equal(table_a[idx_a][colname],table_b[idx_b][colname], 4)
                   else:
                       assert table_a[idx_a][colname] == table_b[idx_b][colname], '%s!=%s' %(table_a[idx_a][colname],
                                                                                             table_b[idx_b][colname])
            
    assert 1
            
            
            
            
            
    