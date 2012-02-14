# -*- mode: python -*-
"""Main server for usage}
"""
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates 
from bq.core.service import ServiceController

from lxml import etree
from datetime import datetime, timedelta

import bq
from bq.client_service.controllers import aggregate_service
from bq import data_service

log = logging.getLogger("bq.usage")
class usageController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "usage"

    def __init__(self, server_url):
        super(usageController, self).__init__(server_url)
        
    @expose('bq.usage.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from usage'))
        
        
    @expose(content_type="text/xml")
    def stats(self, **kw):
        log.info('stats %s'%kw)        
        wpublic = kw.pop('wpublic', not bq.core.identity.current)
        images2d = aggregate_service.count("image", wpublic=wpublic, images2d=True)
        all_count = aggregate_service.count("image", wpublic=wpublic, welcome=True)
        image_count = aggregate_service.count("image", wpublic=wpublic)
        tag_count = aggregate_service.count("tag", wpublic=wpublic, welcome=True )
        
        resource = etree.Element('resource', uri='/usage/stats')
        etree.SubElement(resource, 'tag', name='number_images', value=str(all_count))
        etree.SubElement(resource, 'tag', name='number_images_user', value=str(image_count))
        etree.SubElement(resource, 'tag', name='number_images_planes', value=str(images2d))  
        etree.SubElement(resource, 'tag', name='number_tags', value=str(tag_count))
                              
        return etree.tostring(resource)


    #http://loup.ece.ucsb.edu:9090/data_service/images?ts=%3E2010-06-01T12:00:00&ts=%3C2011-06-01T12:00:00&view=count
    #<resource>
    #<image count="3673"/>
    #</resource>
    def get_counts(self, resource_type, num_days):
        now = datetime.now() 
        counts = []
        days = []
        for i in range(31): 
            d1 = now - timedelta(days=i)
            d2 = now - timedelta(days=i+1)
            ts = ['>%s'%d2.isoformat(), '<%s'%d1.isoformat()]
            days.append(d2.isoformat(' '))
            req = data_service.query(resource_type, view='count', ts=ts, welcome=True)
            log.debug('=============================== %s'%etree.tostring(req))
            c = req.xpath('//%s[@count]'%resource_type)
            if len(c)>0:
                counts.append( c[0].get('count') ) 
            else:           
                counts.append('0') 

        counts.reverse()
        days.reverse()
        return counts, days

    @expose(content_type="text/xml")
    def uploads(self, **kw):
        log.info('uploads %s'%kw)        
        counts, days = self.get_counts('image', 31)
        resource = etree.Element('resource', uri='/usage/uploads')
        etree.SubElement(resource, 'tag', name='counts', value=','.join(counts))
        etree.SubElement(resource, 'tag', name='days', value=','.join(days))        
        return etree.tostring(resource)

    @expose(content_type="text/xml")
    def analysis(self, **kw):
        log.info('uploads %s'%kw)        
        counts, days = self.get_counts('mex', 31)
        resource = etree.Element('resource', uri='/usage/analysis')
        etree.SubElement(resource, 'tag', name='counts', value=','.join(counts))
        etree.SubElement(resource, 'tag', name='days', value=','.join(days))            
        return etree.tostring(resource)




def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.info ("initialize " + uri)
    service =  usageController(uri)
    #directory.register_service ('usage', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'usage', 'public'))]

#def get_model():
#    from bq.usage import model
#    return model

__controller__ =  usageController
