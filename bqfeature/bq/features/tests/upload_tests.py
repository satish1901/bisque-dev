"""
upload_test.py

Uploads all the images and features to the bisque depo

To recalibrate the feature tests run SetupFeatureTestTable

Do no forget to change the IMAGE_ARCHIVE_ZIP and the FEATURE_ARCHIVE_ZIP
"""


from utils import zipfiles
import TestGlobals
import os

image_list = [
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.BISQUE_ARCHIVE_1),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.BISQUE_ARCHIVE_2),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.BISQUE_ARCHIVE_3),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.BISQUE_ARCHIVE_4),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.MASK_1),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.MASK_2),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.MASK_3),
        os.path.join(TestGlobals.LOCAL_STORE_IMAGES, TestGlobals.MASK_4),
    ]

zipfiles(image_list,'feature_test_images.zip',root=TestGlobals.LOCAL_STORE_IMAGES)
print 'zipped feature_test_images.zip'

image_list = [
        os.path.join(TestGlobals.LOCAL_FEATURES_STORE, TestGlobals.FEATURE_1),
        os.path.join(TestGlobals.LOCAL_FEATURES_STORE, TestGlobals.FEATURE_2),
        os.path.join(TestGlobals.LOCAL_FEATURES_STORE, TestGlobals.FEATURE_3),
        os.path.join(TestGlobals.LOCAL_FEATURES_STORE, TestGlobals.FEATURE_4),
    ]

zipfiles(image_list,'feature_test_features.zip', root = TestGlobals.LOCAL_FEATURES_STORE)
print 'zipped feature_test_features.zip'


print 'Upload the zipfiles to the bisque depot using:'
print ''
print '    bqdev-upload-binary -u tracusername -p tracuserpasswd feature_test_images.zip'
print '    bqdev-upload-binary -u tracusername -p tracuserpasswd feature_test_features.zip'
print ''
print 'Write the returned file names into the TestGlobals'
