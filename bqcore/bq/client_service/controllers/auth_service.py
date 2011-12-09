###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008                                               ##
##      by the Regents of the University of California                       ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========

DESCRIPTION
===========
  Authorization for web requests

"""
import logging
#import cherrypy
import base64

from datetime import datetime, timedelta
from lxml import etree
import tg
from tg import request, response, session, flash, require
from tg import controllers, expose, redirect, url
from tg import config, validate
from pylons.i18n import _
from repoze.what import predicates

#from turbogears.visit import enable_visit_plugin

from bq.core.service import ServiceController
from bq.core import identity
from bq.core.model import DBSession
from bq.data_service.model import ModuleExecution
from bq import module_service

from bq import data_service
log = logging.getLogger("bq.auth")


class AuthenticationServer(ServiceController):
    service_type = "auth_service"
    

    @expose('bq.client_service.templates.login')
    def login(self, came_from='/'):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    #@expose ()
    #def login_handler(self, **kw):
    #    log.debug ("login_handler %s" % kw)
    #    return self.login(**kw)

#    @expose ()
#    def openid_login_handler(self, **kw):
#        log.debug ("openid_login_handler %s" % kw)
#        #return self.login(**kw)


    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.
        
        """
        log.debug ('POST_LOGIN')
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect(url('/auth_service/login',params=dict(came_from=came_from, __logins=login_counter)))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        self._begin_mex_session()
        timeout = int (config.get ('bisque.visit.timeout', 0))
        if timeout:
            session['expires']  = datetime.now() + timedelta(minutes=timeout)
        session.save()
        redirect(came_from)


    # This function is never called but used as token to recognize the logout
    # @expose ()
    # def logout_handler(self, **kw):
    #     log.debug ("logout %s" % kw)
    #     #session = request.environ['beaker.session']
    #     #session.delete()
    #     try:
    #         self._end_mex_session()
    #         session.delete()
    #     except:
    #         log.exception("logout")

    #     redirect ('/')

    #@expose ()
    #def logout_handler(self, **kw):
    #    log.debug ("logout_handler %s" % kw)


    @expose()
    def post_logout(self, came_from='/'):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        
        """
        #self._end_mex_session()
        #flash(_('We hope to see you soon!'))
        log.debug("post_logout")
        try:
            self._end_mex_session()
            session.delete()
        except:
            log.exception("post_logout")

        redirect(came_from)
    
    @expose(content_type="text/xml")
    def credentials(self, **kw):
        response = etree.Element('resource', type='credentials')
        cred = identity.get_user_pass()
        if cred:
            etree.SubElement(response,'tag', name='user', value=cred[0])
            etree.SubElement(response,'tag', name='pass', value=cred[1])
            etree.SubElement(response,'tag',
                             name="basic-authorization",
                             value=base64.encodestring("%s:%s" % cred))
        #tg.response.content_type = "text/xml"
        return etree.tostring(response)



    @expose(content_type="text/xml")
    def session(self):
        sess = etree.Element ('session', )
        if identity.not_anonymous():
            #vk = tgidentity.current.visit_link.visit_key
            #log.debug ("session_timout for visit %s" % str(vk))
            #visit = Visit.lookup_visit (vk)
            #expire =  (visit.expiry - datetime.now()).seconds
            timeout = int(session.get ('timeout', 20 )) *60
            expires = session.get ('expires', datetime(2100, 1,1))
            
            current_user = identity.get_user()
            if current_user:
                etree.SubElement(sess,'tag',
                                 name='user', value=data_service.uri() + current_user.uri)

            etree.SubElement (sess, 'tag',
                              name='expires',
                              value= str((expires - datetime.now()).seconds))
            etree.SubElement (sess, 'tag',
                              name='timeout',
                              value= str(timeout) )
                             


        return etree.tostring(sess)
            

    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def newmex (self, module_url=None):
        mexurl  = self._begin_mex_session()
        return mexurl
            
    def _begin_mex_session(self):
        """Begin a mex associated with the visit to record changes"""

        #
        #log.debug('begin_session '+ str(tgidentity.current.visit_link ))
        #log.debug ( str(tgidentity.current.visit_link.users))
        mex = module_service.begin_internal_mex()
        mexid  = mex.get('uri').rsplit('/',1)[1]
        session['mex_id']  = mexid
        session['mex_uri'] = mex.get('uri')
        #v = Visit.lookup_visit (tgidentity.current.visit_link.visit_key)
        #v.mexid = mexid
        #session.flush()
        return mex

    def _end_mex_session(self):
        """Close a mex associated with the visit to record changes"""
        try:
            mexuri = session.get('mex_uri')
            if mexuri:
                module_service.end_internal_mex (mexuri)
        except AttributeError:
            pass
        return ""
    


    def _begin_mex_session_old(self):
        """Begin a mex associated with the visit to record changes"""

        #
        #log.debug('begin_session '+ str(identity.current.visit_link ))
        #log.debug ( str(tgidentity.current.visit_link.users))
        #log.debug ( str(tgidentity.current.visit_link.visit))


        mexurl = session.get('mex.url', None)
        if mexurl is None:
            mex = None# module_service.begin_internal_mex(module='session')
            if mex is not None:
                mexurl = mex.get('uri')
                session['mex.url'] = mexurl
                session['mex.id']  = mexurl.split ('/')[-1]
                session.save()
                log.debug ("BEGIN MEX Session %s" % mexurl)
        else:
            log.warn ("ALREADY HAVE mex")

    def _end_mex_session_old(self):
        """Close a mex associated with the visit to record changes"""
        if session.has_key('mex.url'):
            mexurl =  session['mex.url']
            #module_service.end_internal_mex (mexurl)
            log.debug ("ENDED MEX Session %s" % mexurl)
            del session['mex.url'];
            del session['mex.id'];
            session.save();
    


def initialize(url):
    service =  AuthenticationServer(url)
    return service


__controller__ = AuthenticationServer
__staticdir__ = None
__model__ = None
