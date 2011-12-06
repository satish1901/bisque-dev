from cStringIO import StringIO
from lxml import etree
import os

class AbstractArchiver():

    def getContentType(self):
        return 'text/plain'

    def getFileExtension(self):
        return '.log'
    
    def beginFile(self, file):
        if file.get('extension') == '.xml':
            self.reader = StringIO(etree.tostring(file.get('XML')))
        else:
            self.reader = open(file.get('path'), 'rb')
        return
    
    def readBlock(self, block_size):
        return 
    
    def EOF(self):
        return True
    
    def endFile(self):
        self.reader.close()
        return
    
    def readEnding(self):
        return ''
    
    def close(self):
        return
    
    def destinationPath(self, file):
        path = file.get('dataset') + os.sep if file.get('dataset') is not '' else ''
        path += '(' + file.get('uniq')[-4:] + ') ' + file.get('name') + file.get('extension')
        return path


class ArchiverFactory():
    
    from bq.export_service.controllers.archiver.tar_archiver import TarArchiver
    from bq.export_service.controllers.archiver.zip_archiver import ZipArchiver
    from bq.export_service.controllers.archiver.gzip_archiver import GZipArchiver
    from bq.export_service.controllers.archiver.bz2_archiver import BZip2Archiver

    supportedArchivers = {
                             'tar' : TarArchiver,
                             'zip' : ZipArchiver,
                             'gzip' : GZipArchiver,
                             'bz2' : BZip2Archiver,
                         }  
    
    @staticmethod
    def getClass(compressionType):
        archiver = ArchiverFactory.supportedArchivers.get(compressionType)
        archiver = AbstractArchiver if archiver is None else archiver  

        return archiver()
