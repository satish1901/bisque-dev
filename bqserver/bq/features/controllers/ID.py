# -*- mode: python -*-
""" Base Feature library
"""

import os
import tables
import bq
import random
import numpy as np
import uuid
import logging
log = logging.getLogger("bq.features")

from bq.image_service.controllers.locks import Locks
from pylons.controllers.util import abort
from bq.util.paths import data_path

from .var import FEATURES_TABLES_FILE_DIR
import Feature


class ID():
    """
        Initalizes ID table, returns ID, and places ID into the HDF5 table
    """ 
    #initalize parameters
    name = 'IDTable'
    description = 'ID table'
    hash = 2
    index = True
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)
        self.columns()

    def localfile(self,hash):
        return os.path.join( self.path, hash[:self.hash]+'.h5')    

    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            
        self.Columns = Columns
                
    def createtable(self,filename):
        """
            Initializes the Feature table returns the column class
        """ 
        
        #creating table
        with Locks(None, filename):
            with tables.openFile(filename,'a', title=self.name)  as h5file: 
                table = h5file.createTable('/', 'values', self.Columns, expectedrows=1000000000)

                if self.index: #turns on the index
                    table.cols.idnumber.removeIndex()
                    table.cols.idnumber.createIndex()                    

                table.flush()
            
            vlarray = h5file.create_vlarray(h5file.root, 'URI',
                                            tables.StringAtom(itemsize=2000),
                                            filters=tables.Filters(1))
            vlarray.flavor = 'python'
            
        return

    
#    def indexTable(self,hash):
#        """
#            information for table to know what to index
#        """
#        file = os.path.join( self.path, hash+'.h5')
#        with Locks(None, self.path), tables.openFile(self.localfile(hash),'a', title=self.name) as h5file:
#            table=h5file.root.values
#            table.cols.idnumber.removeIndex()
#            table.cols.idnumber.createIndex()
#    




