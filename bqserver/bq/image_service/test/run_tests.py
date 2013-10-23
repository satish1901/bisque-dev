#!/usr/bin/python 

""" Image service testing framework
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

import urllib
import os
import posixpath
import ConfigParser

from lxml import etree
from subprocess import Popen, call, PIPE

from bq.api.bqclass import fromXml # bisque
from bq.api.comm import BQSession, BQCommError # bisque
from bq.api.util import save_blob # bisque
#from bqapi.bqclass import fromXml # local
#from bqapi.comm import BQSession, BQCommError # local
#from bqapi.util import save_blob # local

IMGCNV='imgcnv'

url_image_store     = 'http://hammer.ece.ucsb.edu/~bisque/test_data/images/' 
local_store_images  = 'images' 
local_store_tests   = 'tests'

service_data        = 'data_service'
service_image       = 'image_service'
resource_image      = 'image'
 
image_rgb_uint8     = 'flowers_24bit_nointr.png'
image_zstack_uint16 = '161pkcvampz1Live2-17-2004_11-57-21_AM.tif'
image_float         = 'autocorrelation.tif'

###############################################################
# info comparisons
###############################################################

def print_failed(s, f='-'):
    print 'X FAILED %s'%(s)
      
class InfoComparator(object):
    '''Compares two info dictionaries''' 
    def compare(self, iv, tv):
        return False
    def fail(self, k, iv, tv):
        print_failed('%s failed comparison [%s] [%s]'%(k, iv, tv))
        pass

class InfoEquality(InfoComparator):
    def compare(self, iv, tv):
        return (iv==tv)
    def fail(self, k, iv, tv):
        print_failed('%s failed comparison %s = %s'%(k, iv, tv))
        pass

class InfoNumericLessEqual(InfoComparator):
    def compare(self, iv, tv):
        return (int(iv)<=int(tv))
    def fail(self, k, iv, tv):
        print_failed('%s failed comparison %s <= %s'%(k, iv, tv))
        pass

def compare_info(meta_req, meta_test, cc=InfoEquality() ):
    for tk in meta_req:
        if tk not in meta_test:
            return False
        if not cc.compare(meta_req[tk], meta_test[tk]):
            cc.fail( tk, meta_req[tk], meta_test[tk] )            
            return False 
    return True

###############################################################
# xml comparisons
###############################################################

def compare_xml(meta_req, meta_test, cc=InfoEquality() ):
    for t in meta_req:
        req_xpath = t['xpath'] 
        req_attr  = t['attr']
        req_val   = t['val']
        l = meta_test.xpath(req_xpath)
        if len(l)<1:
            print_failed( 'xpath did not return any results' )      
            return False
        e = l[0]
        if req_val is None:
            return e.get(req_attr, None) is not None
        v = e.get(req_attr)
        if not cc.compare(req_val, v):
            cc.fail( '%s attr %s'%(req_xpath, req_attr), req_val, v )            
            return False 
    return True

##################################################################
# utils
##################################################################

def parse_imgcnv_info(s):
    d = {}
    for l in s.splitlines():
        k = l.split(': ', 1)
        if len(k)>1:
            d[k[0]] = k[1]
    return d

def metadata_read( filename ):
    command = [IMGCNV, '-i', filename, '-meta']
    r = Popen (command, stdout=PIPE).communicate()[0]
    if r is None or r.startswith('Input format is not supported'):
        return None     
    return parse_imgcnv_info(r)

##################################################################
# ImageServiceTestBase
##################################################################

class ImageServiceTestBase(unittest.TestCase):
    """
        Test image service operations
    """
    
    @classmethod
    def setUpClass(self):
        config = ConfigParser.ConfigParser()
        config.read('config.cfg')
        
        self.root = config.get('Host', 'root') or 'localhost:8080'
        self.user = config.get('Host', 'user') or 'test'
        self.pswd = config.get('Host', 'password') or 'test'

        self.session = BQSession().init_local(self.user, self.pswd,  bisque_root=self.root, create_mex=False)
        
        # download and upload test images ang get their IDs        
        self.uniq_2d_uint8  = self.ensure_bisque_file(image_rgb_uint8)
        self.uniq_3d_uint16 = self.ensure_bisque_file(image_zstack_uint16)
        self.uniq_2d_float  = self.ensure_bisque_file(image_float)                

    @classmethod
    def tearDownClass(self):
        self.delete_resource(self.uniq_2d_uint8)
        self.delete_resource(self.uniq_3d_uint16)
        self.delete_resource(self.uniq_2d_float)
        self.cleanup_tests_dir()
        pass

    @classmethod        
    def fetch_file(self, filename):
        url = posixpath.join(url_image_store, filename)
        path = os.path.join(local_store_images, filename)  
        if not os.path.exists(path): 
            urllib.urlretrieve(url, path)
        return path

    @classmethod
    def upload_file(self, path):
        r = save_blob(self.session,  path)
        print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
        return r
        
    @classmethod
    def delete_resource(self, r):
        url = r.get('uri')
        print 'Deleting id: %s url: %s'%(r.get('resource_uniq'), url)
        self.session.postxml(url, etree.Element ('resource') , method='DELETE')

    @classmethod
    def ensure_bisque_file(self, filename):
        path = self.fetch_file(filename)
        return self.upload_file(path)        

    @classmethod
    def cleanup_tests_dir(self):
        print 'Cleaning-up %s'%local_store_tests
        for root, dirs, files in os.walk(local_store_tests, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))

    def validate_image_variant(self, resource, filename, commands, meta_required):
        path = os.path.join(local_store_tests, filename) 
        try:
            image = fromXml(resource, session=self.session)
            px = image.pixels()
            for c,a in commands:
                px = px.command(c, a)
            px.fetch(path)
        except BQCommError:
            self.fail()
        
        meta_test = metadata_read(path)
        #print meta_test
        self.assertTrue(compare_info(meta_required, meta_test), msg='Retrieved metadata differs from test template')  

    def validate_xml(self, resource, filename, commands, xml_parts_required):
        path = os.path.join(local_store_tests, filename) 
        try:
            image = fromXml(resource, session=self.session)
            px = image.pixels()
            for c,a in commands:
                px = px.command(c, a)
            px.fetch(path)
        except BQCommError:
            self.fail()
        
        xml_test = etree.parse(path).getroot()
        #print meta_test
        self.assertTrue(compare_xml(xml_parts_required, xml_test), msg='Retrieved XML differs from test template')  

##################################################################
# ImageServiceTests
##################################################################

class ImageServiceTests(ImageServiceTestBase):
        
    def test_thumbnail_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '128', 
            'image_num_y': '96', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 
        
    def test_ui_thumbnail_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.ui_thumbnail.jpg'
        commands = [('slice', ',,1,1'), ('thumbnail', '280,280')]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '280', 
            'image_num_y': '210', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 
    
    def test_thumbnail_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '128', 
            'image_num_y': '128', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_ui_thumbnail_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.ui_thumbnail.jpg'
        commands = [('slice', ',,1,1'), ('thumbnail', '280,280')]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '280', 
            'image_num_y': '280', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_thumbnail_2d_1c_float(self):
        resource = self.uniq_2d_float
        filename = 'im_2d_float.thumbnail.jpg'
        commands = [('thumbnail', None)]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '128', 
            'image_num_y': '128', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)
        
    def test_resize_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.resize.320,320,BC,MX.tif'
        commands = [('resize', '320,320,BC,MX')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '320', 
            'image_num_y': '240', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)          

    def test_resize_2d_1c_float(self):
        # resizing floating point image
        resource = self.uniq_2d_float
        filename = 'im_2d_float.resize.128,128,BC,MX.tif'
        commands = [('resize', '128,128,BC,MX')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '128', 
            'image_num_y': '128', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '32',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)         

        # larger bounding box than the image itself, should simply return original file
        resource = self.uniq_2d_float
        filename = 'im_2d_float.resize.320,320,BC,MX.tif'
        commands = [('resize', '320,320,BC,MX')]
        meta_required = { 'format': 'TIFF', 
            'image_num_x': '256', 
            'image_num_y': '256', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '32',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)   
        
    def test_resize_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.resize.320,320,BC,MX.tif'
        commands = [('resize', '320,320,BC,MX')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '320', 
            'image_num_y': '320', 
            'image_num_c': '2', 
            'image_num_z': '1', # this is a tiff and does not have metadata
            'image_num_p': '13',                
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer', }
            #'pixel_resolution_x': '0.207160',
            #'pixel_resolution_y': '0.207160',
            #'pixel_resolution_z': '1.000000' }  # this is a tiff and does not have metadata        
        self.validate_image_variant(resource, filename, commands, meta_required)    

    def test_ui_tile_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.tile.jpg'
        commands = [('slice', ',,1,1'), ('tile', '0,0,0,512'), ('depth', '8,f'), ('fuse', '255,0,0;0,255,0;0,0,255;:m'), ('format', 'jpeg')]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_ui_tile_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.tile.jpg'
        commands = [('slice', ',,1,1'), ('tile', '0,0,0,512'), ('depth', '8,d'), ('fuse', '0,255,0;255,0,0;:m'), ('format', 'jpeg')]
        meta_required = { 'format': 'JPEG', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_resize3d_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.resize3d.256,256,BC,MX.tif'
        commands = [('resize3d', '256,256,7,TC,MX')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '256', 
            'image_num_y': '256', 
            'image_num_c': '2', 
            'image_num_z': '1', # this is a tiff and does not have metadata
            'image_num_p': '7',                
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer', }
            #'pixel_resolution_x': '0.207160',
            #'pixel_resolution_y': '0.207160',
            #'pixel_resolution_z': '1.000000' }  # this is a tiff and does not have metadata        
        self.validate_image_variant(resource, filename, commands, meta_required)                       

    def test_rearrange3d_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.rearrange3d.xzy.tif'
        commands = [('rearrange3d', 'xzy')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '512', 
            'image_num_y': '13', 
            'image_num_c': '2', 
            'image_num_z': '1', # this is a tiff and does not have metadata
            'image_num_p': '512',                
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer', }
            #'pixel_resolution_x': '0.207160',
            #'pixel_resolution_y': '0.207160',
            #'pixel_resolution_z': '1.000000' }  # this is a tiff and does not have metadata        
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_deinterlace_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.deinterlace.tif'
        commands = [('deinterlace', None)]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 
        
    def test_negative_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.negative.tif'
        commands = [('negative', None)]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)
           
    def test_threshold_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.threshold.tif'
        commands = [('threshold', '128,both')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)
        
    def test_levels_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.levels.tif'
        commands = [('levels', '15,200,1.2')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)           
        
    def test_brightnesscontrast_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.brightnesscontrast.tif'
        commands = [('brightnesscontrast', '0,30')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_rotate_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.rotate.tif'
        commands = [('rotate', '90')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '768', 
            'image_num_y': '1024', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_roi_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.roi.tif'
        commands = [('roi', '1,1,100,100')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '100', 
            'image_num_y': '100', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_remap_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.remap.tif'
        commands = [('remap', '1')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_superpixels_2d_3c_uint8(self):
        # superpixels
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.superpixels.tif'
        commands = [('remap', '1'), ('transform', 'superpixels,32,0.5')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '32',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_fourier_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.fourier.tif'
        commands = [('remap', '1'), ('transform', 'fourier')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '64',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_chebyshev_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.chebyshev.tif'
        commands = [('remap', '1'), ('transform', 'chebyshev')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '768', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '64',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_wavelet_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.wavelet.tif'
        commands = [('remap', '1'), ('transform', 'wavelet')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1032', 
            'image_num_y': '776', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '64',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_radon_2d_3c_uint8(self):        
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.radon.tif'
        commands = [('remap', '1'), ('transform', 'radon')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '180', 
            'image_num_y': '1283', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '64',
            'image_pixel_format': 'floating point' }           
        self.validate_image_variant(resource, filename, commands, meta_required)          
        
    def test_edge_2d_3c_uint8(self):        
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.edge.tif'
        commands = [('remap', '1'), ('transform', 'edge')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_wndchrmcolor_2d_3c_uint8(self):
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.wndchrmcolor.tif'
        commands = [('remap', '1'), ('transform', 'wndchrmcolor')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '1', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  
        
    def test_HSV_2d_3c_uint8(self):
        # rgb2hsv
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.rgb2hsv.tif'
        commands = [('transform', 'rgb2hsv')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  

        # hsv2rgb
        resource = self.uniq_2d_uint8
        filename = 'im_2d_uint8.hsv2rgb.tif'
        commands = [('transform', 'rgb2hsv'), ('transform', 'hsv2rgb')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '1024', 
            'image_num_y': '768', 
            'image_num_c': '3', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '8',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)  

    def test_projectmin_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.projectmin.jpg'
        commands = [('projectmin', None)]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '2', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_projectmax_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.projectmax.jpg'
        commands = [('projectmax', None)]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '2', 
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_frames_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.frames.jpg'
        commands = [('frames', '1,2')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '2', 
            'image_num_p': '2',                
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required) 

    def test_sampleframes_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.sampleframes.jpg'
        commands = [('sampleframes', '2')]
        meta_required = { 'format': 'BigTIFF', 
            'image_num_x': '512', 
            'image_num_y': '512', 
            'image_num_c': '2', 
            'image_num_p': '7',                
            'image_num_z': '1',
            'image_num_t': '1',
            'image_pixel_depth': '16',
            'image_pixel_format': 'unsigned integer' }           
        self.validate_image_variant(resource, filename, commands, meta_required)

    #################################
    # XML outputs
    #################################
    def test_meta_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.meta.xml'
        commands = [('meta', None)]
        meta_required = [
            { 'xpath': '//tag[@name="pixel_resolution_x"]', 'attr': 'value', 'val': '0.20716' },
            { 'xpath': '//tag[@name="pixel_resolution_z"]', 'attr': 'value', 'val': '1.0' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)          

    def test_dims_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.dims.xml'
        commands = [('thumbnail', None), ('dims', None)]
        meta_required = [
            { 'xpath': '//tag[@name="image_num_x"]', 'attr': 'value', 'val': '128' },
            { 'xpath': '//tag[@name="image_num_y"]', 'attr': 'value', 'val': '128' },
            { 'xpath': '//tag[@name="image_num_c"]', 'attr': 'value', 'val': '2' },                
            { 'xpath': '//tag[@name="image_pixel_depth"]', 'attr': 'value', 'val': '16' },                   
        ]
        self.validate_xml(resource, filename, commands, meta_required)    

    def test_localpath_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.localpath.xml'
        commands = [('localpath', None)]
        meta_required = [
            { 'xpath': '//resource', 'attr': 'src', 'val': None }, # simply test if attribute is present
            { 'xpath': '//resource', 'attr': 'type', 'val': 'file' },
        ]
        self.validate_xml(resource, filename, commands, meta_required)          

    def test_histogram_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.histogram.xml'
        commands = [('histogram', None)]
        meta_required = [
            { 'xpath': '//histogram[@value="0"]/tag[@name="data_value_max"]', 'attr': 'value', 'val': '65535.000000' },
            { 'xpath': '//histogram[@value="0"]/tag[@name="data_bits_per_pixel"]', 'attr': 'value', 'val': '16' },
            { 'xpath': '//histogram[@value="1"]/tag[@name="data_value_max"]', 'attr': 'value', 'val': '65535.000000' },
            { 'xpath': '//histogram[@value="1"]/tag[@name="data_bits_per_pixel"]', 'attr': 'value', 'val': '16' },                
        ]
        self.validate_xml(resource, filename, commands, meta_required)     
        
    def test_pixelcounter_3d_2c_uint16(self):
        resource = self.uniq_3d_uint16
        filename = 'im_3d_uint16.pixelcounter.xml'
        commands = [('pixelcounter', '128')]
        meta_required = [
            { 'xpath': '//pixelcounts[@value="0"]/tag[@name="above"]', 'attr': 'value', 'val': '206168' },
            { 'xpath': '//pixelcounts[@value="0"]/tag[@name="below"]', 'attr': 'value', 'val': '55976' },
            { 'xpath': '//pixelcounts[@value="1"]/tag[@name="above"]', 'attr': 'value', 'val': '125912' },
            { 'xpath': '//pixelcounts[@value="1"]/tag[@name="below"]', 'attr': 'value', 'val': '136232' },                
        ]
        self.validate_xml(resource, filename, commands, meta_required)          


#def suite():
#    tests = ['test_thumbnail']
#    return unittest.TestSuite(map(ImageServiceTests, tests))
        
if __name__=='__main__':
    if not os.path.exists('images'):
        os.makedirs('images')
    if not os.path.exists('tests'):
        os.makedirs('tests')
    unittest.main(verbosity=2)













    
           
