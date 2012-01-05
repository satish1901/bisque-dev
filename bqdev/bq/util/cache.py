import threading

from time import time as _current_time # so we can stub out for unit testing
import cherrypy
import urllib
import os
from email.Utils import formatdate

try:
    import cPickle as pickle
except:
    import pickle
import marshal

import StringIO

from turbogears import identity, config

class PicklingCache(object):
    def get(self,key,default=None):
        data=self._raw_get(key)
        if data is None:
            return default
        return pickle.load(StringIO.StringIO(data))
    
    def set(self,key,value,timeout_seconds):
        out=StringIO.StringIO();
        pickle.dump(value, out, protocol=pickle.HIGHEST_PROTOCOL)
        data=out.getvalue()
        self._raw_set(key,data,timeout_seconds)

class DummyCache(object):
    '''cache that does nothing for dev use'''
    
    def __init__(self,*args):
        pass
    
    def get(self,key,default=None):
        return default
    
    def set(self,key,value,timeout_seconds):
        pass
    
    def delete(self,key):
        pass

class SimpleCache(PicklingCache):
    '''basic in memory cache for dev use'''
    
    def __init__(self,*args):
        self.values={}
    
    def _raw_get(self,key):
        expiration,value=self.values.get(key,(None,None))
        if value is None:
            return None
        if expiration < _current_time():
            del self.values[key]
            return None
        return value
    
    def _raw_set(self,key,value,timeout_seconds):
        self.values[key]=(_current_time()+timeout_seconds,value)
    
    def delete(self,key):
        del self.values[key]
    
    def clear(self):
        self.values.clear()

class LocalMemCache(SimpleCache):
    '''in memory cache (thread-safe)'''

    def __init__(self,*args):
        SimpleCache.__init__(self,*args)
        self.lock=threading.Lock()

    def _raw_get(self,key):
        self.lock.acquire()
        try:
            return SimpleCache._raw_get(self,key)
        finally:
            self.lock.release()

    def _raw_set(self,key,value,timeout_seconds):
        self.lock.acquire()
        try:
            SimpleCache._raw_set(self,key,value,timeout_seconds)
        finally:
            self.lock.release()

    def delete(self,key):
        self.lock.acquire()
        try:
            SimpleCache.delete(self,key)
        finally:
            self.lock.release()

    def clear(self):
        self.lock.acquire()
        try:
            SimpleCache.clear(self)
        finally:
            self.lock.release()


class FileCache(PicklingCache):
    
    def __init__(self,file_path):
        self.file_path=file_path
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
    
    def _file_name(self,key):
        return os.path.join(self.file_path,urllib.quote_plus(key))
    
    def _raw_get(self,key):
        file_name=self._file_name(key)
        try:
            f = open(file_name,'rb')
            expiration_time=marshal.load(f)
            if expiration_time < _current_time():
                f.close()
                self.delete(key)
                return None
            data = marshal.load(f)
            f.close()
            return data
        except:
            pass
        return None
    
    def _raw_set(self,key,value,timeout_seconds):
        file_name=self._file_name(key)
        try:
            f = open(file_name,'wb')
            marshal.dump(_current_time()+timeout_seconds,f);
            marshal.dump(value,f);
            f.close()
        except:
            pass
    
    def delete(self,key):
        file_name=self._file_name(key)
        try:
            os.remove(file_name)
        except:
            pass

class MemCache(PicklingCache):
    def __init__(self,servers):
        #print servers.split(';')
        import memcache
        self._cache=memcache.Client(servers.split(';'))

    def _raw_get(self,key):
        return self._cache.get(key)

    def _raw_set(self,key,value,timeout_seconds):
        self._cache.set(key,value,timeout_seconds)

    def delete(self,key):
        self._cache.delete(key)

BACKENDS = {
 'dummy': DummyCache,
 'simple': SimpleCache,
 'localmem': LocalMemCache,
 'file': FileCache,
 'memcache': MemCache
}

def load_backend(uri):
    #print "using cache uri: %s" % uri
    prefix,params=uri.split('://')
    backend_class=BACKENDS[prefix]
    return backend_class(params)

_decorator_timeout_seconds=config.get('cache.decorator.timeout_seconds',60*30)
_decorator_enabled=config.get('cache.decorator.enabled',True)
_decorator_anon_only=config.get('cache.decorator.anon_only',True)
cache=load_backend(config.get('cache.backend','simple://'))

def _get(key,default=None):
    '''return (cached value, expiration time, version #)'''
    data=cache.get(key,default)
    if data is None:
        return (None,None,None)
    return data

def _set(key, value, timeout_seconds, version=1):
    cache.set(key,(value,_current_time()+timeout_seconds,version),timeout_seconds+(2*60)) # add two min back-off to let recalc while stale data available

def _delete (key):
    cache.delete (key)

def default_version(*arg,**kw):
    return 1

def url_key(*arg,**kw):
    '''provided as a default key function based on a requests URL'''
    if _decorator_anon_only and not identity.current.anonymous:
        return None
    
    # don't cache if flash cookie set
    if cherrypy.request.simple_cookie.has_key('tg_flash'):
        return None
    
    url = cherrypy.request.path
    qs = cherrypy.request.query_string
    if qs:
        url = url + '?' + qs
    
    if not identity.current.anonymous:
        # prepend user id to make key unique to user
        return "%s@%s" % (identity.current.user.id,url)
    
    return url


def cache_result(key_fn=url_key,version_fn=default_version,timeout_seconds=_decorator_timeout_seconds):
    '''
    key_fn - a function that returns a string to lookup the cached value or None if 
             the value should not be cached.
             
    version_fn - a function to indicate a "version number" can return an arbitary string
                 and is used to determine if the cached value is stale, though it has not
                 expired yet
    
    timeout_seconds - expiration time in seconds (or fractions of)
    
    key_fn and version_fn both must accept the same arguments that the decorated function
    takes.  These arguments are used by the key/version functions to determine the
    key/version for the cached value.
    e.g.
    
    def my_key_fn(user):
        return user.user_name
    
    def my_version_fn(user):
        return str(user.updated) # when user object last updated
    
    @cache_result(key_fn=my_key_fn,version_fn=my_version_fn,timeout_seconds=60*60)
    def user_details(user):
        return "user name: %s last updated: %s" % (user.user_name,user.updated)
    
    Hence whenever user.updated is changed this should trigger a refresh of the cached
    value, before the expiration time is up.  This is handy for refreshing cached values
    without having to manually clear anything.  Though of course this may result in a
    database hit if the version function you use performs database access.  Often though
    this can be an acceptable cost/tradeoff for the freshness of served data.
    '''
    lock=threading.Lock() # lock for this cache decorator
    def decorator(fn):
        def decorated(*arg,**kw):
            if not _decorator_enabled:
                return fn(*arg,**kw)
            
            key = key_fn(*arg,**kw)
            if key is None:
                # key of non indicates we shouldn't use the cache
                return fn(*arg,**kw)
            
            value,expiration,version=_get(key)
            
            if value is not None:
                # check to see if has expired (or wrong version)
                current_version=version_fn(*arg,**kw)
                stale=False
                if expiration < _current_time():
                    stale=True
                else:
                    if version != current_version:
                        stale=True
                
                if stale:
                    # serve stale data if another thread is writing 
                    # to the cache
                    if lock.acquire(False):
                        try:
                            value=fn(*arg,**kw)
                            _set(key,value,timeout_seconds,current_version)
                        finally:
                            lock.release()
                    #else:
                    #    print "**********serving stale*************"
            else:
                lock.acquire()
                try:
                    version=version_fn(*arg,**kw)
                    value=fn(*arg,**kw)
                    _set(key,value,timeout_seconds,version)
                finally:
                    lock.release()
            return value
        return decorated
    return decorator

def expires(seconds=0):
    '''set expire headers for client-size caching'''
    def decorator(fn):
        def decorated(*arg,**kw):
            cherrypy.response.headers['Expires']=formatdate(_current_time()+seconds)
            return fn(*arg,**kw)
        return decorated
    return decorator


def default_invalidate(key):
    pass

def invalidate_cache(key_fn=url_key, invalidate_fn=default_invalidate):
    '''Decorator to invalidate cached pages that depend on this operation'''
    def decorator (fn):
        def decorated(*arg, **kw):
            value =  fn(*arg, **kw)
            key = key_fn(*arg, **kw)
            if key is not None:
                invalidate_fn (key)
            return value 
        return decorated
    return decorator



def invalidate_cache_entries (*arg, **kw):
    pass
