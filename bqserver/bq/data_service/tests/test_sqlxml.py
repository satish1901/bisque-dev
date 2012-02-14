
import sys
import os
import StringIO
import re
import transaction

#from lxml import etree
from lxml import etree as ET
from StringIO import StringIO
from nose import with_setup
from nose.tools import assert_true, assert_equal, assert_false
from tg import config
from sqlalchemy import and_
from sqlalchemy.orm import lazyload

from bq.core.tests import TestController, DBTest, teardown_db, setup_db
from bq.data_service.model  import BQStoreManager


xml1 = '<image x="1" y="2"><tag name="foo" value="bar"/></image>'

man = None
def setup():
    'setup test'
    #init_db()
    setup_db()
    global man
    man = BQStoreManager.get_manager("sqlxml://ignored")
    


def teardown():
    teardown_db()
    man.close()

class TestManager(object):

    def __init__(self):
        print "INIT"

    def fill(self):
        man.create("/A", xml1)
    def empty(self):
        man.delete("/A")

    def test_a_exists(self):
        """Check that inserted document exists and non-inserted don't
        """
        doc = man.create(xml1)
        assert_true(man.exists(doc.filename))
        assert_false(man.exists("/nothere"))
    
    def test_b_fetch(self):
        "Check that a fetch return the same document"
        doc = man.create(xml1)
        doc, xml = man.fetch(doc.filename)
        assert_true(xml.tag == 'image')
        #assert_equal(xml1.replace("\n", ''), ET.tostring (xml))
        print "FETCH->", ET.tostring(xml)

    @with_setup(fill,empty)
    def test_c_delete(self):
        "ensure that document can be deleted"
        doc = man.create(xml1)
        assert_true(man.exists(doc.filename))
        man.delete(doc.filename)
        assert_false (man.exists(doc.filename))

    def test_d_xpath(self):
        "xpath expression return documents"
        doc = man.create(xml1)
        doc = man.create(xml1)
        images = man.query_xpath("/image/tag[@name=foo]")
        print "got %s" % ([d.filename for d in images])
        assert_true(len(images)== 4)

    def test_e_partial_update(self):
        "partial update change the document"
        
        doc = man.create(xml1)
        print "DOCS = ", man.dir()
        images = man.query_xpath("/image/tag[@name=foo]")
        print "XPATH", images
        uri = images[0].root().xpath('/image/tag/@uri')[0]
        xml = ET.XML("<tag name='foo' value='barnone'/>")
        print "updating %s with %s" % (uri, ET.tostring(xml))
        man.update(uri, xml)
        docs = man.query_xpath("/image/tag[@name=foo]")
        print "GOT tags=",docs
        print ET.tostring(docs[0].root())
        assert docs[0].root().xpath('./tag')[0].get('value')=='barnone'


    def test_f_partial_remove(self):
        "remove a portion of the document"

