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
    return "00-%s" % shortuuid.uuid()



def make_uniq_code (version = 0, length=40):
    return "00-%s" % shortuuid.uuid()


def is_uniq_code(uniq, version = None):
    """Check that the code is a bisque uniq code

    @param uniq: The uniq code
    @param version: Test for a particular version:
    @return:  The version of the code or None
    """
    return uniq.startswith('00-') or None



