
from lxml import etree
from bqapi import BQSession
from bqapi.bqclass import BQFactory
from tg import config

def test_load ():
    'Check that loading works'

    host = config.get ('host.root')
    user = config.get ('host.user')
    passwd = config.get ('host.password')
    bq = BQSession()
    bq.init_local (user, passwd, bisque_root = host, create_mex = False)
    x = bq.load ('/data_service/image/?limit=10')
    print "loading /data_service/images->", BQFactory.to_string((x))


def test_load_pixels():
    'check that you can load pixels from an image'
    bq = BQSession()
    x = bq.load ('http://loup.ece.ucsb.edu/ds/images/?limit=10&view=short')

    i0 = x.kids[0]

    pixels = i0.pixels().slice(t=0).fetch()
    f = open('/tmp/image','wb')
    f.write(pixels)
    f.close
    print len(pixels)
