###############################################################################
##  Bisque                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011,2012,2013,2014                 ##
##     by the Regents of the University of California                        ##
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
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY         ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE         ##
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR        ##
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR           ##
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,     ##
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,       ##
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR        ##
## PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF    ##
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING      ##
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS        ##
## SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.              ##
##                                                                           ##
## The views and conclusions contained in the software and documentation     ##
## are those of the authors and should not be interpreted as representing    ##
## official policies, either expressed or implied, of <copyright holder>.    ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

"""

import os
import logging
import httplib2
import urlparse
import datetime
from bq.release import __VERSION__

from tg import request, response, config
from lxml import etree
from bq import data_service, blob_service
from .archiver.archiver_factory import ArchiverFactory

log = logging.getLogger("bq.export_service.archive_streamer")

class ArchiveStreamer():

    block_size = 1024 * 64

    def __init__(self, compression):
        self.archiver = ArchiverFactory().getClass(compression)


    def init(self, archiveName='Bisque', fileList=None, datasetList=None, urlList=None, dirList=None, export_meta=True, export_mexs=False):
        self.fileList = fileList or []
        self.datasetList = datasetList or []
        self.urlList = urlList or []
        self.dirList = dirList or []
        self.export_meta = export_meta
        self.export_mexs = export_mexs

        filename = archiveName + self.archiver.getFileExtension()
        try:
            disposition = 'attachment; filename="%s"'%filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8'))
        response.headers['Content-Type'] = self.archiver.getContentType()
        response.headers['Content-Disposition'] = disposition

    def stream(self):
        log.debug("ArchiveStreamer: Begin stream %s" % request.url)

        flist = self.fileInfoList(self.fileList, self.datasetList, self.urlList, self.dirList)
        if self.export_meta is True:
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
        summary = etree.Element('resource', type='bisque_package')
        etree.SubElement(summary, 'tag', name='origin', value=config.get('bisque.root'))
        etree.SubElement(summary, 'tag', name='version', value=__VERSION__)
        etree.SubElement(summary, 'tag', name='datetime', value=str(datetime.datetime.now()))

        index = 0
        for f in flist:
            log.debug('writeSummary: %s', f)
            if f.get('dataset') is None and f.get('path') is None:
                log.debug('writeSummary Adding: %s', f)
                v = etree.SubElement(summary, 'value', index='%s'%index, type='object')
                v.text = f.get('outpath')
                index += 1

        flist.append(dict( name      = '.bisque.xml',
                           content   = etree.tostring(summary),
                           outpath   = '.bisque.xml'))

        return flist


    # Returns a list of fileInfo objects based on files' URIs
    def fileInfoList(self, fileList, datasetList, urlList, dirList):
        log.debug('fileInfoList fileList: %s'%fileList)
        log.debug('fileInfoList datasetList: %s'%datasetList)
        log.debug('fileInfoList urlList: %s'%urlList)
        log.debug('fileInfoList dirList: %s'%dirList)
        flist = []
        fileHash = {}   # Use a URI hash to look out for file repetitions

        def fileInfo(relpath, uri, index=0):
            xml = data_service.get_resource(uri, view='deep,clean')
            if xml is None:
                log.warn ('skipping unreadable uri %s', uri)
                return None

            name = xml.get('name')
            uniq = xml.get('resource_uniq', None)

            # try to figure out a name for the resource
            if not name:
                name = xml.xpath('./tag[@name="filename"]') or xml.xpath('./tag[@name="name"]')
                name = name and name[0].get('value')
            if not name and uniq:
                name = uniq[-4]
            if not name:
                name = str(index)

            path = None
            if uniq is not None:
                del xml.attrib['resource_uniq'] # dima: strip resource_uniq from exported xml
                b = blob_service.localpath(uniq)
                path = b.path
                files = b.files
                if path and not os.path.exists(path):
                    path = None

            # if resource is just an XML doc
            content = None
            if path is None:
                content = etree.tostring(xml)
                name = '%s_%s'%(name, uniq)
                xml = None

            # disambiguate file name if present
            ext = '' if path is not None else '.xml'
            outpath = os.path.join(relpath, '%s%s'%(name, ext)).replace('\\', '/')
            if outpath in fileHash:
                fname, ext = os.path.splitext(name)
                name = '%s%s%s'%(fname, uniq, ext)
                outpath = os.path.join(relpath, '%s%s'%(name, ext)).replace('\\', '/')
            fileHash[outpath] = name

            return dict(
                 xml     = xml,
                 content = content,
                 name    = name,
                 uniq    = uniq,
                 path    = path,
                 relpath = relpath,
                 outpath = outpath,
            )

        def xmlInfo(finfo):
            file = finfo.copy()
            file['outpath'] = '%s.xml'%file['outpath']
            # need to modify the resource value to point to a local file
            #file['xml'].set('value', os.path.basename(file['xml'].get('value', '')))
            file['xml'].set('value', finfo['name'])
            file['content'] = etree.tostring(file['xml'])
            del file['path']
            del file['xml']
            return file

        def urlInfo(url, index=0):
            httpReader = httplib2.Http( disable_ssl_certificate_validation=True)
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

            return  dict(name      = fileName,
                         content   = content,
                         outpath   = fileName)


        # processing a list of resources
        if len(fileList)>0:
            for index, uri in enumerate(fileList):
                finfo = fileInfo('', uri)
                if finfo is None:
                    continue
                flist.append(finfo)
                if self.export_meta is True and finfo.get('xml') is not None:
                    flist.append(xmlInfo(finfo))
                # find all mexs that use this resource explicitly
                # dima: we'll not get any second level mexs
                # mexs that use mexs, will need closure query in the db for that
                if self.export_mexs:
                    mexq = data_service.query('mex', tag_query=finfo['xml'].get('uri'))
                    members = mexq.xpath('//mex')
                    for m in members:
                        uri = m.get('uri')
                        flist.append(fileInfo('', uri))

        # processing a list of datasets
        if len(datasetList)>0:
            for uri in datasetList:
                dataset = data_service.get_resource(uri, view='deep,clean')
                name = dataset.xpath('/dataset/@name')[0]
                members = dataset.xpath('/dataset/value')
                uniq = dataset.get('resource_uniq', '')
                del dataset.attrib['resource_uniq'] # dima: strip resource_uniq from exported xml

                for index, member in enumerate(members):
                    finfo = fileInfo(name, member.text, index)
                    if finfo is None:
                        continue
                    finfo['dataset'] = name
                    flist.append(finfo)

                    # update reference in the dataset xml
                    if self.export_meta is True and finfo.get('xml') is not None:
                        flist.append(xmlInfo(finfo))
                        member.text = '%s.xml'%finfo.get('outpath','')
                    else:
                        member.text = finfo.get('outpath','')

                if self.export_meta:
                    # disambiguate file name if present
                    name = '%s.xml'%name
                    if name in fileHash:
                        fname, ext = os.path.splitext(name)
                        name = '%s%s%s'%(fname, uniq, ext)
                    fileHash[name] = name

                    # Insert dataset XML into file list
                    flist.append(dict( name      = name,
                                       content   = etree.tostring(dataset),
                                       outpath   = name))

        # processing a list of directories
        if len(dirList)>0:
            for uri in dirList:
                # read dir from blob storage, dima: need to access blob storage
                folder = data_service.get_resource(uri, view='deep')
                members = folder.xpath('//link')

                for index, member in enumerate(members):
                    # dima: need to compute proper URI
                    uniq = member.get('value', None)
                    uri = '/data_service/%s'%uniq # compute URI from uniq, dima: does not work today: 403 forbidden

                    # compute path for each link by traversing up the tree
                    folder = [] # relative path to the resource from currently selected dir with no trailing slash
                    parent = member
                    while parent is not None:
                        parent = parent.xpath('..')
                        parent = parent[0] if len(parent)>0 else None
                        if parent is not None:
                            folder.append(parent.get('name', None))
                    folder.reverse()
                    finfo = fileInfo('/'.join(folder), uri, index)
                    if finfo is None:
                        continue
                    flist.append(finfo)
                    if self.export_meta is True and finfo.get('xml') is not None:
                        flist.append(xmlInfo(finfo))

        # processing a list of URLs
        if len(urlList)>0:
            for index, url in enumerate(urlList):
                if fileHash.get(url)!=None:
                    continue
                else:
                    fileHash[url] = 1
                    finfo = urlInfo(url, index)
                    flist.append(finfo)

        return flist
