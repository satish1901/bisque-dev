import os
import tarfile
import copy
import string
import logging
import httplib2 
import urlparse
import os
import datetime
from bq.release import __VERSION__

from tg import request, response, expose, config
from lxml import etree
from cStringIO import StringIO
from bq.exceptions import IllegalOperation
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
        
        filename = archiveName + self.archiver.getFileExtension()
        try:
            disposition = 'attachment; filename="%s"'%filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8'))        
        response.headers['Content-Type'] = self.archiver.getContentType()
        response.headers['Content-Disposition'] = disposition
    
    def stream(self):
        log.debug("ArchiveStreamer: Begin stream %s" % request.url)
        
        flist = self.fileInfoList(self.fileList, self.datasetList, self.urlList)
        flist = self.writeSummary(flist, self.archiver)
        
        for finfo in flist:
            log.debug ('archiving %s' % finfo)
            self.archiver.beginFile(finfo)
            while not self.archiver.EOF():
                yield self.archiver.readBlock(self.block_size)
            self.archiver.endFile()

        yield self.archiver.readEnding()
        self.archiver.close()
        log.debug ("ArchiveStreamer: End stream %s" % request.url)

    # ------------------------------------------------------------------------------------------
    # Utility functions 
    # ------------------------------------------------------------------------------------------
    
    # Creates an export summary file
    def writeSummary(self, flist, archiver):
        if len(flist) == 1:
            return flist

        summary = etree.Element('resource', type='BISQUE Export Log')
        etree.SubElement(summary, 'tag', name='Server', value=config.get('bisque.root'))
        etree.SubElement(summary, 'tag', name='Version', value=__VERSION__)
        etree.SubElement(summary, 'tag', name='Export_DateTime', value=str(datetime.datetime.now()))



        flist.append(dict(  name        =   '_bisque.xml',
                            content     =   etree.tostring(summary),
                            dataset     =   '',
                            extension   =   'URL'))
        
        return flist

    
    # Returns a list of fileInfo objects based on files' URIs
    def fileInfoList(self, fileList, datasetList, urlList):
        
        def fileInfo(dataset, uri, index=0):
            xml     =   data_service.get_resource(uri, view='deep,clean')
            name    =   xml.get('name') 

            # try to figure out a name for the resource
            if not name:
                name = xml.xpath('./tag[@name="filename"]') or xml.xpath('./tag[@name="name"]')
                name = name and name[0].get('value')
            if not name and xml.get('resource_uniq'):
                name = xml.get('resource_uniq')[-4] 
            if not name: 
                name = str(index)
            try:
                path       =   blob_service.localpath(xml.get('resource_uniq')),
            except IllegalOperation: 
                path = None
                
            return  dict(XML        =   xml, 
                         type       =   xml.tag,
                         name       =   name ,
                         uniq       =   xml.get('resource_uniq'),
                         path       =   path,
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
            
            if not header['status'].startswith('200'):
                log.error("URL request returned %s" % header['status'])
                return None
            items = (header.get('content-disposition') or header.get('Content-Disposition') or '').split(';')
            fileName = str(index) + '.'
            
            log.debug('Respose headers: %s'%header)
            log.debug('items: %s'%items)
            
            for item in items:
                pair = item.split('=')
                if (pair[0].lower().strip()=='filename'):
                    fileName = pair[1].strip('"\'')
                if (pair[0].lower().strip()=='filename*'):
                    try:
                        fileName = pair[1].strip('"\'').decode('utf8')
                    except UnicodeDecodeError:                    
                        pass
            
            return  dict(name       =   fileName,
                         content    =   content,
                         dataset    =   '',
                         extension  =   'URL')
                    
        flist = []
        fileHash = {}   # Use a URI hash to look out for file repetitions

        if len(fileList)>0:       # empty fileList
            for index, uri in enumerate(fileList):
                finfo = fileInfo('', uri)
                if fileHash.get(finfo.get('name'))!=None:
                    fileHash[finfo.get('name')] = fileHash.get(finfo.get('name')) + 1
                    namef, ext = os.path.splitext(finfo.get('name'))
                    finfo['name'] = namef + '_' + str(fileHash.get(finfo.get('name'))-1) + ext
                else:
                    fileHash[finfo.get('name')] = 1
                    
                flist.append(finfo)      # blank dataset name for orphan files
                if finfo.get('uniq') is not None:
                    flist.append(xmlInfo(finfo))

        if len(datasetList)>0:     # empty datasetList
            for uri in datasetList:
                fileHash = {}

                dataset = data_service.get_resource(uri, view='full,clean')
                name = dataset.xpath('/dataset/@name')[0]
                members = dataset.xpath('/dataset/value')

                # Insert dataset XML into file list
                flist.append(dict(  name        =   name+'.xml',
                                    content     =   etree.tostring(dataset),
                                    dataset     =   '',
                                    extension   =   'URL'))

                
                for index, member in enumerate(members):
                    finfo = fileInfo(name, member.text, index)

                    if fileHash.get(finfo.get('name'))!=None:
                        fileHash[finfo.get('name')] = fileHash.get(finfo.get('name')) + 1
                        namef, ext = os.path.splitext(finfo.get('name'))
                        finfo['name'] = namef + '_' + str(fileHash.get(finfo.get('name'))-1) + ext
                    else:
                        fileHash[finfo.get('name')] = 1

                    flist.append(finfo)
                    if finfo.get('type') == 'image':
                        flist.append(xmlInfo(finfo))

        if len(urlList)>0:       # empty urlList
            for index, url in enumerate(urlList):
                if fileHash.get(url)!=None:
                    continue
                else:
                    fileHash[url] = 1
                    finfo = urlInfo(url, index)
                    flist.append(finfo)      # blank dataset name for orphan files

        return flist
