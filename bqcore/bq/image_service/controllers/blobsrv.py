#import web
import shutil
import logging
import os
from lxml import etree
import fileinput
import StringIO
import blobdb




# ImageServer
#
#
#
#  /datasrv/blob/1

#  /datasrv/image/(\d+)[?format=(jpg,tiff,raw)]
#  htpp://datasrv/image/(\d+)/t/1-10/z/1/
#  /datasrv/thumbnail[/(\d+)]
#  /datasrv/blob/(\d)
#  htpp://datasrv/image/methods
#  http://datasrv/image/(\d+)[?(method)(&method)*]
# 
#     method = thumbnail
#              x=100&y=100
#              equalize
#              dimensions
#              binarize
#              t=1&z=1&c=1&format=jpg

#  /datasev/feature

BLOBCNT=1000
BLOBLOG='bloblog.log'

from XFile import *

log = logging
log = logging.getLogger('bq.blobsrv')

###########################################################################
# Utils
###########################################################################

def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        #print "_mkdir %s" % repr(newdir)
        if tail:
          try:
            os.mkdir(newdir)
          except OSError, e:
            log.error ('MKDIR: '+ str(e))            

###########################################################################
# Hashing Utils
###########################################################################

import sys
import hashlib

def file_hash_SHA1( filename ):
    '''Takes a file path and returns a SHA-1 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.sha1()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()

def file_hash_MD5( filename ):
    '''Takes a file path and returns a MD5 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.md5()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()	  
   



###########################################################################
# BlobServer
###########################################################################

class BlobServer(object):
    '''Manage a set of blob files'''
    
    def __init__(self, top, url, dirmax = BLOBCNT):
        self.top = top
        self.dirmax = dirmax
        self.url = url
        #self.counter_file = top + '/next'
        #if not os.path.exists(self.counter_file):
        #   self.resetFilenames()

    def storeBlob(self, src, name, ownerId = None, permission = None, id = None, **kw):
        """Store the file object in the next blob and return the
        descriptor"""
        if id == None:
            id, filepath = self.nextEmptyBlob()
        else:
            filepath = id2path(id)
            
        log.debug('storeBlob: ' +str(name) +' '+ str(filepath) )               
            
        if not src and name:
            src = open(name,'rb')
        src.seek(0)
            
        trg = open(filepath, 'wb')            
        shutil.copyfileobj(src, trg)
        #trg.flush()
        trg.close()

        fhash = file_hash_SHA1( filepath )
        ftype = None
        flocal = filepath[len(self.top)+1:]

        blobdb.updateFile (dbid=id, uri = self.geturi(id), original = name, owner = ownerId, perm = permission, fhash=fhash, ftype=ftype, flocal=flocal )
        self.loginfo (name, id, **kw)
        return id, filepath

    def id2path (self, id):
        filedir = str(int(id) / self.dirmax)
        return self.top +'/'+ filedir +'/'+ str(id)        

    def getBlobInfo(self, id): 
        fobj = blobdb.get_image_info(self.geturi(id))
        return fobj     

    def setBlobInfo(self, image_uri, **kw): 
        blobdb.set_image_info( image_uri, kw )
        
    def setBlobCredentials(self, image_uri, owner_name, permission ): 
        blobdb.set_image_credentials( image_uri, owner_name, permission )        

    def set_file_acl(self, image_uri, owner_name, permission ): 
        blobdb.set_file_acl( image_uri, owner_name, permission )        

    def getBlobFileName(self, id): 
        fobj = self.getBlobInfo(id)
        fname = str(id)
        if fobj != None and fobj.original != None:
            fname = str( fobj.original )
        log.debug('Blobsrv - original name for id: ' +str(id) +' '+ fname )    
        return fname   

    def getBlobOwner(self, id): 
        fobj = self.getBlobInfo(id)
        fown = None
        if fobj != None and fobj.owner != None:        
            fown = str( fobj.owner )
        log.debug('Blobsrv - original owner for id: ' +str(id) +' '+ fown )    
        return fown       

    def getBlobPerm(self, id): 
        fobj = self.getBlobInfo(id)
        fown = None
        if fobj != None and fobj.perm != None:            
            fown = str( fobj.perm )
        log.debug('Blobsrv - original perm for id: ' +str(id) +' '+ fown )    
        return fown    

    def getBlobHash(self, id): 
        fobj = self.getBlobInfo(id)
        fhash = None
        if fobj != None and fobj.sha1 != None:          
            fhash = fobj.sha1
        if fhash == None:
            fhash = file_hash_SHA1( self.originalFileName(id) )
            fobj.sha1 = fhash
            blobdb.set_image_info (fobj.uri, fobj)
            
        log.debug('Blobsrv - hash for id: ' +str(id) +' '+ str(fhash) )    
        return fhash   
        
    def blobExists(self, fhash):
        return blobdb.find_image_id(fhash)

    def blobsExist(self, fhashes):
        blobsfound = []
        for fhash in fhashes:
           if blobdb.find_image_id(fhash) != None:
               blobsfound.append(fhash)
        return blobsfound

    def blobUris(self, fhash):
        return blobdb.find_uris(fhash)

    def originalFileName(self, id): 
        return self.getBlobFileName(id) 
        
        
    def accessPermission(self, id, userId):
        if id==None: return True
        if not self.fileExists(id):
            return True
        permit_access = False

        binfo = self.getBlobInfo(id)
        log.debug ("Blobinfo %s => %s" % (id, binfo))
        if binfo:
            log.debug( 'user: %s, id: %s, owner: %s, perm: %s'%( userId, id, binfo.owner, binfo.perm ))
            permit_access = ((binfo.perm == None or binfo.perm == 0)
                             or(binfo.owner==None or (binfo.owner==userId or userId==u'admin'))
                             or(userId!=None and blobdb.has_access_permission(binfo, userId)))

        return permit_access

    def changePermission(self, id, userId):
        if id==None: return False
        if not self.fileExists(id): return False
        permit_access = False
        binfo = self.getBlobInfo(id)    
        if binfo:
            log.debug( 'user: %s, id: %s, owner: %s, perm: %s'%( str(userId), str(id), str(binfo.owner), str(binfo.perm) )  )
            if (binfo.owner == None) or (binfo.owner == userId): permit_access = True    
        return permit_access

    def fileExists(self, id):
        if id==None: return False      
        fileName = self.id2path(id)    
        return os.path.exists(fileName)
        
    def geturi(self, id):
        return self.url + '/' + str(id)


    def nextEmptyBlob(self):
        "Return a file object to the next empty blob"
        while 1:
            id = blobdb.reserveFile()            
            
            fn = self.id2path(id)
            _mkdir (os.path.dirname(fn))
            if os.path.exists (fn):
                log.warning('%s already exists' % fn)
            else:
                break
        return id, fn
            


    def loginfo (self, original_name, id, **kw):
        f  = etree.Element('file')
        f.attrib['uri'] = self.geturi(id)
        f.attrib['original'] = original_name
        for k,v in kw.items():
            n = etree.SubElement(f, k)
            n.text = unicode(v).encode('utf-8')
        
        try:
            bloblog = open(BLOBLOG, 'a+')
            etree.ElementTree(f).write(bloblog)
            bloblog.write('\n')
            bloblog.close()
        except IOError, (errno, strerr):
            log.error ("can't append to blob log: %s" % (strerr) )
        except:
            log.error ("Upexpected %s " % ( sys.exc_info()[0]))

    @classmethod
    def retrieve_log (cls):
        #beg_log  = StringIO.StringIO('<log>')
        #end_log  = StringIO.StringIO('</log>')
        #return fileinput.input(files = [beg_log, open(BLOBLOG), end_log])
        return  '<log>' + open(BLOBLOG).read() + '</log>'
    
       



#web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
    #web.run(urls, globals())

    srv = BlobServer()
    srv.resetFilenames()
    for i in range(10):
        p = open ('/etc/passwd')
        srv.addBlob(p)
