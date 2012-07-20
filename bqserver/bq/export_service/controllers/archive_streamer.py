import os
import tarfile
import copy
import string
import logging
import httplib2 
import urlparse

from tg import request, response, expose, config
from lxml import etree
from cStringIO import StringIO
from bq import data_service, image_service, blob_service
from bq.export_service.controllers.archiver.archiver_factory import ArchiverFactory

log = logging.getLogger("bq.export_service.archive_streamer")

class ArchiveStreamer():
    
    block_size = 1024 * 64

    def __init__(self, compressionType):
        self.archiver = ArchiverFactory().getClass(compressionType)
    
    
    def init(self, archiveName='Bisque archive', fileList=[], datasetList=[], urlList=[]):
        self.fileList = fileList
        self.datasetList = datasetList
        self.urlList = urlList
        
        response.headers['Content-Type'] = self.archiver.getContentType()
        response.headers['Content-Disposition'] = 'attachment;filename="' + archiveName + self.archiver.getFileExtension() + '"'
    
    def stream(self):
        log.debug("ArchiveStreamer: Begin stream %s" % request.url)
        
        flist = self.fileInfoList(self.fileList, self.datasetList, self.urlList)
        for file in flist:
            self.archiver.beginFile(file)
            while not self.archiver.EOF():
                yield self.archiver.readBlock(self.block_size)
            self.archiver.endFile()

        yield self.archiver.readEnding()
        self.archiver.close()
        log.debug ("ArchiveStreamer: End stream %s" % request.url)

    # ------------------------------------------------------------------------------------------
    # Utility functions 
    # ------------------------------------------------------------------------------------------
    
    # Returns a list of fileInfo objects based on files' URIs
    def fileInfoList(self, fileList, datasetList, urlList):
        
        def fileInfo(dataset, uri, index=0):
            xml     =   data_service.get_resource(uri, view='deep')
            name    =   xml.get('name') 

            # try to figure out a name for the resource
            if not name:
                name = xml.xpath('./tag[@name="filename"]') or xml.xpath('./tag[@name="name"]')
                name = name and name[0].get('value')
            if not name and xml.get('resource_uniq'):
                name = xml.get('resource_uniq')[-4] 
            if not name: 
                name = str(index)
            return  dict(XML        =   xml, 
                         type       =   xml.tag,
                         name       =   name ,
                         uniq       =   xml.get('resource_uniq'),
                         path       =   blob_service.localpath(xml.get('resource_uniq')),
                         dataset    =   dataset,
                         extension  =   '')
        
        def xmlInfo(finfo):
            file = finfo.copy()
            file['extension'] = '.xml'
            return file

        def urlInfo(url, index=0):
            httpReader = httplib2.Http()
            # This hack gets around bisque internal authentication mechanisms 
            # please refer to http://biodev.ece.ucsb.edu/projects/bisquik/ticket/597
            headers  = dict ( (name, request.headers.get(name)) for name in ['Authorization', 'Mex', 'Cookie' ]
                              if name in request.headers)

            # test if URL is relative, httplib2 does not fetch relative
            if urlparse.urlparse(url).scheme == '':
                url = urlparse.urljoin(config.get('bisque.root'), url)
            
            log.debug ('ArchiveStreamer: Sending %s with %s'  % (url, headers))
            header, content = httpReader.request(url, headers=headers)
            
            items = (header.get('content-disposition') or header.get('Content-Disposition') or '').split(';')
            fileName = str(index) + '.'
            log.debug('Respose headers: %s'%header)
            log.debug('items: %s'%items)
            
            for item in items:
                pair = item.split('=')
                if (pair[0].lower().strip()=='filename'):
                    fileName = pair[1].strip('"\'')
            
            return  dict(name       =   fileName,
                         content    =   content,
                         dataset    =   '',
                         extension  =   'URL')
                    
        flist = []

        if len(fileList)>0:       # empty fileList
            for uri in fileList:
                finfo = fileInfo('', uri)
                flist.append(finfo)      # blank dataset name for orphan files
                if finfo.get('type') == 'image':
                    flist.append(xmlInfo(finfo))

        if len(datasetList)>0:     # empty datasetList
            for uri in datasetList:
                dataset = data_service.get_resource(uri, view='full')
                name = dataset.xpath('/dataset/@name')[0]
                members = dataset.xpath('/dataset/tag[@name="members"][1]/value')
                
                for index, member in enumerate(members):
                    finfo = fileInfo(name, member.text, index)
                    flist.append(finfo)
                    if finfo.get('type') == 'image':
                        flist.append(xmlInfo(finfo))

        if len(urlList)>0:       # empty urlList
            for index, url in enumerate(urlList):
                finfo = urlInfo(url, index)
                flist.append(finfo)      # blank dataset name for orphan files

        return flist
