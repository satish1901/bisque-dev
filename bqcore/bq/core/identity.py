#from turbogears import identity
#from turbogears.util import request_available


from tg import request
import logging
from bq.exceptions import BQException
from bq.core.model import DBSession, User

user_admin = None
current_user = None
log = logging.getLogger("bq.identity")



class BQIdentityException (BQException):
    pass

#################################################
# Simple checks
def request_valid ():
    try:
        return 'repoze.who.userid' in request.identity
    except (TypeError, AttributeError):
        return False

def anonymous():
    try:
        return request.identity.get('repoze.who.userid') is None
    except (TypeError, AttributeError):
        return True
    
def not_anonymous():
    return not anonymous()

    

# NOTE:
# BisqueIdentity is an object even though the methods could be imlemented as classmethod
# in order to 'property' style access
class BisqueIdentity(object):
    "helper class to fetch current user object"

    def get_username (self):
        if request_valid():
            return request.identity['repoze.who.userid']
        return None
    #def set_username (cls, v):
    #    if request_valid():
    #        request.identity['repoze.who.userid'] = v
    #user_name = property(get_username, set_username)
    user_name = property(get_username)

    def _get_tguser(self):
        if not request_valid():
            return None

        return request.identity.get ('user')
        # user = request.identity.get ('bisque.user')
        # if user:
        #     return user
        # user_name = self.user_name
        # if user_name is None:
        #     return None
        # user = DBSession.query (User).filter_by(user_name = user_name).first()
        # request.identity['bisque.user'] = user
        return user
    #user = property(get_user)

    def _get_bquser(self):
        if not request_valid():
            return None
        bquser = request.identity.get ('bisque.bquser')
        if bquser:
            return bquser

        user_name = self.get_username()
        if not user_name:
            return None

        from bq.data_service.model.tag_model import BQUser
        bquser =  DBSession.query (BQUser).filter_by(resource_name = user_name).first()
        request.identity['bisque.bquser'] = bquser
        #log.debug ("bq user = %s" % user)
        log.debug ('user %s -> %s' % (user_name, bquser))
        return bquser

    def set_current_user (self, user):
        'Set the user identity to user'
        if isinstance (user, basestring):
            from bq.data_service.model.tag_model import BQUser
            user =  DBSession.query (BQUser).filter_by(resource_name = user).first()
        request.identity['bisque.bquser'] = user
        request.identity['repoze.who.userid'] = user and user.resource_name


####################################
##  Current user object
current  = BisqueIdentity()


    
def set_admin (admin):
    global user_admin
    user_admin = admin

def get_admin():
    user_admin = None
    if hasattr(request, 'identity'):
        user_admin = request.identity.get ('bisque.admin_user', None)
    if user_admin is None:
        from bq.data_service.model.tag_model import BQUser
        user_admin = DBSession.query(BQUser).filter_by(resource_name=u'admin').first()
        if hasattr(request, 'identity'):
            request.identity['bisque.admin_user'] = user_admin
    return user_admin

def get_admin_id():
    user_admin = get_admin()
    return user_admin and user_admin.id
    

#     if request_available():
#         return identity.not_anonymous()
#     return current_user

def get_user_id():
    bquser = current._get_bquser()
    return bquser and bquser.id 

def get_username():
    return current.get_username()
    
def get_user():
    """Get the current user object"""
    return current._get_bquser()

def set_current_user(username):
    "set the current user by name"
    return current.set_current_user(username)


def add_credentials(headers):
    """add the current user credentials for outgoing http requests

    This is a place holder for outgoing request made by the server
    on behalf of the logged in user.  Will depend on login methods
    (password, CAS, openid) and avaialble methods.
    """
    pass


def set_admin_mode (v=True):
    if v:
        user_admin = get_admin()
        current.set_current_user (user_admin)
    else:
        current.set_current_user (None)


def mex_authorization_token():
    try:
        mex_id =  request.identity['bisque.mex_id']
        return mex_id
    except (TypeError, KeyError):
        pass
    return None
        
    mex_token = current_mex()
    return str(mex_token)


