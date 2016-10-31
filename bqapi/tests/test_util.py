from bqapi import BQSession, BQServer
from bqapi.util import  fetch_dataset
from collections import OrderedDict
import nose
from nose import with_setup
import os
from bq.util.mkdir import _mkdir
from util import fetch_file
import ConfigParser
from bqapi.comm import BQCommError
from bqapi.util import *
import numpy as np
import urllib
from datetime import datetime
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

TEST_PATH = 'tests_%s'%urllib.quote(datetime.now().strftime('%Y%m%d%H%M%S%f'))  #set a test dir on the system so not too many repeats occur


from bqapi import USENODE
if USENODE:
    from bqapi.bqnode import  BQMex, BQNode, BQFactory
else:
    from bqapi.bqclass import  BQMex, BQNode, BQFactory

#setup comm test
def setUp():
    global results_location
    global store_local_location
    global file1_location
    global filename1
    global bqsession

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

    #start session
    bqsession = BQSession().init_local(user, pwd, bisque_root=root, create_mex=False)


def test_saveblob_1():
    """
        Saves an image to the blob service
    """
    try:
        result = save_blob(bqsession, localfile=file1_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status
    if result is None:
        assert False, 'XML Parsing error'


def test_saveblob_2():
    """
        Save an image to the blob service with xml tags
    """

    try:
        result = save_blob(bqsession, localfile=file1_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status
    if result is None:
        assert False, 'XML Parsing error'


def setup_fetchblob():
    """
        uploads an image
    """
    global image_uri
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))
    content = bqsession.postblob(file1_location, xml=resource)
    image_uri = etree.XML(content)[0].attrib['uri']


def teardown_fetchblob():
    pass


@with_setup(setup_fetchblob, teardown_fetchblob)
def test_fetchblob_1():
    """
        fetch blob and return path
    """
    try:
        result = fetch_blob(bqsession, image_uri, dest=results_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


@with_setup(setup_fetchblob, teardown_fetchblob)
def test_fetchblob_2():
    """
        fetch blob and return local path
    """
    try:
        result = fetch_blob(bqsession, image_uri, uselocalpath=True)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


def setup_fetchimageplanes():
    """
        uploads an image
    """
    global image_uri
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))
    content = bqsession.postblob(file1_location, xml=resource)
    image_uri = etree.XML(content)[0].attrib['uri']


def teardown_fetchimageplanes():
    pass


@with_setup(setup_fetchimageplanes, teardown_fetchimageplanes)
def test_fetchimageplanes_1():
    """
        fetch image planes and return path
    """
    try:
        result = fetch_image_planes(bqsession, image_uri, results_location, uselocalpath=False)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


@with_setup(setup_fetchimageplanes, teardown_fetchimageplanes)
def test_fetchimageplanes_2():
    """
        Fetch image planes and return path. Routine is run on same host as server.
    """
    try:
        result = fetch_image_planes(bqsession, image_uri, results_location,uselocalpath=True)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


def setup_fetchimagepixels():
    """
        uploads an image
    """
    global image_uri
    resource = etree.Element('resource', name=u'%s/%s'%(TEST_PATH, filename1))
    content = bqsession.postblob(file1_location, xml=resource)
    image_uri = etree.XML(content)[0].attrib['uri']

def teardown_fetchimagepixels():
    pass

@with_setup(setup_fetchimagepixels, teardown_fetchimagepixels)
def test_fetchimagepixels_1():
    """
        fetch image planes and return path
    """
    try:
        result = fetch_image_pixels(bqsession, image_uri, results_location,uselocalpath=True)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status

@with_setup(setup_fetchimagepixels, teardown_fetchimagepixels)
def test_fetchimagepixels_2():
    """
        fetch image planes and return path. Routine is run on same host as server.
    """
    try:
        result = fetch_image_pixels(bqsession, image_uri, results_location,uselocalpath=True)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status

def setup_fetchdataset():
    """
        uploads an dataset
    """
    global dataset_uri
    dataset = etree.Element('dataset', name='test')
    for _ in xrange(4):
        resource = etree.Element('resource', name=u'%s/%s'%(TEST_PATH, filename1))
        content = bqsession.postblob(file1_location, xml=resource)
        value=etree.SubElement(dataset,'value', type="object")
        value.text = etree.XML(content)[0].attrib['uri']
    content = bqsession.postxml('/data_service/dataset', dataset)
    dataset_uri = content.attrib['uri']

def teardown_fetchdataset():
    pass

@with_setup(setup_fetchdataset, teardown_fetchdataset)
def test_fetchdataset():
    """
        fetch dataset images
    """
    try:
        result = fetch_dataset(bqsession, dataset_uri, results_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


def setup_fetchImage():
    """
        uploads an image
    """
    global image_uri
    resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))
    content = bqsession.postblob(file1_location, xml=resource)
    image_uri = etree.XML(content)[0].attrib['uri']


def teardown_fetchImage():
    pass


@with_setup(setup_fetchImage, teardown_fetchImage)
def test_fetchImage_1():
    """
        fetch Image
    """
    try:
        result = fetchImage(bqsession, image_uri, results_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


@with_setup(setup_fetchImage, teardown_fetchImage)
def test_fetchImage_2():
    """
        fetch Image with localpath
    """
    try:
        result = fetchImage(bqsession, image_uri, results_location, uselocalpath=True)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


def setup_fetchDataset():
    """
        uploads an dataset
    """
    global dataset_uri
    dataset = etree.Element('dataset', name='test')
    for _ in xrange(4):
        resource = etree.Element ('resource', name=u'%s/%s'%(TEST_PATH, filename1))
        content = bqsession.postblob(file1_location, xml=resource)
        value=etree.SubElement(dataset,'value', type="object")
        value.text = etree.XML(content)[0].attrib['uri']
    content = bqsession.postxml('/data_service/dataset', dataset)
    dataset_uri = content.attrib['uri']


def teardown_fetchDataset():
    pass


@with_setup(setup_fetchDataset, teardown_fetchDataset)
def test_fetchDataset():
    """
        fetch Dataset images
    """
    try:
        result = fetchDataset(bqsession, dataset_uri, results_location)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status


def setup_saveimagepixels():
    """
        uploads an image
    """
    global image_uri
    resource = etree.Element('resource', name=u'%s/%s'%(TEST_PATH, filename1))
    content = bqsession.postblob(file1_location, xml=resource)
    image_uri = etree.XML(content)[0].attrib['uri']


def teardown_saveimagepixels():
    pass


@with_setup(setup_saveimagepixels, teardown_saveimagepixels)
def test_saveimagepixels():
    """
        Test save image pixels
    """
    #doesnt work without name on image
    xmldoc = """
    <image name="%s">
        <tag name="my_tag" value="test"/>
    </image>
    """%u'%s/%s'%(TEST_PATH, filename1)
    #bqimage = fromXml(etree.XML(xmldoc))
    bqimage = bqsession.factory.from_string (xmldoc)
    try:
        result = save_image_pixels(bqsession, file1_location, image_tags=bqimage)
    except BQCommError, e:
        assert False, 'BQCommError: Status: %s'%e.status
