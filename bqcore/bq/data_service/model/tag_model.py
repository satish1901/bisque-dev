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

 Main model for bisquik database

DESCRIPTION
===========

 Usage::
   image = Image()
   image.addTag ('name', 'image 1')
   for tg in image.tags:
       print tg.name, tg.value


"""
import urlparse
import sqlalchemy
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, String, DateTime, Unicode, Float, Boolean
from sqlalchemy import Text, UnicodeText
from sqlalchemy.orm import relation, class_mapper, object_mapper, validates, backref, synonym
from sqlalchemy import exceptions
from sqlalchemy.sql import and_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from tg import config, session

from bq.core.model import mapper
from bq.core.model import DBSession as current_session
from bq.core.model import DBSession

from datetime import datetime

#import turbogears
#from turbogears.database import metadata, session
#from turbogears.util import request_available
from bq.core import identity
from bq.core.model import DeclarativeBase, metadata
from bq.core.model import User, Group
from bq.core.permission import PUBLIC, PRIVATE, perm2code, perm2str
from bq.util.memoize import memoized

#from bq.MS import module_service
#session.mex = None


import logging
log = logging.getLogger("bq.data_service")

global admin_user, init_module, init_mex
admin_user =  init_module = init_mex = None


def create_tables1(bind):
    metadata.bind = bind
    """Create the appropriate database tables."""
    log.info( "Creating tag_model tables" )
    engine = config['pylons.app_globals'].sa_engine
    metadata.create_all (bind=engine, checkfirst = True)


taggable = Table('taggable', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('mex_id', Integer, ForeignKey('taggable.id')),
                 Column('ts', DateTime(timezone=False)),
                 Column('perm', Integer), #ForeignKey('permission_sets.set_id')
                 Column('owner_id', Integer, ForeignKey('taggable.id')),
                 Column('resource_uniq', String(40)),
                 Column('resource_index', Integer),
                 Column('resource_hidden', Boolean),
                 Column('resource_type', Unicode(255) ),  # will be same as tb_id UniqueName
                 Column('resource_name', Unicode (1023), ),
                 Column('resource_user_type', Unicode(1023), ),
                 Column('resource_value',  UnicodeText),
                 Column('resource_parent_id', Integer, ForeignKey('taggable.id')),
                 Column('document_id', Integer, ForeignKey('taggable.id')), # Unique Element
                 

                 )

# images= Table ('images', metadata,
#                Column('id', Integer, ForeignKey('taggable.id'),primary_key=True),
#                Column('src', Text),
#                Column('x', Integer),
#                Column('y', Integer),
#                Column('z', Integer),
#                Column('t', Integer),
#                Column('ch', Integer))

#tags = Table ('tags', metadata,
#              Column('id',  Integer, ForeignKey('taggable.id'), primary_key=True),
#              Column('parent_id', Integer, ForeignKey('taggable.id'), index=True),
#              Column('type_id',  Integer, ForeignKey('names.id')),
#              Column('name_id', Integer, ForeignKey('names.id'), index=True),
#              Column('indx', Integer),
#              )

# gobjects = Table ('gobjects', metadata,
#               Column('id', Integer, ForeignKey('taggable.id'), primary_key=True),
#               Column('parent_id', Integer, ForeignKey('taggable.id'), index=True),
#               Column('type_id',  Integer, ForeignKey('names.id')),
#               Column('name_id', Integer, ForeignKey('names.id')),
#               Column('indx', Integer),
#               )


              
#simplevalues = Table ('simplevalues', metadata,
#          Column('id',  Integer, ForeignKey('taggable.id'), primary_key=True),
values = Table ('values', metadata,
          Column('resource_parent_id',Integer, ForeignKey('taggable.id'),primary_key=True),
          Column('document_id',Integer, ForeignKey('taggable.id')),
          Column('indx', Integer, primary_key = True, autoincrement=False),
          Column('valstr', UnicodeText),
          Column('valnum', Float),
          Column('valobj', Integer, ForeignKey('taggable.id'))
                      )

vertices = Table ('vertices', metadata,
#                Column('id', Integer, ForeignKey('taggable.id'), primary_key=True),
                Column('resource_parent_id',Integer, ForeignKey('taggable.id'), primary_key=True),
#                Column('document_id',Integer, ForeignKey('taggable.id')),
                Column('indx', Integer, primary_key=True, autoincrement=False),
                Column('x', Float),
                Column('y', Float),
                Column('z', Float),
                Column('t', Float),
                Column('ch', Integer))



# users = Table ('users', metadata,
#                Column('id', Integer, ForeignKey('taggable.id'), primary_key=True),
#                Column('user_name', UnicodeText),
#                Column('display_name', UnicodeText),
#                Column('email_address', UnicodeText),
#                Column('password', UnicodeText),
#                )

# groups = Table ('groups', metadata,
#                 Column('id', Integer, ForeignKey('taggable.id'), primary_key=True),
#                 Column ('group_name', UnicodeText),
#                 Column ('display_name', UnicodeText))


# templates = Table ('templates', metadata,
#                    Column('id', Integer, ForeignKey('taggable.id'),  primary_key=True),
#                    Column ('name', Text))

#engines = Table('engines', metadata,
#                Column('id', Integer, primary_key=True),
#                Column('name', String))

# modules = Table ('modules', metadata,
#                  Column('id', Integer,
#                         ForeignKey('taggable.id'), primary_key=True),
#                  Column('name', Text),
#                  Column('codeurl', Text),
#                  Column('module_type_id', Integer, ForeignKey('names.id'))
#                  )

# mex = Table ('mex', metadata,
#              Column('id',  Integer,
#                     ForeignKey('taggable.id'), primary_key=True),
#              Column('module', Text),
#              Column('status', Text)
#              )

# dataset = Table ('datasets', metadata,
#                  Column('id', Integer, ForeignKey('taggable.id'), primary_key=True),
#                  Column('name', Text),
#                  )

taggable_acl = Table('taggable_acl', metadata,
                     Column('taggable_id', Integer, ForeignKey('taggable.id'), primary_key=True),
                     Column('user_id', Integer, ForeignKey('taggable.id'),primary_key=True),
                     Column('permission', Integer, key="action"),
                     )


#dataset_members = Table ('dataset_member',
#                         Column ('dataset_id', 
#                                 ForeignKey('taggable.id'), primary_key=True),
#                         Column ('item_id', 
                 

#
# Registered services
# Allow bisquik installation to access remote services defined here.
# services = Table ('service', metadata,
#                   Column('id',  Integer,
#                          ForeignKey('taggable.id'), primary_key=True),
#                   Column('type', Text),
#                   Column('uri', Text),
#                   )

# permission_tokens = Table ('permission_tokens', metadata,
#                             Column('id', Integer, primary_key=True),
#                             Column ('name', String),
#                             Column ('description', String))
# permission_sets = Table ('permission_sets', metadata,
#       Column('set_id', Integer, primary_key=True),
#       Column('taggable_id', Integer, ForeignKey('taggable.id'), nullable=True),
# )
# permission_set_tokens = Table ('permission_set_tokens', metadata,
#       Column('token_id', Integer, ForeignKey('permission_tokens.id')),
#       Column('set_id', Integer, ForeignKey('permission_sets.set_id')),
# )


######################################################################
#
def parse_uri(uri):
    ''' Parse a bisquik uri into host , dbclass , and ID
    @type  uri: string
    @param uri: a bisquik uri representation of a resourc
    @rtype:  A triplet (host, dbclass, id)
    @return: The parse resouece
    '''
    url = urlparse.urlsplit(uri)
    name, id = url[2].split('/')[-2:]
    return url[1], name, id

def map_url (uri):
    '''Load the object specified by the root tree and return a rsource
    @type   root: Element 
    @param  root: The db object root with a uri attribute
    @rtype:  tag_model.Taggable
    @return: The resource loaded from the database
    '''
    # Check that we are looking at the right resource.
    
    net, name, ida = parse_uri(uri)
    name, dbcls = dbtype_from_name(name)
    resource = DBSession.query(dbcls).get (ida)
    #log.debug("loading uri name (%s) type (%s) = %s" %(name,  str(dbcls), str(resource)))
    return resource
    

################################
# Taggable types
# 

class Taggable(object):
    """
    Base type for taggable objects.  Taggable
    objects can have any number of name/value pairs
    associated with it.
    """
    xmltag = 'resource'
    
    def __init__(self, resource_type = None, parent = None):
        if resource_type is None:
            resource_type = self.xmltag
        self.resource_type = resource_type
        # By defualt you are the document
        if parent: 
            parent.children.append(self)
            self.document = parent.document
        else:
            self.document = self

        #if self.resource_type == 'mex':
        #    self.mex = self
        #    session['mex'] = self

        #if self.resource_type == 'user':
        #    self.owner = self

        self.perm = PUBLIC
        self.ts = datetime.now()
        #log.debug("new taggable user:" + str(session.dough_user.__dict__) )
        owner  = identity.current.get_bq_user()
        mex = session.get('mex', None)
        log.debug ("owner = %s mex = %s" % (owner, mex))
        if owner:
            self.owner_id = owner.id
            self.perm = PRIVATE
        if mex:
            self.mex = mex
        else:
            mexid = session.get('mex_id')
            log.debug ("mex_id = %s" % mexid)
            if mexid:
                self.mex = DBSession.query(ModuleExecution).get(mexid)
                session['mex'] = self.mex
            else:
                # Default to the system/init mex
                self.mex = DBSession.query(ModuleExecution).filter_by(
                    resource_user_type = "initialization").first()
                #session['mex'] = self.mex

        if owner is None:
            log.warn ("CREATING taggable %s with no owner" % str(self) )
            admin = identity.get_admin()
            if admin:
                log.warn("Setting owner to admin")
                self.owner_id = admin.id
    
    def resource (self):
        return "%s/%s" % ( self.table , self.id)
    resource = property(resource)

    def uri (self):
        if hasattr(self,'parent') and self.parent is not None:
            parent = self.parent.loadFull()
            return "%s/%s/%s" % (parent.uri , self.resource_type, self.id)
        else:
            return "%s/%s" % (self.resource_type, self.id)
            
    uri = property(uri)


    @validates('owner')
    def validate_owner (self, key, owner):
        if isinstance(owner, basestring) and owner.startswith ('http'):
            return map_url (owner)
        return owner
        

#    def get_owner (self):
#        if self.owner_ob:
#            return self.owner_ob.user_name
#    def set_owner (self,name):
#        self.owner_ob = BQUser.filter_by (user_name=name).one()
#    owner = property(get_owner, set_owner)

    def clear(self, what=['all']):
        '''Clear all the children'''
        results = []
        if 'all' in what:
            results.extend(self.children)
            self.children = []
            self.tags = []
            self.gobjects = []
            log.debug ('cleared all')
            return results
        if 'tags' in what:
            results.extend(self.tags)
            self.children = list (set(self.children) - set(self.tags))
            self.tags = []
            log.debug ('cleared tags')
        if 'gobjects' in what:
            results.extend(self.gobjects)
            self.children = list (set(self.children) - set(self.gobjects))
            self.gobjects = []
            log.debug ('cleared gobjects')
        return results

    def findtag (self, nm, create=False):
        for t in self.tags:
            if t.resource_name == nm:
                return t
        t=None
        if create:
            t = Tag(parent = self)
            t.resource_name = nm
        return t

    def loadFull(self):
        'hack to load polymorphic taggable type'
        #table, dbtype = dbtype_from_name(self.table)
        #if dbtype != Taggable:
        #    return DBSession.query(dbtype).get (self.id)
        return self

    # Tag.indx used for ordering tags
    def get_index(self):
        return self.resource_index
    def set_index(self, v):
        self.resource_index = v
    index = property(get_index, set_index)

    # Tag.indx used for ordering tags
    def get_name(self):
        return self.resource_name
    def set_name(self, v):
        self.resource_name = v
    name = property(get_name, set_name)
    # Tag.indx used for ordering tags
    def get_type(self):
        return self.resource_user_type
    def set_type(self, v):
        self.resource_user_type = v
    type = property(get_type, set_type)


    def get_permission(self):
        return perm2str.get(self.perm)

    def set_permission(self, v):
        self.perm = perm2code.get(v)
    permission = property(get_permission, set_permission)

    # Tag.value helper functions
    def newval(self, v, i = 0):
        if isinstance(v,basestring):
            v = Value(i, s = v)
        elif type(v) == int or type(v) == float:
            v = Value(i, n = v)
        elif isinstance(v, Taggable):
            v = Value(i, o = v)
        else:
            raise BadValue("Tag "+self.name, v)
        return v
    def getvalue(self):
        if self.resource_value is not None:
            return self.resource_value
        else:
            # call SimpleValue decoder
            values =  [ v.value for v in self.values ] 
            if len(values) == 0:
                return None
            return values

    def setvalue(self, v):
        self.resource_value = None
        if isinstance(v, list):
            l = [ self.newval(v[i], i) for i in xrange(len(v)) ]
            self.values = l
        elif isinstance(v, basestring):
            self.resource_value = v
        else:
            l = [ self.newval(v, 0) ]
            self.values = l
            

    value = property(fget=getvalue,
                     fset=setvalue,
                     doc="resource_value")


    #def __repr__(self):
    #    return u"<%s: %s=%s>" % (self.resource_type, self.resource_name, self.resource_value)
    def __str__(self):
        #return "%s/%s" % (self.__class__.xmltag,  str(self.id))
        return self.uri 


class Image(Taggable):
    """
    Image object
    """
    xmltag = 'image'


class Tag(Taggable):
    '''
    Tag object (name,value) pair.
    Tag have for the following properties:
    '''
    xmltag = 'tag'

    def __str__(self):
        return 'tag "%s":"%s"' % (unicode(self.name), unicode(self.value))

    def clear(self, what=None):
        '''Clear all the children'''
        super(Tag, self).clear()
        log.debug ('cleared values')
        old = self.values
        self.values = []
        return old
        
class Value(object):
    xmltag = 'value'
    
    def __init__(self, ind=None, s = None, n = None, o = None):
        self.indx = ind
        self.valstr = s
        self.valnum = n
        self.object = o
    
    def getvalue(self):
        value = ''
        if self.valstr: value = self.valstr
        elif self.valobj: value = self.objref
        elif self.valnum: value = self.valnum
        return value
    def setvalue(self, v):
        if type(v) == str or type(v) == unicode:
            self.valstr = v
            self.valnum = None
            self.valobj = None
        elif type(v) == int or type(v) == float:
            self.valnum = v
            self.valstr = None
            self.valobj = None
        elif isinstance(v, Taggable):
            self.objref = v
            self.valnum = None
            self.valstr = None
        
    def remvalue(self):
        self.valstr = None
        self.valnum = None
        self.valobj = None
        
    value = property(fget=getvalue,
                     fset=setvalue,
                     fdel=remvalue,
                     doc="Value of tag")
    
    def gettype (self):
        if self.valobj: return "object"
        elif self.valnum: return "number"
        return "string"
    def settype (self,x):
        pass
    type = property (gettype, settype)

    def getobjid(self):
        return self.valobj
    taggable_id = property(getobjid)

    # Tag.indx used for ordering tags
    def get_index(self):
        return self.indx
    def set_index(self, v):
        self.indx = v
    index = property(get_index, set_index)
    

    def __str__ (self):
        return unicode( self.value )


class Vertex(object):
    xmltag = 'vertex'

    def get_index(self):
        return self.indx
    def set_index(self, v):
        self.indx = v
    index = property(get_index, set_index)
    def __str__ (self):
        return "<vertex x=%s y=%s z=%s t=%s ch=%s index=%s />" % (self.x, self.y,self.z,self.t,self.ch, self.indx)


class GObject(Taggable):
    xmltag = 'gobject'
        
    def clear(self, what=None):
        '''Clear all the children'''
        super(GObject, self).clear()
        log.debug ('cleared vertices')
        old = self.vertices
        self.vertices = []
        return old
    
#    def __str__(self):
#        return 'gobject %s:%s' % (self.name, str(self.type))



class BQUser(Taggable):
    '''
    User object
    '''
    xmltag = 'user'

    def __init__(self, user_name=None, password=None, 
					email_address=None, display_name=None,
					create_tg=False, tg_user = None, **kw):
        super(BQUser, self).__init__()
        if not display_name: display_name = user_name

        if create_tg and tg_user is None:
            tg_user = User()
            tg_user.user_name = user_name
            tg_user.email_address = email_address
            tg_user.password = password
            tg_user.display_name = display_name
            DBSession.add(tg_user)

        self.perm = PUBLIC
        self.name = tg_user.user_name
        self.value = tg_user.email_address
        dn = Tag (parent = self)
        dn.name = 'display_name'
        dn.value = tg_user.display_name
        dn.owner = self
        self.owner = self
        DBSession.add(self);
        
    @classmethod
    def new_user (cls, email, password, create_tg = False):
        bquser =  cls( user_name= email,
                       email_address=email,
                       display_name=email,
                       password = password)
        DBSession.add (bquser)
        DBSession.flush()
        DBSession.refresh(bquser)
        bquser.owner_id = bquser.id

        if create_tg:
            tg_user = User()
            tg_user.user_name = user_name
            tg_user.email_address = email_address
            tg_user.password = password
            tg_user.display_name = display_name
            #tg_user.dough_user_id = self.id
            DBSession.add(tg_user)
            DBSession.flush()

        return bquser

    def user_id(self):
        return self.id
    user_id = property(user_id)

class Template(Taggable):
    '''
    A pre-canned group of tags
    '''
    xmltag = 'template'
    
class Module(Taggable):
    '''
    A module is a runnable routine that modifies the database
    There are several required tags for every module:
    for each input/output a type tag exists:
       (formal_input: [string, float, tablename])
       (formal_output: [tagname, tablename])
    
    '''
    xmltag ='module'
    # def get_module_type(self):
    #     if self.module_type:
    #         return self.module_type
    #     return ""
    # def set_module_type(self, v):
    #     self.module_type = UniqueName(v)
    # type = property(get_module_type, set_module_type)

class ModuleExecution(Taggable):
    '''
    A module execution is an actual execution of a module.
    Executions must have the folling tags available:
      (actual_input: taggable_id)
      (actual_output: taggable_id)
    '''
    xmltag ='mex'

    def closed(self):
        return self.status in ('FINISHED', 'FAILED')
    # alias for resource_value
    #status = taggable.c.resource_value
    #@hybrid_property
    def getstatus(self):
        return self.resource_value
    #@status.setter
    def setstatus(self, v):
        self.resource_value = v
    status = property(getstatus,setstatus)


class Dataset(Taggable):
    xmltag = 'dataset'
    

class PermissionToken(object):
    '''
    Permission Token object i.e. R_all, W_user1
    '''

class PermissionSetToken(object):
    '''
    Permission Token object i.e. R_all, W_user1
    '''

class PermissionSet(object):
    '''
    A Set of permissions.  
    '''
    def __init__(self, o):
        '''Create a permissionSet for object o'''
        if o:
            self.taggable = o
    def add(self, token):
        pst = PermissionSetToken()
        pst.token=token
        pst.set = self
            
        self.tokens.append (pst)

class TaggableAcl(object):
    """A permission for EDIT or READ on a taggable object
    """
    xmltag = "auth"


    def setperm(self, perm):
        self.action = { "read":0, "edit":1 } .get(perm, 0)
    def getperm(self):
        return [ "read", "edit"] [self.action]
        
    permission = property(getperm, setperm)
    
    def __str__(self):
        return "resource:%s  user:%s permission:%s" % (self.taggable_id,
                                                       self.user_id,
                                                       self.action)


class Service (Taggable):
    """A executable service"""
    xmltag = "service"
    
    #def __str__(self):
    #    return "%s module=%s engine=%s" % (self.uri, self.module, self.engine)
    
#################################################
# Simple Mappers
#mapper( UniqueName, names)
#session.mapper(UniqueName, names)
        
mapper( Value, values,
        properties = {
        #'resource_parent_id' : values.c.parent_id,
        #'parent' : relation (Taggable,
        #                 primaryjoin =(taggable.c.id == values.c.parent_id)),
        'objref' : relation(Taggable, uselist=False,
                            primaryjoin=(values.c.valobj==taggable.c.id),
                            enable_typechecks=False
                            ),
        }
        )

mapper( Vertex, vertices)
mapper(TaggableAcl, taggable_acl,
       properties = {
#           'user'    : relation(User, 
#                                passive_deletes="all",
#                                uselist=False,
#                                primaryjoin=(taggable_acl.c.user_id== taggable.c.id),
#                                foreign_keys=[taggable.c.id])
           })

############################
# Taggable mappers

mapper( Taggable, taggable,
        #polymorphic_on = taggable.c.resource_type,
        #polymorphic_identity = '', 
                       properties = {
    'tags' : relation(Taggable, lazy=True, viewonly=True, cascade="all, delete-orphan",

                         primaryjoin= and_(taggable.c.resource_parent_id==taggable.c.id,
                                           taggable.c.resource_type == 'tag')),
    'gobjects' : relation(Taggable, lazy=True, viewonly=True, cascade="all, delete-orphan",

                         primaryjoin= and_(taggable.c.resource_parent_id==taggable.c.id,
                                           taggable.c.resource_type == 'gobject')),
    'acl'  : relation(TaggableAcl, lazy=True, cascade="all, delete-orphan",
                      primaryjoin = (TaggableAcl.taggable_id == taggable.c.id),
                      backref = backref('resource', remote_side=[taggable.c.id] ),
                      ),
    'children' : relation(Taggable, lazy=True, cascade="all, delete-orphan",
                          enable_typechecks = False, 
                          backref = backref('parent', enable_typechecks=False, remote_side = [ taggable.c.id]),
                          primaryjoin = (taggable.c.id == taggable.c.resource_parent_id)),
    'values' : relation(Value,  lazy=True, cascade="all, delete-orphan",
                        primaryjoin =(taggable.c.id == values.c.resource_parent_id),
                        backref = backref('parent', enable_typechecks = False, remote_side=[taggable.c.id])
                        #foreign_keys=[values.c.parent_id]
                        ),
    'vertices' : relation(Vertex, lazy=True, cascade="all, delete-orphan",
                          primaryjoin =(taggable.c.id == vertices.c.resource_parent_id),
                          #foreign_keys=[vertices.c.resource_parent_id]
                          ),

    'tagq' : relation(Taggable, lazy='dynamic',
                      primaryjoin= and_(taggable.c.resource_parent_id==taggable.c.id,
                                        taggable.c.resource_type == 'tag')),


    'docnodes': relation(Taggable, lazy=True, 
                         cascade = "all, delete-orphan",
                         enable_typechecks = False, 
                         post_update=True,
                         primaryjoin = (taggable.c.id == taggable.c.document_id),
                         backref = backref('document', post_update=True, 
                                           enable_typechecks=False, remote_side=[taggable.c.id]),
                         )
    }
        )

mapper( Image, inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'image',)
mapper( Tag, inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'tag',)
mapper( GObject,  inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'gobject',)
mapper(BQUser,  inherits=Taggable,
       polymorphic_on = taggable.c.resource_type,
       polymorphic_identity = 'user',
       properties = { 
        'tguser' : relation(User, uselist=False, 
            primaryjoin=(User.user_name == taggable.c.resource_name),
            foreign_keys=[User.user_name]),


        'owns' : relation(Taggable, lazy=True,
                          cascade = "all, delete-orphan",
                          post_update = True,
                          enable_typechecks=False,
                          primaryjoin = (taggable.c.id == taggable.c.owner_id),
                          backref = backref('owner', post_update=True, remote_side=[taggable.c.id]),
                          ),

        'user_acls': relation(TaggableAcl,  lazy=True, cascade="all, delete-orphan",
                              primaryjoin= (taggable.c.id == taggable_acl.c.user_id),
                              backref = backref('user'),
                              )
                              
        }
       )
def bquser_callback (tg_user, operation, **kw):
    # Deleted users will receive and update callback
    if tg_user is None:
        return
    if operation =='create':
        u = DBSession.query(BQUser).filter_by(resource_name=tg_user.user_name).first()
        if u is None:
            log.info ('creating BQUSER ')
            BQUser(tg_user=tg_user)
            return
    if operation  == 'update':
        u = DBSession.query(BQUser).filter_by(resource_name=tg_user.user_name).first()
        if u is not None:
            u.value = tg_user.email_address
            dn = u.findtag('display_name', create=True)
            dn.value = tg_user.display_name
            pass
        return
User.callbacks.append (bquser_callback)

def registration_hook(action, **kw):
    if action=="new_user":
        u = kw.pop('user', None)
        if u:
            BQUser.new_user (u.email_adress)
    elif action=="update_user":
        u = kw.pop('user', None)
        if u:
            bquser = DBSession.query(BQUser).filter_by(resource_value=u.email_address).first()
            if not bquser:
                bquser = BQUser.new_user (u.email_adress)
            dn = bq_user.findtag('display_name', create=True)
            dn.value = tg_user.display_name
                
            #bquser.display_name = u.display_name
            bquser.resource_name = u.user_name
            log.error('Fix the display_name')
    elif action =="delete_user":
        pass



mapper(Template, inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'template')
mapper(Module, inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'module',)
mapper(ModuleExecution,  inherits=Taggable,
       polymorphic_on = taggable.c.resource_type,
       polymorphic_identity = 'mex',
       properties = {
        #"status":synonym("resource_value"), # map_column=True) ,
        'owns' : relation(Taggable, 
                          lazy = True,
                          cascade = "all, delete-orphan",
                          #cascade = None,
                          post_update = True,
                          enable_typechecks=False,
                          primaryjoin = (taggable.c.id == taggable.c.mex_id),
                          backref = backref('mex', post_update=True, remote_side=[taggable.c.id])),
        })
mapper( Dataset,  inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'dataset',)
mapper( Service, inherits=Taggable,
        polymorphic_on = taggable.c.resource_type,
        polymorphic_identity = 'service')

#################################################
# Support Functions

#class_mapper(User).add_property('dough_user',
#    relation(BQUser,
#         primaryjoin=(User.dough_user_id == Taggable.id),
#         foreign_keys=[Taggable.id],
#    )
#)

        
# def db_setup():
#     global admin_user, init_module, init_mex
#     admin_user = BQUser.query.filter(BQUser.user_name == u'admin').first()
#     if not admin_user:
#         admin_user = BQUser.new_user(password=u'admin', email = u'admin')
#         init_module = Module ()
#         init_mex = ModuleExecution ()
#         DBSession.add (init_module)
#         DBSession.add (init_mex)
#         DBSession.flush()
    
#         DBSession.refresh (init_module)
#         DBSession.refresh (init_mex)
#         admin_user.mex_id = init_mex.id

#         init_module.owner_id = admin_user.id
#         init_module.mex_id = init_mex.id
#         init_module.name  = "initialize"

#         init_mex.mex_id = init_mex.id
#         init_mex.owner_id = admin_user.id
#         init_mex.module = "initialize"
#         init_mex.status = "FINISH"
#     identity.set_admin (admin_user)
        

# def db_load():
#     global admin_user, init_module, init_mex
#     admin_user = DBSession.query(BQUser).filter_by(user_name=u'admin').first()
#     init_module= DBSession.query(Module).filter_by(name='initialize').first()
#     init_mex   = DBSession.query(ModuleExecution).filter_by(module='initialize').first()
#     log.info( "initalize mex = %s" % init_mex)


def init_admin():
#    admin_group = Group.query.filter(Group.group_name == u'admin').first()
#    if not admin_group:
#        admin_group = Group(group_name = u'admin', display_name = u'Administrators')
#        session.add(admin_group)
#        session.flush()
        
    log.debug ("admin user = %s" %  admin_user)
    return admin_user






@memoized
def dbtype_from_name(table):
    ''' Return a tuple of table name and the most specific database type'''
    if table in metadata.tables:
        for mapper_ in  list(sqlalchemy.orm._mapper_registry):
            #logger.debug ("map"+str(mapper_.local_table))
            if mapper_.local_table == metadata.tables[table]:
                return (table, mapper_.class_)
    return (table, Taggable)

@memoized
def dbtype_from_tag(tag):
    ''' Given a tag,
    Return a tuple of table name and the most specific database type
    '''
    for mapper_ in  list(sqlalchemy.orm._mapper_registry):
        #logger.debug ("map"+str(mapper_.local_table))
        if hasattr(mapper_.class_, 'xmltag') and mapper_.class_.xmltag == tag:
            return (tag, mapper_.class_)
    return (tag, Taggable)

@memoized
def all_resources ():
    ''' Return the setof unique names that are taggable objects
    '''
    #names = DBSession.query(UniqueName).filter(UniqueName.id == Taggable.tb_id).all()
    #log.debug ('all_resources' + str(names))
    names = [ x[0] for x in DBSession.query(Taggable.resource_type).distinct().all() ]

    return names

    

