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
import ConfigParser
from bqapi.comm import BQSession, BQCommError

from bq.image_service.tests.tests_base import ImageServiceTestBase

image_unicode       = 'пустыня.jpg' #utf-8 encoded filename

##################################################################
# ImageServiceTests
##################################################################

class ImageServiceTestsUnicode(ImageServiceTestBase):

    # setups

    @classmethod
    def setUpClass(self):
        config = ConfigParser.ConfigParser()
        config.read('config.cfg')

        self.root = config.get('Host', 'root') or 'localhost:8080'
        self.user = config.get('Host', 'user') or 'test'
        self.pswd = config.get('Host', 'password') or 'test'

        self.session = BQSession().init_local(self.user, self.pswd,  bisque_root=self.root, create_mex=False)

        # download and upload test images ang get their IDs
        self.resource_unicode   = self.ensure_bisque_file(image_unicode.decode('utf-8'))
           

    @classmethod
    def tearDownClass(self):
        self.delete_resource(self.resource_unicode)
        self.cleanup_tests_dir()
        pass

    # tests

    def test_thumbnail_unicode(self):
        resource = self.resource_unicode
        self.assertIsNotNone(resource, 'Resource was not uploaded')
        filename = 'unicode.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '73',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }
        self.validate_image_variant(resource, filename, commands, meta_required)


#def suite():
#    tests = ['test_thumbnail']
#    return unittest.TestSuite(map(ImageServiceTests, tests))

if __name__=='__main__':
    if not os.path.exists('images'):
        os.makedirs('images')
    if not os.path.exists('tests'):
        os.makedirs('tests')
    unittest.main(verbosity=2)
