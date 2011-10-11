
import webob
from bq.config.middleware import bisque_app
from bq.util import http
from urlparse import urlparse


import logging

log = logging.getLogger('bq.core')

from paste.proxy import make_proxy
from pylons.controllers.util import abort
from tg import  config

proxy = make_proxy(config, 'http://loup.ece.ucsb.edu:9090')

class Request(object):

    def __init__(self,url):
        self.url = url
    def get(self):
        'route the rquest locally if possible'

        req = webob.Request.blank(self.url)
        response = req.get_response(proxy)
        
        if response.status_int == 200:
            return response.body
    
        log.info ('ReMOTE %s' % self.url)
        return ''


    
    
    
