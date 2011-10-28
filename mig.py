from sqlalchemy import *
from sqlalchemy.sql import *

import transaction 
import os

from paste.deploy import appconfig
from bq.config.environment import load_environment
from bq.core import model
from bq.blob_service.controllers.blobsrv import make_uniq_hash




def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)



load_config('config/site.cfg')

from bq.data_service.model import *
from bq.image_service.model import *


def move_files_to_resources():
    for fi in DBSession.query(FileEntry):
        image = DBSession.query (Image).filter_by(src = fi.uri).first()
        if image is None:
            print "processing file", fi.local
            resource = DBSession.query(Taggable).filter_by(resource_uniq = fi.sha1).first()
            if resource is None:
                resource = Taggable(resource_type='file')
                DBSession.add(resource)
        else:
            resource = image
            print "processing image", fi.local
            image.src = "/image_service/images/%s" % fi.sha1

        resource.resource_name = fi.original
        resource.resource_uniq = fi.sha1
        resource.resource_val  = fi.local
        resource.resource_type = resource.table
    transaction.commit()



def apply_to_all(resource, fn, *args, **kw):
    fn (resource, *args, **kw)
    for tag in resource.tags:
        apply_to_all(tag, fn, *args, **kw)
    for gob in resource.gobjects:
        apply_to_all(gob, fn, *args, **kw)

def set_document(resource, document):
    resource.document = document

def build_document_pointers():
    for resource in  DBSession.query(Taggable).filter_by(parent_id = None):
        # Given a top level resource create a document 
        document = Document()
        document.uniq = resource.uniq
        document.owner

        apply_to_all(resource, set_document, document=document)

def move_all_to_resource():
    types_ [ Tag, GObject, Dataset, Module, ModuleExecution, Service, Templates ] 

    def map_(r, ty):
        r.resource_type = ty.xmltag
        r.uname = getattr(r, 'name', None)
        r.utype = getattr(r, 'type', None):
        r.resource_parent_id = getattr(r, 'parent_id', None)

    for ty_ in type_:
        for r in DBSession.query (type_):
            map_(r, ty_)

    # Special type here
    for r in DBSession.query(BQUser):
        map_(r, BQUser)
        t  = BQTag()
        t.uname = 'display_name'
        t.resource_val = r.display_name
        r.tags.append(t)
        t  = BQTag()
        t.uname = 'email_address'
        t.resource_val = r.email_address
        r.tags.append(t)

    for r in DBSession.query(Module):
        r.resource_val = r.codeurl
        
    for r in DBSession.query(ModuleExecution):
        r.resource_val = r.status
        
    for r in DBSession.query(Service):
        r.resource_type = 'app'
        r.resource_val = r.uri
        
        







if __name__ == '__main__':

    move_files_to_resources()
