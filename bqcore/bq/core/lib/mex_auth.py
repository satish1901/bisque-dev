import logging
from paste.httpheaders import AUTHORIZATION
from repoze.who.interfaces import IIdentifier
from zope.interface import implements

from bq.core.model import DBSession
from bq.data_service.model import ModuleExecution

log = logging.getLogger("bq.mex_auth")

class MexAuthenticatePlugin(object):

    implements(IIdentifier) 
    
    def identify(self, environ):
        """Lookup the owner """
        # OLD Way using custom header 
        mexid = environ.get('HTTP_MEX', None)
        #log.info ("MexAuthenticate %s" % mexid)
        if mexid :
            return { 'bisque.mex_id' : mexid }

        # New way using standard Authencation header
        authorization = AUTHORIZATION(environ)
        try:
            authmeth, auth = authorization.split(' ', 1)
        except ValueError: # not enough values to unpack
            return None
        if authmeth.lower() == 'mex':
            return { 'bisque.mex_id' : auth }

        return None
    def remember(self, environ, identity):
        pass
    def forget(self, environ, identity):
        pass
    def authenticate(self, environ, identity):
        try:
            mexid = identity['bisque.mex_id']
        except KeyError:
            return None

        log.debug("MexAuthenticate:auth %s" % (identity))
        mex = DBSession.query(ModuleExecution).get (mexid)

        # NOTE: Commented out during system debugging
        # 
        #if  mex.closed():
        #    log.warn ('attempt with  closed mex %s' % mexid)
        #    return None
        if mex:
            identity['bisque.mex'] = mex
            owner = mex.owner.tguser
            log.info ("MEX_IDENTITY %s->%s" % (mexid, owner.user_name))
            return owner.user_name
        log.warn("Mex authentication failed due to invalid mex %s" % mexid)
        return None
            
    #def challenge(self, environ, status, app_headers, forget_headers):
    #    pass


def make_plugin():
    return MexAuthenticatePlugin()
