# -*- coding: utf-8 -*-
"""Setup the bqcore application"""

import logging
from tg import config
from bq.core import model

import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup bq here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError

    try:
        ######
        # 
        from  bq.data_service.model import Taggable, Tag


        from bq.data_service.model import UniqueName
        
        system = model.DBSession.query(Taggable).filter_by (tb_id = UniqueName('system').id).first()
        if system is None:
            system = Taggable(resource_type = 'system')
            version = Tag ()
            version.name ='version'
            version.value  = '0.5'
            prefs = Tag()
            prefs.name = 'Preferences'
            system.tags.append(version)
            system.tags.append(prefs)
            model.DBSession.add(system)
            transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your system object, it may have already been added:'
        #import traceback
        #print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'


    try:
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
        model.DBSession.flush()

        

        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        #import traceback
        #print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
