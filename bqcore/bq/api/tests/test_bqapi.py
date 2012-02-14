
from lxml import etree
from bqapi import BQSession
from bqapi.bqclass import fromXml, toXml

def test_load ():
    'Check that loading works'

    bq = BQSession()
    x = bq.load ('http://loup.ece.ucsb.edu/ds/images/?limit=10&view=short')
    print "loading /ds/images->", etree.tostring(toXml(x), pretty_print=True)


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

    
