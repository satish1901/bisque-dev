import sys
import os
import StringIO
import re
import transaction

#from lxml import etree
from lxml import etree as ElementTree
from StringIO import StringIO
from nose.tools import assert_true, assert_equal
from tg import config
from sqlalchemy import and_
from sqlalchemy.orm import lazyload

#from bq.core.tests import TestController, ModelTest, DBTest
from bq.data_service.model.xml_model import (meta,
          Document, _Node, _Attribute, documents, query_xpath)
from bq.core.model import DBSession


xml1 = """
<resource type="image" name="t1.tiff" >
  <tag name="geometry" value="100,100,5" />
  <tag name="t1" type="resource-list" >
     <value type="resource">http://aa.com</value>
  </tag>
</resource>
"""

def setup():
    print "Setup"
    engine = config['pylons.app_globals'].sa_engine 
    meta.create_all(engine)
    for f in (u'test.xml', u'test2.xml', u'test3.xml', u'test5.xml'):
        filename = os.path.join(os.path.dirname(__file__), f)
        print filename
        doc = ElementTree.parse(filename)
        DBSession.add(Document(f, doc))

    print "\nSaving three documents..."
    #DBSession.flush()
    print "Done."

    # clear session (to illustrate a full load), restore
    #DBSession.clear()
    #transaction.commit()

    #print "\nFull text of document 'text.xml':"
    #document = DBSession.query(Document).filter_by(filename="test.xml").first()
    
def teardown():
    print "Teardown"
    DBSession.rollback()
    DBSession.expunge_all()
    engine = config['pylons.app_globals'].sa_engine
    meta.drop_all(engine)
    

class TestResource(object):

    def setup (self):
        pass
    def teardown(self):
        pass
        #assert_true(False)
#    def teardown(self):
#        #assert_true(False)
#        pass
#    def test_save (self):
        # get ElementTree documents

    def test_manual_search(self):
        # manually search for a document which contains "/somefile/header/field1:hi"

        print "\nManual search for /somefile/header/field1=='hi':"
        d = DBSession.query(Document).join('_nodes', aliased=True).filter(and_(_Node.parent_id==None, _Node.tag==u'somefile')).\
            join('children', aliased=True, from_joinpoint=True).filter(_Node.tag==u'header').\
            join('children', aliased=True, from_joinpoint=True).filter(and_(_Node.tag==u'field1', _Node.text==u'hi')).\
            one()
        print d


    def test_find (self):
        for path, compareto in (
            (u'/somefile/header/field1', u'hi'),
            (u'/somefile/field1', u'hi'),
            (u'/somefile/header/field2', u'there'),
            (u'/somefile/header/field2[@attr=foo]', u'there')
            ):
            print "\nDocuments containing '%s=%s':" % (path, compareto)
            print [d.filename for d in query_xpath(path, compareto)]

        
    

        
