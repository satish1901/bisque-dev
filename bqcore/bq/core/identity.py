#from turbogears import identity
#from turbogears.util import request_available


from tg import request
import logging
from bq.core.exceptions import BQException
from bq.core.model import DBSession, User

user_admin = None
current_user = None
log = logging.getLogger("bq.identity")



class BQIdentityException (BQException):
    pass


def request_valid ():
    try:
        return request.identity is not None
    except (TypeError, AttributeError):
        return False
    

class Identity(object):
    def get_username (self):
        if request_valid():
            return request.identity['repoze.who.userid']
        return None
    user_name = property(get_username)

    def get_user(self):
        user_name = self.user_name
        if user_name is None:
            return None
        return DBSession.query (User).filter_by(user_name = user_name).first()
    user = property(get_user)

    def get_bq_user(self):
        from bq.data_service.model.tag_model import BQUser
        user_name = self.user_name
        #log.debug ("bq user = %s" % user_name)
        if user_name is None:
            return None
        user =  DBSession.query (BQUser).filter_by(user_name = user_name).first()
        #log.debug ("bq user = %s" % user)
        log.debug ('user %s -> %s' % (user_name, user))
        return user
    
current  = Identity()

def set_admin (admin):
    global user_admin
    user_admin = admin

def get_admin():
    global user_admin
    if user_admin is None:
        from bq.data_service.model.tag_model import BQUser
        user_admin = DBSession.query(BQUser).filter_by(user_name=u'admin').first()
    else:
        user_admin = DBSession.merge (user_admin)
    return user_admin

def anonymous():
    return request.identity is None

def not_anonymous():
    return request.identity is not None
#     if request_available():
#         return identity.not_anonymous()
#     return current_user

def get_user_id():
    if request_valid():
        #log.debug ("identity = %s" % ( request.identity['repoze.who.userid'] ))
        bq_user = current.get_bq_user()
        if bq_user:
            return bq_user.id
    if current_user:
        return current_user.id
    #log.debug ('no user id set')
    return None

def get_user():
    """Get the current user object"""
    user_id = get_user_id()
    if user_id is not None:
        from bq.data_service.model.tag_model import BQUser
        return DBSession.query(BQUser).get (user_id)
    return None



def get_user_pass():
    if request.identity:
        if not_anonymous():
            u = current.user
            return (u.user_name, u.password)
        return None
    return current_user


def set_current_user(user=None):
    '''Set the user identity to user. Should be tg_user objects '''
    current_user = user


def set_admin_mode (a):
    if a:
        set_current_user (user_admin)
    else:
        set_current_user (None)


def current_mex():
    try:
        return request_valid() and request.headers['Mex']
    except (TypeError, KeyError):
        pass
    return None

def mex_authorization_token():
    mex_token = current_mex()
    return str(mex_token)


