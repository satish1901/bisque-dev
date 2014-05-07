#global variables for the test script
import ConfigParser
import os
import ntpath
from lxml import etree
import urllib
import zipfile
from bqapi.bqclass import fromXml # local
from bqapi.comm import BQSession, BQCommError
from bqapi.util import save_blob # local
import posixpath
import sys
import glob
from TestGlobals import ROOT,LOCAL_STORE_IMAGES, IMAGE_ARCHIVE_ZIP, TEMP_DIR, URL_FILE_STORE


#test initalization
def ensure_bisque_file( bqsession, filename, achieve = False, local_dir='.'):
    """
        Checks for test files stored locally
        If not found fetches the files from a store
    """
    
    path = fetch_file(filename,local_dir)
    if achieve:
        return upload_achieve_file( bqsession, path)
    else:
        return upload_new_file(bqsession, path)


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


def upload_new_file( bqsession, path):
    """
        uploads files to bisque server
    """
    r = save_blob(bqsession,  path)
    print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
    return r


def upload_achive_file( bqsession, path):
    """
        upload bisque archive files
    """
    filename = ntpath.basename(path)
    resource = etree.Element('resource', name = filename)
    tag = etree.SubElement(resource,'tag', name = 'ingest')
    etree.SubElement(tag,'tag', name = 'type', value = 'zip-bisque')
    r = save_blob( bqsession,  path, resource = resource)
    print 'Uploaded id: %s url: %s'%(r.get('resource_uniq'), r.get('uri'))
    return r


def resource_info(bqsession, bisque_archive, mask, feature_filename):
    
    
    path = os.path.join( LOCAL_STORE_IMAGES, bisque_archive)
    check_for_file( bisque_archive, IMAGE_ARCHIVE_ZIP, local_dir=LOCAL_STORE_IMAGES)
    
    bisque_archive_data_xml_top    = upload_achive_file( bqsession, path)

    path = os.path.join(LOCAL_STORE_IMAGES, mask)
    check_for_file(mask, IMAGE_ARCHIVE_ZIP,local_dir=LOCAL_STORE_IMAGES)
    
    mask_xml_top               = upload_new_file( bqsession, path)
    
    bisque_archive_xml         = bqsession.fetchxml('%s?view=deep,clean'%bisque_archive_data_xml_top.attrib['uri'])
    #polygon_xml                = bisque_archive_xml.xpath('//polygon')
    #bisque_archive_polygon     = polygon_xml[0].attrib['uri']
    
    return ({
             'filename'        : bisque_archive,
             'mask_filename'   : mask,
             'feature_filename': feature_filename,
             'image'           : ROOT+'/image_service/image/'+bisque_archive_data_xml_top.attrib['resource_uniq'],
             'image_xml'       : bisque_archive_data_xml_top,
             'mask'            : ROOT+'/image_service/image/'+mask_xml_top.attrib['resource_uniq'],
             'mask_xml'        : mask_xml_top,
             #'polygon'         : bisque_archive_polygon   
             })

#test breakdown
def delete_resource(bqsession, r):
    """
        Remove uploaded resource from bisque server
    """
    url = r.get('uri')
    print 'Deleting id: %s url: %s'%(r.get('resource_uniq'), url)
    bqsession.postxml(url, etree.Element ('resource') , method='DELETE')


def cleanup_dir():
    """
        Removes files downloaded into the local store
    """
    print 'Cleaning-up %s'%TEMP_DIR
    for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except:
                pass

        

#upload functions
def zipfiles(filelist, zipped_filename, root = '.'):
    with zipfile.ZipFile(zipped_filename,'w') as zip:
        for fname in filelist:
            zip.write(fname, os.path.relpath(fname, root))
    return  

        