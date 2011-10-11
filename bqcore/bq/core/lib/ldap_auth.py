import logging

from repoze.who.plugins.ldap import (
    LDAPAttributesPlugin, LDAPAuthenticatorPlugin, LDAPSearchAuthenticatorPlugin, 
)
import ldap

log = logging.getLogger('bq.ldap')


class URISaver(object):
    """ Saves the ldap_connection str given to repoze authn and authz """
    def __init__(self, *args, **kw):
        self.uri = kw['ldap_connection']
        super(URISaver, self).__init__(*args, **kw)

class LDAPAttributesPluginExt(LDAPAttributesPlugin, URISaver):
    """ Gets attributes from LDAP.  Refreshes connection if stale. """

    def add_metadata(self, environ, identity):
        """ Add ldap attributes to the `identity` entry. """
        try:
            userdata = identity.get('userdata', '')
            if 'userdata' in identity:
                log.debug('metadata identity=%s' % userdata)
                r = super(LDAPAttributesPluginExt, self).add_metadata(
                    environ, identity)
                return r
            
        except Exception, e:
            log.warn( "FAILED TO CONNECT TO LDAP 1 : " + str(e))
            log.warn( "Retrying...")
            self.ldap_connection = ldap.initialize(self.uri)
            return super(LDAPAttributesPluginExt, self).add_metadata(
                environ, identity)

class LDAPAuthenticatorPluginExt(LDAPSearchAuthenticatorPlugin, URISaver):
    """ Authenticates against LDAP.

    - Refreshes connection if stale.
    - Denies anonymously-authenticated users

    """

    def __init__(self, auto_register, **kw):
        super(LDAPAuthenticatorPluginExt, self).__init__(**kw)
        self.auto_register = auto_register

    def authenticate(self, environ, identity):
        """ Extending the repoze.who.plugins.ldap plugin to make it much
        more secure. """

        log.debug ("authenticate %s" % identity)
        res = None

        try:
            # This is unbelievable.  Without this, ldap will
            # let you bind anonymously
            if not identity.get('password', None):
                return None
            #try:
            #    dn = self._get_dn(environ, identity)
            #except (KeyError, TypeError, ValueError):
            #    return None

            res = super(LDAPAuthenticatorPluginExt, self).authenticate(
                environ, identity)

            # Sanity check here (for the same reason as the above check)
            #if "dn:%s" % dn != self.ldap_connection.whoami_s():
            #    return None

            log.debug ('authenticate user=%s' % res)
            return res

        except ldap.LDAPError, e:
            log.warn( "FAILED TO CONNECT TO LDAP 2 : " + str(e))
            log.warn( "Retrying...")
            self.ldap_connection = ldap.initialize(self.uri)

        return res
