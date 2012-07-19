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

  1. Accept metadata as XML file along with packed image files
  1.

"""

__module__    = "export_service"
__author__    = "Dmitry Fedorov, Kris Kvilekval, Santhoshkumar Sunderrajan"
__version__   = "1.3"
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
from repoze.what import predicates 


from bq.core.service import ServiceController

# additional includes
import sys
import traceback
import datetime
import time
import re
import threading
import shutil
import tarfile
import zipfile
import logging
import gdata.docs
import gdata.docs.service

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from urllib import quote
from lxml import etree
from time import strftime

import tg
from tg import request, response, session, flash, require
from repoze.what import predicates

from bq import data_service
from create_archive import CreateArchive

#---------------------------------------------------------------------------------------
# inits
#---------------------------------------------------------------------------------------

NO_BYTES=16*1024
max_size=1024*1024*1024*2
CHARREGEX=re.compile("\W+")
log  = logging.getLogger('bq.export_service')

#---------------------------------------------------------------------------------------
# controller 
#---------------------------------------------------------------------------------------

log = logging.getLogger("bq.export_service")
class export_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "export"

    def __init__(self, server_url):
        super(export_serviceController, self).__init__(server_url)
        
    @expose('bq.export_service.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from export_service'))


#------------------------------------------------------------------------------
# Google Docs Export
#------------------------------------------------------------------------------

    @expose(template='bq.export_service.templates.to_gdocs')
    @require(predicates.not_anonymous())
    def to_gdocs (self, **kw):
        return { 'opts': kw }        

    @expose(template='bq.export_service.templates.to_gdocs_send')
    @require(predicates.not_anonymous())
    def to_gdocs_send (self, **kw):
        if not 'google_id' in kw: return 'Google e-mail is needed'
        if not 'google_password' in kw: return 'Google password is needed'
        if not 'document_url' in kw: return 'Document to be exported is not provided'

        # get the document
        google_id = str(kw['google_id'])
        google_pass = str(kw['google_password'])
        url = str(kw['document_url'])

        s = data_service.load(url+'?view=deep&format=csv')
        #s = data_service.get_resource(url, view='deep', format='csv')
        
        input_file = StringIO(s)
        #log.debug('Google Docs input: ' + s )

        # upload to google docs
        gd_client = gdata.docs.service.DocsService()
        gd_client.email = str(google_id)
        gd_client.password = str(google_pass)
        gd_client.source = 'CBI_UCSB-Bisque-1'
        try:
            gd_client.ProgrammaticLogin()
        except:
            return dict(error= str(sys.exc_value) )

        m_file_handle = input_file
        m_content_type = 'text/csv'
        m_content_length = len(s)
        m_file_name = quote(url)
        m_title = 'Bisque data - '+url

        ms = gdata.MediaSource(file_handle = m_file_handle, content_type = m_content_type, content_length = m_content_length, file_name = m_file_name )
        entry = gd_client.UploadSpreadsheet(ms, m_title)
        return dict(error=None, google_url=str(entry.GetAlternateLink().href))


    @expose()
    def exportString(self, **kw):
        value = kw.pop('value', '')
        return value
    
    #------------------------------------------------------------------
    # new ArchiveStreamer - Utkarsh
    #------------------------------------------------------------------

    @expose()
    def initStream(self, **kw):
        """Create and return a streaming archive

        :param compressionType: tar, zip, gzip, bz2
        :param files: a comma separated list of resource URIs to include in the archive
        :param datasets: a comma separated list of dataset resource URIs to include in the archive
        :param urls: a comma separated list of any url accessible over HTTP to include in the archive

        ------------------------------------
        Sample XML when POSTing to this app
        ------------------------------------
        
        <resource>
            <value type="FILE">    ...    </value>
            <value type="URL">     ...    </value>
            <value type="DATASET"> ...    </value>
        </resource>
        
        """
        
        from bq.export_service.controllers.archive_streamer import ArchiveStreamer
        files    = []
        datasets = []
        urls     = []

        if (tg.request.method.upper()=='POST' and tg.request.body):
            try:
                data = etree.XML(tg.request.body)
            except etree.ParseError:
                data = []
            for resource in data:
                type = resource.get('type', 'URL').upper() 
                if (type == 'FILE'):
                    files.append(resource.text)
                elif (type == 'DATASET'):
                    datasets.append(resource.text)
                elif (type == 'URL'):
                    urls.append(resource.text)
                else:
                    urls.append(resource.text)

        compressionType = kw.pop('compressionType', '')
        if 'files' in kw: files = files + kw.pop('files').split(',')
        if 'datasets' in kw: datasets = datasets + kw.pop('datasets').split(',')
        if 'urls' in kw: urls = urls + kw.pop('urls').split(',')    
        filename = kw.pop('filename', None) or 'Bisque-archive '+time.strftime('%H.%M.%S')
        
        archiveStreamer = ArchiveStreamer(compressionType)
        archiveStreamer.init(archiveName=filename, fileList=files, datasetList=datasets, urlList=urls)
        return archiveStreamer.stream()


##------------------------------------------------------------------------------
## Tar file export, by Santosh
##------------------------------------------------------------------------------
#    @expose(template='bq.export_service.templates.to_tar')
#    @require(predicates.not_anonymous())    
#    def to_tar (self, **kw):
#        return { 'opts': kw }
#
#    #to export tar file, called from export service page
#    @expose()
#    @require(predicates.not_anonymous())      
#    def exportTar(self,**kw):
#        resource_url=str(kw.pop('resource_url',''))
#        resource_url=self.refineUrl(resource_url)#refine the url
#        url_list=resource_url.split('/')
#        lenList=len(url_list)
#        tarName=url_list[lenList-2]+'_'+url_list[lenList-1]
#        tf=self.checkCache(tarName)#checking the cache for the .tar file
#        if tf is not None:
#            filePath=os.path.abspath(tf)
#            return serve_file(filePath, "application/x-tar", "attachment")
#        try:
#            check_index=url_list.index('datasets')
#            url=resource_url
#            if url is not '':
#                try:
#                    xmldata=data_service.load(url+'?view=full')
#                except:
#                    return dict(error= str(sys.exc_value))
#            response=etree.Element('response')
#            document=etree.ElementTree(response)
#            doc=etree.fromstring(xmldata)
#            for elt in doc.getiterator():
#                if elt.tag=='resource':
#                    if elt.attrib.has_key('type'):
#                        if elt.get('type') == 'image':
#                            uri=elt.get('uri')
#                            imgdata=data_service.load(uri+'?view=full')
#                            imdoc=etree.fromstring(imgdata)
#                            for imelt in imdoc.getiterator('image'):
#                                if imelt.tag=='image':
#                                    image=etree.SubElement(response,'image',src=imelt.get('src'),uri=uri)
#            cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"'%(tarName+'.tar')
#            cherrypy.response.headerMap['Content-Type'] = "application/x-tar"
#            zipDict=self.checkTarFileSize(document)
#            num_files=zipDict['num_files']
#            total_size=zipDict['total_size']
#            contLength=total_size+num_files*512+10*1024*1024 #10 additional MB of buffer size
#            log.debug("content length::::::::::::::::::::::::::::::::"+str(contLength))
#            cherrypy.response.headerMap['Content-Length'] = str(contLength)
#            archive=CreateArchive(tarName, self.userpass)
#            return archive.createTarFile(document)
#        except ValueError:
#            check_index=-1
#        if check_index==-1:
#            if resource_url is not '':
#                try:
#                    xmldata=data_service.load(resource_url+'?view=full')
#                except:
#                    return dict(error= str(sys.exc_value))
#                cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"'%(tarName+'.tar')
#                cherrypy.response.headerMap['Content-Type'] = "application/x-tar"
#                response=etree.Element('response')
#                document=etree.ElementTree(response)
#                doc=etree.fromstring(xmldata)
#                for elt in doc.getiterator('image'):
#                    if elt.tag=='image':
#                        image=etree.SubElement(response,'image',src=elt.get('src'),uri=elt.get('uri'))
#                zipDict=self.checkTarFileSize(document)
#                num_files=zipDict['num_files']
#                total_size=zipDict['total_size']
#                contLength=total_size+num_files*512+10*1024*1024 #10 additional MB of buffer size
#                log.debug("content length::::::::::::::::::::::::::::::::"+str(contLength))
#                cherrypy.response.headerMap['Content-Length'] = str(contLength)
#                archive=CreateArchive(tarName, self.userpass)
#                return archive.createTarFile(document)
#        return
#
#    @expose()
#    @require(predicates.not_anonymous())    
#    def segmentationDsTar(self,**kw):
#        dataset_label=kw['dataset_label']
#        tarName=re.sub(CHARREGEX,'_',dataset_label)
#        tf=self.checkCache(tarName)
#        if tf is not None:
#            filePath=os.path.abspath(tf)
#            return serve_file(filePath, "application/x-tar", "attachment")
#        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"'%(tarName+'.tar')
#        cherrypy.response.headerMap['Content-Type'] = "application/x-tar"
#        server=data_service.uri()
#        datasetUrl=kw['dataset_uri']+'/tags'
#        headers,imagesXml=http_client.request(datasetUrl)
#        imagesXml=str(imagesXml)
#        response=etree.Element('response')
#        document=etree.ElementTree(response)
#        xpathExpression='//resource[@type="image"]'
#        xmlDoc=etree.fromstring(imagesXml)
#        eltList=xmlDoc.xpath(xpathExpression)
#        len_elements=len(eltList)
#        for x in range(len_elements):
#            log.debug("index"+str(x))
#            elt=eltList[x]
#            uri=elt.attrib['uri']
#            headers,srcrequest=http_client.request(uri)
#            srcrequest=str(srcrequest)
#            xpathExpression='//image'
#            xmlDoc=etree.fromstring(srcrequest)
#            elementList=xmlDoc.xpath(xpathExpression)
#            element=elementList[0]
#            src=element.attrib['src']
#            image=etree.SubElement(response,'image',src=src,uri=uri)
#        zipDict=self.checkTarFileSize(document)
#        num_files=zipDict['num_files']
#        total_size=zipDict['total_size']
#        contLength=total_size+num_files*512+10*1024*1024 #10 additional MB of buffer size
#        log.debug("content length::::::::::::::::::::::::::::::::"+str(contLength))
#        cherrypy.response.headerMap['Content-Length'] = str(contLength)
#        archive=CreateArchive(tarName, self.userpass)
#        return archive.createTarFile(document)
#
#    def findDataSetUrl(self,xmldata,dataset_label):
#        xmlDoc=etree.fromstring(xmldata)
#        xpathExpression='//dataset[@name="'+dataset_label+'"]'
#        eltList=xmlDoc.xpath(xpathExpression)
#        log.debug(eltList)
#        elt=eltList[0];
#        return elt.attrib['uri']
#
#    #check the size of the download files and make parts
#    @expose('bq.export_service.templates.downloadTarFiles')
#    @require(predicates.not_anonymous())    
#    def checkDownloadTar(self,**kw):
#        query = kw.pop('tag_query', None)
#        view=kw.pop('view', 'short')
#        wpublic = kw.pop('wpublic', not identity.not_anonymous())
#        offset = int(kw.pop('offset', 0))
#        response = etree.Element('response')
#        images = aggregate_service.query("image" ,
#                                         tag_query=query,
#                                         view=view,
#                                         wpublic=wpublic, **kw)
#        for i in images[offset:]:
#            response.append(i)
#        document=etree.ElementTree(response)
#        log.debug('Tag Query Response:'+etree.tostring(document))
#        zipDict=self.checkTarFileSize(document)
#        limits=zipDict['limits']
#        offsets=zipDict['offsets']
#        total_size=zipDict['total_size']
#        num_files=zipDict['num_files']
#        if total_size > max_size:
#            return dict(limits=limits,offsets=offsets,query=query,wpublic=wpublic,view="short")
#        else:
#            part=kw.pop('part',1)
#            tarName=re.sub(CHARREGEX,'_',query)+'_'+str(part)
#            cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"'%(tarName+'.tar')
#            cherrypy.response.headerMap['Content-Type'] = "application/x-tar"
#            contLength=512-total_size%512 +total_size+num_files*512+5*1024*1024
#            log.debug("content length::::::::::::::::::::::::::::::::"+str(contLength))
#            cherrypy.response.headerMap['Content-Length'] = str(contLength)
#            offset=0
#            limit=-1
#            tf=self.checkCache(tarName)
#            if tf is not None:
#                filePath=os.path.abspath(tf)
#                return serve_file(filePath, "application/x-tar", "attachment")
#            view=kw.pop('view', 'short')
#            wpublic = kw.pop('wpublic', not identity.not_anonymous())
#            response = etree.Element('response')
#            images = aggregate_service.query("image" ,
#                                         tag_query=query,
#                                         view=view,
#                                         wpublic=wpublic, **kw)
#            if limit != -1:
#                for i in images[offset:limit]:
#                    response.append(i)
#            else:
#                for i in images[offset:]:
#                    response.append(i)
#            document=etree.ElementTree(response)
#            archive=CreateArchive(tarName, self.userpass)
#            return archive.createTarFile(document)
#
#    #check the size of the tar file using image size info
#    def checkTarFileSize(self,document):
#        count=0
#        no_bytes=0
#        no_gb=max_size
#        offsets=[0]
#        limits=[]
#        end_ind=0
#        total_size=0
#        num_files=0
#        for elt in document.getiterator():
#            if elt.tag == 'image':
#                num_files=num_files+1
#                src=str(elt.get('src'))
#                imageSize=self.getImageSizeFromInfo(src)
#                if no_bytes < no_gb:
#                    no_bytes=no_bytes+int(imageSize)
#                    total_size=total_size+int(imageSize)
#                    log.debug('Info:Total Size so far'+str(no_bytes))
#                    count=count+1
#                    end_ind=0
#                else:
#                    offsets.append(count)
#                    no_bytes=int(imageSize)
#                    end_ind=1
#        if end_ind==1:
#            offsets.append(count)
#        for x in range(len(offsets)-1):
#            limits.append(offsets[x+1])
#        limits.append(-1)
#        return dict(limits=limits,offsets=offsets,no_bytes=no_bytes,total_size=total_size,num_files=num_files)
#
#    @expose()
#    @require(predicates.not_anonymous())    
#    def downloadTar(self,**kw):
#        query = kw.pop('tag_query', None)
#        part=kw.pop('part',1)
#        tarName=re.sub(CHARREGEX,'_',query)+'_'+str(part)
#        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"'%(tarName+'.tar')
#        cherrypy.response.headerMap['Content-Type'] = "application/x-tar"
#        tf=self.checkCache(tarName)
#        if tf is not None:
#            filePath=os.path.abspath(tf)
#            return serve_file(filePath, "application/x-tar", "attachment")
#        view=kw.pop('view', 'short')
#        wpublic = kw.pop('wpublic', not identity.not_anonymous())
#        offset = int(kw.pop('offset', 0))
#        limit = int(kw.pop('limit', 0))
#        response = etree.Element('response')
#        images = aggregate_service.query("image" ,
#                                         tag_query=query,
#                                         view=view,
#                                         wpublic=wpublic, **kw)
#        if limit != -1:
#            for i in images[offset:limit]:
#                response.append(i)
#        else:
#            for i in images[offset:]:
#                response.append(i)
#        document=etree.ElementTree(response)
#        zipDict=self.checkTarFileSize(document)
#        num_files=zipDict['num_files']
#        total_size=zipDict['total_size']
#        contLength=total_size+num_files*512+10*1024*1024
#        log.debug("content length::::::::::::::::::::::::::::::::"+str(contLength))
#        cherrypy.response.headerMap['Content-Length'] = str(contLength)
#        archive=CreateArchive(tarName, self.userpass)
#        return archive.createTarFile(document)
#
#    #get the size of the image using image info-filesize
#    def getImageSizeFromInfo(self,src):
#        #header,responseXml = http_client.xmlrequest(url=src+'?info')
#        #xmlResp=str(responseXml)
#        #log.debug("Response XML:"+str(xmlResp))
#        #xmlDoc=etree.fromstring(str(xmlResp))
#        log.debug("URI::::::::::::::::::::::::::::::"+src)
#        try:
#            xmlStr=image_service.info (src)
#            xmlDoc=etree.fromstring(xmlStr)
#        except:
#             header,responseXml = http_client.xmlrequest(url=src+'?info',userpass=self.userpass)
#             xmlResp=str(responseXml)
#             log.debug("Response XML:"+str(xmlResp))
#             try:
#                 xmlDoc=etree.fromstring(str(xmlResp))
#             except etree.XMLSyntaxError:
#                 log.error("SizeFromInfo: BAD INFO from imageserver %s" % xmlResp)
#                 return 0
#             #xmlDoc=data_service.load(src+'?info')
#        eltList=xmlDoc.xpath('//tag[@name="filesize"]')
#        log.debug(etree.tostring(eltList[0]))
#        elt=eltList[0];
#        return elt.attrib['value']
#
#    #download the tar from the cache
#    def checkCache(self,tarName):
#        try:
#            curDir=os.curdir
#            downDir=curDir+'/downloads'
#            if os.path.exists(downDir):
#                tempf=open(downDir+'/'+tarName+'.tar','rb')
#                tempf.close()
#                log.debug("Returning cache file:::::::::::::::::")
#                filename='downloads/'+tarName+'.tar'
#                return filename
#            else:
#                os.mkdir("downloads")
#                return None
#        except IOError:
#            tempf=None
#            return tempf
#
#    def fileGenerator(self,fp):
#        no_bytes=8
#        while True:
#            bytes = fp.read(1024 * no_bytes) # Read blocks of 8KB at a time
#            if not bytes: break
#            yield bytes
#
#    def refineUrl(self,resource_url):
#        check_deep=resource_url.find('?view=deep')
#        if check_deep > 0:
#            resource_url=resource_url.replace('?view=deep','')
#        check_full=resource_url.find('?view=full')
#        if check_full > 0:
#            resource_url=resource_url.replace('?view=full','')
#        return resource_url
#
#    def readMetaData(self,extractDir):
#        try:
#           metaF=open(extractDir+'/metadata.xml')
#           metadata=metaF.read()
#           metaXml=etree.fromstring(metadata)
#        except IOError:
#           return None
#        return metaXml
#
#    def sanitize_filename(self, filename):
#        """ Removes any path info that might be inside filename, and returns results. """
#        import urllib
#        return urllib.unquote(filename).split("\\")[-1].split("/")[-1]


#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------
def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  export_serviceController(uri)
    #directory.register_service ('export_service', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'export_service', 'public'))]

__controller__ =  export_serviceController
