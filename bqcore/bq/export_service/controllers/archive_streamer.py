import os
import tarfile
import copy
from tg import response, expose
from lxml import etree
from cStringIO import StringIO
from bq import data_service, image_service
from bq.export_service.controllers.archiver.archiver_factory import ArchiverFactory


class ArchiveStreamer():
    
    block_size = 1024 * 64

    def __init__(self, compressionType):
        self.archiver = ArchiverFactory().getClass(compressionType)
    
    
    def init(self, archiveName='Bisque archive', fileList=[''], datasetList=['']):
        self.fileList = fileList
        self.datasetList = datasetList
        
        response.headers['Content-Type'] = self.archiver.getContentType()
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Content-Disposition'] = 'attachment;filename=' + archiveName + self.archiver.getFileExtension()
        
    
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
            file = {}

            file['XML'] = data_service.get_resource(uri, view='deep')
            file['source'] = file.get('XML').get('src')
            file['name'] = image_service.getFileName(file.get('source'))
            file['path'] = image_service.image_path(file.get('source'))
            file['id'] = image_service.getImageID(file.get('source'))
            file['dataset'] = dataset
            file['extension'] = ''
            
            return file
        
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
