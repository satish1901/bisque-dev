import os
import tarfile
import copy
import string
import logging

from tg import request, response, expose
from lxml import etree
from cStringIO import StringIO
from bq import data_service, image_service, blob_service
from bq.export_service.controllers.archiver.archiver_factory import ArchiverFactory

log = logging.getLogger("bq.export_service.archive_streamer")

class ArchiveStreamer():
    
    block_size = 1024 * 64

    def __init__(self, compressionType):
        self.archiver = ArchiverFactory().getClass(compressionType)
    
    
    def init(self, archiveName='Bisque archive', fileList=[''], datasetList=['']):
        self.fileList = fileList
        self.datasetList = datasetList
        
        response.headers['Content-Type'] = self.archiver.getContentType()
        response.headers['Content-Disposition'] = 'attachment;filename="' + archiveName + self.archiver.getFileExtension() + '"'
    
    def stream(self):
        log.debug ("BEGIN STREAM %s" % request.url)
        flist = self.fileInfoList(self.fileList, self.datasetList)
        for file in flist:
            self.archiver.beginFile(file)
            while not self.archiver.EOF():
                yield self.archiver.readBlock(self.block_size)
            self.archiver.endFile()

        yield self.archiver.readEnding()
        self.archiver.close()
        log.debug ("END STREAM %s" % request.url)

    # ------------------------------------------------------------------------------------------
    # Utility functions 
    # ------------------------------------------------------------------------------------------
    
    # Returns a list of fileInfo objects based on files' URIs
    def fileInfoList(self, fileList, datasetList):
        
        def fileInfo(dataset, uri):
            from random import randint
            
            file_info   =   {}
            xml         =   data_service.get_resource(uri, view='deep')
            name        =   (xml.get('name') or xml.xpath('./tag[@name="filename"]') or xml.xpath('./tag[@name="name"]')) and name[0]
            file_info   =   dict(XML        =   xml, 
                                 type       =   xml.tag,
                                 name       =   name or xml.get('uniq')[-4:] if xml.get('uniq') is not None else str(randint(1000,9999)),
                                 uniq       =   xml.get('uniq'),
                                 path       =   blob_service.localpath(file_info['uniq'])
                                 dataset    =   dataset,
                                 extension  =   '')

            return file_info

        
        def xmlInfo(finfo):
            file = finfo.copy()
            file['extension'] = '.xml'
            return file
            
        flist = []

        if fileList != ['']:       # empty fileList
            for uri in fileList:
                finfo = fileInfo('', uri)
                flist.append(finfo)      #blank dataset name for orphan files
                if finfo.get('type') == 'image':
                    flist.append(xmlInfo(finfo))

        if datasetList != ['']:     # empty datasetList
            for uri in datasetList:
                dataset = data_service.get_resource(uri, view='full')
                name = dataset.xpath('/dataset/@name')[0]
                members = dataset.xpath('/dataset/tag[@name="members"][1]/value')
                
                for member in members:
                    finfo = fileInfo(name, member.text)
                    flist.append(finfo)
                    if finfo.get('type') == 'image':
                        flist.append(xmlInfo(finfo))

        return flist
