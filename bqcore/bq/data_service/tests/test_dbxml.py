
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
from nose.plugins.skip import SkipTest

from tg import config
#from sqlalchemy import and_
#from sqlalchemy.orm import lazyload

#from bq.core.tests import TestController, DBTest
from bq.data_service.model import BQStoreManager

xml1 = '<image x="1" y="2"><tag name="foo" value="bar"/></image>'
man = None
def setup():
    'module test setup '
    global man
    DBNAME = 'dbxml://testdb.dbx'
    drive, name = DBNAME.split ('://')
    print "TEST_DBXML SETUP"
    if os.path.exists (name):
        os.unlink (name)
    man = BQStoreManager.get_manager(DBNAME)
    if man is None:
        raise SkipTest('no dbxml installed')


def teardown():
    #teardown_db()
    man.close()

class TestManager(object):

    def __init__(self):
        print "INIT"

    def test_exists(self):
        """Check that inserted document exists and non-inserted don't
        """
        doc = man.create(xml1)
        assert_true(man.exists(doc.filename))
        assert_false(man.exists("/nothere"))
    
    def test_fetch(self):
        "Check that a fetch return the same document"
        doc = man.create(xml1)
        doc, xml = man.fetch(doc.filename)
        assert_true(xml.tag == 'image')
        #assert_equal(xml1.replace("\n", ''), ET.tostring (xml))
        print "FETCH->", ET.tostring(xml)

    def test_delete(self):
        "ensure that document can be deleted"
        doc = man.create(xml1)
        assert_true(man.exists(doc.filename))
        man.delete(doc.filename)
        assert_false (man.exists(doc.filename))

    def test_xpath(self):
        "xpath expression return documents"
        images = man.query_xpath("/image/tag[@name='foo']")
        print "got %s" % ([d.filename for d in images])
        assert_true(len(images)== 2)

    def test_partial_update(self):
        "partial update change the document"
        print "DOCS = ", man.dir()
        images = man.query_xpath("/image/tag[@name='foo']")
        print images[0]
        xml = ET.XML("<tag name='foo' value='barnone'/>")
        man.update("/image/3/tag/4", xml)
        doc = man.query_xpath("/image/tag[@name='foo']")[0]
        print "XPATH  =>", ET.tostring(doc.root())
        assert_true(doc.root().xpath('/image/tag/@value')[0]=='barnone')


    def test_partial_remove(self):
        "remove a portion of the document"

