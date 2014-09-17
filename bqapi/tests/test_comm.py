from bqapi import BQSession, BQServer
from bqapi.util import  fetch_dataset
from collections import OrderedDict
import nose
from nose import with_setup
import os
from bq.util.mkdir import _mkdir
from util import fetch_file
from lxml import etree
import urllib
from datetime import datetime
import ConfigParser
import time
from threading import Thread
import Queue
#
#def test_fetch_dataset():
#    """
#        check that you can place a dataset locally
#    """
#
#    bq = BQSession().init_local('kgk', 'Al1brary')
#    dsdir = bq.load('http://loup.ece.ucsb.edu/ds/datasets')
#    ds1 = dsdir.kids[0]
#    print "FOUND ", ds1.uri
#    #fetch_dataset(bq, ds1.uri, ".")
#
#    fetch_dataset(bq, ds1.uri, ".", uselocalpath=True)

TEST_PATH = 'tests_%s'%urllib.quote(datetime.now().strftime('%Y%m%d%H%M%S%f'))  #set a test dir on the system so not too many repeats occur

#setup comm test
def setUp():
    """
        Setup comm test
    """
    global root
    global user
    global pwd
    global results_location
    global store_local_location
    global file1_location
    global filename1
    
    config = ConfigParser.ConfigParser()
    config.read('setup.cfg')
    root = config.get('Host', 'root') or 'localhost:8080'
    user = config.get('Host', 'user') or 'test'
    pwd = config.get('Host', 'password') or 'test'
    results_location = config.get('Store', 'results_location') or 'Results'
    _mkdir(results_location)
    
    store_location = config.get('Store', 'location') or None
    if store_location is None: raise NameError('Requre a store location to run test properly')
    
    store_local_location = config.get('Store', 'local_location') or 'SampleData'
    
    
    filename1 = config.get('Store','filename1') or None
    if filename1 is None: raise NameError('Requre an image to run test properly')
    file1_location = fetch_file(filename1, store_location, store_local_location)


def tearDownClass():
    """
        Tear Down comm test
    """
    pass

#############################
###   BQServer
#############################
def test_prepare_url_1():
    """
    """
    server = BQServer()
    check_url = 'http://bisque.ece.ucsb.edu/image/00-123456789?remap=gray&format=tiff'
    url = 'http://bisque.ece.ucsb.edu/image/00-123456789'
    odict = OrderedDict([('remap','gray'),('format','tiff')])
    url = server.prepare_url(url, odict=odict)
    assert url == check_url

def test_prepare_url_2():
    """
    """
    server = BQServer()
    check_url = 'http://bisque.ece.ucsb.edu/image/00-123456789?remap=gray&format=tiff'
    url = 'http://bisque.ece.ucsb.edu/image/00-123456789'
    url = server.prepare_url(url, remap='gray', format='tiff')
    assert url == check_url

def test_prepare_url_3():
    """
    """
    server = BQServer()
    check_url = 'http://bisque.ece.ucsb.edu/image/00-123456789?format=tiff&remap=gray'
    url = 'http://bisque.ece.ucsb.edu/image/00-123456789'
    odict = OrderedDict([('remap','gray')])
    url = server.prepare_url(url, odict=odict, format='tiff')
    assert url == check_url


#Test BQSession
def test_open_session():
    """
        Test Initalizing a BQSession locally
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root, create_mex=False)
    bq.close()
    
    
def test_initalize_mex_locally():
    """
        Test initalizing a mex locally
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    bq.close()
    

def test_initalize_session_From_mex():
    """
        Test initalizing a session from a mex
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    mex_url = bq.mex.uri
    token = bq.mex.resource_uniq
    bqmex = BQSession().init_mex(mex_url, token, user, bisque_root=root)
    bqmex.close()
    bq.close()
    
    
def test_fetchxml_1():
    """
        Test fetch xml 
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    response_xml = bq.fetchxml(root+'/data_service/'+user) #fetches the user
    bq.close()
    if not isinstance(response_xml, etree._Element):
        assert False %'Did not return XML!'

def test_fetchxml_2():
    """
        Test fetch xml and save the document to disk
    """
    filename = 'fetchxml_test_2.xml'
    path = os.path.join(results_location,filename)
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    path = bq.fetchxml(root+'/data_service/'+user, path=path) #fetches the user
    bq.close()
    
    try:
        with open(path,'r') as f:
            etree.XML(f.read()) #check if xml was returned
            
    except etree.Error:
        assert False %'Did not return XML!'


def test_postxml_1():
    """
        Test post xml
    """
    
    test_document ="""
    <file name="test_document">
        <tag name="my_tag" value="test"/>
    </file>
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    response_xml = bq.postxml(root+'/data_service/file', xml=test_document)
    bq.close()
    if not isinstance(response_xml, etree._Element):
        assert False %'Did not return XML!'
        
        
def test_postxml_2():
    """
        Test post xml and save the document to disk
    """
    
    test_document ="""
    <file name="test_document">
        <tag name="my_tag" value="test"/>
    </file>
    """
    filename = 'postxml_test_2.xml'
    path = os.path.join(results_location,filename)
    
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    path = bq.postxml(root+'/data_service/file', test_document, path=path)
    bq.close()
    
    try:
        with open(path,'r') as f:
            etree.XML(f.read()) #check if xml was returned
            
    except etree.Error:
        assert False %'Did not return XML!'


def setup_fetchhdf():
    """
        uploads an image, initalized session and constructs the 
        resource_uri
    """
    global resource_uri #features service requests
    global bqsession
    bqsession = BQSession().init_local(user, pwd, bisque_root=root)
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1)) 
    content = bqsession.postblob(file1_location, xml=resource) #upload image
    resource_uniq = etree.XML(content)[0].attrib['resource_uniq']
    resource_uri = '%s/features/EHD/hdf?image=%s/image_service/image/%s'%(root,root,resource_uniq)
    
    
def teardown_fetchhdf():
    pass


@with_setup(setup_fetchhdf, teardown_fetchhdf)
def test_fetchhdf_1():
    """
        Test fetching an hdf file from feature service and returning
        a pytables object
    """
    hdf5object = bqsession.fetchhdf(resource_uri)
    hdf5object.close()


@with_setup(setup_fetchhdf, teardown_fetchhdf)
def test_fetchhdf_2():
    """
        Test fetching an hdf file from feature service and saving file
        to disk
    """
    filename = 'fetchhdf_test_2.h5'
    path = os.path.join(results_location,filename)
    path = bqsession.fetchhdf(resource_uri, path=path)


def setup_posthdf():
    """
        uploads a list of image, initalized session, constructs xml body, 
    """
    global resource_uri
    global resource_body
    global bqsession
    bqsession = BQSession().init_local(user, pwd, bisque_root=root)
    resource_body = etree.Element('resource')
    for _ in xrange(4):
        resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))        
        content = bqsession.postblob(file1_location, xml=resource)
        resource_uniq = etree.XML(content)[0].attrib['resource_uniq']
        image = '%s/image_service/image/%s'%(root,resource_uniq)
        etree.SubElement(resource_body,'feature',image=image)
    resource_uri = '%s/features/EHD/hdf'%root
    
    
def teardown_posthdf():
    pass


@with_setup(setup_posthdf, teardown_posthdf)
def test_posthdf_1():
    """
        Test posting xml and hdf file from feature service and returning
        a pytables object
    """
    hdf5object = bqsession.posthdf(resource_uri, xml=resource_body)
    hdf5object.close()


@with_setup(setup_posthdf, teardown_posthdf)
def test_posthdf_2():
    """
        Test fetching and hdf file from feature service and saving file
        to disk
    """
    filename = 'posthdf_test_2.h5'
    path = os.path.join(results_location,filename)
    path = bqsession.posthdf(resource_uri, xml=resource_body, path=path)


def test_fetchblob_1():
    """
        
    """
    pass


def test_postblob_1():
    """
        Test post blob
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))        
    content = bqsession.postblob(file1_location, xml=resource)
    bq.close()


def test_postblob_2():
    """
        Test post blob and save the returned document to disk
    """
    filename = 'postblob_test_2.xml'
    path = os.path.join(results_location,filename)
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))        
    path = bqsession.postblob(file1_location, xml=resource, path=path)
    bq.close()
    
    try:
        with open(path,'r') as f:
            etree.XML(f.read()) #check if xml was returned
            
    except etree.Error:
        assert False %'Did not return XML!'    
    
def test_postblob_3():
    """
        Test post blob with xml attached
    """
    
    test_document = """
    <image name="%s">
        <tag name="my_tag" value="test"/>
    </image>
    """%u'%s/%s'%(TEST_PATH, filename1)      
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    content = bq.postblob(file1_location, xml=test_document)
    bq.close()
    

def test_run_mex():
    """
        Test run mex 
    """
    bq = BQSession().init_local(user, pwd, bisque_root=root)
    mex_uri = bq.mex.uri
    bq.update_mex(status="IN PROGRESS", tags = [], gobjects = [], children=[], reload=False)
    response_xml = bq.fetchxml(mex_uri) #check xml
    
    bq.finish_mex()
    response_xml = bq.fetchxml(mex_uri) #check xml
    
    bq.close()
    