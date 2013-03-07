import hashlib
import datetime
import random
import shortuuid

def make_uniq_hash(filename, dt = None):
    rand_str = str(random.randint(1, 1000000))
    rand_str = filename.encode('utf-8') + rand_str + str( (dt or datetime.datetime.now()).isoformat()) 
    rand_hash = hashlib.sha1(rand_str).hexdigest()
    return rand_hash



def make_short_uuid (filename=None, dt=None):
    return shortuuid.uuid()
