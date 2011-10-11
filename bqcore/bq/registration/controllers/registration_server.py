# -*- mode: python -*-
"""Main server for registration}
"""
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates 
from bq.core.service import ServiceController
from bq.registration import model


log = logging.getLogger("bq.registration")
class registrationController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "registration"

    def __init__(self, server_url):
        super(registrationController, self).__init__(server_url)
        
    @expose('bq.registration.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from registration'))

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  registrationController(uri)
    #directory.register_service ('registration', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqcore")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'registration', 'public'))]

def get_model():
    from bq.registration import model
    return model

__controller__ =  registrationController
