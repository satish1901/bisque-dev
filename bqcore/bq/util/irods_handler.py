import os
import re
import urlparse
import shutil
import atexit
import logging
import irods

from bq.util.mkdir import _mkdir

CONNECTION_POOL = {}
IRODS_CACHE = 'data/irods_cache/'


log = logging.getLogger('bq.irods')

parse_net = re.compile('^((?P<user>[^:]+):(?P<password>[\w.#^!;]+)?@)?(?P<host>[^:]+)(?P<port>:\d+)?')
irods_env, status = irods.getRodsEnv()


if not os.path.exists(IRODS_CACHE):
    _mkdir (IRODS_CACHE)

def irods_cleanup():
    for key, conn in CONNECTION_POOL.items():
        print "disconnecting %s" % key
        conn.disconnect()

atexit.register(irods_cleanup)

def irods_conn(url):
    global CONNECTION_POOL

    irods_url = urlparse.urlparse(url)
    assert irods_url.scheme == 'irods'
    env = parse_net.match(irods_url.netloc).groupdict()

    user  = env['user'] or irods_env.getRodsUserName()
    host  = env['host'] or irods_env.getRodsHost()
    port  = env['port'] or irods_env.getRodsPort() or 1247
    password  = env['password'] or '7#959^3~Uq'  # Bisque irods password

    path = ''
    zone = ''
    if irods_url.path:
        path = irods_url.path.split('/')
        if len(path):
            zone = path[1]
        path = '/'.join(path)
    if not zone:
        zone = irods_env.getRodsZone()
        

    print [user, password, host, port]
    key = ','.join([user, host, str(port)])
    conn = CONNECTION_POOL.get(key)
    if conn is None:
        print "Connecting"
        conn, err = irods.rcConnect(host, port, user, zone)
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
    assert path.startswith(nm)

    return conn, irods_url, nm, path
    

import pdb
def irods_fetch_dir(url):
    
    conn, base_url, basedir, path = irods_conn(url)
    #print 'path1 Null', '\x00' in path
    coll = irods.irodsCollection(conn)
    coll.openCollection(path); 
    # Bug in openCollection (appends \0)
    path = path.strip('\x00')
    #print 'path2 Null', '\x00' in path

    result = []
    # Construct urls for objects contained
    for nm in coll.getSubCollections():
        #print " '%s' '%s' '%s' " % (base_url, path, nm)
        #print 'nm Null', '\x00' in nm
        #print 'path3 Null', '\x00' in path
        result.append('/'.join([base_url, path[1:], nm, '']))
        
    for nm, resource in  coll.getObjects():
        result.append( '/'.join([base_url, path[1:], nm]))
    return result

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
    
def irods_fetch_file(url):
    conn, base_url, basedir, path = irods_conn(url)
    print "irods-path",  path
    localname = irods_cache_fetch(path)
    if localname is None:
        print "fetching"
        f = irods.iRodsOpen(conn, path)
        localname = irods_cache_save(f, path)
        f.close()
    return localname

def irods_push_file(fileobj, url, savelocal=True):
    conn, base_url, basedir, path = irods_conn(url)
    irods.mkCollR(conn, basedir, os.path.dirname(path))
    print "irods-path",  path
    f = irods.iRodsOpen(conn, path, 'w')
    localname = irods_cache_save(fileobj, path, f)
    f.close()
    return localname





    
    
    
    
