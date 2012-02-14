""" Base module for BQ Storage.

A BQStore is any system capable of storing XML documents and quering
them.  This base class is used to abstract differences between
relations and pure XML storage systems.

The BQStoreManager determines what constitutes a document in the
store.  For example are all images stored in a single document (not likely).

"""
import logging
try:
    from lxml import etree as ET
except:
    from xml.etree import ElementTree as ET

try:
    from bq.data_service.model.xmlstore import SQLXMLStore
    STORES = [ SQLXMLStore ]
    from bq.data_service.model.dbxmlstore import DBXMLStore
    STORES.append (DBXMLStore)
except ImportError:
    pass
except:
    pass

__module__    = "bqstore"
__author__    = "Kris Kvilekval"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


log = logging.getLogger('bq.data_service.store')

class StoreError(Exception):
    pass

class BQDocumentBase(object):
    """Base class for derived Document classes implemented by
    the actual XML storage driver
    """
    def root(self):
        """Return the root element of the document as an ElementTree
        """
        return None

def  get_unique_code():
    for x in xrange(1000000):
        yield x



def make_et(xml):
    if isinstance(xml, basestring):
        xml = ET.XML(xml)
        #self.attribute_in(doc, xml, mex = "/mex/yyy")
    return xml

def index(seq, f):
    """Return the index of the first item in seq where f(item) == True."""
    return next((i for i in xrange(len(seq)) if f(seq[i])), None)

def find(seq, f):
    """Return first item in sequence where f(item) == True."""
    for it in (item for item in seq if f(item)):
        return it



class BQStoreBase (object):
    """Base class for a Bisque Storage."""
    #  Transactions
    #
    def _txn_begin(self):
        pass
    def _txn_end (self):
        pass
    def set_access (self, user):
        """Set the database user for subsequent operations"""
        pass
    def close(self):
        "Close the store"
        
    # Document functions
    def exists (self, path):
        return False
    def create(self, path, xml):
        """construct and insert a new document returning a unique
        document id
        """
        return None
    def exists(self, path):
        """Check if the path exists as a document in the store"""
        return False
    def open(self, path):
        """Return the document designated by path """
        return None
    def update(self, path):
        """Update the contents of path"""
        pass
    def delete(path):
        """Delete the document at path"""

    ############################
    # Query functions
    def xquery (self, query):
        pass
    def xpath  (self, query):
        pass
    def tag_query(self, query):
        pass


class BQStoreManager (object):
    """Manage the granularity of the document store

    The StoreManager maps paths to document, subdocuments
    and XML fragements.


    Example:
       image = manager.new ("/images", "<image name='test.fig'>")
       <image id="/images/1" name="test.fig" />
       gob = manager.new("/images/1", "<gobject name='gob1'>...</gobject>")
       <gobject id="/images/1/gobjects/2" name="gob1">... </gobject>

       manager.isdocument(image)
       True
       manager.isdocument(gob)
       False

       gob = manager.put ("/image/1/gobjects/2", "<gobject name='HUGE'>...</gobject>")
       manager.isdocument(gob)
       True
       manager.descendents (image)
       [ <Document> ] 
    """

    stores = {}
    
    @classmethod
    def get_manager(cls, dburl):
        if not cls.stores.has_key(dburl):
            driver_name, dbname = dburl.split('://')
            drive_cls = find(STORES, lambda x: x.driver == driver_name)
            if drive_cls is not None:
                driver = drive_cls(dburl)
                cls.stores[dburl] =  BQStoreManager(driver)
                log.info ("CREATING MANAGER %s" %(dburl))
            else:
                log.error ('NO Driver for db %s' % dburl)
                return None
        return cls.stores[dburl]

    def __init__(self, store):
        self.store = store
        self.unique_code = get_unique_code()
        self.unique_code.next()

    def close(self):
        self.store.close()
        #del self.manager

    def _xpath_expr(self, docid, partial):
        """convert path to an xpath express for a portion of the document

        document -> /images/1
        path     -> /images/1/gobjects/10

        return "./gobjects/*[@id='/images/1/gobjects/10']"
        """
        return "*[@uri='%s%s']" % (docid, partial)

    def find_document(self, path):
        """Find the closest document specified by the path

        return: document_path, sub-path
        """
        original_path = path
        parts = path.split('/')

        while True:
            if self.store.exists (path):
                return path, original_path[len(path):]
            if len(parts)==0:
                break
            parts.pop()
            path = '/'.join(parts)
        return None, original_path

    def _get (self, docid, path=None):
        doc = self.store.open(docid)
        root = doc.root()
        self.attribute_out(root)
        if path:
            root = root.xpath(self._xpath_expr(docid, path))
        #self.store.close(doc)
        return doc, root

    def _set (self, docid, xml, path=None):
        doc = self.store.open(docid)
        root = doc.root()
        if path:
            
            xpr = self._xpath_expr(docid, path)
            print "XPATH=", xpr
            element = root.xpath(xpr)
            print "XPATH EL", element
            element =  len(element) and element[0]
            parent =  element.getparent()
            if parent is not None:
                parent.replace (element, xml)
            else:
                root = xml
        self.attribute_in (root)
        self.store.update(docid)
        return doc, xml

    ##
    def exists(self,path):
        docid, partial = self.find_document(path)
        return docid != None

    def dir(self):
        return self.store.dir()
        
        
    def create(self, xml=None ):
        """Create a new resource

        Create a new resource by adding it to an existing document 
        or creating  a new document
        """
        xml = make_et(xml)
        self.attribute_in (root=xml, mex="/ds/mex/new")
        docid = xml.get('uri')
        doc =  self.store.create(docid, xml)
        return doc

    def fetch(self, path):
        docid, partial = self.find_document(path)
        doc, element =  self._get(docid, path=partial)
        return doc, element
        

    def update (self, path, xml):
        """Replace the resource
        """
        xml = make_et(xml)
        docid, partial = self.find_document(path)
        if docid is None:
            raise StoreError('no such document %s' %path)
        print  "Update %s %s with %s" % (docid, partial, ET.tostring(xml))
        doc, element = self._set(docid, xml, path = partial)
        return doc, element
        
    def delete (self, path):
        """Delete the resource
        """
        docid, partial = self.find_document(path)
        if not partial :
            self.store.delete (docid)
            return
        #self._set (docid, None, path = partial)
    ##
    def query_xpath  (self, query):
        """query the store for documents containing the xpath query
        """
        docs = self.store.query_xpath (query)
        return docs

    def query_tag(self, query, order):
        """Perform tag_query
        """
        docs = sefls.store.query_tag(query, order)

    
    ############################
    ## hidden functions for attribute access
    def attribute_in(self, root, **kw):
        """Add default attributed to document based on context
        mex
        owner
        perm
        ts
        resource_type
        """
        stack = [ root ]
        while len(stack):
            node = stack.pop()
            if not node.attrib.has_key('uri'):
                node.attrib['uri'] = self.unique_id(node)
            for key, val in kw.items():
                node.attrib[key] = val
            for kid in node:
                stack.append(kid)
        

    def attribute_out(self, root=None):
        """Set attributes need before delivering the document

        uri
        """
        tag_map = { 'tag':'tags',
                    'image' : 'images',
                    'gobject' : 'gobjects',
                    'point' : 'gobjects',
                    'polygon' : 'gobjects',
                    }


#         stack = [(root, '')]
#         while len(stack):
#             n, uri = stack.pop()
#             uri  = "%s/%s/%s" % (uri,
#                                  tag_map.get(n.tag,'resource'),
#                                  doc.element_ids[n])
#             n.attrib['uri'] = uri
#             for k in n:
#                 stack.append( (k, uri) )
        
    def unique_id(self, node):
        "Create a unique id for this node in the tree"
        parent = node.getparent()
        parenturi = parent is not None and parent.attrib['uri'] or ''
        uri  = u"%s/%s/%s" % (parenturi, node.tag, self.unique_code.next())
        return uri
                                 
            

