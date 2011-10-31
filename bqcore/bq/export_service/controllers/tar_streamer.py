import os
import tarfile
import copy

from tg import response
from cStringIO import StringIO


class TarFileWrapper(tarfile.TarFile):
    
    def addTarInfo(self, tarinfo):
        self._check("aw")

        tarinfo = copy.copy(tarinfo)
        buf = tarinfo.tobuf(self.format, self.encoding, self.errors)
        self.fileobj.write(buf)
        self.offset += len(buf)
        
        self.members.append(tarinfo)

    def writeFileChunk(self, fileobj=None, block_size=tarfile.BLOCKSIZE):
        self.fileobj.write(fileobj.read(block_size))
   
    def finishWrite(self, filesize):
        blocks, remainder = divmod(filesize, tarfile.BLOCKSIZE)
        if remainder > 0:
            self.fileobj.write(tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
            blocks += 1
        self.offset += blocks * tarfile.BLOCKSIZE


class TarStreamer():
    
        block_size = 1024*64
        
        def sendResponseHeader(self,  tarFileName):
            response.headers['Content-Type'] = 'application/x-tar'
            response.headers['Transfer-Encoding'] = 'chunked'
            response.headers['Content-Disposition'] = 'attachment;filename='+tarFileName
            
        def getTarInfo(self, filename):
            tarInfo = tarfile.TarInfo(filename);
            tarInfo.name = os.path.basename(filename)
            tarInfo.size = os.path.getsize(filename)
            return tarInfo
            
        def stream(self, files):
            buffer, block = StringIO(), True
            tarWriter = TarFileWrapper.open(None, mode='w', fileobj=buffer)
            
            for filename in files:
                file = open(filename, 'rb')
                tarInfo, block = self.getTarInfo(filename), True
                tarWriter.addTarInfo(tarInfo)

                while block:
                    tarWriter.writeFileChunk(fileobj=file, block_size=self.block_size)
                    block = buffer.getvalue()
                    buffer.truncate(0)
                    
                    yield block

                tarWriter.finishWrite(tarInfo.size)
                file.close()
            
            tarWriter.close()
            yield buffer.getvalue()
