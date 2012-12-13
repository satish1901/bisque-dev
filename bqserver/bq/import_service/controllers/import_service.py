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

log = logging.getLogger("bq.import_service")


UPLOAD_DIR = config.get('bisque.import_service.upload_dir', data_path('uploads'))
#---------------------------------------------------------------------------------------
# Direct transfer handling (reducing filecopies ) 
# Patch to allow no copy file uploads (direct to destination directory)
#---------------------------------------------------------------------------------------
import cgi
#if upload handler has been inited in webob
if hasattr(cgi, 'file_upload_handler'):
    tmp_upload_dir = UPLOAD_DIR 
    #config.get('bisque.blob_service.tmp_upload_dir', os.path.join(data_path(),'tmp_upload_dir'))
    _mkdir(tmp_upload_dir)
    log.warn ('Configure special upload handler in %s' % tmp_upload_dir)
    
    #register callables here
    def import_transfer_handler(filename):
        import tempfile
        return tempfile.NamedTemporaryFile('w+b', suffix = os.path.basename(filename), dir=tmp_upload_dir, delete = False)
    
    #map callables to paths here
    cgi.file_upload_handler['/import/transfer'] = import_transfer_handler

#---------------------------------------------------------------------------------------
# inits 
#---------------------------------------------------------------------------------------

imgcnv_needed_version = '1.43'
bioformats_needed_version = '4.3.0'




#---------------------------------------------------------------------------------------
# Misc functions
#---------------------------------------------------------------------------------------


def sanitize_filename(filename):
    """ Removes any path info that might be inside filename, and returns results. """
    return urllib.unquote(filename).split("\\")[-1].split("/")[-1]


def merge_resources (*resources):
    """merge attributes and subtags of parameters
    
    later resource overwrite earlier ones
    """
    final = copy.deepcopy (resources[0])
    log.debug ('initially : %s' % etree.tostring(final))
    for rsc in resources[1:]:
        final.attrib.update(rsc.attrib)
        final.extend (copy.deepcopy (list (rsc)))
        log.debug ('updated : %s -> %s' % (etree.tostring(rsc), etree.tostring(final)))
    return final

#---------------------------------------------------------------------------------------
# File object 
#---------------------------------------------------------------------------------------

class UploadedResource(object):
    """ Object encapsulating upload resource+file """
    filename = None
    fileobj  = None
    path     = None

    def __init__(self, resource, fileobj=None ):
        self.resource = resource
        self.fileobj = fileobj
        
        path = resource.get('value')
        if path and path.startswith('file://'):
            self.path = path.replace('file://', '')
        if resource.get ('name'):
            self.filename = sanitize_filename(resource.get('name'))
        elif fileobj :
            # POSTed fileobject will have a filename (which may be path)
            # http://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/forms/file_uploads.html
            self.path = getattr(fileobj, 'filename', '')
            self.filename = sanitize_filename (self.path)
            resource.set('name', self.filename)

    def localpath(self):
        'retrieve a local path for this uploaded resource'

    def close(self):
        'close fileobj'
        if self.fileobj:
            self.fileobj.close()
        
    def __del__ (self):
        self.close()

    def __repr__(self):
        return 'UploadFile([%s] [%s] [%s] [%s]'%(self.path, self.filename, self.resource, self.fileobj)



#---------------------------------------------------------------------------------------
# controller 
#---------------------------------------------------------------------------------------

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

    def localcopy (self, upload_file, suggested):
        'force a local copy to be created for the uploadfile'
        if upload_file.path:
            return upload_file.path
        if upload_file.fileobj:
            path = os.path.abspath(upload_file.fileobj.name)
            if os.path.isfile (path):
                upload_file.path = path
                return path
            with open(suggested,'wb') as trg:
                shutil.copyfileobj(upload_file.fileobj, trg)
                return suggested
        if upload_file.resource.get('value'):
            path = blob_service.fetch_blob (upload_file.resource.get('value'))
            upload_file.path = path
            return path
        return None
            

    def unpackPackagedFile(self, upload_file, preserve_structure=False):
        ''' This method unpacked uploaded file into a proper location '''
        
        uploadroot = UPLOAD_DIR #config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name
        filename   = sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.UNPACKED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)

#        log.debug('unpackPackagedFile ::::: uploadroot\n %s'% uploadroot )
#        log.debug('unpackPackagedFile ::::: upload_dir\n %s'% upload_dir )
#        log.debug('unpackPackagedFile ::::: filepath\n %s'% filepath )
#        log.debug('unpackPackagedFile ::::: unpack_dir\n %s'% unpack_dir )
        
        #filepath = self.localcopy(upload_file, filepath)
        filepath = blob_service.localpath (upload_file.resource.get('resource_uniq'))
        # unpack the contents of the packaged file
        try:
            members = self.unPack(filepath, unpack_dir, preserve_structure)
        except:
            log.exception('Problem unpacking %s in %s' % (filepath, unpack_dir))
            raise
 
        return unpack_dir, members

#------------------------------------------------------------------------------
# zip/tar.gz Import for 5D image
#------------------------------------------------------------------------------

    def process5Dimage(self, upload_file, **kw):
        self.check_imgcnv()
        unpack_dir, members = self.unpackPackagedFile(upload_file)

        uploadroot = UPLOAD_DIR #config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name
        filename   = sanitize_filename(upload_file.filename)
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
        
        uploadroot = UPLOAD_DIR #config.get('bisque.image_service.upload_dir', data_path('uploads'))
        upload_dir = '%s/%s'%(uploadroot, str(bq.core.identity.get_user().name)) # .user_name       
        filename   = sanitize_filename(upload_file.filename)
        filepath   = '%s/%s.%s'%(upload_dir, strftime('%Y%m%d%H%M%S'), filename)
        unpack_dir = '%s/%s.%s.EXTRACTED'%( upload_dir, strftime('%Y%m%d%H%M%S'), filename )
        _mkdir (unpack_dir)
        
        filepath = self.localcopy(upload_file, filepath)
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
            
            while root:
                root, nextDir = os.path.split(root)
                dir = dir + [nextDir]
            
            dir.reverse()
            return (dir, name)
        
        #-----------------------------------------------------------------------------------------
        # ingestResource : recursively ingests a file hierarchy and returns top most parent's XML
        #-----------------------------------------------------------------------------------------
        def ingestResource(fileObj):
            xml = etree.parse((fileObj.get('XML'))).getroot()

            if fileObj.get('isDataset') is None:
                if fileObj.get('FILE') is not None:
                    #fileObjUp = UploadedFile(fileObj.get('FILE'), None, None)
                    with open(fileObj.get('FILE')) as f:
                        #sanitize_filename(os.path.basename(fileObj.get('FILE'))), 
                        resource =  blob_service.store_blob(resource=xml, fileobj=f)
                    return resource
                else:
                    return data_service.new_resource(resource = xml)
            else:
                del fileObj['isDataset']
                del fileObj['XML'] 
                
                # delete value fields from the dataset XML
                for value in xml.iter('value'):
                    xml.remove(value)
                
                # iterate through children of the dataset
                for member, fhash in fileObj.items():
                    memberXML = ingestResource(fhash)
                    value = etree.SubElement(xml, 'value', type='object')
                    value.text = memberXML.get('uri')
                
                return data_service.new_resource(resource = xml)
            return None


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
        return self.insert_members([ '%s/%s'%(unpack_dir, m) for m in members ], f)
    
    def filter_zip_bisque(self, f, intags):
        return self.importBisqueArchive(f, intags)

    def filter_zip_tstack(self, f, intags):
        return self.insert_members([self.process5Dimage(f, number_t=0, **intags)], f)
    
    def filter_zip_zstack(self, f, intags):
        return self.insert_members([self.process5Dimage(f, number_z=0, **intags)], f)
    
    def filter_5d_image(self, f, intags):
        return self.insert_members([self.process5Dimage(f, **intags)], f)

    def filter_series_bioformats(self, f, intags):
        unpack_dir, members = self.extractSeriesBioformats(f)
        return self.insert_members([ '%s/%s'%(unpack_dir, m) for m in members ], f)

    def filter_zip_volocity(self, f, intags):
        unpack_dir, members = self.extractSeriesVolocity(f)
        return self.insert_members([ '%s/%s'%(unpack_dir, m) for m in members ], f)

#------------------------------------------------------------------------------
# file ingestion support functions
#------------------------------------------------------------------------------
   
    def insert_resource(self, uf):
        """ effectively inserts the file into the bisque database and returns 
        a document describing an ingested resource
        """
        # try inserting the file in the blob service            
        try:
            # determine if resource is already on a blob_service store
            log.debug('Inserting %s ' % uf)
            resource = blob_service.store_blob(resource=uf.resource, fileobj=uf.fileobj)
            log.debug('Inserted resource :::::\n %s'% etree.tostring(resource) )
        except Exception, e:
            log.exception("Error during store %s" % etree.tostring(uf.resource))
            return None
        finally:
            uf.close()

        #uf.fileobj = None
        #uf.resource = resource
        return resource

    def insert_members(self, filelist, uf):
        parent_uri =  uf.resource.get('uri')
        # pre-process succeeded          
        log.debug('filter filelist: %s'% filelist )
        resources = []
        for fn in filelist:
            name = os.path.basename(fn)
            # Construct name based on original name
            if uf.filename not in name:
                name = '%s.%s'%(uf.filename, name )
            resource = etree.Element ('resource', name=name)
            resource.extend (copy.deepcopy (list (uf.resource)))
            etree.SubElement(resource, 'tag', name="original_upload", value=parent_uri, type='resource' )      
            myf = UploadedResource(fileobj=open(fn), resource=resource)
            ### NOTE ### 
            # could easily use self.process (myf)
            resources.append(self.insert_resource(myf))
        
        return resources
        
    
    def process(self, uf):
        """ processes the UploadedResource and either ingests it inplace or first applies 
        some special pre-processing, the function returns a document 
        describing an ingested resource
        """

        # This forces the the filename to part of actually file 
        #if uf.path and not os.path.basename (uf.path).endswith( uf.filename):
        #    newpath = "%s-%s" % (uf.path, uf.filename)
        #    shutil.move ( uf.path, newpath)
        #    uf.path = newpath
        #    uf.resource.set ('value', 'file://%s' % newpath)
            
        # first if tags are present ensure they are in an etree format
        # figure out if a file requires special processing
        intags = {}
        xl = uf.resource.xpath('//tag[@name="ingest"]')
        if len(xl):
            intags = dict([(t.get('name'), t.get('value')) 
                           for t in xl[0].xpath('tag') 
                               if t.get('value') is not None and t.get('name') is not None ])
            # remove the ingest tags from the tag document
            uf.resource.remove(xl[0])

        # append processing tags based on file type and extension
        mime = mimetypes.guess_type(sanitize_filename(uf.filename))[0]
        if mime in self.filters:
            intags['type'] = mime
        # no processing required   
        if intags.get('type') not in self.filters:
            return self.insert_resource(uf)
        # Processing is required
        return self.process_filtered(uf, intags)

    def process_filtered(self, uf, intags):
        # start processing
        log.debug('process -------------------\n %s'% intags )
        error = None
        # Ensure the uploaded file is local and named properly.
        tags = copy.deepcopy (list (uf.resource))
        del uf.resource[:]
        resource = self.insert_resource (uf)
        resource.extend (tags)
        try:
            # call filter on f with ingest tags
            resources = self.filters[ intags['type'] ](UploadedResource(resource), intags)
        except Exception, e:
            log.exception('Problem in processing file: %s : %s'  % (intags['type'], uf))
            error = 'Problem processing the file: %s'%e

        # some error during pre-processing
        if error is not None:
            log.debug('filters error: %s'% error )                
            resource = etree.Element('file', name=uf.filename)
            etree.SubElement(resource, 'tag', name='error', value=error)
            return resource

        # some error during pre-processing
        if len(resources)<1:
            log.debug('error while extracting images, none extracted' )
            resource = etree.Element('file', name=uf.filename)
            etree.SubElement(resource, 'tag', name='error', value='error while extracting images, none extracted')
            return resource    

        # if only one resource was inserted, return right away
        if len(resources)==1:
            return resources[0]

        # multiple resources ingested, we need to group them into a dataset and return a reference to it
        # now we'll just return a stupid stub
        ts = datetime.now().isoformat(' ')
        resource = etree.Element('dataset', name='%s'%(uf.filename))
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

        log.debug('processed resource :::::\n %s'% etree.tostring(resource) )
        resource = data_service.new_resource(resource=resource, view='deep') # dima: possible to request on post???
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
        #log.debug("TRANSFER %s"  % kw)
        #log.debug("BODY %s " % request.body[:100])
        files = []
        transfers = dict(kw)
        '''find a related parameter (to pname) containing resource XML
        
            :param transfer: hash of form parameters
            :param pname   : field parameter of file object
            '''

        def find_upload_resource(transfers, pname):
            log.debug ("transfers %s " % (transfers))
            
            resource = transfers.pop(pname+'_resource', None) #or transfers.pop(pname+'_tags', None)
            log.debug ("found %s _resource/_tags %s " % (pname, resource))
            if resource is not None:
                try:
                    if hasattr(resource, 'file'):
                        log.warn("XML Resource has file tag")
                        resource = f.file.read()
                    if isinstance(resource, basestring):
                        log.debug ("reading XML %s" % resource)
                        resource = etree.fromstring(resource)
                except:
                    log.exception("Couldn't read resource parameter %s" % resource)
                    resource = None
            return resource

        log.debug("INITIAL TRANSFER %s"  % transfers)
        for pname, f in dict(transfers).items():
            if pname.endswith ('_resource') or pname.endswith('_tags'): continue
            if hasattr(f, 'file'):
                # Uploaded File from multipart-form 
                transfers.pop(pname)
                resource = find_upload_resource(transfers, pname) or etree.Element('resource', name=sanitize_filename (getattr(f, 'filename', '')))
                files.append(UploadedResource(fileobj=f.file, resource=resource))
                log.debug ("TRASNFERED %s %s" % (f.filename, etree.tostring(resource)))
            if pname.endswith('.uploaded'):
                # Entry point for NGINX upload and insert
                transfers.pop(pname)
                resource = etree.fromstring (f)
                payload_resource = find_upload_resource(transfers, pname.replace ('.uploaded', '')) or etree.Element('resource')
                if payload_resource:
                    resource = merge_resources (resource, payload_resource)
                upload_resource  = UploadedResource(resource=resource)
                files.append(upload_resource)
                log.debug ("UPLOADED %s %s" % (upload_resource, etree.tostring(resource)))
        log.debug("TRANSFER after files %s"  % transfers)

        for pname, f in transfers.items():
            if (pname.endswith ('_resource')): 
                transfers.pop(pname)
                resource = etree.fromstring(f)
                files.append(UploadedResource(resource=resource))

        log.debug("TRANSFER after resources %s"  % transfers)
        # Should reject anything not matching

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
        """
        log.info ('insert %s for %s' % (url, user))
        log.warn ("DEPRECATED ENTRY POINT: use insert_resource")

        if user is not None and identity.current.user_name == 'admin':
            identity.current.set_current_user( user )
        resource = etree.Element('resource', name=filename, permission=permission, value=url)
        if 'tags' in kw:
            try:
                tags = etree.fromstring(kw['tags'])
                resource.extend(list(tags))
            except Exception,e: # dima: possible exceptions here, ValueError, XMLSyntaxError
                del kw['tags']
        kw['insert.resource'] = etree.tostring(resource)
        return self.transfer (** kw)

    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def insert_XXresource(self, resource,  user=None, **kw):
        """insert a  fixed resource. This allows  insertion 
        of  resources  when they are already present on safe media
        i.e on the local server drives or remote irods, hdfs etc.

        Supported URL schemes must be enabled in blob_storage.
        This routine will report an error for illegal schemes
        """
        # Note: This entrypoint should allow permission and tags to be inserted
        # in a similar way to tranfers.. maybe combining the two would be needed.
        log.info ('insert %s for %s' % (url, user))

        if hasattr(resource, 'file'):
            resource = etree.parse(resource.file)
        else:
            resource = etree.fromstring(resource)
        
        try:
            if user is not None and identity.current.user_name == 'admin':
                identity.current.set_current_user( user )

            rlist  = [ UploadedResource ( resource = resource) ]
            response = self.ingest (rlist)
            return etree.tostring(response)
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
