from urllib import quote_plus, urlencode
import httplib2
import logging

from webob import Request, Response
from webob.exc import HTTPFound, HTTPUnauthorized

from zope.interface import implements
from repoze.who.interfaces import IChallenger, IIdentifier, IAuthenticator
from repoze.who.interfaces import IRequestClassifier, IChallengeDecider

log = logging.getLogger('bq.auth.cas')

def make_plugin(cas_base_url, 
                saml_validate = None,
                login_form="/login",
                login_path="/login_handler", 
                logout_path="/logout_handler", 
                post_logout = "/post_logout",
                remember_name="auth_tkt",
                auto_register = None,
                ):
    return CASPlugin (cas_base_url,  saml_validate,
                      login_form, login_path, 
                      logout_path, post_logout, 
                      remember_name, auto_register)


class CASPlugin(object):
    implements(IChallenger, IIdentifier, IAuthenticator)

    def __init__(self, 
                 cas_base_url,
                 saml_validate,
                 login_form,
                 login_path,
                 logout_path,
                 post_logout,
                 rememberer_name, 
                 auto_register):
        if cas_base_url[-1] == '/':
            cas_base_url = cas_base_url[0:-1]
        self.cas_login_url = "%s/login" % cas_base_url
        self.cas_logout_url = "%s/logout" % cas_base_url
        self.cas_validate_url = "%s/validate" % cas_base_url
        self.cas_saml_validate = saml_validate or ("%s/samlValidate" % cas_base_url)
        self.login_form = login_form
        self.logout_path = logout_path
        self.login_path = login_path
        self.post_logout = post_logout
        # rememberer_name is the name of another configured plugin which
        # implements IIdentifier, to handle remember and forget duties
        # (ala a cookie plugin or a session plugin)
        self.rememberer_name = rememberer_name
        self.auto_register = auto_register
        self.http = httplib2.Http(disable_ssl_certificate_validation=True)

    
    # IChallenger
    def challenge(self, environ, status, app_headers, forget_headers):
        #log.debug ('challenge')
        request = Request(environ, charset="utf8")
        service_url = request.url

        login_type = request.params.get ('login_type', '')
        # if environ['PATH_INFO'] == self.logout_path:
        #     # Let's log the user out without challenging.
        #     came_from = environ.get('came_from', '')
        #     if self.post_logout:
        #         # Redirect to a predefined "post logout" URL.
        #         destination = self.post_logout
        #     else:
        #         # Redirect to the referrer URL.
        #         script_name = environ.get('SCRIPT_NAME', '')
        #         destination = came_from or script_name or '/' 
        # else:
        if login_type == 'cas':
            log.debug ('CAS challenge redirect to %s' % self.cas_login_url)
            destination =  "%s?service=%s" % (self.cas_login_url, quote_plus(service_url))
            return HTTPFound(location=destination)
        return None

        # redirect to login_form
        #res = Response()
        #res.status = 302
        #res.location = "%s?came_from=%s" % (self.login_form , request.url)
        #return res

    def _get_rememberer(self, environ):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer

    # IIdentifier
    def remember(self, environ, identity):
        """remember the openid in the session we have anyway"""
        #log.debug("remember")
        rememberer = self._get_rememberer(environ)
        r = rememberer.remember(environ, identity)
        return r

    # IIdentifier
    def forget(self, environ, identity):
        """forget about the authentication again"""
        #log.debug("forget")
        rememberer = self._get_rememberer(environ)
        return rememberer.forget(environ, identity)
    
    # IIdentifier
    def identify(self, environ):
        request = Request(environ)

        # first test for logout as we then don't need the rest
        if request.path == self.logout_path:

            userdata = environ.get('REMOTE_USER_DATA', '')
            cas_ticket = userdata.startswith('cas:') and userdata[4:]
            log.debug ("logout cas ticket %s" % cas_ticket)
            if cas_ticket:
                res = Response()
                # set forget headers
                for a,v in self.forget(environ,{}):
                    res.headers.add(a,v)
                    res.status = 302
                    res.location = "%s?url=%s" % (self.cas_logout_url, self.post_logout)
                    environ['repoze.who.application'] = res
                return {}

        identity = {}

        # first we check we are actually on the URL which is supposed to be the
        # url to return to (login_handler_path in configuration)
        # this URL is used for both: the answer for the login form and
        # when the openid provider redirects the user back.
        if request.path == self.login_path and request.params.get('login_type', None)=='cas':
            ticket = request.params.get('ticket', None)
            log.debug ("login_path ticket=%s" % ticket)
            environ['repoze.who.plugins.cas'] = True
            if ticket is not None:
                identity['userdata'] = "cas:%s" % ticket
                identity['repoze.who.plugins.cas.ticket' ] = ticket
                del environ['repoze.who.plugins.cas']
                return identity
            #identity.update(self._validate(environ, identity))
        return None

    def _validate_simple(self, environ, identity):
        request = Request(environ)

        if identity.has_key('repoze.who.plugins.cas.ticket'):
            service_url = request.url
            validate_url = '%s?service=%s&ticket=%s' % (
                self.cas_validate_url,
                service_url,
                identity['repoze.who.plugins.cas.ticket'])
            headers, response = self.http.request(validate_url)
            if headers.status == 200:
                okayed, username = response.split("\n")[:2]
                log.debug ('validate got %s %s' % (okayed, username))
                if okayed == 'yes':
                    return username
        return None


    def _validate_saml(self, environ, identity):
        from cas_saml import create_soap_saml, parse_soap_saml

        request = Request(environ)
        if identity.has_key('repoze.who.plugins.cas.ticket'):
            service_url = request.url
            ticket = identity['repoze.who.plugins.cas.ticket']
            url = "%s?TARGET=%s" % (self.cas_saml_validate, service_url)
            body = create_soap_saml(ticket)
            headers = { 'content-type': 'text/xml',
                        'accept' : 'text/xml',
                        'connection': 'keep-alive',
                        'cache-control': 'no-cache',
                        'soapaction' :'http://www.oasis-open.org/committees/security'}
            log.debug ("SENDING %s %s %s" % (url, headers, body))
            headers, content = self.http.request(url, method="POST", headers=headers, body=body)
            log.debug ("RECEIVED %s %s" % (headers, content))
            found = parse_soap_saml(content)
            if headers['status'].startswith('200') and found:
                for k,v in found.items():
                    identity['repoze.who.plugins.cas.%s' % k] = v
                return found['user_id']

        return None

    #IAuthenticator
    def authenticate(self, environ, identity):
        ''
        user_id = None
        if self.cas_saml_validate:
            user_id =  self._validate_saml(environ, identity)
            if user_id:
                log.debug ('CAS authenticate : %s' % user_id)
        #else:
        #    return self._validate_simple(environ, identity)

        try:
            if self.auto_register and user_id:
                log.debug ('CAS autoregister')
                user_id = self._auto_register(environ, identity, user_id)
        except:
            log.error ("couldn't authenticate %s"  % user_id)
            return None

        return user_id


    def _auto_register(self, environ, identity, user_id):
        registration = environ['repoze.who.plugins'].get(self.auto_register)
        log.debug('looking for %s found %s ' % (self.auto_register, registration))
        
        if registration:
            user_name = identity["repoze.who.plugins.cas.user_id"]

            if identity.has_key('repoze.who.plugins.cas.firstName'):
                name = identity["repoze.who.plugins.cas.firstName"]

            if identity.has_key('repoze.who.plugins.cas.lastName'):
                name = "%s %s" % (name, identity["repoze.who.plugins.cas.lastName"])

            email = 'unknown@nowhere.org'
            if identity.has_key('repoze.who.plugins.cas.email'):
                email =  identity["repoze.who.plugins.cas.email"]
            return registration.register_user(user_name, values = {
                    'display_name' : name,
                    'email_address' : email,
                    #password =  illegal password so all authentication goes through openid
                    })
        else:
            log.debug('%s not found in %s. Ensure autoreg is enabled' % (self.auto_register, environ['repoze.who.plugins']))
        return user_id


