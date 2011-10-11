import shutil
import os

def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        #print "_mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)



class BQXmlFile(BQDocumentBase):
    def __init__(self, path):
        self.path = "/".join(path) + "/index.xml"
    def read(self):
        return open(self.path).read()
    def write(self, xml):
        open(self.path,'w').write (xml)
    def root(self):
        return ElementTree.parse (self.path)

        
class BQFileStore (BQStoreBase):
    def __init__(self, top):
        self.top = top

    def set_access (self, user):
        """Set the database user for subsequent operations"""
        pass

    #  Transactions
    #

    def txn_begin(self):
        pass
    def txn_end (self):
        pass

    def make_path(self, path):
        local_path = "/".join(path)
        _mkdir (local_path)
    # Document functions
    def new_document(self, path, xml):
        """construct and insert a new document returning
        a unique document id
        """
        doc = open(path).write (xml)
        return doc
    def exists(self, path):
        """Check if the path exists as a document in the store"""
        return os.path.exists(path)
    def open_document(self, path):
        """Return the document designated by path """
        return  BQXmlFile(path)
    def update_document(self, path, xml):
        """Update the contents of path"""
        
    def delete_document(path):
        """Delete the document at path"""

    ############################
    # Query functions
    def xquery (self, query):
        pass
    def xpath  (self, query):
        pass
    def tag_query(self, query):
        pass
        
