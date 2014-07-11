"""
Handles tables for the feature server
"""
#python imports
import os
import time
import tables
import logging
import Queue
import numexpr
numexpr.set_num_threads(1) #make numexpr thread-safe

LOCKING_DELAY = .5 #secs

#bisque imports
from bq.image_service.controllers.locks import Locks
from bq.util.mkdir import _mkdir

#fs imports
from PytablesMonkeyPatch import pytables_fix
from exceptions import FeatureExtractionError, FeatureServiceError, FeatureExtractionError, InvalidResourceError
from .var import FEATURES_TABLES_FILE_DIR, EXTRACTOR_DIR, FEATURES_TABLES_WORK_DIR, FEATURES_REQUEST_ERRORS_DIR
from ID import ID

log = logging.getLogger("bq.features")



class QueryQueue(object):
    """
        Generates a queue of querys to be requested on
        the tables at once. 
    """
    def __init__(self,table_module):
        self.query_queue = {}
        self.table_module = table_module
        
        
    def push(self, hash):
        """
            
        """
        path = self.table_module.localfile(hash)
        if path in self.query_queue:  # checking the first few element on the hash
            self.query_queue[path].put(hash)  # place the output in the queue
        else:
            self.query_queue[path] = Queue.Queue()  # build queue since none were found
            self.query_queue[path].put(hash)
        
        return True


    def keys(self):
        """
        
        """
        return self.query_queue.keys()
    
    
    def __getitem__(self, key):
        """
        """
        return self.query_queue[key]
    

class Rows(object):
    """
        Generates rows to be placed into the tables
    """
    def __init__(self, table_module):
        self.table_queue = {}
        self.table_module = table_module


    def push(self, **resource):
        """
            creates a list to append to the feature table
            if feature calculation was a success return true
            otherwise return false
        """
        try:
            log.debug('Calculate Feature')
            output = self.table_module.calculate(resource)  # finds the feature
            path = self.table_module.localfile(output[0][0]) #reads the hash of the first elemenet since all the elements should have the same hash
            if path in self.table_queue:  # checking the first few element on the hash
                self.table_queue[path].put(output)  # place the output in the queue
            else:
                self.table_queue[path] = Queue.Queue()  # build queue since none were found
                self.table_queue[path].put(output)

            return True

        except InvalidResourceError as e:
            raise FeatureExtractionError( resource, e.code, e.message)

        except StandardError, err:
            # creating a list of uri were the error occured
            resource_string = ''
            for r in resource.keys():
                resource_string += r + ' : ' + resource[r] + ', '
            else:
                resource_string = resource_string[:-2]            
            log.exception('Calculation Error: URI:%s  %s Feature failed to be calculated' % (resource_string, self.table_module.name))
            raise FeatureExtractionError( resource, 500, 'Internal Server Error: Feature failed to be calculated')
            return False


class IDRows(Rows):
    """
        Generates rows to be placed into the ID tables
    """
    def __init__(self, table_module):
        self.table_queue = {}
        self.init_id = ID()
        self.table_module = table_module
    
    def push(self, **resource):
        """
            creates the rows to store urls with there ids in the idtable
        """
        log.debug('Calculated Hash')
        hash = self.table_module.returnhash(**resource)  # get hash from features
        path = self.init_id.localfile(hash)
        output = [hash]
        for r in self.table_module.resource:
            output += [r + '=' + resource[r]]  # append the uris
        if self.init_id.localfile(hash) in self.table_queue:  # checking the first few element on the hash
            self.table_queue[path].put(output)  # place the output in the queue
        else:
            self.table_queue[path] = Queue.Queue()  # build queue since none were found
            self.table_queue[path].put(output)

        return True


class WorkDirRows(Rows):
    """
        Generates rows to be placed into the uncached tables
    """
    def push(self, **resource):
        """
            creates a list to append to the feature table
            if feature calculation was a successs return true
            otherwise return false
        """
        try:
            log.debug('Calculate Feature')
            output = self.table_module.calculate(resource)
            if 'feature' in self.table_queue:  # feature is used to maintain the structure
                self.table_queue['feature'].put(output)  # the row is pushed into the queue
            else:  # creates a queue if no queue is found
                self.table_queue['feature'] = Queue.Queue()
                self.table_queue['feature'].put(output)

            return True

        except InvalidResourceError as e:
            raise FeatureExtractionError( resource, e.code, e.message)

        except StandardError, err:
            # creating a list of uri were the error occured
            resource_string = ''
            for r in resource.keys():
                resource_string += r + ' : ' + resource[r] + ', '
            else:
                resource_string = resource_string[:-2]
            
            log.exception('Calculation Error: %s  %s feature failed to be calculated' % (resource_string, self.feature.name))
            raise FeatureExtractionError(resource,500,'Calculation Error: Feature failed to be calculated')

            return False


class Tables(object):
    """
        Creates table to store features
    """
    def __init__(self, init_feature):
        """
            Requires a Feature Class to intialize. Will search for table in the
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.init_feature = init_feature
        _mkdir(self.init_feature.path)  # creates a table dir if it cannot find one
        
        self.table_parameters = []
        self.table_parameters.append(('values',self.init_feature.cached_columns(),['idnumber']))      
            

    def get_path(self):
        """
        """
        return self.init_feature.path

    def init_h5(self,filename,table_parameters, func=None):
        """
            Must be placed within a lock
        """
        try:
            with tables.openFile(filename,'w')  as h5file:
                for (table_name, columns, indexed) in table_parameters:
                    table = h5file.createTable('/', table_name, columns, expectedrows=1000000000)
                    for col_name in indexed:
                        column = getattr(table.cols,col_name)
                        column.removeIndex()
                        column.createIndex()
                    table.flush()
                    
                if func:
                    func(h5file)        
        
        except tables.exceptions.HDF5ExtError:
            log.debug('Failed to find table %s'%filename)
            #raise FeatureServiceError()
         
        
    def write_to_table(self,filename, table_parameters, func=None):
        """
            Initalizes a table in the file
            
            @filename - name of the file
            @table_parameters - takes a list of [(tablename, columns, [list of columns to index])]  
            @func - function accepting a h5 tabel object
            
            @returns none
        """
        with Locks( None, filename, failonexist = True) as l:
            if not l.locked:
                log.debug('Already initialized h5 table path: %s'%filename)
                return #tables was made already
            self.init_h5(filename,self.table_parameters,func=func)
            log.debug('Initialized h5 table path: %s'%filename)
            return

    def read_from_table(self, filename, func):
        """
            Read from the table 
            @func - function excepting a h5 table object
            
            @return index
        """
        if not os.path.exists(filename):
            self.create_h5_file(filename)
        
        while 1:
            with Locks(filename) as l: 
                if not l.locked: #tries to lock the table again
                    time.sleep(LOCKING_DELAY)
                    log.debug('Table was not locked: %s attempting to relock the table after %s sec.'%(filename,LOCKING_DELAY))
                    continue
                    
                log.debug('Reading from table path: %s'%filename)
                try:
                    with tables.openFile(filename, 'r') as h5file:
                        return func(h5file)
                    
                except tables.exceptions.HDF5ExtError:
                    log.debug('Failed to find table %s'%filename)
                    return None
                    #raise FeatureServiceError()
                

    def append_to_table(self, filename, func):
        """
            Appends rows to the table
            @func - pass a function to append to the table
            
            @return - none
        """
        if not os.path.exists(filename):
            self.create_h5_file(filename)
            
        while 1: 
            with Locks(None, filename, mode="ab") as l:
                
                if not l.locked:
                    time.sleep(LOCKING_DELAY)
                    log.debug('Table was not locked: %s attempting to relock the table after %s sec.'%(filename,LOCKING_DELAY))
                    continue      
                
                log.debug('Appending to table path: %s'%filename)
                try:
                    with tables.openFile(filename, 'a') as h5file:
                        return func(h5file)
                    
                except tables.exceptions.HDF5ExtError:
                    log.debug('Failed to find table %s'%filename)
                    return
                    #raise FeatureServiceError()

    
    def create_h5_file(self, filename, func = None):
        """
            creates hdf5 table with index on column id
        """
        self.write_to_table(filename, self.table_parameters, func)


    def find(self, query_queue):
        """
            checks to see if anything is stored in the table under
            the query
            
            @query_queue - list of hashes to query the table
            
            @return - generator([bool(if the query was found),hash],..)
        """
        for filename in query_queue.keys():
            log.debug('filename: %s'%filename)
            def func(h5file):
                query_results = []
                table = h5file.root.values
                  
                while not query_queue[filename].empty():
                    hash = query_queue[filename].get()
                    query = 'idnumber=="%s"' % str(hash)
                    #log.debug('Find: query -> %s'%query)
                    
                    try:
                        table.where(query).next() #if the list contains one element
                        query_results.append((True,hash))
                        log.debug('Find: query: %s -> Found!'%query)
                    except StopIteration: #fails to get next
                        query_results.append((False,hash))
                        log.debug('Find: query: %s -> Not Found!'%query)
                
                return query_results
                    
            yield self.read_from_table(filename,func)


    def store(self, row_genorator):
        """
            store elements to tables
        """
        for filename in row_genorator.table_queue.keys():
            queue = row_genorator.table_queue[filename]

            def func(h5file):
                table = h5file.root.values
                while not queue.empty():
                    row = queue.get()
                    query = 'idnumber=="%s"' % str(row[0][0])  # queries the hash to see if a feature has been already added
                    #log.debug('Query table -> %s'%query)
                    try:
                        table.where(query).next() #if the list contains one element
                        log.debug('Skipping %s - already found in table'%str(row[0][0]))   
                                   
                    except StopIteration: #fails to get next
                        log.debug('Appending %s to table'%str(row[0][0]))
                        for r in row:
                            table.append([r])                  

                table.flush()
                
            self.append_to_table(filename,func)
            
        return 


    def get(self, query_queue):
        """
            query for elements and return results
        """
        for filename in query_queue.keys():

            def func(h5file):
                query_results = []
                table = h5file.root.values
                  
                while not query_queue[filename].empty():
                    hash = query_queue[filename].get()
                    query = 'idnumber=="%s"' % str(hash)
                    log.debug('Find: query -> %s'%query)
                    
                    index = table.getWhereList(query)
                    
                    if index.size == 0:
                        query_results.append((None,hash))
                    else:
                        query_results.append((table[index],hash))
                
                return query_results
                    
            yield self.read_from_table(filename,func)
                        

    def copy(self):
        pass


    def remove(self):
        """
            remove rows
        """
        pass


    def delete(self):
        """
            delete tables
        """
        pass


    def __len__(self):
        """
            opens each table in a particular feature directory and sums up the length of all the features
            (note: take a noticable amount of time)
        """
        import glob
        feature_tables = glob.glob(os.path.join(self.init_feature.path, '*.h5'))
        log.debug('feature table list %s' % str(os.path.join(self.init_feature.path, '*.h5')))
        l = 0
        for filename in feature_tables:
            with Locks(filename):
                with tables.openFile(filename, 'r') as h5file:
                    l += len(h5file.root.values)
        return l


class IDTables(Tables):
    """
        a subclass of tables but operates only on the ID table
    """

    def __init__(self):
        """
            Requires a Feature Class to intialize. Will search for table in the
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.init_ID = ID()
        _mkdir(self.init_ID.path)  # creates a table dir if it cannot find one
        self.table_parameters = []
        self.table_parameters.append(('values',self.init_ID.cached_columns(),['idnumber'])) 


    def get_path(self):
        """
        """
        return
    

    def init_h5(self,filename,table_parameters, func=None):
        """
            Must be placed within a lock
        """
        with tables.openFile(filename,'w')  as h5file:
            for (table_name, columns, indexed) in table_parameters:
                table = h5file.createTable('/', table_name, columns, expectedrows=1000000000)
                for col_name in indexed:
                    column = getattr(table.cols,col_name)
                    column.removeIndex()
                    column.createIndex()

            vlarray = h5file.create_vlarray(h5file.root, 'URI',
                                tables.StringAtom(itemsize=2000),
                                filters=tables.Filters(1))
            vlarray.flavor = 'python'
            table.flush()
                
            if func:
                func(h5file)
        

        self.write_to_table(filename, self.table_parameters,func=func)


    def store(self, rowgenorator):
        """
            store elements to tables
        """
        for filename in rowgenorator.table_queue.keys():
            queue = rowgenorator.table_queue[filename]
            
            def func(h5file):
                table = h5file.root.values
                url_vlarray = h5file.root.URI  #finding the variable length array
                while not queue.empty():
                    row = queue.get()
                    query = 'idnumber=="%s"' % str(row[0])  # queries the hash to see if a feature has been appended already
                    index = table.getWhereList(query)
                    if len(index) == 0:
                        table.append((row[0]))
                        url_vlarray.append(row[1:])
                
                table.flush()
                
            self.append_to_table(filename,func)
        return

    def get(self, hash):
        pass


class WorkDirTable(Tables):
    """
    Places a table into the workdir without index
    """

    def __init__(self, init_feature):
        """
            Requires a Feature Class to intialize. Will search for table in the
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.init_feature = init_feature
        self.path = os.path.join(FEATURES_TABLES_WORK_DIR, self.init_feature.name)
        _mkdir(self.path) # creates a table dir if it cannot find one
        
        self.table_parameters = []
        self.table_parameters.append(('values',self.init_feature.output_feature_columns(),[]))
            
    def get_path(self):
        """
        """
        return

    def store(self, rowgenorator, filename):
        """
            store row elements to an output table
        """
        queue = rowgenorator.table_queue['feature']

        if not os.path.exists(filename):
            log.debug('Writing hdf file into workdir: %s'%filename)
            self.create_output_h5(filename)  # creates the table
        else:
            raise FeatureServiceError( 500,'File already exists in workdir: %s'%filename)


        # appends elements to the table        
        def func(h5file):
            table = h5file.root.values
            while not queue.empty():
                table.append(queue.get())
            table.flush()
            

        self.append_to_table(filename,func)
        
        return

    def find(self, hash):
        pass

    def get(self, hash):
        pass

    def __len__(self):
        pass
