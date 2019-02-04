#!/usr/bin/python

""" Image service testing framework
update config to your system: config.cfg
call by: python run_tests.py
"""

__module__    = "run_tests"
__author__    = "Dmitry Fedorov"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
if sys.version_info  < ( 2, 7 ):
    import unittest2 as unittest
else:
    import unittest
import os
import posixpath
import urlparse
import time
from lxml import etree
import ConfigParser
import cPickle as pickle
from datetime import datetime

from bqapi import BQSession, BQCommError
from bqapi.util import save_blob, localpath2url

url_data  = '/data_service/'

config_file = 'config.cfg'
classes_file = 'classes_full.p'
classes_final_file = 'classes_final.p'
classes_test_file = 'test_results.p'

##################################################################
# Load classes
##################################################################

with open( classes_file, "rb" ) as f:
    classes = pickle.load(f)

with open( classes_final_file, "rb" ) as f:
    classes_final = pickle.load(f)

with open( classes_test_file, "rb" ) as f:
    classes_test = pickle.load(f)

##################################################################
# model document
##################################################################

resource = etree.Element('connoisseur', name="Watersipora: aiBrandon", resource_uniq="00-4Eq9rrT6SuWoApxPUNDgUf" )

files = [
    '/XYZ/network_weights.caffemodel',
    '/XYZ/mean.binaryproto',
    '/XYZ/deploy.prototxt',
    '/XYZ/solver.prototxt',
]
for f in files:
    v = etree.SubElement(resource, 'value')
    v.text = localpath2url(f)

etree.SubElement(resource, 'tag', name="author", value="dima")
etree.SubElement(resource, 'tag', name="license", type="license", value="unrestricted")
etree.SubElement(resource, 'tag', name="copyright", type="copyright", value="CBI, UCSB")
etree.SubElement(resource, 'tag', name="description", value="This model is trained on the Watersipora dataset for all species with at least 400 samples")
etree.SubElement(resource, 'tag', name="thumbnail", value="thumbnail.png")

# model attributes
etree.SubElement(resource, 'tag', name="status", value="finished")
etree.SubElement(resource, 'tag', name="framework", value="caffe")
etree.SubElement(resource, 'tag', name="model_output", value="classes")
etree.SubElement(resource, 'tag', name="training_set", type="dataset", value="http://localhost:8080/data_service/00-J5jBBavKHSNthrCqsyr8Fh")

etree.SubElement(resource, 'tag', name="minimum_samples", type="number", value="2000")
etree.SubElement(resource, 'tag', name="minimum_samples_augmentation", type="number", value="3000")
etree.SubElement(resource, 'tag', name="minimum_accuracy", type="number", value="0.70")
etree.SubElement(resource, 'tag', name="minimum_goodness", type="number", value="0.95")

etree.SubElement(resource, 'tag', name="batch_size", type="number", value="10")
etree.SubElement(resource, 'tag', name="model_patch_size", type="number,list", value="227,227,1,1,3")
etree.SubElement(resource, 'tag', name="db_patch_size", type="number,list", value="256,256,1,1,3")

# data adapters
a = etree.SubElement(resource, 'tag', name="adapter_pixels", value="rgb_2d_resized")
etree.SubElement(a, 'tag', name="accept_gobjects", value="point,polygon", type="string,list")
etree.SubElement(a, 'tag', name="width", value="6000", type="number")
etree.SubElement(a, 'tag', name="height", value="6000", type="number")

a = etree.SubElement(resource, 'tag', name="adapter_gobjects", value="gob_type_replace")
etree.SubElement(a, 'tag', name="accept_gobjects", value="point,polygon", type="string,list")
etree.SubElement(a, 'tag', name="replace_text", value="(Primary - |Secondary - )")
etree.SubElement(a, 'tag', name="replace_with", value="")

# classes in the data
t = etree.SubElement(resource, 'tag', name="classes_data")
for k,v in classes.iteritems():
    cc = etree.SubElement(t, 'tag', name='class', value=v['label'])
    etree.SubElement(cc, 'tag', name='id', type="number", value=str(v['class_label']))
    etree.SubElement(cc, 'tag', name='samples', type="number", value=str(v['total']))
print 'Number of classes in data: ', len(classes)

# classes selected for the model
t = etree.SubElement(resource, 'tag', name="classes_model")
for k,v in classes_test.iteritems():
    cc = etree.SubElement(t, 'tag', name='class', value=v['label'])
    etree.SubElement(cc, 'tag', name='id', type="number", value=str(v['class_label']))
    etree.SubElement(cc, 'tag', name='id_original', type="number", value=str(classes[v['label']]['class_label']))
    etree.SubElement(cc, 'tag', name='samples', type="number", value=str(v['total']))
    etree.SubElement(cc, 'tag', name='samples_training', type="number", value=str(v['n_train']))
    etree.SubElement(cc, 'tag', name='samples_validation', type="number", value=str(v['n_val']))
    etree.SubElement(cc, 'tag', name='samples_testing', type="number", value=str(v['n_test']))

    etree.SubElement(cc, 'tag', name='goodness', type="number,list", value='0.99')
    etree.SubElement(cc, 'tag', name='accuracy', type="number,list", value=str(v['accuracy']))
    etree.SubElement(cc, 'tag', name='error', type="number,list", value=str(v['error']))
    etree.SubElement(cc, 'tag', name='F1', type="number,list", value=str(v['F1']))
    etree.SubElement(cc, 'tag', name='MCC', type="number,list", value=str(v['F1']))
    etree.SubElement(cc, 'tag', name='false_positive', type="number", value=str(v['false_positive']))
    etree.SubElement(cc, 'tag', name='false_negative', type="number", value=str(v['false_negative']))
    etree.SubElement(cc, 'tag', name='true_positive', type="number", value=str(v['true_positive']))
print 'Number of classes in model: ', len(classes_test)

##################################################################
# Upload
##################################################################

config = ConfigParser.ConfigParser()
config.read(config_file)

root = config.get('Host', 'root') or 'localhost:8080'
user = config.get('Host', 'user') or 'test'
pswd = config.get('Host', 'password') or 'test'

session = BQSession().init_local(user, pswd,  bisque_root=root, create_mex=False)

url = urlparse.urljoin(root, url_data)
r = session.postxml(url, xml=etree.tostring(resource))
print r.get('uri')
