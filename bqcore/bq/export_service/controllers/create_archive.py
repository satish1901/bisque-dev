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

"""

__author__    = "Santhoshkumar Sunderrajan"

import sys
import os
import logging
import traceback
import datetime
import time
import re
import threading
import shutil
import tarfile
import zipfile

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from urllib import quote
from lxml import etree
from time import strftime

from file_from_generator import FileFromGenerator

###############################################################################
# Tar handling ?
###############################################################################

class CreateArchive():
    def __init__(self,tarName, userpass= None):
        curDir=os.curdir
        downDir=curDir+'/downloads'
        self.path=downDir+'/'+tarName+'.tar'
        self.z=tarfile.open(self.path,'w')
        self.z.posix=True
        self.tell_pos=0
        self.userpass = userpass

    #creating tar file with generators
    def createTarFile(self,document):
        """This method creates a tar file on the fly.
           There is a hack while using z.fileobj.flush() or z.fileobj.seek().
           Warning: Change in tarfile.py might cause some problem.
        """
        curDir=os.curdir
        downDir=curDir+'/downloads'
        fp=open(self.path,'r')
        response=etree.Element('resource')
        metaXml=response
        for elt in document.getiterator():
            if elt.tag == 'image':
                src=str(elt.get('src'))
                uri=str(elt.get('uri'))
                imageName=self.nameImage(src)
                metaXml=self.loadImageXml(metaXml,imageName,uri)
                info=tarfile.TarInfo(name=imageName)
                info.external_attr = 0777 << 16L
                info.size=int(self.getImageSizeFromInfo(src))
                info.mtime=time.time()
                self.tell_pos=self.z.fileobj.tell()
                added=False
                while not added:
                    try:
                        lock=threading.Lock()
                        lock.acquire()
                        self.z=self.addTarMember(self.z,src,info)
                        added = True
                    except IOError:
                        log.debug('MAKING DELETE IMAGE REQUEST FOR REFETCH')
                        http_client.request(url=src,method="DELETE")
                        self.z=self.deleteTarMember(self.z,self.tell_pos)
                        continue
                    finally:
                        lock.release()
                while(1):
                    bytes=fp.read(NO_BYTES)
                    if not bytes:
                        break
                    yield bytes
        info=tarfile.TarInfo(name='metadata.xml')
        info.external_attr = 0777 << 16L
        info.mtime=time.time()
        docResp=etree.tostring(metaXml,pretty_print=True)
        info.size=len(docResp)
        xmlF=StringIO(docResp)
        self.z.addfile(tarinfo=info, fileobj=xmlF)
        self.z.fileobj.flush()
        xmlF.close()
        self.z.close()
        while(1):
            bytes=fp.read(NO_BYTES)
            if not bytes:
                break
            yield bytes
        fp.close()
        log.debug("******************************Tarring completed******************************")

    def addTarMember(self,z,src,info):
        header,responseImg = http_client.request(url=src,genUse=True)
        z.addfile(tarinfo=info,fileobj=FileFromGenerator(responseImg.genobj))
        z.fileobj.flush()
        return z

    def deleteTarMember(self,z,pos):
        z.fileobj.seek(pos)
        return z

    def loadImageXml(self,metaXml,imageName,uri):
        try:
            xmlData=data_service.load(uri+'?view=deep')
            doc=etree.fromstring(xmlData)
            metaXml=self.scrubTags(doc,imageName,metaXml)
        except:
            log.exception ("Couldn't fetch tags for %s" % uri)
        return metaXml

    #name the image based on the imgsrv name and query
    def nameImage(self,src):
        imgSrcID=src.rsplit ('/',1)[1]
        xmlStr=image_service.info (src)
        xmlDoc=etree.fromstring(xmlStr)
        formatList=xmlDoc.xpath('//tag[@name="format"]')
        format=formatList[0]
        imgFormat=format.attrib['value']
        fNameList=xmlDoc.xpath('//tag[@name="filename"]')
        fName=fNameList[0]
        imgName=fName.attrib['value']
        imageName=imgSrcID+'_'+imgName#+'.'+imgFormat
        log.debug('naming image:'+imageName)
        return imageName

    #scrubbing the tags
    def scrubTags(self,doc,imageName,metaXml):
        log.debug("Scrubbing XML")
        attr_action={'uri':None,'owner_id':None,'ts':None,'perm':None,'src':'YES'}
        #keyList=attr_action.keys()
        childNodes=doc.getchildren()
        child_len=len(childNodes)
        for x in range(child_len):
            element=childNodes[x]
            for elt in element.getiterator():
                keyList=elt.attrib.keys()
                for x in keyList:
                    if attr_action.has_key(x):
                        keyVal=attr_action[x]
                        if keyVal is None:
                            del elt.attrib[x]
                        if keyVal is not None:
                            elt.set(x,imageName)
            metaXml.append(element)
        return metaXml

    def getImageSizeFromInfo(self,src):
        log.debug("URI::::::::::::::::::::::::::::::"+src)
        try:
            xmlStr=image_service.info (src)
            xmlDoc=etree.fromstring(xmlStr)
        except:
             header,responseXml = http_client.xmlrequest(url=src+'?info', userpass=self.userpass)
             xmlResp=str(responseXml)
             log.debug("Response XML:"+str(xmlResp))
             xmlDoc=etree.fromstring(str(xmlResp))
             #xmlDoc=data_service.load(src+'?info')
        eltList=xmlDoc.xpath('//tag[@name="filesize"]')
        log.debug(etree.tostring(eltList[0]))
        elt=eltList[0];
        return elt.attrib['value']

