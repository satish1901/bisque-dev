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
__version__   = "2.2"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

# -*- mode: python -*-

# default includes
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
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
from bq.image_service.controllers.blobsrv import _mkdir


#---------------------------------------------------------------------------------------
# inits 
#---------------------------------------------------------------------------------------

imgcnv_needed_version = '1.43'

#---------------------------------------------------------------------------------------
# File object 
#---------------------------------------------------------------------------------------

AccessRights = { 'private': permission.PRIVATE, 'published': permission.PUBLIC }

class UploadedFile:
    """ Object encapsulating upload file """
    filename   = None
    file       = None
    tags       = None
    original   = None
    permission = permission.PRIVATE
    
    def __init__(self, path, name, tags=None):
        self.filename = name
        self.file = open(path, 'rb')
        self.tags = tags
        
    def __del__ (self):
        if not self.file is None:
            self.file.close()

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
        self.filters['zip-multi-file']  = self.filter_zip_multifile   
        self.filters['zip-time-series'] = self.filter_zip_tstack   
        self.filters['zip-z-stack']     = self.filter_zip_zstack   
        self.filters['zip-5d-image']    = self.filter_5d_image   
        self.filters['image/slidebook'] = self.filter_series_bioformats
        self.filters['image/volocity']  = self.filter_series_bioformats
        
        
    @expose('bq.import_service.templates.upload')
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

#------------------------------------------------------------------------------
# zip/tar.gz support functions
#------------------------------------------------------------------------------

    # dima - allow files inside directories

    def unTarFiles(self, filename, folderName):
        tar = tarfile.open(filename)
        members = tar.getmembers()
        tar.extractall('%s/'%(folderName))
        tar.close()
        return [ str(m.name) for m in members ]

    def unZipFiles(self, filename, folderName):
        zipF = zipfile.ZipFile(filename,'r')
        members = zipF.infolist()
        namelist = []
        for znames in zipF.namelist():
            lName = os.path.basename(znames)
            if lName:
                fName = '%s/%s'%(folderName, lName)
                file(fName,'wb').write(zipF.read(znames))
                namelist.append(lName)
        zipF.close()
        return namelist

    def unPackFiles(self, filename, folderName):
        if filename.lower().endswith('zip'):
            members=self.unZipFiles(filename, folderName)
        else:
            members=self.unTarFiles(filename, folderName)
        return members

    def unpackPackagedFile(self, upload_file):
        ''' This method unpacked uploaded file into a proper location '''
        
        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().user_name))        
        filename   = self.sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.UNPACKED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)

#        log.debug('unpackPackagedFile ::::: uploadroot\n %s'% uploadroot )
#        log.debug('unpackPackagedFile ::::: upload_dir\n %s'% upload_dir )
#        log.debug('unpackPackagedFile ::::: filepath\n %s'% filepath )
#        log.debug('unpackPackagedFile ::::: unpack_dir\n %s'% unpack_dir )
        
        # we'll store the original uploaded file
        out = open (filepath,'wb')
        shutil.copyfileobj (upload_file.file, out)
        out.close()

        # unpack the contents of the packaged file
        members = self.unPackFiles(filepath, unpack_dir)
 
        return unpack_dir, members

#------------------------------------------------------------------------------
# zip/tar.gz Import for 5D image
#------------------------------------------------------------------------------

    def process5Dimage(self, upload_file, **kw):
        self.check_imgcnv()
        unpack_dir, members = self.unpackPackagedFile(upload_file)

        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().user_name))
        filename   = self.sanitize_filename(upload_file.filename)
        combined_filename = '%s.%s.ome.tif'%(strftime('%Y%m%d%H%M%S'), filename)
        combined_filepath = '%s/%s'%(upload_dir, combined_filename)

#        log.debug('process5Dimage ::::: uploadroot\n %s'% uploadroot )
#        log.debug('process5Dimage ::::: upload_dir\n %s'% upload_dir )
#        log.debug('process5Dimage ::::: combined_filename\n %s'% combined_filename )
#        log.debug('process5Dimage ::::: combined_filepath\n %s'% combined_filepath )

        num_pages = len(members)
        z=1; t=1
        if 'number_z' in kw: z = int(kw['number_z'])
        if 'number_t' in kw: t = int(kw['number_t'])
        if t==0: t=num_pages; z=1
        if z==0: z=num_pages; t=1

        # combine unpacked files into a multipage image file
        self.assemble5DImage(unpack_dir, members, combined_filepath, z=z, t=t, **kw)

        return combined_filepath

    # dima - add a better sorting algorithm for sorting based on alphanumeric blocks
    def assemble5DImage(self, unpack_dir, members, combined_filepath, **kw):
        geom = {'z':1, 't':1}
        res = { 'resolution-x':0, 'resolution-y':0, 'resolution-z':0, 'resolution-t':0 }

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
            extra = '%s -resolution %s,%s,%s,%s'%(extra, params['resolution-x'], params['resolution-y'], params['resolution-z'], params['resolution-t'])        
            
        log.debug('assemble5DImage ========================== extra: \n%s'% extra )
        imgcnv.convert_list(members, combined_filepath, fmt='ome-tiff', extra=extra )
        return combined_filepath

#------------------------------------------------------------------------------
# multi-series files supported by bioformats
#------------------------------------------------------------------------------

    def extractSeriesBioformats(self, upload_file):
        ''' This method unpacked uploaded file into a proper location '''
        
        uploadroot = config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().user_name))        
        filename   = self.sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.EXTRACTED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)
        
        # we'll store the original uploaded file
        out = open (filepath,'wb')
        shutil.copyfileobj (upload_file.file, out)
        out.close()
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


#---------------------------------------------------------------------------------------
# filters, take f and return a list of file names
#---------------------------------------------------------------------------------------

    def filter_zip_multifile(self, f, intags):
        unpack_dir, members = self.unpackPackagedFile(f)
        return [ '%s/%s'%(unpack_dir, m) for m in members ]
    
    def filter_zip_tstack(self, f, intags):
        return [self.process5Dimage(f, number_t=0, **intags)]
    
    def filter_zip_zstack(self, f, intags):
        return [self.process5Dimage(f, number_z=0, **intags)]
    
    def filter_5d_image(self, f, intags):
        return [self.process5Dimage(f, **intags)]

    def filter_series_bioformats(self, f, intags):
        unpack_dir, members = self.extractSeriesBioformats(f)
        return [ '%s/%s'%(unpack_dir, m) for m in members ]



    def insert_image_url(self, url):
        filename = url.rsplit('/',1)[1]
        uniq = blob_service.make_uniq_hash(filename)
        perm = permission.PRIVATE

        resource_type = blob_service.guess_type(filename)

        resource = etree.Element(resource_type, perm=str(perm),
                                 resource_uniq = uniq,
                                 resource_name = filename,
                                 resource_value  = url)
        if resource_type == 'image':
            resource.set('src', "/image_service/images/%s" % uniq)

        etree.SubElement(resource, 'tag', name="filename", value=filename)
        etree.SubElement(resource, 'tag', name="upload_datetime", value=datetime.now().isoformat(' '), type='datetime' ) 
            
        #log.debug("\n\ninsert_image tags: \n%s\n" % etree.tostring(tags))

        log.info ("NEW IMAGE <= %s" % (etree.tostring(resource)))
        resource = data_service.new_resource(resource = resource)
        return resource

#------------------------------------------------------------------------------
# file ingestion support functions
#------------------------------------------------------------------------------
   
    def insert_image(self, f):
        """ effectively inserts the file into the bisque database and returns 
        a document describing an ingested resource
        """
        filename = f.filename
        src      = f.file
        
        # check the presense of tags with the file        
        tags     = None
        if hasattr(f, 'tags'): 
            tags = copy.deepcopy(f.tags)
            #tags = f.tags
        
        # check the presense of permission with the file
        perm = permission.PRIVATE
        if hasattr(f, 'permission'):             
            perm = f.permission

        # try inserting the image in the image service            
        #info = image_service.new_image(src=src, name=filename, userPerm=perm)

        try:
            uri, uniq = blob_service.store_blob (src, filename)
            resource_type = blob_service.guess_type(filename)
            log.debug ("stored %s at %s" % (filename, uri))
        except Exception, e:
            log.exception("Error during store")
        # the image was successfuly added into the image service
        resource = etree.Element(resource_type, perm = str(perm),
                                 resource_uniq = uniq,
                                 resource_name = filename,
                                 resource_value  = uri)
        if resource_type == 'image':
            resource.set('src', "/image_service/images/%s" % uniq)
        etree.SubElement(resource, 'tag', name="filename", value=filename)
        etree.SubElement(resource, 'tag', name="upload_datetime", value=datetime.now().isoformat(' '), type='datetime' ) 
        if hasattr(f, 'original') and f.original:
            etree.SubElement(resource, 'tag', name="original_upload", value=f.original, type='link' )              
            
        log.debug("\n\ninsert_image tags: \n%s\n" % etree.tostring(tags))
                          
        # ingest extra tags
        if tags is not None:
            if tags.tag == 'resource':
                #resource.extend(copy.deepcopy(list(tags)))
                resource.extend(list(tags))
        log.info ("NEW IMAGE <= %s" % (etree.tostring(resource)))
        resource = data_service.new_resource(resource = resource)
        #else:
        #    # error happened or the file was filtered during the pre-processing stage                
        #    resource = etree.Element('file', name=filename)                
        #    etree.SubElement(resource, 'tag', name='error', value='Problem inserting this image')
        
        log.debug('insert_image :::::\n %s'% etree.tostring(resource) )
        return resource

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
        f.permission = permission.PRIVATE
        if intags is not None and 'permission' in intags:
            f.permission = AccessRights[intags['permission']]
        
        # no processing required        
        if intags is None or 'type' not in intags or intags['type'] not in self.filters:
            return self.insert_image(f)

        # start processing
        else:
            log.debug('process -------------------\n %s'% intags )
            error = None
            try:
                nf = self.filters[ intags['type'] ](f, intags)
            except e:
                log.exception('Problem in processing file: %s'  % intags['type'])
                error = 'Problem processing the file: %s'%e
           
            # some error during pre-processing
            if error is not None:
                log.debug('filters error: %s'% error )                
                resource = etree.Element('file', name=f.filename)
                etree.SubElement(resource, 'tag', name='error', value=error)
                return resource

            # include the parent file into the database
            info = image_service.new_file(src=f.file, name=os.path.split(f.filename)[-1], userPerm=f.permission )
            if info and 'src' in info:
                parent_uri = info['src']

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
            resource = etree.Element('dataset', type='datasets', name='%s (uploaded %s)'%(f.filename, ts))
            etree.SubElement(resource, 'tag', name="upload_datetime", value=ts, type='datetime' )             
            if parent_uri:
                etree.SubElement(resource, 'tag', name="original_upload", value=parent_uri, type='link' )   
                        
            members = etree.SubElement(resource, 'tag', name='members')
            index=0
            for r in resources:
                # check for ingest errors here as well
                if r.get('uri') is not None:
                    # index is giving trouble
                    #v = etree.SubElement(members, 'value', index='%s'%index, type='object')
                    v = etree.SubElement(members, 'value', type='object')
                    v.text = r.get('uri')
                else:
                    s = 'Error ingesting element %s with the name "%s"'%(index, r.get('name'))
                    etree.SubElement(resource, 'tag', name="error", value=s )                    
                index += 1
                
            log.debug('process resource :::::\n %s'% etree.tostring(resource) )
                
            resource = data_service.new_resource(resource=resource)
            resource = data_service.get_resource(resource.get('uri'), view='deep')
            log.debug('process created resource :::::\n %s'% etree.tostring(resource) )
            return resource            

    def ingest(self, files):
        """ ingests each elemen of the list of files
        """
        response = etree.Element ('resource', type='uploaded')
        for f in files:
            response.append(self.process(f))
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

    @expose()
    @require(predicates.not_anonymous())
    def insert(self, **kw):
        return self.insert_image_url (**kw)

        
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
    package = pkg_resources.Requirement.parse ("bqcore")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'import_service', 'public'))]


__controller__ =  import_serviceController
