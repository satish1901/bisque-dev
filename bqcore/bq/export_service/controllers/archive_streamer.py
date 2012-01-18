import os
import tarfile
import copy
import string
from tg import response, expose
from lxml import etree
from cStringIO import StringIO
from bq import data_service, image_service, blob_service
from bq.export_service.controllers.archiver.archiver_factory import ArchiverFactory


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
        flist = self.fileInfoList(self.fileList, self.datasetList)
        
        for file in flist:
            self.archiver.beginFile(file)
            while not self.archiver.EOF():
                yield self.archiver.readBlock(self.block_size)
            self.archiver.endFile()

        yield self.archiver.readEnding()
        self.archiver.close()

    # ------------------------------------------------------------------------------------------
    # Utility functions 
    # ------------------------------------------------------------------------------------------
    
    # Returns a list of fileInfo objects based on files' URIs
    def fileInfoList(self, fileList, datasetList):
        
        def fileInfo(dataset, uri):
            file_info = {}
            
            xml = data_service.get_resource(uri, view='deep')
            file_info['XML'] = xml
            file_info['source'] = xml.get('value')
            file_info['name'] = xml.get('name')
            file_info['uniq']  = xml.get('resource_uniq')
            file_info['path'] = blob_service.localpath(file_info['uniq'])
            file_info['dataset'] = dataset
            file_info['extension'] = ''
            
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
                flist.append(xmlInfo(finfo))

        if datasetList != ['']:     # empty datasetList
            for uri in datasetList:
                dataset = data_service.get_resource(uri, view='full')
                name = dataset.xpath('/dataset/@name')[0]
                members = dataset.xpath('/dataset/tag[@name="members"][1]/value')
                
                for member in members:
                    finfo = fileInfo(name, member.text)
                    flist.append(finfo)
                    flist.append(xmlInfo(finfo))

        return flist
