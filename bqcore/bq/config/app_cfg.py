# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in bqcore.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""
import os
import tg
import logging

from paste.deploy.converters import asbool
from pylons.middleware import StatusCodeRedirect
from pylons.util import call_wsgi_application

from tg.configuration import AppConfig, config
from tg.util import  Bunch
from tg.error import ErrorHandler
#import tgscheduler

import bq
from bq.core import model
from bq.core.lib import app_globals, helpers
from bq.util.etreerender import render_etree
from direct_cascade import DirectCascade
from paste.urlparser import StaticURLParser

log = logging.getLogger("bq.config")

class BisqueErrorFilter(object):

    def __init__(self, app, codes = []):
        self.app = app
        self.codes = tuple ([ str(x) for x in codes ] )

    def __call__(self, environ, start_response):
        # Check the request to determine if we need
        # to respond with an error message or just the code.

        status, headers, app_iter, exc_info = call_wsgi_application(
            self.app, environ, catch_exc_info=True)
        #log.debug ("ENV=%s" % environ)
        if status[:3] in self.codes and environ.has_key('HTTP_USER_AGENT') and \
           environ['HTTP_USER_AGENT'].startswith('Python'):
            environ['pylons.status_code_redirect'] = True
            log.info ('ERROR: disabled status_code_redirect')
        start_response(status, headers, exc_info)
        return app_iter

class BisqueAppConfig(AppConfig):
    def add_error_middleware(self, global_conf, app):
        """Add middleware which handles errors and exceptions."""
        app = ErrorHandler(app, global_conf, **config['pylons.errorware'])

        # Display error documents for self.handle_status_codes status codes (and
        # 500 when debug is disabled)

        if asbool(config['debug']):
            app = StatusCodeRedirect(app, self.handle_status_codes)
        else:
            app = StatusCodeRedirect(app, self.handle_status_codes + [500])
        app = BisqueErrorFilter (app, [401, 500])
        return app

    def setup_sqlalchemy(self):
        from tg import config
        sqlalchemy_url = config.get ('sqlalchemy.url')
        if not sqlalchemy_url.startswith('sqlite://'):
            return super(BisqueAppConfig, self).setup_sqlalchemy()
        from sqlalchemy.pool import NullPool
        from sqlalchemy import engine_from_config
        engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
        config['pylons.app_globals'].sa_engine = engine
        # Pass the engine to initmodel, to be able to introspect tables
        self.package.model.init_model(engine)

    def after_init_config(self):
        "after config"
        config['pylons.response_options']['headers'].pop('Cache-Control', None)
        config['pylons.response_options']['headers'].pop('Pragma', None)
        print "DATA", config.get('use_sqlalchemy'), config.get('bisque.use_database')
    
    #kage - patch to use direct cascade
    def add_static_file_middleware(self, app):
        static_app = StaticURLParser(config['pylons.paths']['static_files'])
        app = DirectCascade([static_app, app])
        return app

base_config = BisqueAppConfig()



#base_config = AppConfig()
#### Probably won't work for egg
#### Couldn't use pkg_resources ('bq') as it was picking up plugins dir
root=os.path.abspath(__file__ + "/../../core/")
base_config.paths = Bunch(root=root,
                          controllers=os.path.join(root, 'controllers'),
                          static_files=os.path.join(root, 'public'),
                          templates=[os.path.join(root, 'templates')])


#base_config.call_on_startup = [ tgscheduler.start_scheduler ] 
base_config.renderers = []
base_config.package = bq.core

#Enable json in expose
base_config.renderers.append('json')
#Set the default renderer
base_config.default_renderer = 'genshi'
base_config.renderers.append('genshi')
base_config.render_functions.etree = render_etree


# if you want raw speed and have installed chameleon.genshi
# you should try to use this renderer instead.
# warning: for the moment chameleon does not handle i18n translations
#base_config.renderers.append('chameleon_genshi')

#  add a set of variable to the template 
base_config.variable_provider = helpers.add_global_tmpl_vars


#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = bq.core.model
base_config.DBSession = bq.core.model.DBSession

# from repoze.who.plugins import basicauth 
# from bq.core.lib.mex_auth import MexAuthenticatePlugin
# # Configure the authentication backend
# # Undocumented TG2.1 way of adding identifiers
# # http://docs.repoze.org/who/2.0/configuration.html#module-repoze.who.middleware
# # http://turbogears.org/2.1/docs/main/Config/Authorization.html
# base_config.sa_auth.identifiers = [
#     ('mexuath',  MexAuthenticatePlugin() ),
#     ('basicauth', basicauth.make_plugin() )
#     ] 

# try:
#      #from repoze.who.plugins.ldap import LDAPAuthenticatorPlugin, LDAPAttributesPlugin
#     from bq.core.lib.auth import LDAPAuthenticatorPluginExt, LDAPAttributesPluginExt
#     ldap_host='ldap://directory.ucsb.edu'
#     ldap_basedn ='o=ucsb'
    
#     base_config.sa_auth.authenticators = [
#         ('mexuath',  MexAuthenticatePlugin() ),
#         #('ldap', LDAPAuthenticatorPlugin(ldap_host, ldap_basedn)),
#         ('ldap', LDAPAuthenticatorPluginExt(ldap_host, ldap_basedn)),
#         ] 

#     base_config.sa_auth.mdproviders = [ 
#         #('ldap_attributes', LDAPAttributesPlugin (ldap_host, ['cn', 'sn', 'email']))
#         #('ldap_attributes', LDAPAttributesPluginExt (ldap_host, None))
#         ]
# except ImportError, e:
#     pass


# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP 
base_config.sa_auth.cookie_secret = "images" 
#base_config.auth_backend = 'sqlalchemy'
base_config.sa_auth.dbsession = model.DBSession
# what is the class you want to use to search for users in the database
base_config.sa_auth.user_class = model.User
# what is the class you want to use to search for groups in the database
base_config.sa_auth.group_class = model.Group
# what is the class you want to use to search for permissions in the database
base_config.sa_auth.permission_class = model.Permission

# override this if you would like to provide a different who plugin for
# managing login and logout of your application
#base_config.sa_auth.form_plugin = None

# override this if you are using a different charset for the login form
#base_config.sa_auth.charset = 'utf-8'

# You may optionally define a page where you want users to be redirected to
# on login:
#base_config.sa_auth.post_login_url = '/auth_service/post_login'

# You may optionally define a page where you want users to be redirected to
# on logout:
#base_config.sa_auth.post_logout_url = '/auth_service/post_logout'
#base_config.sa_auth.login_url = "/auth_service/login"


