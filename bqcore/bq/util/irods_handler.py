import os
import re
import urlparse
import shutil
import atexit
import logging
import irods
import subprocess

from bq.util.mkdir import _mkdir
from bq.util.paths import data_path
IRODS_CACHE = data_path('irods_cache')

CONNECTION_POOL = {}


class IrodsError(Exception):
    pass

log = logging.getLogger('bq.irods')

parse_net = re.compile('^((?P<user>[^:]+):(?P<password>[\w.#^!;]+)?@)?(?P<host>[^:]+)(?P<port>:\d+)?')
irods_env, status = irods.getRodsEnv()


if not os.path.exists(IRODS_CACHE):
    _mkdir (IRODS_CACHE)

def irods_cleanup():
    for key, conn in CONNECTION_POOL.items():
        print "disconnecting %s" % key
        conn.disconnect()

#atexit.register(irods_cleanup)



class IrodsConnection(object):
    def __init__(self, url, user=None, host=None, port=None, password = None):
        irods_url = urlparse.urlparse(url)
        assert irods_url.scheme == 'irods'
        env = parse_net.match(irods_url.netloc).groupdict()
        log.debug ("irods_handler url %s -> env %s" % (url, env))

        self.user  = user or env['user'] or irods_env.getRodsUserName()
        self.host  = host or env['host'] or irods_env.getRodsHost()
        self.port  = port or env['port'] or irods_env.getRodsPort() or 1247
        self.password = password or env['password'] 

        path = ''
        zone = ''
        if irods_url.path:
            path = irods_url.path.split('/')
            if len(path):
                zone = path[1]
            path = '/'.join(path)
        if not zone:
            zone = irods_env.getRodsZone()

        self.irods_url = irods_url
        self.path = path
        self.zone = zone
        self.conn = None

    def open(self):
        conn, err = irods.rcConnect(self.host, self.port, self.user, self.zone)
        if conn is None:
            raise IrodsError("Can't create connection to %s " % self.host)
        if self.password:
            irods.clientLoginWithPassword(conn, self.password)
        else:
            irods.clientLogin(conn)

        coll = irods.irodsCollection(conn)
        nm = coll.getCollName()
        
        self.irods_url = urlparse.urlunparse(list(self.irods_url)[:2] + ['']*4)
        if self.path in ['', '/']:
            self.path = nm

        self.conn = conn
        self.base_dir = nm
        return self
        
    def close(self):
        if self.conn:
            self.conn.disconnect()
            self.conn = None


    def __enter__(self):
        if self.conn is None:
             self.open()
        return self

    def __exit__(self, ty, val, tb):
        self.close()
        return False

        

def irods_conn(url, user=None, host=None, port=None, password = None):
    global CONNECTION_POOL

    irods_url = urlparse.urlparse(url)
    assert irods_url.scheme == 'irods'
    env = parse_net.match(irods_url.netloc).groupdict()
    log.debug ("irods_handler url %s -> env %s" % (url, env))

    user  = user or env['user'] or irods_env.getRodsUserName()
    host  = host or env['host'] or irods_env.getRodsHost()
    port  = port or env['port'] or irods_env.getRodsPort() or 1247
    password = password or env['password'] 

    path = ''
    zone = ''
    if irods_url.path:
        path = irods_url.path.split('/')
        if len(path):
            zone = path[1]
        path = '/'.join(path)
    if not zone:
        zone = irods_env.getRodsZone()
        

    log.debug("irods_connect with %s" % ( [user, password, host, port] ))
    key = ','.join([user, host, str(port)])
    conn = CONNECTION_POOL.get(key)
    if conn is None:
        log.debug ( "Connecting" )
        conn, err = irods.rcConnect(host, port, user, zone)
        if conn is None:
            raise IrodsError("Can't create connection to %s " % host)
        if password:
            irods.clientLoginWithPassword(conn, password)
        else:
            irods.clientLogin(conn)
        CONNECTION_POOL[key] = conn

    coll = irods.irodsCollection(conn)
    nm = coll.getCollName()
        
    irods_url = urlparse.urlunparse(list(irods_url)[:2] + ['']*4)
    if path in ['', '/']:
        path = nm
    #assert path.startswith(nm)

    return conn, irods_url, nm, path
    

def irods_cache_name(path):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    return cache_filename
def irods_cache_fetch(path):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    if os.path.exists(cache_filename):
        return cache_filename
    return None

BLOCK_SZ=512*1024
def copyfile(f1, *dest):
    'copy a file to multiple destinations'
    while True:
        buf = f1.read(BLOCK_SZ)
        if not buf:
            break
        for fw in dest:
            fw.write(buf)
        if len(buf) < BLOCK_SZ:
            break

def irods_cache_save(f, path, *dest):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    _mkdir(os.path.dirname(cache_filename))
    with open(cache_filename, 'wb') as fw:
        #shutil.copyfileobj(f, fw)
        copyfile(f, fw, *dest)
    return cache_filename
    
def irods_fetch_file(url, **kw):
    ic = IrodsConnection(url, **kw)
    #conn, base_url, basedir, path = irods_conn(url, **kw)
    log.debug( "irods-path %s" %  ic.path)
    localname = irods_cache_fetch(ic.path)
    if localname is None:
        with ic:
            log.debug( "irods_fetching %s -> %s" % (url, ic.path))
            f = irods.iRodsOpen(ic.conn, ic.path)
            if not f:
                raise IrodsError("can't read from %s" % url)
            localname = irods_cache_save(f, ic.path)
            f.close()
    return localname

def irods_fetch_file_IGET(url, **kw):
    ic = IrodsConnection(url, **kw)
    #conn, base_url, basedir, path = irods_conn(url, **kw)
    log.debug( "irods-path %s" %  ic.path)
    localname = irods_cache_fetch(ic.path)
    if localname is None:
        with ic:
            log.debug( "irods_fetching %s -> %s" % (url, ic.path))
            localname = irods_cache_name(ic.path)
            _mkdir(os.path.dirname(localname))
            log.info('irods %s' %  ['iget', ic.path, localname])
            retcode = subprocess.call(['iget',ic.path, localname])
            if retcode:
                raise IrodsError("can't read from %s  %s %s error (%s)" % (url, ic.path, localname, retcode))
    return localname


def irods_push_file(fileobj, url, savelocal=True, **kw):
    #conn, base_url, basedir, path = irods_conn(url, **kw)
    with IrodsConnection(url, **kw) as ic:
        # Hmm .. if an irodsEnv exists then it is used over our login name provided above, 
        # meaning even though we have logged in as user X we may be the homedir of user Y (in .irodsEnv)
        # irods.mkCollR(conn, basedir, os.path.dirname(path))
        retcode = irods.mkCollR(ic.conn, '/', os.path.dirname(ic.path))
        log.debug( "irods-path %s" %  ic.path)
        f = irods.iRodsOpen(ic.conn, ic.path, 'w')
        if f:
            localname = irods_cache_save(fileobj, ic.path, f)
            f.close()
            return localname
        raise IrodsError("can't write irods url %s" % url)

def irods_push_file_IPUT(fileobj, url, savelocal=True, **kw):
    #conn, base_url, basedir, path = irods_conn(url, **kw)
    with IrodsConnection(url, **kw) as ic:
        # Hmm .. if an irodsEnv exists then it is used over our login name provided above, 
        # meaning even though we have logged in as user X we may be the homedir of user Y (in .irodsEnv)
        # irods.mkCollR(conn, basedir, os.path.dirname(path))
        retcode = irods.mkCollR(ic.conn, '/', os.path.dirname(ic.path))
        if retcode:
            raise IrodsError("can't write irods url %s" % url)
        log.debug( "irods-path %s" %  ic.path)
        localname = irods_cache_save(fileobj, ic.path)
        log.info ('iput %s %s' % (localname, ic.path))
        retcode = subprocess.call(['iput', localname, ic.path])
        if retcode:
            raise IrodsError("can't write irods url %s" % url)
        return localname



def irods_fetch_dir(url, **kw):

    #conn, base_url, basedir, path = irods_conn(url, **kw)
    with IrodsConnection(url, **kw) as ic:
        coll = irods.irodsCollection(ic.conn)
        path = coll.openCollection(ic.path); 
        # Bug in openCollection (appends \0)
        path = path.strip('\x00')
        #print 'path2 Null', '\x00' in path

        result = []
        # Construct urls for objects contained
        for nm in coll.getSubCollections():
            #print " '%s' '%s' '%s' " % (base_url, path, nm)
            #print 'nm Null', '\x00' in nm
            #print 'path3 Null', '\x00' in path
            result.append('/'.join([ic.base_url, ic.path[1:], nm, '']))
        
        for nm, resource in  coll.getObjects():
            result.append( '/'.join([ic.base_url, ic.path[1:], nm]))
        return result





    
    
    
    
