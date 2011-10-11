# -*- mode: python -*-
"""Main server for dataset_service}
"""
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates 
from bq.core.service import ServiceController
from bq.dataset_service import model


log = logging.getLogger("bq.dataset_service")
class dataset_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "dataset_service"

    def __init__(self, server_url):
        super(dataset_serviceController, self).__init__(server_url)
        
    @expose('bq.dataset_service.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from dataset_service'))

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  dataset_serviceController(uri)
    #directory.register_service ('dataset_service', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqcore")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'dataset_service', 'public'))]

def get_model():
    from bq.dataset_service import model
    return model

__controller__ =  dataset_serviceController
