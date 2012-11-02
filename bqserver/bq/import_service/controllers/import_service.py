###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========

DESCRIPTION
===========

TODO
===========

  1. Add regexp sorting for files in the composed Zip
  2. Problem with OME-XML in the imgcnv
  

"""

__module__    = "import_service"
__author__    = "Dmitry Fedorov, Kris Kvilekval"
__version__   = "2.3"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

# -*- mode: python -*-

# default includes
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from pylons.controllers.util import abort
from tg import expose, flash
from tg import config
from repoze.what import predicates 
from bq.core.service import ServiceController

# additional includes
import sys
import traceback
import time
import re
import threading
import shutil
import tarfile
import zipfile
import os.path
import urllib
import copy
import mimetypes
import traceback

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from urllib import quote
from lxml import etree
from time import strftime
from datetime import datetime

import tg
from tg import request, response, session, flash, require
from repoze.what import predicates

import bq
from bq.core import permission, identity
from bq.util.paths import data_path
from bq import image_service
from bq import data_service
from bq import blob_service

import bq.image_service.controllers.imgcnv as imgcnv
import bq.image_service.controllers.bioformats as bioformats
from bq.util.mkdir import _mkdir


#---------------------------------------------------------------------------------------
# inits 
#---------------------------------------------------------------------------------------

imgcnv_needed_version = '1.43'
bioformats_needed_version = '4.3.0'

#---------------------------------------------------------------------------------------
# File object 
#---------------------------------------------------------------------------------------

class UploadedFile:
    """ Object encapsulating upload file """
    filename        =   None
    file            =   None
    tags            =   None
    original        =   None
    resource_type   =   None
    permission      =   'private'
    
    def __init__(self, path, name, tags=None):
        self.filename = name
        self.file = open(path, 'rb')
        self.tags = tags
        
    def __del__ (self):
        if not self.file is None:
            self.file.close()

#patch to allow no copy file uploads (direct to destination directory)
#---------------------------------------------------------------------------------------------#
import cgi

#if upload handler has been inited in webob
if hasattr(cgi, 'file_upload_handler'):
    tmp_upload_dir = config.get('bisque.blob_service.tmp_upload_dir', os.path.join(data_path(),'tmp_upload_dir'))
    _mkdir(tmp_upload_dir)
    
    #register callables here
    def import_transfer_handler(filename):
        import tempfile
        return tempfile.NamedTemporaryFile('w+b', suffix = filename, dir=tmp_upload_dir, delete = False)
    
    #map callables to paths here
    cgi.file_upload_handler['/import/transfer'] = import_transfer_handler

#---------------------------------------------------------------------------------------------#

#---------------------------------------------------------------------------------------
# controller 
#---------------------------------------------------------------------------------------

log = logging.getLogger("bq.import_service")
class import_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "import"

    def __init__(self, server_url):
        super(import_serviceController, self).__init__(server_url)
        
        mimetypes.add_type('image/slidebook', '.sld')
        mimetypes.add_type('image/volocity', '.mvd2')
        
        self.filters = {}
        self.filters['zip-bisque']      = self.filter_zip_bisque
        self.filters['zip-multi-file']  = self.filter_zip_multifile   
        self.filters['zip-time-series'] = self.filter_zip_tstack   
        self.filters['zip-z-stack']     = self.filter_zip_zstack   
        self.filters['zip-5d-image']    = self.filter_5d_image   
        self.filters['zip-volocity']    = self.filter_zip_volocity
        self.filters['image/slidebook'] = self.filter_series_bioformats
        self.filters['image/volocity']  = self.filter_series_bioformats
        
        
    @expose('bq.import_service.templates.upload')
    @require(predicates.not_anonymous())
    def index(self, **kw):
        """Add your first page here.. """
        return dict()

#------------------------------------------------------------------------------
# misc functions
#------------------------------------------------------------------------------

    def sanitize_filename(self, filename):
        """ Removes any path info that might be inside filename, and returns results. """
        return urllib.unquote(filename).split("\\")[-1].split("/")[-1]

    def check_imgcnv (self):
        if not imgcnv.installed():
            raise Exception('imgcnv not installed')
        imgcnv.check_version( imgcnv_needed_version )

    def check_bioformats (self):
        if not bioformats.installed():
            raise Exception('bioformats not installed')
        if not bioformats.ensure_version( bioformats_needed_version ):
            raise Exception('Bioformats needs update! Has: '+bioformats.version()['full']+' Needs: '+ bioformats_needed_version)        

#------------------------------------------------------------------------------
# zip/tar.gz support functions
#------------------------------------------------------------------------------

#with ZipFile('spam.zip', 'w') as myzip:
#    myzip.write('eggs.txt')

    # unpacking that preserves structure
    def unZip(self, filename, foldername):
        z = zipfile.ZipFile(filename, 'r')

        # first test if archive is valid
        names = z.namelist()        
        for name in names:
            if name.startswith('/') or name.startswith('\\') or name.startswith('..'):
                z.close()
                return []
                 
        # extract members if all is fine
        z.extractall(foldername)
        z.close()
        return names

    # unpacking that preserves structure
    def unTar(self, filename, foldername):
        z = tarfile.open(filename, 'r')

        # first test if archive is valid
        names = z.getnames()
        for name in names:
            if name.startswith('/') or name.startswith('\\') or name.startswith('..'):
                z.close()
                return []
                 
        # extract members if all is fine
        z.extractall(foldername)
        z.close()
        return names

    # unpacking that flattens file structure
    def unTarFlat(self, filename, folderName):
        z = tarfile.open(filename, 'r')
        names = []
        for n in z.getnames():
            basename = os.path.basename(n)
            i = z.getmember(n)
            if basename and i.isfile() is True:
                filename = os.path.join(folderName, basename)
                with file(filename, 'wb') as f:
                    f.write(z.extractfile(i).read())
                names.append(basename)
        z.close()
        return names

    # unpacking that flattens file structure
    def unZipFlat(self, filename, folderName):
        z = zipfile.ZipFile(filename, 'r')
        names = []
        for n in z.namelist():
            basename = os.path.basename(n)
            i = z.getinfo(n)
            if basename and i.compress_type is not zipfile.ZIP_STORED and i.file_size > 0:
                filename = os.path.join(folderName, basename)
                with file(filename, 'wb') as f:
                    f.write(z.read(n))
                names.append(basename)
        z.close()
        return names

    def unPack(self, filename, folderName, preserve_structure=False):
        if preserve_structure is False:
            if filename.lower().endswith('zip'):
                return self.unZipFlat(filename, folderName)
            else:
                return self.unTarFlat(filename, folderName)
        else:            
            if filename.lower().endswith('zip'):
                return self.unZip(filename, folderName)
            else:
                return self.unTar(filename, folderName)

    def unpackPackagedFile(self, upload_file, preserve_structure=False):
        ''' This method unpacked uploaded file into a proper location '''
        
        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name
        filename   = self.sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.UNPACKED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)

#        log.debug('unpackPackagedFile ::::: uploadroot\n %s'% uploadroot )
#        log.debug('unpackPackagedFile ::::: upload_dir\n %s'% upload_dir )
#        log.debug('unpackPackagedFile ::::: filepath\n %s'% filepath )
#        log.debug('unpackPackagedFile ::::: unpack_dir\n %s'% unpack_dir )
        
        # we'll store the original uploaded file
        #patch for no copy file uploads - check for regular file or file like object
        abs_path_src = os.path.abspath(upload_file.file.name)
        if os.path.isfile(abs_path_src):
            filepath = abs_path_src
        else:
            with open(filepath, 'wb') as trg:
                shutil.copyfileobj(upload_file.file, trg)

        # unpack the contents of the packaged file
        members = self.unPack(filepath, unpack_dir, preserve_structure)
 
        return unpack_dir, members

#------------------------------------------------------------------------------
# zip/tar.gz Import for 5D image
#------------------------------------------------------------------------------

    def process5Dimage(self, upload_file, **kw):
        self.check_imgcnv()
        unpack_dir, members = self.unpackPackagedFile(upload_file)

        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name
        filename   = self.sanitize_filename(upload_file.filename)
        combined_filename = '%s.%s.ome.tif'%(strftime('%Y%m%d%H%M%S'), filename)
        combined_filepath = '%s/%s'%(upload_dir, combined_filename)

#        log.debug('process5Dimage ::::: uploadroot\n %s'% uploadroot )
#        log.debug('process5Dimage ::::: upload_dir\n %s'% upload_dir )
#        log.debug('process5Dimage ::::: combined_filename\n %s'% combined_filename )
#        log.debug('process5Dimage ::::: combined_filepath\n %s'% combined_filepath )
#        log.debug('process5Dimage ::::: args:\n %s'% kw )

        num_pages = len(members)
        z=None; t=None
        if 'number_z' in kw: z = int(kw['number_z'])
        if 'number_t' in kw: t = int(kw['number_t'])            
        if z==0: z=num_pages; t=1
        if t==0 or z is None or t is None: t=num_pages; z=1

        # combine unpacked files into a multipage image file
        self.assemble5DImage(unpack_dir, members, combined_filepath, z=z, t=t, **kw)

        return combined_filepath

    # dima - add a better sorting algorithm for sorting based on alphanumeric blocks
    def assemble5DImage(self, unpack_dir, members, combined_filepath, **kw):
        geom = {'z':1, 't':1}
        res = { 'resolution_x':0, 'resolution_y':0, 'resolution_z':0, 'resolution_t':0 }

        params = geom
        params.update(res)
        params.update(kw)
        log.debug('assemble5DImage ========================== params: \n%s'% params )
        
        members.sort()
        members = [ '%s/%s'%(unpack_dir, m) for m in members ]
        
        # geometry is needed
        extra = '-multi -geometry %d,%d'%(params['z'], params['t'])
        
        # if any resolution value was given, spec the resolution  
        if sum([float(params[k]) for k in res.keys()])>0:
            extra = '%s -resolution %s,%s,%s,%s'%(extra, params['resolution_x'], params['resolution_y'], params['resolution_z'], params['resolution_t'])        
            
        log.debug('assemble5DImage ========================== extra: \n%s'% extra )
        imgcnv.convert_list(members, combined_filepath, fmt='ome-tiff', extra=extra )
        return combined_filepath

#------------------------------------------------------------------------------
# multi-series files supported by bioformats
#------------------------------------------------------------------------------

    def extractSeriesBioformats(self, upload_file):
        ''' This method unpacked uploaded file into a proper location '''
        self.check_bioformats()
        
        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name       
        filename   = self.sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.EXTRACTED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)
        
        # we'll store the original uploaded file
        #patch for no copy file uploads - check for regular file or file like object
        abs_path_src = os.path.abspath(upload_file.file.name)
        if os.path.isfile(abs_path_src):
            filepath = abs_path_src
        else:
            with open(filepath, 'wb') as trg:
                shutil.copyfileobj(upload_file.file, trg)
        members = []
        
        # extract all the series from the file
        if bioformats.supported(filepath):
            info = bioformats.info(filepath)
            if 'number_series' in info:
                n = info['number_series']
                for i in range(n):
                    fn = 'series_%.5d.ome.tif'%i
                    outfile = '%s/%s'%(unpack_dir, fn)
                    bioformats.convert(ifnm=filepath, ofnm=outfile, original=None, series=i)
                    if os.path.exists(outfile) and imgcnv.supported(outfile):
                        members.append(fn)

        return unpack_dir, members

#------------------------------------------------------------------------------
# volocity files supported by bioformats
#------------------------------------------------------------------------------

    def extractSeriesVolocity(self, upload_file):
        ''' This method unpacks uploaded file and converts from Volocity to ome-tiff '''
        self.check_bioformats()
        unpack_dir, members = self.unpackPackagedFile(upload_file, preserve_structure=True)      
        
        log.debug('unpack_dir:\n %s'% unpack_dir ) 
        log.debug('members:\n %s'% members )         
        
        # find all *.mvd2 files in the package
        mvd2 = []
        for m in members:
            if m.endswith('.mvd2'):
                log.debug('Found volocity: %s'% m )
                fn = '%s.ome.tif'%m 
                fn_in  = os.path.join(unpack_dir, m)
                fn_out = os.path.join(unpack_dir, fn)
                if bioformats.supported(fn_in):
                    bioformats.convert(ifnm=fn_in, ofnm=fn_out)
                    if os.path.exists(fn_out) and imgcnv.supported(fn_out):
                        mvd2.append(fn)
                             
        log.debug('Converted: \n%s'% mvd2 )    
        return unpack_dir, mvd2









#------------------------------------------------------------------------------
# Import archives exported by a BISQUE system
#------------------------------------------------------------------------------
    def importBisqueArchive(self, file, tags):
        
        #-------------------------------------------------------------------
        # parsePath : parses a path into hash of directories and a filename
        #-------------------------------------------------------------------
        def parsePath(filename):
            (root, name) = os.path.split(filename)
            dir = []
            
            while root!='':
                root, nextDir = os.path.split(root)
                dir = dir + [nextDir]
            
            dir.reverse()
            return (dir, name)
        
        #-----------------------------------------------------------------------------------------
        # ingestResource : recursively ingests a file hierarchy and returns top most parent's XML
        #-----------------------------------------------------------------------------------------
        def ingestResource(fileObj):
            xml = parseXML(fileObj.get('XML'))

            if fileObj.get('isDataset') is None:
                if fileObj.get('FILE') is not None:
                    fileObjUp = UploadedFile(fileObj.get('FILE'), None, None)
                    return blob_service.store_fileobj(fileObjUp.file, self.sanitize_filename(os.path.basename(fileObj.get('FILE'))), xml)
                else:
                    return data_service.new_resource(resource = xml)
            else:
                del fileObj['isDataset']
                del fileObj['XML'] 
                
                # delete value fields from the dataset XML
                for value in xml.iter('value'):
                    xml.remove(value)
                
                # iterate through children of the dataset
                for member in fileObj:
                    memberXML = ingestResource(fileObj.get(member))
                    value = etree.SubElement(xml, 'value', type='object')
                    value.text = memberXML.get('uri')
                
                return data_service.new_resource(resource = xml)
            return None

        #--------------------------------------------------------------
        # parseXML : read and return a resource's XML from a .xml file 
        #--------------------------------------------------------------
        def parseXML(filePath):
            file = open(filePath)
            xml = file.read()
            file.close()
            return etree.fromstring(xml)

        #---------------------------------------------------------------
        #---------------------------------------------------------------
        
        unpack_dir, members = self.unpackPackagedFile(file, preserve_structure=True)
        self.parent_uri = None
        
        memberHash = {}

        # create a hash that maps flat file structure into a hierarchy
        for member in members:
            
            if member == '_bisque.xml':
                continue
            
            (dirs, name) = parsePath(member)
            parent = memberHash
            for dir in dirs:
                parent[dir] = parent.get(dir) or {}
                parent[dir]['isDataset'] = True
                parent = parent[dir]
            
            (fname, ext) = os.path.splitext(name)
            value = 'XML' if ext.lower() == '.xml' else 'FILE' 
            entry = parent.get(fname) or {}
            entry[value] = os.path.normpath(os.path.join(unpack_dir, member))
            parent[fname] = entry

        resources = []

        # store resources and blobs with proper XML attached
        for file in memberHash:
            resources.append(ingestResource(memberHash.get(file)))
        
        return resources


#---------------------------------------------------------------------------------------
# filters, take f and return a list of file names
#---------------------------------------------------------------------------------------

    def filter_zip_multifile(self, f, intags):
        unpack_dir, members = self.unpackPackagedFile(f)
        return self.insertResources([ '%s/%s'%(unpack_dir, m) for m in members ], f)
    
    def filter_zip_bisque(self, f, intags):
        return self.importBisqueArchive(f, intags)

    def filter_zip_tstack(self, f, intags):
        return self.insertResources([self.process5Dimage(f, number_t=0, **intags)], f)
    
    def filter_zip_zstack(self, f, intags):
        return self.insertResources([self.process5Dimage(f, number_z=0, **intags)], f)
    
    def filter_5d_image(self, f, intags):
        return self.insertResources([self.process5Dimage(f, **intags)], f)

    def filter_series_bioformats(self, f, intags):
        unpack_dir, members = self.extractSeriesBioformats(f)
        return self.insertResources([ '%s/%s'%(unpack_dir, m) for m in members ], f)

    def filter_zip_volocity(self, f, intags):
        unpack_dir, members = self.extractSeriesVolocity(f)
        return self.insertResources([ '%s/%s'%(unpack_dir, m) for m in members ], f)


#    def insert_resource_url(self, url):
#        filename = url.rsplit('/',1)[1]
#        uniq = blob_service.make_uniq_hash(filename)
#        perm = permission.PRIVATE
#
#        resource_type = blob_service.guess_type(filename)
#
#        resource = etree.Element(resource_type, perm=str(perm),
#                                 resource_uniq = uniq,
#                                 resource_name = filename,
#                                 resource_value  = url)
#        if resource_type == 'image':
#            resource.set('src', "/image_service/images/%s" % uniq)
#
#        etree.SubElement(resource, 'tag', name="filename", value=filename)
#        etree.SubElement(resource, 'tag', name="upload_datetime", value=datetime.now().isoformat(' '), type='datetime' ) 
#            
#        #log.debug("\n\ninsert_image tags: \n%s\n" % etree.tostring(tags))
#
#        log.info ("NEW IMAGE <= %s" % (etree.tostring(resource)))
#        resource = data_service.new_resource(resource = resource)
#        return resource

#------------------------------------------------------------------------------
# file ingestion support functions
#------------------------------------------------------------------------------
   
    def insert_image(self, f):
        """ effectively inserts the file into the bisque database and returns 
        a document describing an ingested resource
        """
        filename = self.sanitize_filename(f.filename)
        src      = f.file
        
        # check the presense of tags with the file        
        tags     = None
        if hasattr(f, 'tags'): 
            tags = copy.deepcopy(f.tags)
            #tags = f.tags
        
        # check the presense of permission with the file
        perm = 'private'
        if hasattr(f, 'permission'):             
            perm = f.permission

        # dima: fix to add the tag
        if hasattr(f, 'original') and f.original:
            if tags is None:
                tags = etree.Element('resource')
            etree.SubElement(tags, 'tag', name="original_upload", value=f.original, type='resource' )      

        # try inserting the file in the blob service            
        try:
            log.debug('Inserting blob: [%s] [%s] [%s] [%s]'%(src, filename, perm, tags))
            resource = blob_service.store_blob (filesrc=src, filename=filename, permission=perm, tags=tags)
            log.debug('Inserted resource :::::\n %s'% etree.tostring(resource) )
            # dima: Add specific image tags here
        except Exception, e:
            log.exception("Error during store")
            return None
        finally:
            src.close()
        
        return resource

    def insertResources(self, nf, f):
        parent_uri = self.storeOriginal(f)
        self.parent_uri = parent_uri
        
        # pre-process succeeded          
        log.debug('filters nf: %s'% nf )
        resources = []
        
        for n in nf:
            name = os.path.split(n)[-1]
            if f.filename not in name:
                name = '%s.%s'%(f.filename, name )
            myf = UploadedFile(n, name, f.tags)
            if parent_uri: myf.original = parent_uri
            myf.permission = f.permission
            resources.append( self.insert_image(myf) )
        
        return resources
        
    def storeOriginal(self, f):
        # include the parent file into the database            
        parent_uri = None
        try:
            resource_parent = blob_service.store_blob (filesrc=f.file, filename=os.path.split(f.filename)[-1], permission=f.permission)
            parent_uri = resource_parent.get('uri')
        except Exception, e:
            log.exception("Error during store")  
        finally:
            f.file.close()
        
        return parent_uri
    
    def process(self, f):
        """ processes the file and either ingests it inplace or first applies 
        some special pre-processing, the function returns a document 
        describing an ingested resource
        """
            
        # first if tags are present ensure they are in an etree format
        if hasattr(f, 'tags') and f.tags is not None:
            if hasattr(f.tags, 'file'):
                f.tags = etree.parse (f.tags.file).getroot()
            elif isinstance(f.tags, basestring):
                f.tags = etree.fromstring(f.tags)

        # figure out if a file requires special processing
        intags = None
        if hasattr(f, 'tags') and f.tags is not None: 
            xl = f.tags.xpath('//tag[@name="ingest"]')
            if len(xl)>0:
                intags = dict([(t.get('name'), t.get('value')) 
                               for t in xl[0].xpath('tag') 
                                   if t.get('value') is not None and t.get('name') is not None ])
                # remove the ingest tags from the tag document
                f.tags.remove(xl[0])

        # append processing tags based on file type and extension
        mime = mimetypes.guess_type(self.sanitize_filename(f.filename))[0]
        if mime in self.filters:
            if intags is not None:
                intags['type'] = mime
            else:
                intags = {'type': mime}
        
        # check access permission
        f.permission = 'private'
        if intags is not None and 'permission' in intags:
            f.permission = intags['permission']
        
        # no processing required        
        if intags is None or 'type' not in intags or intags['type'] not in self.filters:
            return self.insert_image(f)

        # start processing
        else:
            log.debug('process -------------------\n %s'% intags )
            error = None
            try:
                resources = self.filters[ intags['type'] ](f, intags)
            except Exception, e:
                log.exception('Problem in processing file: %s'  % intags['type'])
                error = 'Problem processing the file: %s'%e
           
            # some error during pre-processing
            if error is not None:
                log.debug('filters error: %s'% error )                
                resource = etree.Element('file', name=f.filename)
                etree.SubElement(resource, 'tag', name='error', value=error)
                return resource

            # some error during pre-processing
            if len(resources)<1:
                log.debug('error while extracting images, none extracted' )
                resource = etree.Element('file', name=f.filename)
                etree.SubElement(resource, 'tag', name='error', value='error while extracting images, none extracted')
                return resource    
            
            # if only one resource was inserted, return right away
            if len(resources)==1:
                return resources[0]
                
            # multiple resources ingested, we need to group them into a dataset and return a reference to it
            # now we'll just return a stupid stub
            ts = datetime.now().isoformat(' ')
            resource = etree.Element('dataset', name='%s'%(f.filename))
            etree.SubElement(resource, 'tag', name="upload_datetime", value=ts, type='datetime' )             
            
            if self.parent_uri is not None:
                etree.SubElement(resource, 'tag', name="original_upload", value=self.parent_uri, type='resource' )   
                        
            index=0
            for r in resources:
                # check for ingest errors here as well
                if r.get('uri') is not None:
                    # index is giving trouble
                    #v = etree.SubElement(resource, 'value', index='%s'%index, type='object')
                    v = etree.SubElement(resource, 'value', type='object')
                    v.text = r.get('uri')
                else:
                    s = 'Error ingesting element %s with the name "%s"'%(index, r.get('name'))
                    etree.SubElement(resource, 'tag', name="error", value=s )                    
                index += 1
                
            log.debug('process resource :::::\n %s'% etree.tostring(resource) )
                
            resource = data_service.new_resource(resource=resource) # dima: possible to request on post???
            resource = data_service.get_resource(resource.get('uri'), view='deep')
            log.debug('process created resource :::::\n %s'% etree.tostring(resource) )
            return resource            

    def ingest(self, files):
        """ ingests each elemen of the list of files
        """
        response = etree.Element ('resource', type='uploaded')
        for f in files:
            x = self.process(f)
            if x is not None:
                response.append(x)
            else:
                etree.SubElement(response, 'tag', name="error", value='Error ingesting file' )  
        return response

#------------------------------------------------------------------------------
# Main import for files
# Accepts multi-part form with a file and associated tags in XML format
# form parts should be something like this: file and file_tags
#
# The tag XML document is in the following form:
# <resource>
#     <tag name='any tag' value='any value' />
#     <tag name='another' value='new value' />
# </resource>
#
#
#The document can also contain special tag for prosessing and additional info:
#<resource>
#    <tag name='any tag' value='any value' />
#    <tag name='ingest'>
#        
#        Permission setting for imported image as: 'private' or 'published'
#        <tag name='permission' value='private' />
#        or
#        <tag name='permission' value='published' />
#                
#        Image is a multi-file compressed archive, should be uncompressed and images ingested individually:
#        <tag name='type' value='zip-multi-file' />
#        or
#        Image is a compressed archive containing multiple files composing a time-series image:        
#        <tag name='type' value='zip-time-series' />
#        or
#        Image is a compressed archive containing multiple files composing a z-stack image:                
#        <tag name='type' value='zip-z-stack' />
#        or
#        Image is a compressed archive containing multiple files composing a 5-D image:
#        <tag name='type' value='zip-5d-image' />
#        This tag must have two additional tags with numbers of T and Z planes:
#        <tag name='number_z' value='XXXX' />
#        <tag name='number_t' value='XXXXX' />                
#
#    </tag>
#</resource>
#
#Example for a file "example.zip":
#
#<resource>
#    <tag name='any tag' value='any value' />
#    <tag name='ingest'>
#        <tag name='permission' value='published' />
#        <tag name='type' value='zip-5d-image' />
#        <tag name='number_z' value='XXXX' />
#        <tag name='number_t' value='XXXXX' />
#    </tag>
#</resource>
#
#------------------------------------------------------------------------------
    

    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def transfer(self, **kw):
        """Recieve a multipart form with images and possibly tag documents

        :param kw: A keyword dictionary of file arguments.  The
        arguments are organized as follows: Each datafile and its tag
        document are associated by the parameters named 'x' and
        'x_tags' where x can be any string. 
        
        """
        #log.debug("TRANSFER %s"  % (kw))
        #log.debug("BODY %s " % request.body[:100])
        params = dict (kw)
        files = []
        for pname, f in params.items():
            if (pname.endswith ('_tags')): continue
            if hasattr(f, 'file'):
                f.tags = params.get (pname+'_tags', None)
                files.append(f)

        # process the file list see if some files need special processing
        # e.g. ZIP needs to be unpacked
        # then ingest all
        response = self.ingest(files)
        # respopnd with an XML containing links to created resources
        return etree.tostring(response)

    @expose("bq.import_service.templates.upload")
    @require(predicates.not_anonymous())
    def upload(self, **kw):
        """ Main upload entry point """
        return dict()

    @expose("bq.import_service.templates.uploaded")
    @require(predicates.not_anonymous())
    def transfer_legacy(self, **kw):
        """This is a legacy function for non html5 enabled browsers, this will only accept one upload
           no tag uploads are allowed either
        """
        if 'file' not in kw:
            return dict(error='No file uploaded...')
        resource = self.process( kw['file'] )
        if resource is not None and resource.get('uri') is None:
            # try to define the error
            t=resource.xpath('//tag[@name="error"]')
            if len(t)>0:
                return dict(error=t[0].get('value'))              
        elif resource is not None and resource.get('uri') is not None:
            return dict(uri = resource.get('uri'), info = dict(resource.attrib), error=None)            

        return dict(error = 'Some problem uploading the file have occured')

    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def insert(self, url = None, filename=None, permission='private',  user=None, **kw):
        """insert a URL to a fixed resource. This allows  insertion 
        of  resources  when they are already present on safe media
        i.e on the local server drives or remote irods, hdfs etc.

        Local URL should not include  scheme i.e forgot the file://
        irods://irods.host.org/zone/..  The bisque system must have rights to read the file
        """
        # Note: This entrypoint should allow permission and tags to be inserted
        # in a similar way to tranfers.. maybe combining the two would be needed.
        log.info ('insert %s for %s' % (url, user))
        
        if 'tags' in kw:
            try:
                kw['tags'] = etree.fromstring(kw['tags'])
            except Exception,e: # dima: possible exceptions here, ValueError, XMLSyntaxError
                del kw['tags']
        
        try:
            if user is not None and identity.current.user_name == 'admin':
                identity.current.set_current_user( user )
            resource = blob_service.store_blob(filename=filename, url=url, permission=permission, **kw)
            return etree.tostring(resource)
        except Exception,e:
            log.exception("insert: %s %s" % (url, filename))
            abort(500, "exception during url insert")


        
#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  import_serviceController(uri)
    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'import_service', 'public'))]


__controller__ =  import_serviceController
