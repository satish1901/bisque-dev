# -*- coding: utf-8 -*-
"""WSGI middleware initialization for the bqcore application."""
import os
import sys
import logging
import pkg_resources
#from webtest import TestApp

from paste.httpexceptions import HTTPNotFound
#from paste.cascade import Cascade
from paste.fileapp import FileApp
from paste.urlparser import StaticURLParser
from paste.httpheaders import ETAG
from paste.registry import RegistryManager
from paste.deploy.converters import asbool

#from repoze.who.config import make_middleware_with_config
from repoze.who.plugins.testutil import make_middleware_with_config

from bq.config.app_cfg import base_config
from bq.config.environment import load_environment
from bq.core.controllers import root
from bq.util.paths import site_cfg_path
from bq.util.proxy import Proxy
from tg.configuration import config
from .direct_cascade import DirectCascade


__all__ = ['make_app', 'bisque_app']

log = logging.getLogger("bq.config.middleware")


public_file_filter = None
bisque_app = None

def add_profiler(app):
    if config.get('bisque.profiler_enable', None) == 'true': #inialize profiler app
        from bq.util.LinesmanProfiler import BQProfilingMiddleware
        app = BQProfilingMiddleware(app, config.get('sqlalchemy.url', None), config.get('bisque.profiler_path', '__profiler__'))
        log.info("HOOKING profiler app")
    return app #pass through

base_config.register_hook('before_config', add_profiler)

def save_bisque_app(app):
    global bisque_app
    bisque_app = app # RegistryManager(app, streaming = True)
    log.info ("HOOKING App %s", app)
    return app

base_config.register_hook('before_config', save_bisque_app)

# Use base_config to setup the necessary PasteDeploy application factory.
# make_base_app will wrap the TG2 app with all the middleware it needs.
make_base_app = base_config.setup_tg_wsgi_app(load_environment)


class BQStaticURLParser (object):

    def __init__(self):
        self.files = {}

    def add_path(self, top, local, prefix=None):
        """add a set of files to static file server

        @param top: a portion of the filepath to be removed from the web path
        @param local: the  directory path to be served
        @param prefix:
        """
        log.info('static path %s -> %s' % (local, top))
        for root, dirs, files in os.walk(local):
            for f in files:
                pathname = os.path.join(root,f)
                partpath = pathname[len(top):]
                if prefix:
                    #print "PREFIX: ", prefix
                    partpath  = os.path.join(prefix, partpath[1:])

                partpath = partpath.replace('\\', '/')
                if partpath in self.files:
                    log.error("static files : %s will overwrite previous %s "
                              % (pathname, self.files[partpath]))
                    continue
                #log.debug(  "ADDING %s -> %s " % (partpath, pathname) )
                self.files[partpath] = (pathname, None)


    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        #log.debug ('static search for %s' % path_info)
        if path_info in self.files:
            path, app = self.files.get(path_info)
            if not app:
                app = FileApp (path).cache_control (max_age=60*60*24*7*6) #6 weeks
                self.files[path_info] = (path, app)
            log.info ( "STATIC REQ %s" %  path_info)
            if_none_match = environ.get('HTTP_IF_NONE_MATCH')
            if if_none_match:
                mytime = os.stat(path).st_mtime
                if str(mytime) == if_none_match:
                    headers = []
                    ETAG.update(headers, mytime)
                    start_response('304 Not Modified', headers)
                    return [''] # empty body
        else:
            app = HTTPNotFound(comment=path_info)
        return app(environ, start_response)


        #return StaticURLParser.__call__(self, environ, start_response)


class LogWSGIErrors(object):
    def __init__(self, app, logger, level):
        self.app = app
        self.logger = logger
        self.level = level

    def __call__(self, environ, start_response):
        environ['wsgi.errors' ] = self
        return self.app(environ, start_response)

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

class ProxyApp(object):
    def __init__(self, app):
        self.oldapp = app

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith('/proxy/'):
            log.debug('ProxyApp activated')
            command = environ['PATH_INFO'].split('/', 3)
            #log.debug('ProxyApp command: %s', command)
            address = 'http://%s'%command[2]
            path = '/%s'%command[3]
            environ['PATH_INFO'] = path
            proxy = Proxy(address)
            return proxy(environ, start_response)
        return self.oldapp(environ, start_response)


def make_app(global_conf, full_stack=True, **app_conf):
    """
    Set bqcore up with the settings found in the PasteDeploy configuration
    file used.

    :param global_conf: The global settings for bqcore (those
        defined under the ``[DEFAULT]`` section).
    :type global_conf: dict
    :param full_stack: Should the whole TG2 stack be set up?
    :type full_stack: str or bool
    :return: The bqcore application with all the relevant middleware
        loaded.

    This is the PasteDeploy factory for the bqcore application.

    ``app_conf`` contains all the application-specific settings (those defined
    under ``[app:main]``.


    """
    site_cfg = site_cfg_path()
    logging.config.fileConfig(site_cfg)

    global public_file_filter
    global bisque_app

    app = make_base_app(global_conf, full_stack=True, **app_conf)

    #from repoze.profile.profiler import AccumulatingProfileMiddleware

    # Wrap your base TurboGears 2 application with custom middleware here
    #app = AccumulatingProfileMiddleware(
    #    app,
    #    log_filename='/tmp/proj.log',
    #    cachegrind_filename='/tmp/cachegrind.out.bar',
    #    discard_first_request=True,
    #    flush_at_shutdown=True,
    #    path='/__profile__'
    #    )

    if 'who.config_file' in app_conf and asbool(app_conf.get('bisque.has_database')):
        app = make_middleware_with_config(
            app, global_conf,
            app_conf['who.config_file'],
            app_conf['who.log_stream'],
            app_conf['who.log_level'],
            skip_authentication=app_conf.get('skip_authentication', False),
            )
    else:
        log.info ("MEX auth only")
        # Add mex only authentication
        from repoze.who.middleware import PluggableAuthenticationMiddleware
        from repoze.who.plugins.basicauth import BasicAuthPlugin
        from bq.core.lib.mex_auth import make_plugin
        from repoze.who.classifiers import default_request_classifier
        from repoze.who.classifiers import default_challenge_decider
        basicauth = BasicAuthPlugin('repoze.who')
        mexauth   = make_plugin ()

        _LEVELS = {'debug': logging.DEBUG,
                   'info': logging.INFO,
                   'warning': logging.WARNING,
                   'error': logging.ERROR,
                   }
        identifiers = [('mexauth', mexauth)]
        authenticators = [('mexauth', mexauth)]
        challengers = []
        mdproviders = []
        aa = app_conf['who.log_stream'],
        app = PluggableAuthenticationMiddleware(app,
                                                identifiers,
                                                authenticators,
                                                challengers,
                                                mdproviders,
                                                default_request_classifier,
                                                default_challenge_decider,
                                                log_stream = sys.stdout,
                                                log_level = _LEVELS[app_conf['who.log_level']],
                                                )

    # Wrap your base TurboGears 2 application with custom middleware here
    from tg import config

    # used by engine to add module specific static files
    public_file_filter = static_app = BQStaticURLParser()
    app = DirectCascade([static_app, app])
    # Add services static files
    if asbool(config.get ('bisque.static_files', True)):
        log.info( "LOADING STATICS")
        ###staticfilters = []
        for x in pkg_resources.iter_entry_points ("bisque.services"):
            try:
                log.info ('found static service: ' + str(x))
                service = x.load()
                if not hasattr(service, 'get_static_dirs'):
                    continue
                staticdirs  = service.get_static_dirs()
                for d,r in staticdirs:
                    log.debug( "adding static: %s %s" % ( d,r ))
                    static_app.add_path(d,r)
            except Exception:
                log.exception ("Couldn't load bisque service %s" % x)
                continue
            #    static_app = BQStaticURLParser(d)
            #    staticfilters.append (static_app)
        #cascade = staticfilters + [app]
        #print ("CASCADE", cascade)
        log.info( "END STATICS: discovered %s static files " % len(static_app.files.keys()))
    else:
        log.info( "NO STATICS")

    app = ProxyApp(app)
    bisque_app = app


    # Call the loader in the root controller
    log.info ("wsgi - Application : complete")
    root.startup()
    log.info ("Root-Controller: startup complete")

    app = LogWSGIErrors(app, logging.getLogger('bq.middleware'), logging.ERROR)



    return app



class AddValue(object):
    def __init__(self, app, key, value):
        self.app = app
        self.key = key
        self.value = value

    def __call__(self, environ, start_response):
        environ = dict(environ)
        environ[self.key] = self.value
        return self.app(environ, start_response)

def add_global(global_conf, **app_conf):
    def filter(app):
        return AddValue(app, 'global_app', app)
            #app_conf.get('key', 'default'),
            #app_conf.get('value', 'defaultvalue'))
    return filter
