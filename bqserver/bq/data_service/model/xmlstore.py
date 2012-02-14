""" Store BQDocument in an XML Simple Store (relation tables)
"""
import logging
from lxml import etree
from itertools import groupby

from bq.core.model import DBSession
from xml_model import Document, query_xpath
#from store import BQStoreBase, BQDocumentBase

log = logging.getLogger('bq.data_service.xmlstore')

class SQLXMLStore (object):
    """Base class for a Bisque Database"""

    driver = "sqlxml"

    def __init__(self, name, **kw):
        driver, dbname = name.split ('://')

    def set_access (self, user):
        """Set the database user for subsequent operations"""
        pass
    def _fetch(self, docid):
        doc = DBSession.query(Document).filter_by(filename=docid).first()
        return doc

    #  Transactions
    #

    def txn_begin(self):
        pass
    def txn_end (self):
        pass

    # Document functions
    def exists(self, docid):
        return self._fetch(docid) != None

    def dir(self):
        return [ x.filename for x in DBSession.query(Document) ]
    
    def create(self, docid=None, xml=None):
        """construct and insert a new document returning
        a unique document id
        """
            
        doc = Document (docid, xml)
        DBSession.add (doc)
        #self.attribute_out(doc)
        log.debug( "FILENAME %s TYPE %s" % (doc.filename, doc.root().tag))
        return doc

    def open(self, docid):
        doc = self._fetch(docid)
        return doc
    def close(self):
        pass

    def update(self, docid):
        doc = self._fetch(docid)
        doc.refresh()
        # This is the first reference to doc.root().element after writing
        #self.attribute_out(doc)
        return doc
        
        
    def delete(self, docid):
        log.info("delete %s" % docid)
        x = DBSession.query(Document).filter_by(filename = docid).one()
        DBSession.delete (x)
        DBSession.flush()

        

    ############################
    # Query functions
    def query_xquery (self, query):
        """query the store for documents containing the query
        """
        
    def query_xpath  (self, query):
        """query the store for documents containing the xpath query
        """
        result = query_xpath (query)
        return result


    def query_tag(self, query, order):
        """execute a tag_query over the database
        tag queries are simple query of the form
        tag:val [AND/OR] t1:v1
        """
        #./tag[@name='t']
        
        

                                 
            
