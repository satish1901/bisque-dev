""" Store BQDocument in an DB XML 
"""
import os
import logging
from lxml import etree
from itertools import groupby

#from store import BQStoreBase, BQDocumentBase

from bsddb3.db import *
import dbxml


log = logging.getLogger('bq.data_service.xmlstore')

class DBXmlDocument(object):
    def __init__(self,  xml = None, document=None):
        if xml is None:
            xml = document.getContent()

        if isinstance(xml, basestring):
            xml = etree.XML(xml)

        self.element = etree.ElementTree(xml)
        self.document = document
        if document:
            self.filename  = document.getName()
        
    def root(self):
        return self.element.getroot()
    
    def __str__(self):
        return etree.tostring(self.element)


class DBXMLStore (object):
    """Base class for a Bisque Database"""
    driver = "dbxml"

    def __init__(self, name, folder = 'dbxml', **kw):
        self.env = DBEnv()
        self.env.set_cachesize (2,0,1)
        folder = os.path.abspath(folder)
        self.env.open(folder, DB_INIT_LOCK|DB_CREATE| DB_RECOVER|
                      DB_THREAD| DB_INIT_MPOOL|DB_INIT_TXN,
                      #DB_INIT_LOG
                      0)

        self.mgr =  dbxml.XmlManager(self.env, 0)
        driver, dbname = name.split ('://')
        full = os.path.join (folder, dbname)
        if not os.path.exists(full):
            log.info ("creating %s" % name)
            self.container = self.mgr.createContainer(dbname)
        else:
            log.info ("opening %s" % name) 
            self.container = self.mgr.openContainer(dbname)
        self.session = {}
        self.container_name = dbname

    def close(self):
        del self.container
        

    def set_access (self, user):
        """Set the database user for subsequent operations"""
        pass
    def _fetch(self, docid):
        if docid in self.session:
            return self.session[docid]
        try:
            document = self.container.getDocument(docid)
            document =  DBXmlDocument(document = document)
            self.session[docid] = document
        except dbxml.XmlDocumentNotFound:
            return None
        return document

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
        return [x.asDocument().getName()
                for x in self.container.getAllDocuments(0)]

    def create(self, docid=None, xml=None):
        """construct and insert a new document returning a unique
        document id
        """
        doc = DBXmlDocument(xml = xml)
        if docid is None:
            docid = doc.root().get('uri')
        log.debug( "XML=>%s %s" % (docid, etree.tostring(xml)))
        uc = self.mgr.createUpdateContext()
        self.container.putDocument(docid, str(doc), uc)
        del uc
        return self._fetch(docid)

    def open(self, docid):
        doc = self._fetch(docid)
        return doc

    def update(self, docid):
        doc = self.session[docid]
        if doc:
            uc = self.mgr.createUpdateContext()
            doc.document.setContent( str(doc) )
            self.container.updateDocument(doc.document, uc)
        return doc
        
        
    def delete(self, docid):
        log.info("delete %s" % docid)
        doc = self._fetch(docid)
        uc = self.mgr.createUpdateContext()
        self.container.deleteDocument(doc.document, uc)
        del uc
        del self.session[docid]
        


    ############################
    # Query functions
    def query_xquery (self, query):
        """query the store for documents containing the query
        """
        qc = self.mgr.createQueryContext()
        results = self.mgr.query(query, qc)
        results  =[ self._fetch(x.asDocument().getName()) for x in results]
        log.debug ("xquery: %s -> %s" % (query, results) )
        return results
        
        
    def query_xpath  (self, query):
        """query the store for documents containing the xpath query
        """
        xquery = "collection('%s')%s" % (self.container_name,query)
        return self.query_xquery(xquery)


    def query_tag(self, query, order):
        """execute a tag_query over the database
        tag queries are simple query of the form
        tag:val [AND/OR] t1:v1
        """
        #./tag[@name='t']
        
        
