
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
   RESTful access to DoughDB resources

"""
import re
import logging
import string
import textwrap
import posixpath
import random

from sqlalchemy.orm import Query, aliased

from pylons.controllers.util import abort
from paste.deploy.converters import asbool

import tg
from tg import config, url
from tg import controllers, redirect, expose, response, request
from tg import require
from lxml import etree

from bq.util.hash import is_uniq_code
from bq.core import identity
from bq.core.model import metadata, DBSession
from bq.core.identity import get_user_id, is_admin, get_user
from bq.core.model import User
from bq import data_service
from bq.data_service.model  import Taggable, TaggableAcl, BQUser
from bq.client_service.controllers import notify_service
from bq.exceptions import IllegalOperation

from .resource import Resource
from .resource_query import RESOURCE_READ, RESOURCE_EDIT
from .resource_query import resource_load,  resource_permission

from .formats import find_formatter

log = logging.getLogger("bq.data_service.resource_auth")

INVITE_MSG = """
You've been invited by $owner_name <$owner_email> to view an image at
$image_url

A login has been created for you at $root.  Please login
using $name as your login ID and $password as your password.
"""

SHARE_MSG = """
You've been invited by $owner_name <$owner_email> to view an image at $image_url
"""

REMOVE_MSG = """
Access to $image_url has been removed by $owner_name <$owner_email>.
"""


# Dictionary of resource type: callable handler for special share processing
#
SHARE_HANDLERS = {}
def append_share_handler(resource_type, handler):
    """Add  share handler

    @param resource_type : a string resource type e.g. mex, dataset
    @param hander: a callable (resource_uniq, user_uniq, auth, action)
    """
    SHARE_HANDLERS[resource_type] = handler


def force_dbload(item):
    if item and isinstance(item, Query):
        item = item.first()
    return item


def check_access(query, action=RESOURCE_READ):
    if action == RESOURCE_EDIT and not identity.not_anonymous():
        log.debug ("EDIT denied because annonymous")
        abort(401)
    if query is None:
        return None
    if  isinstance(query, Query):
        query = resource_permission(query, action=action)
    else:
        #   Previously loaded resource .. recreate query but with
        #   permission check
        #query = resource_load (self.resource_type, query.id)
        query = resource_load ((query.xmltag, query.__class__), query.id)
        query = resource_permission (query, action=action)

    resource = force_dbload(query)
    if resource is None:
        log.info ("Permission check failure %s" % query)
        if identity.not_anonymous():
            abort(403)
        else:
            abort(401)
    #log.debug ("PERMISSION: user %s : %s" % (user_id, resource))
    return resource


def _aclelem(resource, user, acl=None):
    " Return an etree element <auth > record "
    return  etree.Element ('auth',
                           action = (acl and acl.action) or 'read',
                           user   = "%s/data_service/user/%s" % (request.application_url, user.resource_uniq),
#                           user   =  user.resource_uniq,
                           email  =user.value)


class ResourceAuth(Resource):
    """Handle resource authorization records

    Listing :
    GET /data_service/<uniq>/auth/

    Create:
    POST /data_service/<uniq>/auth/[?notify=false]
    <auth email="ab@com" permission="edit" /> -->
             <auth user="<user uniq>" email="ab@com" permission="edit" />
    <auth user=="<user uniq>" permission="edit" /> -->
             <auth user="<user uniq>" email="ab@com" permission="edit" />


    POST /data_service/<uniq>/auth/[?notify=false]
    <auth email="ab@com" permission="edit" />

    Delete:
    DELETE /data_service/<uniq>/auth/<user uniq>

    Modify::
    POST /data_service/<uniq>/auth/<user uniq>[?notify=false]
    <auth user="<user uniq> email="ab@com" permission="edit" />

    """

    def __init__(self, baseuri):
        self.baseuri = baseuri

    def load(self, token, **kw):
        """ Return a db records for resource, user, and acl
        @param token: A user uniq
        @return A triple (resource, user, acl) or None,None,None if not unable
        """
        log.debug ("Load %s" % token)
        # Can we read the ACLs at all?
        resource = check_access(request.bisque.parent, RESOURCE_READ)
        # token should be a resource_uniq of user .. so join Taggable(user) and  TaggableAcl
        if resource is  None:
            return (None, None,None)
        acl, user = DBSession.query (TaggableAcl, Taggable).filter (TaggableAcl.taggable_id == resource.id,
                                                                    TaggableAcl.user_id == Taggable.id,
                                                                    Taggable.resource_uniq == token).first()
        return resource, user, acl

    def create(self, **kw):
        return int

    def dir(self, **kw):
        'Read the list of authorization records associated with the parent resource'
        #baseuri = request.url
        format = kw.pop('format', None)
        view = kw.pop('view', None)
        resource = check_access(request.bisque.parent, RESOURCE_READ)
        log.info ("AUTH %s  %s" , resource, request.environ)
        response = etree.Element('resource', uri=request.url)
        for auth, user in DBSession.query(TaggableAcl, Taggable)\
                                          .filter(TaggableAcl.taggable_id == resource.id)\
                                          .filter(TaggableAcl.user_id == Taggable.id).all():


            log.debug ("Found %s with user %s", auth, user)
            response.append (_aclelem (resource, user, auth))
        if is_admin() : #and resource.owner_id != current_user.id:
            current_user = get_user()
            admin_auth = _aclelem (resource, current_user)
            admin_auth.set ('action', 'edit')
            response.append (admin_auth)

        formatter, content_type  = find_formatter (format)
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)
    @expose()
    def get(self, useracl , **kw):
        """GET /ds/images/1 : fetch the resource
        """
        resource, user, acl = useracl
        if acl:
            aclelem = _aclelem (resource, user, acl)
            formatter, content_type  = find_formatter ('xml')
            tg.response.headers['Content-Type'] = content_type
            return formatter(aclelem)

    #############
    # Modifies
    def replace_all(self, resource, xml, notify=False, **kw):
        log.info("REPLACE_ALL %s %s", request.url, xml )
        response = etree.Element('resource', uri=request.url)
        resource = check_access(resource, RESOURCE_EDIT)
        log.debug ("REPLACE_ALL resource %s", resource)
        if resource is not None:
            DBSession.autoflush = False
            newacls = []
            auth_list=etree.XML(xml)
            # Update or add any that are listed in xml
            oldauths = DBSession.query (TaggableAcl).filter_by (taggable_id = resource.id).all()
            for newauth in auth_list:
                log.debug ("checking %s", newauth)
                newacls.append(resource_acl(resource, newauth, notify= asbool(notify)))
                log.debug ("Adding auth record %s", etree.tostring(newacls[-1]))
            # Remove any current acls not list in newacls
            authed_users = [ posixpath.basename (x.get ('user')) for x in newacls ]
            for auth in oldauths:
                #log.debug ("Checking user %s in %s" , auth.user.resource_uniq , authed_users)
                # Carefull here: allowed_user is a list of uniq code while auth.user is db object
                if auth.user.resource_uniq not in authed_users:
                    log.debug ("removing %s", auth)
                    delauth = _aclelem (resource, auth.user, auth)
                    resource_acl (resource, delauth, user=auth.user, acl = auth, action="delete")
                    #DBSession.delete (auth)

        formatter, content_type  = find_formatter ('xml')
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)


        return self.new (None, xml, **kw)
    def modify(self, useracl, xml, notify=False, **kw):
        resource, user, acl  = useracl
        response = etree.Element('resource', uri=request.url)
        resource = check_access(resource, RESOURCE_EDIT)
        if resource is not None:
            DBSession.autoflush = False
            newauth=etree.XML(xml)
            acl = resource_acl (resource, newauth, user, acl, notify=asbool(notify))
            response.append (acl)
        formatter, content_type  = find_formatter ('xml')
        tg.response.headers['Content-Type'] = content_type
        return formatter(response)

     #def append(self, resource, xml, **kw):
     #   '''POST /ds/images/1/  : append the document to the resource'''

    #@identity.require(identity.not_anonymous())
    def delete(self, useracl, **kw):
        resource, user, acl = useracl
        resource = check_access(resource, RESOURCE_EDIT)
        #if resource is not None:
        #    DBSession.query(TaggableAcl).join (Taggable).filter (Taggable.resource_uniq == uniq).delete()
        if resource is not None and acl is not None:
            delauth = _aclelem (resource, user, acl)
            resource_acl (resource, delauth, user, acl, action="delete")

    # <auth action="read" email="kkvilekval+12@gmail.com" user="http://loup.ece.ucsb.edu:8888/data_service/00-B4AJtjWbBbuiiQSZH9hTPY"/>
    def new(self, factory,  xml, notify=True, **kw):
        'Create/Modify resource auth records'
        response = etree.Element('resource', uri=request.url)
        resource = check_access(request.bisque.parent, RESOURCE_EDIT)
        if resource is not None:
            log.debug ("AUTH %s with %s" % (resource, xml))
            DBSession.autoflush = False
            newauth=etree.XML(xml)
            acl = resource_acl (resource,  newauth,  notify=asbool(notify))
            response.append (acl)
        formatter, content_type  = find_formatter ('xml')
        tg.response.headers['Content-Type'] = content_type
        #transaction.commit()
        return formatter(response)

    @expose(content_type='text/xml') #, format='xml')
    #@identity.require(identity.not_anonymous())
    def append(self, useracl, xml, notify=True, **kw):
        '''POST /ds/images/1/  : append the document to the resource
        Append value of the resource based on the args
        '''
        resource, user, acl = useracl
        response = etree.Element('resource', uri=request.url)
        if acl:
            DBSession.autoflush = False
            newauth=etree.XML(xml)
            acl = resource_acl (resource, newauth, user, acl, notify=asbool(notify))
        formatter, content_type  = find_formatter ('xml')
        tg.response.headers['Content-Type'] = content_type
        #transaction.commit()
        return formatter(response)


def resource_acls(resources, newauth, user=None, acl=None, notify=False, invalidate=True, action='append'):
    """ Update the list of resources with a new

    """
    results = []
    for resource in resources:
        uniq = posixpath.basename (resource)
        r = DBSession.query(Taggable).filter_by(resource_uniq=uniq).first()
        if r is None:
            log.warn ("uniq %s was not a shareable resource", r)
            continue
        results.append (resource_acl(r, newauth, user, acl, notify, invalidate, action))
    return results


def resource_acl (resource,  newauth, user=None, acl=None, notify=False, invalidate=True, action='append'):
    """Create or modify resource acls

    @param resource:  resource (Taggable)
    @param newauth :  an etree of the acl record or None if deleting
    @param user    :  the user (Taggable) of the acl  or None (will be determined from newauth)
    @param acl     :  the acl (TaggableAcl) or None (will be found or created)
    @param notify  :  send an email on state change (boolean)
    @param invalidate: Invalidate caches (boolean)
    @parama delete : Append/modify or Delete record (boolean)

    @return an etree acl record
    """
    user, passwd = match_user(user =  user,
                              user_uniq = newauth.get ('user'),
                              email     = newauth.get ('email'))
    if acl is None:
        acl = DBSession.query(TaggableAcl).filter_by(taggable_id = resource.id, user_id = user.id).first()
        if acl is None:  # Check if newauth is not None or delete is true???
            acl = TaggableAcl()
            acl.taggable_id = resource.id
            acl.user_id = user.id
            acl.action = "read"
            DBSession.add (acl)

    if action =='delete':
        log.debug ("Removing %s from %s  for %s", newauth.get ('action', RESOURCE_READ), resource.resource_uniq, user.resource_uniq)
        if acl in DBSession.new: # http://stackoverflow.com/questions/8306506/deleting-an-object-from-an-sqlalchemy-session-before-its-been-persisted
            DBSession.expunge(acl)
        else:
            DBSession.delete (acl)
    else:
        log.debug ("Changing share on %s for %s action=%s", resource.resource_uniq, user.resource_uniq,  newauth.get ('action', RESOURCE_READ))
        acl.action = newauth.get ('action', RESOURCE_READ)
    # Special actions on sharing  specific resource types
    handler = SHARE_HANDLERS.get(resource.resource_type)
    if handler:
        log.info ("Special share handling with %s", handler)
        handler(resource.resource_uniq, user.resource_uniq, newauth, action)

    # Notify changes if needed
    if notify:
        notify_user (action, resource, user, passwd)

    if invalidate:
        Resource.hier_cache.invalidate_resource (None, user = user.id)

    # Return the new/updated auth element
    return _aclelem (resource, user, acl)


def notify_user(action, resource, user, passwd):
    """
    """
    if action == 'append':
        msg = INVITE_MSG if passwd is not None else SHARE_MSG
    elif action == 'delete':
        msg = REMOVE_MSG
    else:
        log.error ("Unkown action code %s.. not sending", action)
        return

    # Not really owner, just the person sharing
    owner = get_user()
    params = dict (
        owner_name = owner.name,
        owner_email = owner.value,
        name = user.name,
        email = user.value,
        image_url   = '%s/client_service/view?resource=/%s' % (request.application_url, resource.uri),
        root =  request.application_url,
        password = passwd,
    )
    invite = string.Template(msg).safe_substitute(params)
    log.info ("SENDING %s", invite)
    notify_service.send_mail (params['owner_email'],
                              params['email'],
                              "Invitation to view",
                              invite)


def match_user (user=None, user_uniq=None, email=None ):
    """Match a user by user url or email creating a new one if needed.

    @return: tuple (new user, passwd if created otherwise None)
    """
    if user is  None:
        if user_uniq:
            # may be a user url or  simply a uniq code
            user_uniq = posixpath.basename (user_uniq)
            user = DBSession.query(BQUser).filter_by (resource_uniq = user_uniq).first()
        if  user is None and email:
            user = DBSession.query(BQUser).filter_by(resource_value=unicode(email)).first()
    # did we find a user?
    if  user is not None:
        return (user, None)

    if email is None:
        raise IllegalOperation("Cannot determing user to share with")

    log.debug ('AUTH: no user, sending invite %s',  email)
    return invited_user (email)


def invited_user (email):
    # Validate email with https://github.com/JoshData/python-email-validator  ?
    # Setup a temporary user so that we can add the ACL
    # Also setup the pre-registration info they can
    name = email.split('@',1)[0]
    count = 1
    check_name = name
    while True:
        user = DBSession.query(BQUser).filter_by(resource_name=check_name).first()
        if user is None:
            name = check_name
            break
        check_name = name + str(count)
        count += 1

    password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    log.debug('AUTH: tg_user name=%s email=%s display=%s' ,  name, email, email)
    tg_user = User(user_name=name, password=password, email_address=email, display_name=email)
    DBSession.add(tg_user)
    DBSession.flush()
    log.debug ("AUTH: tg_user = %s" % tg_user)

    # we should have created the BQUser by now.
    user = DBSession.query(BQUser).filter_by(resource_name = name).first()
    return (user, password)


def resource_auth (resource, action=RESOURCE_READ, newauth=None, notify=True, invalidate=True):
    "DEPRECATED user resource_acl"
    return resource_acl(resource, newauth, notify=notify,invalidate=invalidate)



def mex_acl_handler (resource_uniq, user_uniq, newauth, action):
    """Special handling for mexes

    Share A mexes input and outputs
    """
    mex = data_service.resource_load (uniq=resource_uniq,view='deep')

    # extract urls from mex inputs and outputs
    points_from_list = [ x.rsplit('/',1)[1] for x in mex.xpath('./tag[@name="inputs"]/tag/@value')
                         if x.startswith("http") ]
    points_to_list = [ x.rsplit('/',1)[1] for x in mex.xpath('./tag[@name="outputs"]/tag/@value')
                       if x.startswith("http") ]
    mex_resources  = [ x for x in points_from_list + points_to_list if is_uniq_code(x) ]
    log.debug ("Discovered incoming %s outgoing %s = %s", points_from_list, points_to_list, mex_resources)

    resource_acls(mex_resources, newauth, action=action)




append_share_handler('mex', mex_acl_handler)