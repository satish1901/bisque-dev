# -*- coding: utf-8 -*-
"""Setup the bqcore application"""

import logging
from tg import config, session
from bq.core import model
from paste.registry import Registry
from beaker.session import Session, SessionObject

import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup bq here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    from  bq.data_service.model import Taggable, Tag, BQUser, ModuleExecution

    registry = Registry()
    registry.prepare()
    registry.register(session, SessionObject({}))

    try:
        initial_mex = ModuleExecution()
        initial_mex.mex = initial_mex
        initial_mex.name = "initialization"
        initial_mex.type = "initialization"
        model.DBSession.add(initial_mex)
        session['mex'] = initial_mex

        admin = model.User(
            user_name = u"admin",
            display_name = u'Example manager',
            email_address = u'manager@somedomain.com',
            password = u'admin')
        model.DBSession.add(admin)
        
        for g in [ u'admins', u'managers' ] :
            group = model.Group()
            group.group_name = g
            group.display_name = u'Administrators Group'
            group.users.append(admin)
            model.DBSession.add(group)
            
        permission = model.Permission()
        permission.permission_name = u'root'
        permission.description = u'This permission give an administrative right to the bearer'
        permission.groups.append(group)
        model.DBSession.add(permission)
        #model.DBSession.flush()
        # This commit will setup the BQUser also
        transaction.commit()

    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        #import traceback
        #print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'


    try:
        ######
        # 
        #from bq.data_service.model import UniqueName

        admin = model.DBSession.query(BQUser).filter_by(resource_name = 'admin').first()
        admin.mex = initial_mex
        initial_mex.owner = admin
        session['user'] = admin
        
        system = model.DBSession.query(Taggable).filter_by (resource_type='system').first()
        if system is None:
            system = Taggable(resource_type = 'system')
            version = Tag (parent = system)
            version.name ='version'
            version.value  = '0.5'
            prefs = Tag(parent = system)
            prefs.name = 'Preferences'
            model.DBSession.add(system)
            transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your system object, it may have already been added:'
        #import traceback
        #print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'

        

    # <websetup.bootstrap.after.auth>
