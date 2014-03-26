#global variables for the test script
import ConfigParser
import os
import ntpath
from lxml import etree
from bq.api.bqclass import fromXml # local
from bq.api.comm import BQSession, BQCommError
from bq.api.util import save_blob # local
import posixpath

#from Test_Setup import return_archive_info

#url_file_store       = 'http://hammer.ece.ucsb.edu/~bisque/test_data/images/'
URL_FILE_STORE       = 'http://biodev.ece.ucsb.edu/binaries/download/'
LOCAL_STORE_IMAGES   = 'images'
LOCAL_FEATURES_STORE = 'features'
LOCAL_STORE_TESTS    = 'tests'
TEMP                 = 'Temp'

SERVICE_DATA         = 'data_service'
SERVICE_IMAGE        = 'image_service'
RESOURCE_IMAGE       = 'image'
FEATURES             = 'features'

IMAGE_ARCHIVE_ZIP    = 'D91AC09AB1A1086F71BF6EC03E518DA3DF701870-feature_test_images.zip'
FEATURE_ARCHIVE_ZIP  = '4236628712FCF4543F640513AB9DA9F28616BEC5-feature_test_features.zip'

FEATURE_ZIP          = 'feature_test_features'
IMAGE_ZIP            = 'feature_test_images'

#imported files
BISQUE_ARCHIVE_1     = 'image_08093.tar'
MASK_1               = 'mask_8093.jpg'
BISQUE_ARCHIVE_2     = 'image_08089.tar'
MASK_2               = 'mask_8089.jpg'
BISQUE_ARCHIVE_3     = 'image_08069.tar'
MASK_3               = 'mask_8069.jpg'
BISQUE_ARCHIVE_4     = 'image_08043.tar'
MASK_4               = 'mask_8043.jpg'


config = ConfigParser.ConfigParser()
config.read('setup.cfg')

#login
ROOT = config.get('Host', 'root') or 'localhost:8080'
USER = config.get('Host', 'user') or 'test'
PWD  = config.get('Host', 'password') or 'test'

#Starting session
SESSION = BQSession().init_local( USER, PWD, bisque_root=ROOT, create_mex = True)

#test options
TEST_TYPE = config.get('TestOptions', 'test_type') or 'all'
TEST_TYPE = TEST_TYPE.replace(' ','').split(',')

FEATURES_LIST = config.get('TestOptions', 'test_features') or 'all'
FEATURES_LIST = FEATURES_LIST.replace(' ','').split(',')

TEST_METHOD = config.get('TestOptions', 'test_features') or 'all'
TEST_METHOD = TEST_METHOD.replace(' ','').split(',')

#set up attributes
import sys

sys.argv.append('-a %s'%'header')
#asd




#test initalization
def ensure_bisque_file( filename, achieve=False, local_dir='.'):
    """
        Checks for test files stored locally
        If not found fetches the files from a store
    """
    path = fetch_file(filename,local_dir)
    if achieve:
        return upload_achieve_file(path)
    else:
        return upload_new_file(path)


def check_for_file( filename, zip_filename,local_dir='.'):
    """
        Checks for test files stored locally
        If not found fetches the files from a store
    """
    path = os.path.join(local_dir, filename)
    
    if not os.path.exists(path):
        fetch_zip(zip_filename, local_dir)
        if not os.path.exists(path):
            raise DownloadError(filename)
   

def fetch_zip( filename, local_dir='.'):
    """
        Fetches and unpacks a zip file into the same dir
    """
    url = posixpath.join( URL_FILE_STORE, filename)
    path = os.path.join( local_dir, filename)
    if not os.path.exists( local_dir):
        os.makedirs( local_dir)
        
    if not os.path.exists(path):
        urllib.urlretrieve(url, path)
    
    Zip = zipfile.ZipFile(path)
    Zip.extractall(local_dir)
    return
   

def fetch_file( filename, local_dir='.'):
    """
        fetches files from a store as keeps them locally
    """
    url = posixpath.join( URL_FILE_STORE, filename)
    path = os.path.join( local_dir, filename)
    if not os.path.exists( path):
        urllib.urlretrieve( url, path)
    return path


def upload_new_file( path):
    """
        uploads files to bisque server
    """
    r = save_blob(SESSION,  path)
    print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
    return r


def upload_achive_file( path):
    """
        upload bisque archive files
    """
    filename = ntpath.basename(path)
    resource = etree.Element('resource', image = filename)
    tag = etree.SubElement(resource,'tag', name = 'ingest')
    etree.SubElement(tag,'tag', name = 'type', value = 'zip-bisque')
    r = save_blob(SESSION,  path, resource = resource)
    print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
    return r


def return_archive_info( bisque_archive, mask):
    
    
    path = os.path.join( LOCAL_STORE_IMAGES, bisque_archive)
    check_for_file( bisque_archive, IMAGE_ARCHIVE_ZIP, local_dir=LOCAL_STORE_IMAGES)
            
    bisque_archive_data_xml_top    = upload_achive_file(path)
    
    bisque_archive_image_uri       = ROOT+'/image_service/image/'+bisque_archive_data_xml_top.attrib['resource_uniq']


    path = os.path.join(LOCAL_STORE_IMAGES, mask)
    check_for_file(mask, IMAGE_ARCHIVE_ZIP,local_dir=LOCAL_STORE_IMAGES)
    
    mask_xml_top                   = upload_new_file(path)
    
    bisque_archive_xml         = SESSION.fetchxml(bisque_archive_data_xml_top.attrib['uri']+'?view=deep')
    polygon_xml                = bisque_archive_xml.xpath('//polygon')
    bisque_archive_polygon     = polygon_xml[0].attrib['uri']                

    return ({
             'filename'      : bisque_archive,
             'mask_filename' : mask,
             'image'         : ROOT+'/image_service/image/'+bisque_archive_data_xml_top.attrib['resource_uniq'],
             'image_xml'     : bisque_archive_data_xml_top,
             'mask'          : ROOT+'/image_service/image/'+mask_xml_top.attrib['resource_uniq'],
             'mask_xml'      : mask_xml_top,
             'polygon'       : bisque_archive_polygon   
             })

#test breakdown
def delete_resource( r):
    """
        remove uploaded resource from bisque server
    """
    url = r.get('uri')
    print 'Deleting id: %s url: %s'%(r.get('resource_uniq'), url)
    SESSION.postxml(url, etree.Element ('resource') , method='DELETE')


def cleanup_dir():
    """
        Removes files downloaded into the local store
    """
    print 'Cleaning-up %s'%LOCAL_STORE_TESTS
    for root, dirs, files in os.walk(LOCAL_STORE_TESTS, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
            
            
if 'features' in TEST_TYPE or 'all' in TEST_TYPE:
    
    #importing pre-calculated features on images
    check_for_file(BISQUE_ARCHIVE_1+'.h5', FEATURE_ARCHIVE_ZIP,local_dir=LOCAL_FEATURES_STORE)
    fetch_file(BISQUE_ARCHIVE_1+'.h5',local_dir=LOCAL_FEATURES_STORE)
    check_for_file(BISQUE_ARCHIVE_2+'.h5', FEATURE_ARCHIVE_ZIP,local_dir=LOCAL_FEATURES_STORE)
    fetch_file(BISQUE_ARCHIVE_2+'.h5',local_dir=LOCAL_FEATURES_STORE)
    check_for_file(BISQUE_ARCHIVE_3+'.h5', FEATURE_ARCHIVE_ZIP,local_dir=LOCAL_FEATURES_STORE)
    fetch_file(BISQUE_ARCHIVE_3+'.h5',local_dir=LOCAL_FEATURES_STORE)
    check_for_file(BISQUE_ARCHIVE_4+'.h5', FEATURE_ARCHIVE_ZIP,local_dir=LOCAL_FEATURES_STORE)
    fetch_file(BISQUE_ARCHIVE_4+'.h5',local_dir=LOCAL_FEATURES_STORE) 
            
#importing resources
RESOURCE_LIST = []
RESOURCE_LIST.append( return_archive_info( BISQUE_ARCHIVE_1, MASK_1) )
RESOURCE_LIST.append( return_archive_info( BISQUE_ARCHIVE_2, MASK_2) )
RESOURCE_LIST.append( return_archive_info( BISQUE_ARCHIVE_3, MASK_3) )
RESOURCE_LIST.append( return_archive_info( BISQUE_ARCHIVE_4, MASK_4) )

  