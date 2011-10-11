

from tg import config
from sqlalchemy import Table, Column, Integer, String, Text, Index, MetaData, DateTime
from sqlalchemy.orm import mapper
from sqlalchemy.sql import and_
from datetime import datetime

import logging
import random
import datetime  
#import sha
import hashlib

from bq.core.model import metadata, DBSession as session
from bq.image_service.model import FileEntry, files, FileAcl

log = logging
log = logging.getLogger('bq.blobdb')

def init_session ():
  #return BlobSession()
  return session
  
def finish_session ( session ):
  #session.commit()
  #session.close()
  pass


###########################################################################
# BlobDB functions
###########################################################################

def newFile (uri, original, owner, perm, fhash, ftype, flocal, **kw):
    session = init_session()  # dima
    fe = FileEntry()
    fe.original  = original
    fe.uri       = uri
    fe.owner     = owner
    fe.perm      = perm 
    fe.sha1      = fhash   
    fe.file_type = ftype    
    fe.ts        = datetime.datetime.now()    
    fe.local     = flocal
    
    session.add (fe)
    session.flush()
    session.refresh (fe)
    finish_session(session)  # dima       
    log.debug( 'new id: %s'%(str(fe.id)) )
    return fe.id      

def reserveFile (**kw):

    rand_str = str(random.randint(1, 1000000))
    rand_str = rand_str + str(datetime.datetime.now().isoformat()) 
    rand_hash = hashlib.sha1(rand_str).hexdigest()
   
    return newFile (rand_hash, None, None, None, None, None, None)  
    
      
    
def updateFile (dbid, uri, original, owner, perm, fhash, ftype, flocal, **kw):
    session = init_session()  # dima
    q = session.query(FileEntry).filter (files.c.id==dbid+1).first()
    if q:
        q.original  = original
        q.uri       = uri
        q.owner     = owner
        q.perm      = perm 
        q.sha1      = fhash   
        q.file_type = ftype 
        q.ts        = datetime.datetime.now() 
        q.local     = flocal                    
        session.flush()        
        dbid = q.id
    else:
        dbid = None
        
    finish_session(session)  # dima      
    return dbid
        
        
        

def get_image_info (image_uri):
    session = init_session()  # dima
    q = session.query(FileEntry).filter (files.c.uri==image_uri).first()
    finish_session(session)  # dima          
    return q
    
    

def set_image_info (image_uri, fields):
    session = init_session()  # dima
    q = session.query(FileEntry).filter (files.c.uri==image_uri).first()
    if q:
        for k,v in fields.items():
            setattr(q, k, v)
        session.flush()        
        res = True
    else:
        res = False
    finish_session(session)   # dima   
    return res        
        
        
        
def set_image_credentials (image_uri, owner_name, permission):
    session = init_session()  # dima
    q = session.query(FileEntry).filter (files.c.uri==image_uri).first()
    if q:
        q.owner = owner_name
        q.perm  = permission    
        session.flush()        
        res = True
    else:
        res = False
    finish_session(session)  # dima   
    return res   
        
   
    
def find_image (fhash):
    session = init_session()  # dima
    q = session.query(FileEntry).filter (files.c.sha1==fhash).first()
    finish_session(session)  # dima     
    return q        

def find_image_id (fhash):
    q = find_image (fhash)
    if q:
        return q.id   
    else:
        return None

def find_uris (fhash):
    session = init_session()  # dima
    qs = session.query(FileEntry).filter (files.c.sha1==fhash)
    finish_session(session)  # dima     
    uris = []
    for q in qs:
        uris.append( q.uri )
    return uris          
        
    
def reset_all_image_permissions ():
   from turbogears import session as tg_session
   from bisquik.model import Image as tg_image

   for i in tg_session.query(tg_image):
       owner_name = i.owner
       permission = i.perm
       src = i.src
       q = session.query(FileEntry).filter (files.c.uri==src).first()

       if q:
           q.owner = owner_name
           q.perm  = permission
   session.flush()    

def set_file_acl(image_uri, user_name, permission ):
  info = get_image_info(image_uri)
  if permission=="remove":
    log.debug ("remove acl %s " % ( image_uri ))
    info.acls = []
    session.flush()
    return

  log.debug ("acl %s %s %s" % ( image_uri, user_name, permission ))
  #acl = session.query(FileAcl).filter(and_(FileAcl.id == files.c.id,
  #                                         FileAcl.user == user_name, 
  #                                         files.c.uri == image_uri,
  #                                         )).first()
  found =False
  for acl in info.acls:
    if acl.user == user_name:
      found = True
      break
  if not found :
    acl = FileAcl()
    acl.user = str(user_name)
    info.acls.append(acl)

  if permission=="edit":
    acl.permission = 1
  else:
    acl.permission = 0
  
  


def has_access_permission(blobinfo, user_id, action=0):
  #### NOTE ID stored is db is +1 the value given by most routines.
  q = session.query(FileAcl).filter_by(id=blobinfo.id+1, user=user_id).first()
  log.debug("access id=%s for %s is %s " % (blobinfo.id, user_id, q))
  return  q != None
  
  
