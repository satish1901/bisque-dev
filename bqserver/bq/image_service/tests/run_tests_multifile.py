#!/usr/bin/python

""" Image service operational testing framework
update config to your system: config.cfg
call by: python run_tests_thirdpartysupport.py
"""

__module__    = "run_tests_multifile"
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
import time
import shortuuid

from bqapi.comm import BQSession

from bq.image_service.tests.tests_base import ImageServiceTestBase

TEST_PATH = 'tests_multifile_%s'%shortuuid.uuid()

package_bisque = {
    'file': 'bisque-20140804.143944.tar.gz',
    'resource': '<resource name="%s/bisque-20140804.143944.tar.gz"><tag name="ingest" ><tag name="type" value="zip-bisque" /></tag></resource>'%TEST_PATH,
    'count': 20,
    'name': 'COPR Subset',
}

package_different = {
    'file': 'different_images.tar.gz',
    'resource': '<resource name="%s/different_images.tar.gz"><tag name="ingest" ><tag name="type" value="zip-multi-file" /></tag></resource>'%TEST_PATH,
    'count': 4,
    'name': 'different_images.tar.gz',
}


#<resource name="tests_multi/bill_smith_cells_5D_5Z_4T.zip" ><tag name="ingest" ><tag name="type" value="zip-5d-image" /><tag name="number_z" value="5" /><tag name="number_t" value="4" /><tag name="resolution_title" value="" /><tag name="resolution_x" value="0.4" /><tag name="resolution_y" value="0.4" /><tag name="resolution_z" value="0.8" /><tag name="resolution_t" value="2" /></tag></resource>
#package_tiff_5d        = 'smith_4d_5z_4t_simple.zip'

#<resource name="tests_multi/smith_t_stack_simple.zip" ><tag name="ingest" ><tag name="type" value="zip-time-series" /><tag name="resolution_title" value="" /><tag name="resolution_x" value="0.5" /><tag name="resolution_y" value="0.5" /><tag name="resolution_t" value="0.8" /></tag></resource>
#package_tiff_time      = 'smith_t_stack_simple.zip'

#<resource name="tests_multi/smith_z_stack_tiff.zip" ><tag name="ingest" ><tag name="type" value="zip-z-stack" /><tag name="resolution_title" value="" /><tag name="resolution_x" value="0.4" /><tag name="resolution_y" value="0.4" /><tag name="resolution_z" value="0.9" /></tag></resource>
#package_tiff_depth     = 'smith_z_stack_tiff.zip'


######################################
# imarisconvert supported files
######################################

image_leica_lif = {
    'file': 'APDnew.lif',
    'resource': '<resource name="%s/APDnew.lif" />'%TEST_PATH,
    'count': 2,
    'name': 'APDnew.lif',
}

package_andor_iq = {
    'file': 'AndorMM.zip',
    'resource': '<resource name="%s/AndorMM.zip" ><tag name="ingest" ><tag name="type" value="zip-proprietary" /></tag></resource>'%TEST_PATH,
    'count': 3,
    'name': 'AndorMM.zip',
}

package_imaris_leica = {
    'file': 'bad_beads_2stacks_chart.zip',
    'resource': '<resource name="%s/bad_beads_2stacks_chart.zip" ><tag name="ingest" ><tag name="type" value="zip-proprietary" /></tag></resource>'%TEST_PATH,
    'count': 3,
    'name': 'bad_beads_2stacks_chart.zip',
}



##################################################################
# ImageServiceTests
##################################################################

class ImageServiceTestsThirdParty(ImageServiceTestBase):

    # setups

    @classmethod
    def setUpClass(cls):
        config = ConfigParser.ConfigParser()
        config.read('config.cfg')

        cls.root = config.get('Host', 'root') or 'localhost:8080'
        cls.user = config.get('Host', 'user') or 'test'
        cls.pswd = config.get('Host', 'password') or 'test'

        cls.session = BQSession().init_local(cls.user, cls.pswd,  bisque_root=cls.root, create_mex=False)

        # download and upload test packages
        cls.ensure_bisque_package(package_bisque)
        cls.ensure_bisque_package(package_different)
        cls.ensure_bisque_package(image_leica_lif)
        

    @classmethod
    def tearDownClass(cls):
        cls.delete_package(package_bisque)
        cls.delete_package(package_different)
        cls.delete_package(image_leica_lif)
        
        
        cls.cleanup_tests_dir()
        pass

    # tests
    
    # ---------------------------------------------------
    # bisque package
    # ---------------------------------------------------
    def test_contents_bisque_package (self):
        package = package_bisque
        
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertEqual(package['count'], len(package['items']))
        self.assertEqual(package['name'], package['resource'].get('name'))
        
        resource = package['last']
        self.assertTrue('%s/COPR%20Subset'%TEST_PATH in resource.get('value'))
        self.assertEqual(len(resource.xpath('tag[@name="Genus"]')), 1)
        
    def test_thumbnail_bisque_package (self):
        package = package_bisque
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'bisque_package.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 
            'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '128',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' 
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_meta_bisque_package (self):
        package = package_bisque
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'bisque_package.meta.xml'
        commands = [('meta', None)]
        meta_required = [
            { 'xpath': '//tag[@name="image_num_x"]', 'attr': 'value', 'val': '2592' },
            { 'xpath': '//tag[@name="image_num_y"]', 'attr': 'value', 'val': '1728' },
            { 'xpath': '//tag[@name="image_num_c"]', 'attr': 'value', 'val': '3' },
            { 'xpath': '//tag[@name="image_num_z"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_num_t"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_pixel_depth"]', 'attr': 'value', 'val': '8' },
            { 'xpath': '//tag[@name="image_pixel_format"]', 'attr': 'value', 'val': 'unsigned integer' },
            { 'xpath': '//tag[@name="format"]',      'attr': 'value', 'val': 'JPEG' },
            { 'xpath': '//tag[@name="image_num_series"]', 'attr': 'value', 'val': '0' },
            #{ 'xpath': '//tag[@name="pixel_resolution_x"]', 'attr': 'value', 'val': '0.160490234375' },
            #{ 'xpath': '//tag[@name="pixel_resolution_y"]', 'attr': 'value', 'val': '0.160490234375' },
            #{ 'xpath': '//tag[@name="pixel_resolution_z"]', 'attr': 'value', 'val': '1.0' },
            #{ 'xpath': '//tag[@name="pixel_resolution_unit_x"]', 'attr': 'value', 'val': 'microns' },
            #{ 'xpath': '//tag[@name="pixel_resolution_unit_y"]', 'attr': 'value', 'val': 'microns' },
            #{ 'xpath': '//tag[@name="pixel_resolution_unit_z"]', 'attr': 'value', 'val': 'microns' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)

   
    
    # ---------------------------------------------------
    # different package
    # ---------------------------------------------------
    def test_contents_different_package (self):
        package = package_different
        
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertEqual(package['count'], len(package['items']))
        self.assertEqual(package['name'], package['resource'].get('name'))
        
        resource = package['last']
        self.assertTrue('%s/different_images.tar.gz.unpacked/'%TEST_PATH in resource.get('value'))
        
    def test_thumbnail_different_package (self):
        package = package_different
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'different_package.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 
            'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '96',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' 
        }
        self.validate_image_variant(resource, filename, commands, meta_required)
    
    # ---------------------------------------------------
    # image_leica_lif package
    # ---------------------------------------------------

    def test_contents_package_leica_lif (self):
        package = image_leica_lif
        
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertEqual(package['count'], len(package['items']))
        self.assertEqual(package['name'], package['resource'].get('name'))
        
        resource = package['last']
        name = "%s#%s"%(package['file'], len(package['items'])-1)
        self.assertEqual(resource.get('name'), name)        
        self.assertTrue('%s/%s'%(TEST_PATH, name) in resource.get('value'))
        
    def test_thumbnail_bisque_package (self):
        package = image_leica_lif
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'bisque_package.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 
            'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '128',
            'image_num_c': '1',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' 
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_meta_package_leica_lif (self):
        package = image_leica_lif
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'bisque_package.meta.xml'
        commands = [('meta', None)]
        meta_required = [
            { 'xpath': '//tag[@name="image_num_x"]', 'attr': 'value', 'val': '512' },
            { 'xpath': '//tag[@name="image_num_y"]', 'attr': 'value', 'val': '512' },
            { 'xpath': '//tag[@name="image_num_c"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_num_z"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_num_t"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_pixel_depth"]', 'attr': 'value', 'val': '16' },
            { 'xpath': '//tag[@name="image_pixel_format"]', 'attr': 'value', 'val': 'unsigned integer' },
            { 'xpath': '//tag[@name="format"]',      'attr': 'value', 'val': 'Leica: Image File Format LIF' },
            { 'xpath': '//tag[@name="image_num_series"]', 'attr': 'value', 'val': '2' },
            { 'xpath': '//tag[@name="pixel_resolution_x"]', 'attr': 'value', 'val': '0.160490234375' },
            { 'xpath': '//tag[@name="pixel_resolution_y"]', 'attr': 'value', 'val': '0.160490234375' },
            #{ 'xpath': '//tag[@name="pixel_resolution_z"]', 'attr': 'value', 'val': '1.0' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_x"]', 'attr': 'value', 'val': 'microns' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_y"]', 'attr': 'value', 'val': 'microns' },
            #{ 'xpath': '//tag[@name="pixel_resolution_unit_z"]', 'attr': 'value', 'val': 'microns' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)

    # combined test becuase this file has 1 T and 1 Z and so the slice will shortcut and will not be readable by imgcnv
    def test_slice_format_package_leica_lif (self):
        package = image_leica_lif
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'bisque_package.slice.tif'
        commands = [('slice', ',,1,1'), ('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '512',
            'image_num_y': '512',
            'image_num_c': '1',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer'
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_format_package_leica_lif (self):
        package = image_leica_lif
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']

        filename = 'bisque_package.format.ome.tif'
        commands = [('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '512',
            'image_num_y': '512',
            'image_num_c': '1',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer'
        }
        self.validate_image_variant(resource, filename, commands, meta_required)    
    
    # ---------------------------------------------------
    # package_andor_iq
    # ---------------------------------------------------

    def test_contents_package_andor_iq (self):
        package = package_andor_iq
        
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertEqual(package['count'], len(package['items']))
        self.assertEqual(package['name'], package['resource'].get('name'))
        
        resource = package['last']
        name = "%s#%s"%(package['file'], len(package['items'])-1)
        self.assertEqual(resource.get('name'), name)        
        values = [x.text for x in resource.get('value')]
        self.assertEqual(len(values), 243)
        self.assertTrue('%s//AndorMM/AndorMM/DiskInfo5.kinetic#%s'%(TEST_PATH, len(package['items'])-1) in values[0])
        
        
    def test_thumbnail_package_andor_iq (self):
        package = package_andor_iq
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_andor_iq.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 
            'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '128',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' 
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_meta_package_andor_iq (self):
        package = package_andor_iq
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_andor_iq.meta.xml'
        commands = [('meta', None)]
        meta_required = [
            { 'xpath': '//tag[@name="image_num_x"]', 'attr': 'value', 'val': '1024' },
            { 'xpath': '//tag[@name="image_num_y"]', 'attr': 'value', 'val': '1024' },
            { 'xpath': '//tag[@name="image_num_c"]', 'attr': 'value', 'val': '3' },
            { 'xpath': '//tag[@name="image_num_z"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_num_t"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_pixel_depth"]', 'attr': 'value', 'val': '16' },
            { 'xpath': '//tag[@name="image_pixel_format"]', 'attr': 'value', 'val': 'unsigned integer' },
            { 'xpath': '//tag[@name="format"]',      'attr': 'value', 'val': 'Andor: iQ ImageDisk' },
            { 'xpath': '//tag[@name="image_num_series"]', 'attr': 'value', 'val': '3' },
            { 'xpath': '//tag[@name="pixel_resolution_x"]', 'attr': 'value', 'val': '1.09262695313' },
            { 'xpath': '//tag[@name="pixel_resolution_y"]', 'attr': 'value', 'val': '1.06738574219' },
            { 'xpath': '//tag[@name="pixel_resolution_z"]', 'attr': 'value', 'val': '1.08' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_x"]', 'attr': 'value', 'val': 'microns' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_y"]', 'attr': 'value', 'val': 'microns' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_z"]', 'attr': 'value', 'val': 'microns' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)

    # combined test becuase this file has 1 T and 1 Z and so the slice will shortcut and will not be readable by imgcnv
    def test_slice_format_package_andor_iq (self):
        package = package_andor_iq
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_andor_iq.slice.tif'
        commands = [('slice', ',,1,1'), ('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '1024',
            'image_num_y': '1024',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer'
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_format_package_andor_iq (self):
        package = package_andor_iq
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']

        filename = 'package_andor_iq.format.ome.tif'
        commands = [('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '1024',
            'image_num_y': '1024',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer'
        }
        self.validate_image_variant(resource, filename, commands, meta_required)    


    # ---------------------------------------------------
    # package_imaris_leica
    # ---------------------------------------------------

    def test_contents_package_imaris_leica (self):
        package = package_imaris_leica
        
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertEqual(package['count'], len(package['items']))
        self.assertEqual(package['name'], package['resource'].get('name'))
        
        resource = package['last']
        name = "%s#%s"%(package['file'], len(package['items'])-1)
        self.assertEqual(resource.get('name'), name)        
        values = [x.text for x in resource.get('value')]
        self.assertEqual(len(values), 26)
        self.assertTrue('%s/bad_beads_2stacks_chart/bad_beads_2stacks_chart/bad_beads_2stacks_chart.lei#%s'%(TEST_PATH, len(package['items'])-1) in values[0])
        
        
    def test_thumbnail_package_imaris_leica (self):
        package = package_imaris_leica
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_imaris_leica.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 
            'format': 'JPEG',
            'image_num_x': '128',
            'image_num_y': '128',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' 
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_meta_package_imaris_leica (self):
        package = package_imaris_leica
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_imaris_leica.meta.xml'
        commands = [('meta', None)]
        meta_required = [
            { 'xpath': '//tag[@name="image_num_x"]', 'attr': 'value', 'val': '1004' },
            { 'xpath': '//tag[@name="image_num_y"]', 'attr': 'value', 'val': '1004' },
            { 'xpath': '//tag[@name="image_num_c"]', 'attr': 'value', 'val': '3' },
            { 'xpath': '//tag[@name="image_num_z"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_num_t"]', 'attr': 'value', 'val': '1' },
            { 'xpath': '//tag[@name="image_pixel_depth"]', 'attr': 'value', 'val': '8' },
            { 'xpath': '//tag[@name="image_pixel_format"]', 'attr': 'value', 'val': 'unsigned integer' },
            { 'xpath': '//tag[@name="format"]',      'attr': 'value', 'val': 'Leica: Vista LCS' },
            { 'xpath': '//tag[@name="image_num_series"]', 'attr': 'value', 'val': '3' },
            { 'xpath': '//tag[@name="pixel_resolution_x"]', 'attr': 'value', 'val': '0.0' },
            { 'xpath': '//tag[@name="pixel_resolution_y"]', 'attr': 'value', 'val': '0.0' },
            { 'xpath': '//tag[@name="pixel_resolution_z"]', 'attr': 'value', 'val': '1.0' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_x"]', 'attr': 'value', 'val': 'microns' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_y"]', 'attr': 'value', 'val': 'microns' },
            { 'xpath': '//tag[@name="pixel_resolution_unit_z"]', 'attr': 'value', 'val': 'microns' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)

    # combined test becuase this file has 1 T and 1 Z and so the slice will shortcut and will not be readable by imgcnv
    def test_slice_format_package_imaris_leica (self):
        package = package_imaris_leica
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']
        
        filename = 'package_imaris_leica.slice.tif'
        commands = [('slice', ',,1,1'), ('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '1004',
            'image_num_y': '1004',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer'
        }
        self.validate_image_variant(resource, filename, commands, meta_required)

    def test_format_package_imaris_leica (self):
        package = package_imaris_leica
        self.assertIsNotNone(package['resource'], 'Resource was not uploaded')
        self.assertIsNotNone(package['last'], 'Item was not found')
        resource = package['last']

        filename = 'package_imaris_leica.format.ome.tif'
        commands = [('format', 'ome-tiff')]
        meta_required = {
            'format': 'OME-BigTIFF',
            'image_num_x': '1004',
            'image_num_y': '1004',
            'image_num_c': '3',
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer'
        }
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

