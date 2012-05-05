from cStringIO import StringIO
from lxml import etree
import os

class AbstractArchiver():

    def getContentType(self):
        return 'text/plain'

    def getFileExtension(self):
        return '.xml'
    
    def beginFile(self, file):
        if file.get('extension') == '.xml' or file.get('path') is None:
            file['extension'] = '.xml'  # ensure extension is XML if we are only exporting XML
            self.reader = StringIO(etree.tostring(file.get('XML')))
            
            self.reader.seek(0, 2)
            self.fileSize = self.reader.tell()
            self.reader.seek(0)
        else:
            self.reader = open(file.get('path'), 'rb')

        return
    
    def readBlock(self, block_size):
        return self.reader.read(block_size)
    
    def EOF(self):
        return self.reader.tell()==self.fileSize
    
    def endFile(self):
        self.reader.close()
        return
    
    def readEnding(self):
        return ''
    
    def close(self):
        return
    
    def destinationPath(self, file):
        uniq = '-' + file.get('uniq')[-4:] if file.get('uniq') is not None else '' 
        path = file.get('dataset') + os.sep if file.get('dataset') is not '' else ''
        fileName, fileExt = os.path.splitext(file.get('name'))
        path +=  fileName + uniq + (file.get('extension') or fileExt)
        return path


class ArchiverFactory():
    
    from bq.export_service.controllers.archiver.tar_archiver import TarArchiver
    from bq.export_service.controllers.archiver.zip_archiver import ZipArchiver
    from bq.export_service.controllers.archiver.gzip_archiver import GZipArchiver
    from bq.export_service.controllers.archiver.bz2_archiver import BZip2Archiver

    supportedArchivers = {
                             'tar'  :   TarArchiver,
                             'zip'  :   ZipArchiver,
                             'gzip' :   GZipArchiver,
                             'bz2'  :   BZip2Archiver,
                         }  
    
    @staticmethod
    def getClass(compressionType):
        archiver = ArchiverFactory.supportedArchivers.get(compressionType)
        archiver = AbstractArchiver if archiver is None else archiver  

        return archiver()
