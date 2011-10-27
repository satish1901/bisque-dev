from sqlalchemy import *
from sqlalchemy.sql import *

import transaction 
import os

from paste.deploy import appconfig
from bq.config.environment import load_environment
from bq.core import model





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
            resource = DBSession.query(Taggable).filter_by(resource_uniq = f1.sha1).first()
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

if __name__ == '__main__':

    move_files_to_resources()
