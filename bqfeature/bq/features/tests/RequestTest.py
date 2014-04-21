import nose
import unittest
import numpy as np
import tables
from lxml import etree
import TestGlobals

#test caching and noncaching features make a dumby non caching feature


class RequestBase():
    name = 'Base Request'
    request = ''
    response_code = '200'
    body_check = None
    method = 'GET'
    
    def test_request(self):
        
        #make request
        headers = TestGlobals.SESSION.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        command = TestGlobals.ROOT+self.request

        header, content = TestGlobals.SESSION.c.http.request(self.request, headers = headers, method = self.method)

        #etree_content = etree.XML(content)
        #return debug url if present
        def test_header_response_code():
            assert header['status'] == str(self.response_code) , "%r != %r" % (header['status'], str(self.response_code))
            
#        def test_body_response():
#            if body_check:
#                body_check()
#            else:
#                assert 1

        #running tests
        test_header_response_code.description = 'Test: %s   Check header response code'%(self.name)
        yield test_header_response_code
#        test_header_response_code.description = 'Test: %s   Check body response'%(self.name)
#        yield test_body_response

