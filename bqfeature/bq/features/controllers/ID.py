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



class ID(Feature.BaseFeature):
    """
        Initalizes ID table, returns ID, and places ID into the HDF5 table
    """ 
    #initalize parameters
    name = 'IDTable'
    description = 'ID table'
    resource = []
    hash = 2
    cache = True
    index = True
    
    def __init__ (self):
        self.path = os.path.join( FEATURES_TABLES_FILE_DIR, self.name)

    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            
        self.Columns = Columns
        
    def cached_columns(self):
        """
            Columns for the cached tables
        """
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)

        return Columns
        
    def output_feature_columns(self):
        """
            has no relavance to the hash tables for now
        """
        pass

    def output_error_columns(self):
        """
            has no relavance to the hash tables for now
        """
        pass
        




