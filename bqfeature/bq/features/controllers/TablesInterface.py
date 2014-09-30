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
import threading
import gc
import uuid
from collections import namedtuple
import numpy as np
numexpr.set_num_threads(1) #make numexpr thread-safe

LOCKING_DELAY = .5 #secs
FAILED_LOCK_ATTEMPTS = 10


if os.name == 'nt':
    MULTITHREAD_HDF5 = False #will lock every type hdf5 is used
else:
    MULTITHREAD_HDF5 = True
#HDF5_Global_Lock = threading.Lock() get it to run just blocking threads

#bisque imports
from bq.image_service.controllers.locks import Locks
#from bq.util.locks import Locks
from bq.util.mkdir import _mkdir

#fs imports
from PytablesMonkeyPatch import pytables_fix
from exceptions import FeatureExtractionError, FeatureServiceError, FeatureExtractionError, InvalidResourceError
from .var import FEATURES_TABLES_FILE_DIR, EXTRACTOR_DIR, FEATURES_WORK_DIR, FEATURES_REQUEST_ERRORS_DIR
from ID import ID

log = logging.getLogger("bq.features.TablesInterface")


class TablesLock(object):
    """
        Provides locks for hdf5 files
    """
    def __init__(self, filename, mode='w', failonexist=False, *args, **kwargs):
        """
            Opens hdf5 files providing read/write locks for
            thread safety.
            
            If libHDF5 is not configured for thread safety please
            set MULTITHREAD_HDF5 to False to keep you feature
            service working in a mutlithread environment
            
            @param: filename - Name of the hdf5 file
            @param: mode - sets the file access mode (default: 'w')
            @param: failonexist - well not lock if file exists (default: False)
            @param: args - passes arguments to table.open_file
            @param: kwargs - passes arguments to table.open_file
        """
        self.filename = filename
        self.mode = mode
        self.args = args
        self.kwargs = kwargs
        self.h5file = None
        self.hdf5_lock = None
        
        if mode == 'r' and MULTITHREAD_HDF5: #set read locks
            self.bq_lock = Locks(self.filename, failonexist=failonexist, mode=mode+'b')
        else: #set write locks
            if MULTITHREAD_HDF5 is False: #sets a lock on all hdf5 usage in fs
                self.hdf5_lock = Locks(None, 'hdf5_lock', failonexist=False, mode='wb')
            self.bq_lock = Locks(None, self.filename, failonexist=failonexist, mode=mode+'b')
    
    def acquire(self):
        """
            Acquires the locks for the hdf5 file.
            
            If MULTITHREAD_HDF5 is set, the hdf5 file will be 
            locked in write mode and pytables will be locked on 
            file hdf5_lock.
            
            @return: a pytables file handle. If locks fail nothing will be returned.
             If the file cannot be open a FeatureServiceError exception will 
             be raised
        """
        if not self.h5file:
            
            self.bq_lock.acquire(self.bq_lock.ifnm, self.bq_lock.ofnm)
            if not self.bq_lock.locked: #no lock was given on the hdf5 file
                log.debug('Failed to lock hdf5 file!')
                self.release()
                return None
            
            if self.hdf5_lock:
                self.hdf5_lock.acquire(self.hdf5_lock.ifnm, self.hdf5_lock.ofnm)
                if not self.hdf5_lock.locked: #no lock was given on pytables 
                    log.debug('Failed to lock pytables!')
                    self.release()
                    return None            
            
            log.debug('Succesfully acquired locks!')
            self.h5file = self._open_table()
            return self.h5file
            
    def _open_table(self):
        """
            Opens an hdf5 file under locks.
        """
        try:
            self.h5file=tables.open_file(self.filename, self.mode, *self.args, **self.kwargs)
        except tables.exceptions.HDF5ExtError:
            self.release()
            log.debug('Failed to find table %s'%self.filename)
            raise FeatureServiceError(error_message='Fatal Error: Table was not found!')
        
        return self.h5file
            
    def release(self):
        """
            Releases all locks and closes and deletes hdf5 
            file handle
        """
        if self.hdf5_lock:
            self.hdf5_lock.release()
            self.hdf5_lock = None
        
        if self.h5file:
            self.h5file.close()
            del self.h5file
            self.h5file = None
            self.bq_lock.release()
    
    def __enter__(self):
        return self.acquire()
        
    def __exit__(self, type, value, traceback):
        self.release()


class QueryPlan(object):
    """
        Generates a queue of querys to be requested on
        the tables at once. 
    """
    def __init__(self, feature):
        self.query_queue = {}
        self.feature = feature
        
    def push(self, hash):
        """
            @param: hash
        """
        path = self.feature.localfile(hash)
        if path in self.query_queue:  # checking the first few element on the hash
            self.query_queue[path].put(hash)  # place the output in the queue
        else:
            self.query_queue[path] = Queue.Queue()  # build queue since none were found
            self.query_queue[path].put(hash)

    def keys(self):
        return self.query_queue.keys()
    
    def __getitem__(self, key):
        return self.query_queue[key]
    

class Rows(object):
    """
        Generates rows to be placed into the tables
    """
    def __init__(self, feature):
        self.row_queue = {}
        self.feature = feature

    def keys(self):
        return self.row_queue.keys()
    
    def __getitem__(self, key):
        return self.row_queue[key]

    def _calculate_row(self, feature_resource):
        try:
            #log.debug('Calculate Feature')
            return self.feature.calculate(feature_resource)#runs calculation
            #log.debug('Successfully calculated feature!')
        except FeatureExtractionError as e: #in case resource is None 
            raise FeatureExtractionError(feature_resource, e.code, e.message)
        
        except InvalidResourceError as e:
            raise FeatureExtractionError(feature_resource, e.code, e.message)

        except StandardError as err:
            # creating a list of uri were the error occured
            log.exception('Calculation Error: URI:%s  %s Feature failed to be calculated' % (str(feature_resource) , self.feature.name))
            raise FeatureExtractionError(feature_resource, 500, 'Internal Server Error: Feature failed to be calculated')
    

class CachedRows(Rows):
    """
        Generates rows from the feature cache
    """
    def construct_row(self, feature, feature_resource):
        """
        """
        id = self.feature.hash_resource(feature_resource)
        results = self._calculate_row(feature_resource)
        try:
            results = zip(*results)
        except TypeError:
            results = [tuple([results])]
        rows = []
        for (j) in results:
            row = tuple([id])
            row += j
            rows.append(row)
        return rows
    
    def push(self, request_resource):
        """
            creates a list to append to the feature table
            if feature calculation was a success return true
            otherwise return false
            
            @param feature_resource - 
        """
        id = self.feature.hash_resource(request_resource.feature_resource)
        path = self.feature.localfile(id)
        rows = self.construct_row(self.feature, request_resource.feature_resource)
        if path in self.row_queue:  # checking the first few element on the hash
            self.row_queue[path].put(rows)  # place the output in the queue
        else:
            self.row_queue[path] = Queue.Queue()  # build queue since none were found
            self.row_queue[path].put(rows)
        return
    
class WorkDirRows(Rows):
    """
        Generates rows to be placed into the uncached tables
    """
    def construct_row(self, feature, feature_resource, row=None):
        """
            If row is nothing a feature is calculated otherwise the
            row is formated in the workdir table format
            
            @param: feature -
            @param: feature_resource - 
            @param: row - row for a workdir table (default: None)
            
            @return: rows
        """
        if row is None:
            results = self._calculate_row(feature_resource)
            try:
                results = zip(*results)
            except TypeError:
                results = tuple([results])
                
            rows = []; status = []
            for (j) in results:
                row = tuple(feature_resource)
                row += j
                rows.append(row)
                status.append((200))
            return (rows, status)
        else:
            r = list(feature_resource)
            r.append(row['feature'])
            for p in feature.parameter:
                r.append(row[p])
            return (tuple(r), tuple([200]))        
    

    def construct_error_row(self, feature, error):
        """
            Formats the rows where error occured
            in the feature calculations

            @param: feature -
            @param: feature_resource - 
            @param: row - (default: None)
            
            @return: rows
        """
        row = [
            error.resource.image,
            error.resource.mask,
            error.resource.gobject,
            np.zeros([feature.length]),  #feature
        ]
        for p in feature.parameter:
            row.append(0)
        return (tuple(row), tuple([error.code]))
    
    
    def push(self, request_resource):
        """ 
            @param: request_resource
        """
        if request_resource.exception:
            rows, status = self.construct_error_row(self.feature, e)
        else:
            try:
                rows, status = self.construct_row(self.feature, resource)
            except FeatureExtractionError as e:
                rows, status = self.construct_error_row(self.feature, e)
        
        if 'feature' in self.row_queue:  # feature is used to maintain the structure
            self.table_queue['feature'].put([rows,status])  # the row is pushed into the queue
        else:  # creates a queue if no queue is found
            self.row_queue['feature'] = Queue.Queue()
            self.row_queue['feature'].put((rows,status))
        return


class Tables(object):
    """
    """
    TablePlan = namedtuple('ResourceRequest', ['table_name', 'columns', 'index_column'])
    TablePlan.__new__.__defaults__ = ('', {}, [])
    def __init__(self, feature):
        """
            Requires a Feature Class to intialize. Will search for table in the
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.table_plan = []
         

    def write_to_table(self, filename, func=None):
        """
            Initalizes a table in the file if does not already exist
            @param: filename - name of the file
            @param: table_parameters - takes a list of [(tablename, columns, [list of columns to index])]  
            @param: func - function accepting a h5 tabel object
        """
        with TablesLock(filename, 'w', failonexist=True) as h5file:
            if h5file:
                try:
                    for (table_name, columns, indexed) in self.table_plan:
                        table = h5file.create_table('/', table_name, columns, expectedrows=1000000000)
                        for col_name in indexed:
                            column = getattr(table.cols, col_name)
                            column.removeIndex()
                            column.createIndex()
                        table.flush()
                            
                    if func:
                         return func(h5file)
                
                except tables.exceptions.HDF5ExtError:
                    log.debug('Failed to create table %s'%filename)
                    raise FeatureServiceError(error_message='Failed to create table')
            else:
                log.debug('Already initialized h5 table -> path: %s' % filename)
                return #tables was made already


    def read_from_table(self, filename, func):
        """
            Read from the table 
            @func - function excepting a h5 table object
            
            @return index
        """
        self.create_h5_file(filename)
        attempts = 0
        while 1:
            with TablesLock(filename, 'r') as h5file:
                if h5file:
                    log.debug('Reading from table -> path: %s' % filename)
                    return func(h5file)
            
            #tries to lock again
            attempts+=1
            if attempts > FAILED_LOCK_ATTEMPTS:
                raise FeatureServiceError(error_message='Failed to lock the table for the %s time'%FAILED_LOCK_ATTEMPTS)
            else:
                log.debug('Table was not locked: %s attempting to relock the table after %s sec.'%(filename,LOCKING_DELAY))
                time.sleep(LOCKING_DELAY)
                continue


    def append_to_table(self, filename, func):
        """
            Appends rows to the table
            @param: filename -
            @param: func - pass a function to append to the table
        """
        self.create_h5_file(filename)
        
        attempts = 0
        while 1:
            with TablesLock(filename, 'a') as h5file:
                if h5file:
                    log.debug('Appending to table -> path: %s' % filename)
                    return func(h5file)
            
            attempts+=1
            if attempts > FAILED_LOCK_ATTEMPTS:
                raise FeatureServiceError(error_message='Failed to lock the table for the %s time'%FAILED_LOCK_ATTEMPTS)
            else:
                log.debug('Table was not locked: %s attempting to relock the table after %s sec.'%(filename,LOCKING_DELAY))
                time.sleep(LOCKING_DELAY)
                continue
            
            
    def create_h5_file(self, filename, func=None):
        """
            creates hdf5 table with index on column id if file does not exist
        """
        if os.path.exists(filename) is False:
            return self.write_to_table(filename, func)


class CachedTables(Tables):
    """
        Creates tables in the cache
    """
    def __init__(self, feature):
        self.feature = feature
        _mkdir(self.feature.path)
        self.table_plan = []
        self.table_parameters = []
        self.table_plan.append(self.TablePlan('values', self.feature.cached_columns(), ['idnumber']))


    def store(self, rows):
        """
            store elements to tables
            
            @param: rows
        """
        for filename in rows.keys():
            queue = rows[filename]

            def func(h5file):
                table = h5file.root.values
                while not queue.empty():
                    row = queue.get()
                    query = 'idnumber=="%s"' % str(row[0][0])  # queries the hash to see if a feature has been already added
                    try:
                        table.where(query).next() #if the list contains one element
                        log.debug('Skipping %s - already found in table'%str(row[0][0]))   
                                   
                    except StopIteration: #fails to get next
                        log.debug('Appending %s to table'%str(row[0][0]))
                        for r in row:
                            table.append([r])
                table.flush()

            self.append_to_table(filename, func)
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
                        query_results.append((None, hash))
                    else:
                        query_results.append((table[index], hash))
                return query_results
                    
            yield self.read_from_table(filename, func)


    def find(self, query_queue):
        """
            checks to see if anything is stored in the table under
            the query
            
            @param: query_queue - list of hashes to query the table
            
            @return: generator([bool(if the query was found),hash],..)
        """
        for filename in query_queue.keys():
            log.debug('filename: %s'%filename)
            def func(h5file):
                query_results = []
                table = h5file.root.values
                
                while not query_queue[filename].empty():
                    hash = query_queue[filename].get()
                    query = 'idnumber=="%s"' % str(hash)
                    
                    try:
                        table.where(query).next() #if the list contains one element
                        query_results.append((True, hash))
                        log.debug('Find: query: %s -> Found!' % query)
                    except StopIteration: #fails to get next
                        query_results.append((False, hash))
                        log.debug('Find: query: %s -> Not Found!' % query)
                
                return query_results
                    
            yield self.read_from_table(filename, func)


    def delete(self):
        """
            delete tables
        """
        table_list = glob.glob(os.path.join('%s' % self.feature.path,'*.h5'))
        for t in table_list:
            try:
                os.remove(t)
            except OSError:
                log.debug('Workdir hdf5 failed to delete @ %s' % os.path.join(self.path, self.filename))


    def __len__(self):
        """
            opens each table in a particular feature directory and sums up the length of all the features
            (note: take a noticable amount of time)
        """
        import glob
        feature_tables = glob.glob(os.path.join(self.feature.path, '*.h5'))
        log.debug('feature table list %s' % str(os.path.join(self.feature.path, '*.h5')))
        def func(h5file):
            return len(h5file.root.values)
        l = 0
        for filename in feature_tables:
            l+=self.read_from_table(self, filename, func)
        return l


class WorkDirTable(Tables):
    """
        Places a table into the workdir without index
    """
    def __init__(self, feature):
        """
            Requires a Feature Class to intialize. Will search for table in the
            data\features\feature_tables directory. If it does not find the table
            it will create a table.
        """
        self.feature = feature
        self.table_plan = []
        self.table_plan.append(self.TablePlan('values', self.feature.workdir_columns(), []))
        self.table_plan.append(self.TablePlan('status', {'status': tables.Int16Col()}, ['status']))
    
    def set_path(self, path):
        self.path = path
        self.filename = os.path.basename(self.path)
        _mkdir(os.path.dirname(self.path))
        return self

    def find(self, query_plan):
        """
            A pass through since this table whould be queryied
            
            @param: query_plan - list of hashes to query the table
            
            @return: generator([hash, False],..)
        """
        query_results = []
        for filename in query_plan.keys():
            while not query_plan[filename].empty():
                hash = query_plan[filename].get()
            query_results.append(('false', hash))
        return [query_results]
    

    def store(self, row_genorator):
        """
            store row elements to an output table
        """
        for key in row_genorator.keys():
            queue = row_genorator[key]
        
            log.debug('Writing hdf5 file into workdir: %s' % self.filename)
            if self.create_h5_file(self.path, lambda x: True) is None: # creates the table, should return true
                raise FeatureServiceError( 500,'File already exists in workdir: %s' % self.filename)            
    
            # appends elements to the table        
            def func(h5file):
                table = h5file.root.values
                status = h5file.root.status
                while not queue.empty():
                    rows,s = queue.get()
                    table.append(rows)
                    status.append(s)
                table.flush()
                
            self.append_to_table(self.path, func)
        return

    def get(self):
        """
            returns all the rows in the table
        """
        def func(h5file):
            table = h5file.root.values
            status = h5file.root.status
            return zip(table[:], status[:])
        
        return self.read_from_table(self.path, func)

    def remove(self, resource):
        """
            @param: resource
        """
        pass
    
    def delete(self):
        """
            @param: resource
        """
        try:
            os.remove(os.path.join(self.path, self.filename))
        except OSError:
            log.debug('Workdir hdf5 failed to delete @ %s' % os.path.join(self.path, self.filename))

    def __len__(self):
        """
            @return: length of the table stored in workdir
        """
        def func(h5file):
            return len(h5file.root.values)
        return self.read_from_table(self, os.path.join(self.path, self.filename), func)        
