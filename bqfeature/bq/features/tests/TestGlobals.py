"""
    Read in the setup.cfg and set global variables for all the feature tests
"""

#global variables for the test script
import ConfigParser

#from Test_Setup import return_archive_info

#url_file_store       = 'http://hammer.ece.ucsb.edu/~bisque/test_data/images/'
URL_FILE_STORE       = 'http://biodev.ece.ucsb.edu/binaries/download/'
LOCAL_STORE_IMAGES   = 'images'
LOCAL_FEATURES_STORE = 'features'
LOCAL_STORE_TESTS    = 'tests'
TEMP_DIR             = 'temp'

SERVICE_DATA         = 'data_service'
SERVICE_IMAGE        = 'image_service'
RESOURCE_IMAGE       = 'image'
FEATURES             = 'features'

IMAGE_ARCHIVE_ZIP    = '12C28317092495715E6067EBD367C631552CF764-feature_test_images.zip'
FEATURE_ARCHIVE_ZIP  = '5AB6960913ABAEBFB91A7392E61982E8306115EE-feature_test_features.zip'

FEATURE_ZIP          = 'feature_test_features'
IMAGE_ZIP            = 'feature_test_images'

#imported files
BISQUE_ARCHIVE_1     = 'image_08093.tar'
MASK_1               = 'mask_8093.jpg'
FEATURE_1            = 'feature_08093.h5'

BISQUE_ARCHIVE_2     = 'image_08089.tar'
MASK_2               = 'mask_8089.jpg'
FEATURE_2            = 'feature_08089.h5'

BISQUE_ARCHIVE_3     = 'image_08069.tar'
MASK_3               = 'mask_8069.jpg'
FEATURE_3            = 'feature_08069.h5'

BISQUE_ARCHIVE_4     = 'image_08043.tar'
MASK_4               = 'mask_8043.jpg'
FEATURE_4            = 'feature_08043.h5'


config = ConfigParser.ConfigParser()
config.read('setup.cfg')

#login
ROOT = config.get('Host', 'root') or 'localhost:8080'
USER = config.get('Host', 'user') or 'test'
PWD  = config.get('Host', 'password') or 'test'

##test options
#TEST_TYPE = config.get('TestOptions', 'test_type') or 'all'
#TEST_TYPE = TEST_TYPE.replace(' ','').split(',')
#
#FEATURES_LIST = config.get('TestOptions', 'test_features') or 'all'
#FEATURES_LIST = FEATURES_LIST.replace(' ','').split(',')
#
#TEST_METHOD = config.get('TestOptions', 'test_features') or 'all'
#TEST_METHOD = TEST_METHOD.replace(' ','').split(',')

#Set in the Setup of run_test
SESSION = None
RESOURCE_LIST = None





