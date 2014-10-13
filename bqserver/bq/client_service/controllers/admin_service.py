###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
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

"""
import os
import operator
import logging
import transaction

from datetime import datetime
from lxml import etree
from tg import expose, controllers, flash, url, response
from repoze.what.predicates import is_user, in_group, Any
from repoze.what.predicates import not_anonymous
from sqlalchemy import func

import bq
from bq.core.service import ServiceController
from bq.core import identity
from bq.util.paths import data_path
from bq.core.model import   User,Group #, Visit
from bq.core.model import DBSession
from bq.data_service.model import  BQUser, Image, TaggableAcl

#from bq.image_service.model import  FileAcl
from tg import redirect
from tg import request

log = logging.getLogger('bq.admin')

from bq.core import model
from bq.core.model import DBSession

#from tgext.admin import AdminController
#class BisqueAdminController(AdminController):
#    'admin controller'
#    allow_only = Any (in_group("admin"), in_group('admins'))


class AdminController(ServiceController):
    """The admin controller is a central point for
    adminstrative tasks such as monitoring, data, user management, etc.
    """
    service_type = "admin"


    allow_only = Any (in_group("admin"), in_group('admins'))
    #allow_only = is_user('admin')

    #admin = BisqueAdminController([User, Group], DBSession)

    @expose('bq.client_service.templates.admin.index')
    def index(self, **kw):
        log.info ("ADMIN")
        query = kw.pop('query', '')
        wpublic = kw.pop('wpublic', not bq.core.identity.not_anonymous())
        return dict(query = query, wpublic = wpublic, analysis = None, search = None)

    @expose ('bq.client_service.templates.admin.users')
    def users(self, order = "id", **kw):
        ordering = { 'id' : BQUser.id,
                     'user_name' : BQUser.resource_name,
#                     'display_name' : BQUser.display_name,
                     'email_address' : BQUser.resource_value,
                     'images': BQUser.id
                     }
        order_with = ordering.get (order, BQUser.id)
        counter = DBSession.query (Image.owner_id, func.count('*').label('image_count')).group_by(Image.owner_id).subquery()

        user_images = DBSession.query(BQUser, counter.c.image_count).outerjoin(counter, BQUser.id == counter.c.owner_id).order_by(order_with)
        results  = []
        for u,c in user_images:
            results.append ( [u, c] )

        if order == "images":
            results.sort (key = operator.itemgetter (1) )
            results.reverse()

        query = kw.pop('query', '')
        wpublic = kw.pop('wpublic', not bq.core.identity.not_anonymous())
        return dict(users = results, query = query, wpublic = wpublic, analysis = None, search = None)

    @expose ('bq.client_service.templates.admin.edituser')
    def edituser(self, username=None, **kw):
        options = {}

        #Grab passed args
        if options.has_key('page'):
            options['page'] = int(kw.pop('page'))
        else:
            options['page'] = 1

        if not options['page'] > 0:
            options['page'] = 1
        options['perpage'] = 20

        #Grab the user passed from url
        user = BQUser.query.filter(BQUser.resource_name == username).first()

        #If we got a handle on the user
        if user:
            #Find all his images
            results = DBSession.query(Image).filter(Image.owner_id == user.id).all()
        else:
            flash('No user was found with name of ' + username + '. Perhaps something odd happened?')
            redirect(url('/admin/error'))
        options['totalimages'] = len(results)

        #Calculate paging ranges
        myrange = range(0, len(results), options['perpage'])

        #Bounds checking
        if options['page'] <= len(myrange):
            x = myrange[options['page']-1]
            images = results[x:x+options['perpage']]
        else:
            images = []

        return dict(user=user, images=images,  options = options)

    @expose ()
    def deleteimage(self, imageid=None, **kw):
        log.debug("image: " + str(imageid) )
        image = DBSession.query(Image).filter(Image.id == imageid).first()
        DBSession.delete(image)
        transaction.commit()
        redirect(request.headers.get("Referer", "/"))

    @expose ('bq.client_service.templates.admin.confirmdeleteuser')
    def confirmdeleteuser(self, username=None, **kw):
        flash("Caution. You are deleting " + (username or '') + " from the system. All of their images will also be deleted. Are you sure you want to continue?")
        return dict(username = username, query=None, wpublic=None, search=None, analysis=None)

    @expose ()
    def deleteuser(self, username=None,  **kw):
        #DBSession.autoflush = False


        # Remove the user from the system for most purposes, but
        # leave the id for statistics purposes.
        user = DBSession.query(User).filter (User.user_name == username).first()
        log.debug ("Renaming internal user %s" % user)
        if user:
            DBSession.delete(user)
            #user.display_name = ("(R)" + user.display_name)[:255]
            #user.user_name = ("(R)" + user.user_name)[:255]
            #user.email_address = ("(R)" + user.email_address)[:16]

        user = DBSession.query(BQUser).filter(BQUser.resource_name == username).first()
        log.debug("ADMIN: Deleting user: " + str(user) )
        # delete the access permission
        for p in DBSession.query(TaggableAcl).filter_by(user_id=user.id):
            log.debug ("KILL ACL %s" % p)
            DBSession.delete(p)
        #DBSession.flush()

        self.deleteimages(username, will_redirect=False)
        DBSession.delete(user)
        transaction.commit()
        redirect('/admin/users')

    @expose ('bq.client_service.templates.admin.confirmdeleteimages')
    def confirmdeleteimages(self, username=None, **kw):
        flash("Caution. This will delete all images of " + username + " from the system. Are you sure you want to continue?")
        return dict(username = username, query=None, wpublic=None, search=None, analysis=None)

    @expose ()
    def deleteimages(self, username=None,  will_redirect=True, **kw):
        user = DBSession.query(BQUser).filter(BQUser.resource_name == username).first()
        log.debug("ADMIN: Deleting all images of: " + str(user) )
        images = DBSession.query(Image).filter( Image.owner_id == user.id).all()
        for i in images:
            log.debug("ADMIN: Deleting image: " + str(i) )
            DBSession.delete(i)
        if will_redirect:
            transaction.commit()
            redirect('/admin/users')
        return dict()

    @expose ()
    def adduser(self, **kw):
        user_name = unicode( kw['user_name'] )
        password = unicode( kw['user_password'] )
        email_address = unicode( kw['email'] )
        display_name = unicode( kw['display_name'] )


        log.debug("ADMIN: Adding user: " + str(user_name) )
        user = User(user_name=user_name, password=password, email_address=email_address, display_name=display_name)
        DBSession.add(user)
        transaction.commit()
        redirect('/admin/users')

    @expose ()
    def updateuser(self, **kw):
        user_name = unicode( kw.get('user_name', '') )
        password = unicode( kw.get('user_password', '') )
        email_address = unicode( kw.get('email', '') )
        display_name = unicode( kw.get('display_name', '') )

        log.debug("ADMIN: Updating user: " + str(user_name) )

        ####NOTE###
        # Changes to user are propagated so there is no need to update bquser seperately.

        #Grab the user passed from url
        #user = BQUser.query.filter(BQUser.name == user_name).first()

        #If we haven't got a handle on the user
        #if not user:
        #    log.debug('No user was found with name of ' + user_name + '. Perhaps something odd happened?')
        #    redirect(url('/admin/'))
        #user.value = email_address
        #user.tag('display_name') = display_name
        #user.display_name = display_name

        tg_user = DBSession.query(User).filter (User.user_name == user_name).first()
        if not tg_user:
            log.debug('No user was found with name of ' + user_name + '. Please check core tables?')
            redirect(url('/admin/'))
        tg_user.email_address = email_address
        tg_user.password = password
        #tg_user.display_name = display_name
        log.debug("ADMIN: Updated user: " + str(user_name) )
        # Needed for SQLITE? No idea why..
        transaction.commit()
        redirect( '/admin/edituser?username='+ str(user_name) )

    @expose()
    def loginasuser(self, user):
        log.debug ('forcing login as user')

        response.headers = request.environ['repoze.who.plugins']['friendlyform'].remember(request.environ,
                                                                                          {'repoze.who.userid':user})
        redirect("/")

    @expose('bq.client_service.templates.admin.error')
    def default (*l, **kw):
        log.debug ("got " + str(l) + str(kw))
        return dict(query=None, wpublic=None, search=None, analysis=None)


    @expose('bq.client_service.templates.admin.index')
    def clearcache(self):
        log.info("CLEARING CACHE")
        def clearfiles (folder):
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception, e:
                    log.exception('while removing %s' % file_path)

        server_cache = data_path('server_cache')
        clearfiles(server_cache)
        log.info("CLEARED CACHE")
        return dict()



def initialize(url):
    return AdminController(url)


__controller__ = AdminController
__staticdir__ = None
__model__ = None
