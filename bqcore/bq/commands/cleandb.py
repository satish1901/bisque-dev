
import os
from tg import config
from sqlalchemy.sql import and_, or_ 
from bq.util.paths import data_path

__all__  = [ "clean_images" ]

def clean_store(local, options):
    from bq.data_service.model import Taggable, Image, DBSession
    top =  local.top[5:]

    localfiles = set()
    for root, dirs, files in local.walk():
        for f in files:
            #if f.endswith('.info'):
            #    continue
            filepath =  os.path.join(root, f)[len(top)+1:]
            localfiles.add(filepath)

    print "file count ", len(localfiles)

    dbfiles = set()
    locs = DBSession.query(Taggable).filter(or_(Taggable.resource_type=='image', 
                                                  Taggable.resource_type=='file'))
    for f in locs:
        if f.resource_value is None or f.resource_value.startswith ('irods')  or f.resource_value.startswith ('s3'):
            continue
        dbfiles.add(f.resource_value)

    print "DB count", len(dbfiles)
    missing = localfiles - dbfiles
    print "deleting %s files" % len(missing)
    if not options.dryrun:
        for f in missing:
            local.delete(f)
    else:
        print "would delete %s" % missing
    

def clean_images(options):
    print "CLEAN"

    from bq.blob_service.controllers.blobsrv import load_stores
    stores = load_stores()
    
    # Collect ALL files in 'imagedir' 
    for name, store in stores.items():
        if store.scheme == 'file':
            clean_store(store, options)


def bozo():

            image = DBSession.query(Taggable).filter(and_(Taggable.resource_value==filepath,
                                                          or_(Taggable.resource_type=='image', 
                                                              Taggable.resource_type=='file'))).first()

            #print filepath, (image.resource_type, 'exists')  if image else 'missing'
            if not image:
                print filepath, " missing"
            


    
        
