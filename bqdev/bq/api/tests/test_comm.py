

from bqapi import BQSession
from bqapi.util import  fetch_dataset


def test_fetch_dataset():
    'check that you can place a dataset locally'

    bq = BQSession().init_local('kgk', 'Al1brary')
    dsdir = bq.load('http://loup.ece.ucsb.edu/ds/datasets')
    ds1 = dsdir.kids[0]
    print "FOUND ", ds1.uri
    #fetch_dataset(bq, ds1.uri, ".")

    fetch_dataset(bq, ds1.uri, ".", uselocalpath=True)

    
    
