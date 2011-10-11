import logging
import transaction
from zope.interface import implements
from repoze.who.interfaces import IAuthenticator, IMetadataProvider

from bq.core import model

log = logging.getLogger('bq.auth.autoreg')

class AutoRegister (object):
    """This plugin attempts to register users that are so far unknown 
    to the system.  During the metadata phase it looks to see if the user
    name is currently known and if  not so will create a local user structure
    """
    implements(IMetadataProvider)

    key_map = {
        # maps identity : sreg keys
        'display_name': 'fullname',
        #'username': 'nickname',
        'email_address': 'email',
    }


    def __init__( self, key_map = {} ):
        """Create autoregister metadata provider to create local users
        structures.

        """
        log.info("autoreg")
        self.mapping = {}
        self.key_map = key_map

    def register_user( self, user_name, values = {} ):
        """Add SReg extension data to our mapping information"""
        current = model.User.by_user_name( user_name )
        if not current:
            log.info("adding user %s" % user_name )
            model.DBSession.add(
                model.User(user_name = user_name, **values)
                )
            transaction.commit()
        else:
            log.info("found existing user: %s" % current)

        return True

    def add_metadata( self, environ, identity ):
        """Add our stored metadata to given identity if available"""
        user = identity.get('repoze.who.userid', None)
        log.debug ("metadata with user: %s" % user) 
        if user:
            log.debug ('identity  = %s' % identity)

        return identity
