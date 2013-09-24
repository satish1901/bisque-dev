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
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)
        self.temptable = []
    
    
    def createtable(self,hash):
        """
            Initializes the Feature table returns the column class
        """ 
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        if self.parameter_info:
            parameterAtom = tables.Atom.from_type(self.parameter_format, shape=(len(self.parameter_info)))
        class Columns(tables.IsDescription):
                idnumber  = tables.StringCol(32,pos=1)
                uri   = tables.StringCol(2000,pos=2)
                if self.parameter_info:
                    parameter = tables.Col.from_atom(parameterAtom, pos=3)
        self.Columns = Columns
        
        #creating table
        file = os.path.join( self.path, hash+'.h5')
        
        with Locks(None, self.path), tables.openFile(file,'a', title=self.name)  as h5file: 
                table = h5file.createTable('/', 'values', Columns, expectedrows=1000000000)
                
                if self.index: #turns on the index
                    table.cols.idnumber.removeIndex()
                    table.cols.idnumber.createIndex()                    
                
                table.flush() 
        return
    
    def indexTable(self,hash):
        """
            information for table to know what to index
        """
        with Locks(None, self.path), tables.openFile(self.path+'_'hash+'.h5','a', title=self.name) as h5file:
            table=h5file.root.values
            table.cols.idnumber.removeIndex()
            table.cols.idnumber.createIndex()    
    

    @Feature.wrapper
    def calculate(self, uri):
        """
            Appends IDs to the table   
        """    
        #initalizing rows for the table
        return [uri]





