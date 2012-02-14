
import os
import logging
from lxml import etree as ET
from bq.core.tests import TestController, teardown_db, DBSession

log = logging.getLogger('bq.test.doc_resource')

xml1 = '<image x="1" y="2"><tag name="foo" value="bar"/></image>'
DS = "/data_service/doc"

#def teardown():
#    DBSession.rollback()
#    teardown_db()

class TestDocController(TestController):
    application_under_test = 'main'

    def test_a_new(self):
        "new --> create a new document"
        response = self.app.post (DS, params=xml1, content_type="text/xml")
        assert response.status == '200 OK'
        assert 'image' in response.lxml.get('uri')

    def test_b_fetch(self):
        "Fetch a created document"
        response = self.app.post (DS, params=xml1, content_type="text/xml")
        #print "post-> %s" % response.body
        uri = response.lxml.get('uri')
        response = self.app.get (DS + uri)
        #print ('fetch -> %s' % response.body)
        assert response.status == '200 OK'
        assert 'image' in response.lxml.get('uri')
        

    def test_c_fetch_replace(self):
        "Replace a document"
        response = self.app.post (DS, params=xml1, content_type="text/xml")
        uri = response.lxml.get('uri')
        response = self.app.get (DS + uri)
        assert response.status == '200 OK'
        tag = response.lxml.xpath('./tag')[0]
        tag.set('value', 'barnone')
        response = self.app.put (DS + tag.get('uri'), ET.tostring(tag),
                                 content_type="text/xml")
        print response.body
        assert 'barnone' == response.lxml.get('value')
        

    def test_d_fetch_partial(self):
        "Fetch partial document"

    
