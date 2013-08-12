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

class ID():
    """
        Initalizes ID table, returns ID, and places ID into the HDF5 table
    """ 
    #initalize parameters
    file = 'IDTable.h5'
    name = 'IDTable'
    ObjectType = 'ID'
    description = 'ID table'
    temptable = []
    #contents = ''
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.file)
    
    def initalizeTable(self):
        """
            Initializes the ID table
        """ 
        class Columns(tables.IsDescription):
                idnumber  = tables.StringCol(32)
                uri   = tables.StringCol(2000)
        self.Columns=Columns
        
        
    def indexTable(self,table):
        """
            information for table to know what to index
        """
        table.cols.idnumber.createCSIndex()
        
    def appendTable(self, uri, id):
        """
            Appends IDs to the table   
        """    
        #initalizing rows for the table
        self.setRow(id,uri)

    #re-adapted for id-table since its structure is not like the feature tables
    def setRow(self, idnumber, uri):
        """
            allocate data to be added to the h5 tables
            
            Each entry will append a row to the data structure until data
            is dumped into the h5 tables after which data structure is reset.
        """
        self.temptable = [];
        temprow = {'uri':uri,'idnumber':idnumber}
        self.temptable.append(temprow)





