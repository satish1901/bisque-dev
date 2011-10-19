import itertools
import logging
import zope

from webob import Request, Response

from paste.httpheaders import REQUEST_METHOD
from paste.httpheaders import CONTENT_TYPE
from paste.httpheaders import USER_AGENT
from paste.httpheaders import WWW_AUTHENTICATE

from zope.interface import implements
from repoze.who.interfaces import IChallenger, IIdentifier, IAuthenticator
from repoze.who.interfaces import IRequestClassifier, IChallengeDecider
from repoze.who.classifiers import default_request_classifier

log = logging.getLogger('bq.auth.challenge')

def bisque_challenge_decider(environ, status, headers):

    #log.info ('challange_decider')
    # we do the default if it's a 401, probably we show a form then
    if status.startswith('401 '):
        request = Request(environ)
        response = Response(environ)

        req_content = request.headers['content-type']
        content_type = response.headers['content-type']

        log.debug ('req %s resp %s' % (req_content, content_type))
        #log.debug ('challenge_decider %s header=%s environ=%s' % (content_type, headers, environ.keys()))

        #req = environ.get('pylons.original_request')
        #if req:
            #log.debug ('challenge_decider request_header=%s' % req.headers)
            #accept = req.headers.get('accept')
            #accept = accept and [ 
            #log.debug ('challenge_decider request accept=%s' % accept)
            #if accept and 'text/xml' in accept: # or 'application/xml' in accept:
            #    return False

        if 'text/xml' in content_type or 'application/xml' in content_type:
            return False

        return True
    elif environ.has_key('repoze.whoplugins.openid.openid'):
        # in case IIdentification found an openid it should be in the environ
        # and we do the challenge
        return True
    elif environ.has_key('repoze.who.plugins.cas'):
        # in case IIdentification found an cas it should be in the environ
        # and we do the challenge
        return True
    return False
    
zope.interface.directlyProvides(bisque_challenge_decider, IChallengeDecider)


def bisque_request_classifier(environ):
    content_type = CONTENT_TYPE(environ)
    if content_type in ('text/xml', 'application/xml'):
        environ['CLIENT_APP'] = 'clientapp'
    else:
        environ['CLIENT_APP'] = default_request_classifier(environ)
    return environ['CLIENT_APP']
zope.interface.directlyProvides(bisque_request_classifier, IRequestClassifier)
