from bqapi import BQSession, BQServer
from bqapi.util import  fetch_dataset
from collections import OrderedDict, namedtuple
import nose
from nose import with_setup
import os
from bq.util.mkdir import _mkdir
from util import fetch_file
from lxml import etree
import ConfigParser
from bqapi.comm import BQCommError
from bqapi.util import *
import numpy as np
import urllib
from datetime import datetime
from bqapi.bqfeature import *

TEST_PATH = 'tests_%s'%urllib.quote(datetime.now().strftime('%Y%m%d%H%M%S%f'))  #set a test dir on the system so not too many repeats occur


#setup comm test
def setUp():
    global results_location
    global store_local_location
    global file1_location
    global filename1
    global bqsession
    global FeatureResource
    
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
    
    FeatureResource = namedtuple('FeatureResource',['image','mask','gobject'])
    FeatureResource.__new__.__defaults__ = (None, None, None)
    #start session
    bqsession = BQSession().init_local(user, pwd, bisque_root=root, create_mex=False)
    
def setup_bqfeature_fetch():
    """
        uploads an image
    """
    global resource_list
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))  
    content = bqsession.postblob(file1_location, xml=resource)
    uniq = etree.XML(content)[0].attrib['resource_uniq']
    image_uri = '%s/image_service/image/%s'%(bqsession.bisque_root,uniq)
    resource_list = [FeatureResource(image=image_uri)]
    
    
def teardown_bqfeature_fetch():
    pass


@with_setup(setup_bqfeature_fetch, teardown_bqfeature_fetch)
def test_bqfeature_fetch_1():
    """
        Test feature fetch and returning hdf5 file
    """
    filename = 'bqfeature_fetch_1.h5'
    path = os.path.join(results_location, filename)
    filename = Feature().fetch(bqsession, 'CLD', resource_list, path=path)


@with_setup(setup_bqfeature_fetch, teardown_bqfeature_fetch)
def test_bqfeature_fetch_2():
    """
        Test feature fetch and returning pytables object
    """
    hdf5 = Feature().fetch(bqsession, 'CLD', resource_list)
    hdf5.close()
    os.remove(hdf5.filename)

def setup_bqfeature_fetchvector():
    """
        uploads an image
    """
    global resource_list
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))  
    content = bqsession.postblob(file1_location, xml=resource)
    uniq = etree.XML(content)[0].attrib['resource_uniq']
    image_uri = '%s/image_service/image/%s'%(bqsession.bisque_root,uniq)
    resource_list = [FeatureResource(image=image_uri)]
    
    
def teardown_bqfeature_fetchvector():
    pass


def test_bqfeature_fetchvector_1():
    """
        Test fetch vector
    """
    feature_vector = Feature().fetch_vector(bqsession, 'CLD', resource_list)



def setup_bqparallelfeature_fetch():
    """
        uploads a list of images
    """
    global resource_list
    resource_list = []
    for _ in xrange(10):
        resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))  
        content = bqsession.postblob(file1_location, xml=resource)
        uniq = etree.XML(content)[0].attrib['resource_uniq']
        resource_list.append(FeatureResource(image='%s/image_service/image/%s'%(bqsession.bisque_root,uniq)))


def teardown_bqparallelfeature_fetch():
    """
    """
    pass


@with_setup(setup_bqparallelfeature_fetch, teardown_bqparallelfeature_fetch)
def test_bqparallelfeature_fetch_1():
    """
        Test parallel feature fetch vector and returning pytables object
    """
    PF=ParallelFeature()
    PF.set_thread_num(1)
    PF.set_chunk_size(5)
    hdf5 = PF.fetch(bqsession, 'CLD', resource_list)
    hdf5.close()
    os.remove(hdf5.filename)

@with_setup(setup_bqparallelfeature_fetch, teardown_bqparallelfeature_fetch)
def test_bqparallelfeature_fetch_2():
    """
        Test parallel feature fetch vector and return a file
    """
    filename = 'bqparallelfeature_fetch_2.h5'
    path = os.path.join(results_location, filename)
    PF=ParallelFeature()
    PF.set_thread_num(1)
    PF.set_chunk_size(5)
    filename = PF.fetch(bqsession, 'CLD', resource_list, path=path)
    

def setup_bqparallelfeature_fetchvector():
    """
        Uploads a list of images
    """
    global resource_list
    resource_list = []
    for _ in xrange(10):
        resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))  
        content = bqsession.postblob(file1_location, xml=resource)
        uniq = etree.XML(content)[0].attrib['resource_uniq']
        resource_list.append(FeatureResource(image='%s/image_service/image/%s'%(bqsession.bisque_root,uniq)))
    
    
def teardown_bqparallelfeature_fetchvector():
    """
    """
    pass


@with_setup(setup_bqparallelfeature_fetchvector, teardown_bqparallelfeature_fetchvector)
def test_bqparallelfeature_fetchvector_1():
    """
        Test parallel feature fetch vector
    """
    PF=ParallelFeature()
    PF.set_thread_num(1)
    PF.set_chunk_size(5)
    feature_vectors = PF.fetch_vector(bqsession, 'CLD', resource_list)



