import logging
from repoze.who.interfaces import IIdentifier
from zope.interface import implements

from bq.core.model import DBSession
from bq.data_service.model import ModuleExecution

log = logging.getLogger("bq.mex_auth")

class MexAuthenticatePlugin(object):

    implements(IIdentifier) 
    
    def identify(self, environ):
        """Lookup the owner """
        mexid = environ.get('HTTP_MEX', None)
        log.info ("MexAuthenticate %s" % mexid)
        if mexid :
            return { 'Mex' : mexid }
        return None
    def remember(self, environ, identity):
        pass
    def forget(self, environ, identity):
        pass
    def authenticate(self, environ, identity):
        try:
            log.debug("MexAuthenticate:auth %s" % (identity))
            mexid = identity['Mex']
        except KeyError:
            return None
        mex = DBSession.query(ModuleExecution).get (mexid)
        #if  mex.closed():
        #    log.warn ('attempt with  closed mex %s' % mexid)
        #    return None
        owner = mex.owner.tguser
        log.info ("MEX_IDENTITY %s->%s" % (mexid, owner.user_name))
        return owner.user_name
            
    #def challenge(self, environ, status, app_headers, forget_headers):
    #    pass


def make_plugin():
    return MexAuthenticatePlugin()
