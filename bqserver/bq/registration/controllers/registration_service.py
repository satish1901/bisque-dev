
import pkg_resources
import logging
import os


from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates

from bq.core.service import ServiceController, service_registry
from bq.core.model import DBSession
from bq.data_service.model import BQUser
#from controllers import registration_hooks

log = logging.getLogger("bq.registration")

#def user_hook(action, user):
#    if action=='new_user':
#        bquser = BQUser.new_user (user.email_address, user.password)
#
#registration_hooks.append (user_hook)



def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)

    RegistrationController.service_type = "registration"
    controller =   RegistrationController()
    controller.uri = uri
    controller.url = uri

    log.debug ("initialize " + controller.uri)

    return controller


#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("bqserver")
#    package_path = pkg_resources.resource_filename(package,'bqcore')
#    return [(package_path, os.path.join(package_path,  'registration', 'public'))]

def get_model():
    from bq.registration import model
    return model

from tgext.registration2.controllers import UserRegistration as RegistrationController
RegistrationController.service_type = "registration"

__controller__ = RegistrationController
#__staticdir__ = get_static_dirs()
__model__ = get_model()
