from sqlalchemy import *
from sqlalchemy.sql import *

import transaction 
import os
import logging

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

        resource.resource_name   = fi.original
        resource.resource_uniq   = fi.sha1
        resource.resource_value  = fi.local
        resource.resource_type   = resource.table
    transaction.commit()




def move_all_to_resource():
    types_ =  [ Tag, GObject, Dataset, Module, ModuleExecution, Service, Template, Image, BQUser ] 
    #user_types = [ (nm, ty) for nm, ty in [ dbtype_from_name(str(y)) for y in all_resources() ] if ty == Taggable ]

    #DBSession.autoflush = False
    def map_(r, ty):
        r.resource_type = ty.xmltag
        if hasattr(r, 'name'):
            r.resource_name = unicode(getattr(r, 'name'))
        if hasattr(r, 'type_id'):
            r.resource_user_type = unicode(getattr(r, 'type'))
        r.resource_parent_id = getattr(r, 'parent_id', None)

    for ty_ in types_:
        print "processing ", ty_.xmltag
        for r in DBSession.query (ty_):
            map_(r, ty_)

    # Special type here
    print "processing ", BQUser.xmltag
    for r in DBSession.query(BQUser):
        map_(r, BQUser)
        t  = Tag()
        t.mex = r.mex
        t.owner_id = r.owner_id 
        t.resource_name = 'display_name'
        t.resource_value = r.display_name
        #r.children.append(t)
        t  = Tag()
        t.mex = r.mex
        t.owner_id = r.owner_id 
        t.resource_name = 'email_address'
        t.resource_value = r.email_address
        #r.children.append(t)

    print "processing ", Module.xmltag
    for r in DBSession.query(Module):
        r.resource_value = r.codeurl
        r.resource_user_type = r.type
        
    print "processing ", ModuleExecution.xmltag
    for r in DBSession.query(ModuleExecution):
        r.resource_value = r.status
        
    print "processing ", Service.xmltag
    for r in DBSession.query(Service):
        r.resource_user_type = 'app'
        r.resource_value = r.uri

    transaction.commit()


def move_values():
    print "processing ", Tag.xmltag
    for r in DBSession.query(Tag):
        if len(r.values) == 1:
            v = r.values[0] 
            if v.valstr is not None:
                r.resource_value = unicode(v.valstr)
            elif v.valnum is not None:
                r.resource_value = v.valnum
                r.resource_user_type = 'numeric'
            elif v.valobj is not None:
                r.resource_value = v.objref.uri
                r.resource_user_type = 'resource'

            #DBSession.delete (r.values[0])

    print "processing ", GObject.xmltag
    for r in DBSession.query(GObject):
        if len(r.vertices) == 1:
            v = r.vertices[0]
            v = "%s,%s,%s,%s,%s" % (v.x or '', v.y or '',v.z or '',v.t or '',v.ch or '')
            r.resource_value = v
            #DBSession.delete (r.vertices[0])

    transaction.commit()
        
        
def apply_to_all(fn, resource, parent, *args, **kw):
    fn (resource, parent, *args, **kw)
    #if parent is None:
    #    print "processin tags"
    for tag in resource.tags:
        apply_to_all(fn, tag, resource, *args, **kw)
    #if parent is None:
    #    print "processin gobs"
    for gob in resource.gobjects:
        apply_to_all(fn, gob, resource,  *args, **kw)

def set_document(resource, parent, document):
    resource.resource_document_id = document.id
    if parent:
        resource.resource_parent_id = parent.id

def build_document_pointers():
    types_ =  [ Image, Dataset, Module, ModuleExecution, Service, Template ] 

    for ty_ in types_:
        print "processing %s" % ty_.xmltag
        for resource in  DBSession.query(ty_):
            print resource.id 
            resource.resource_type = resource.xmltag
            
            # Given a top level resource create a document 
            #document = Document()
            #document.uniq = resource.resource_uniq
            #document.owner_id = resource.owner_id
            #document.perm     =  resource.perm
            apply_to_all(set_document, resource , parent=None, document=resource)

    user_types = [ (nm, ty) for nm, ty in [ dbtype_from_name(str(y)) for y in all_resources() ] if ty == Taggable ]
    for table, ty_ in user_types:
        print "processing %s" % table
        for resource in  DBSession.query(ty_).filter(ty_.tb_id == UniqueName(table).id):
            resource.resource_type = table
            apply_to_all(set_document, resource , parent=None, document=resource)

    transaction.commit()



if __name__ == '__main__':

    try:
        move_files_to_resources()
        move_all_to_resource()
        build_document_pointers()
        move_values()
    except:
        logging.exception("")
