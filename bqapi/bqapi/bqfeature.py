from lxml import etree
from threading import Thread
import threading
import tempfile
import tables
import os
from math import ceil
import Queue
from bqapi.comm import BQCommError
import numpy as np
import logging
from collections import namedtuple

log = logging.getLogger('bqapi.bqfeature')


FeatureResource = namedtuple('FeatureResource',['image','mask','gobject'])
FeatureResource.__new__.__defaults__ = (None, None, None)

class FeatureCommError(BQCommError):
    """
        Feature Communication Exception
    """

class Feature(object):

    def fetch(self, session, name, resource_list, path=None):
        """
            Requests the feature server to calculate features on provided resources.
            
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            @param: resource_list - list of the resources to extract. format: 
            [(image_url, mask_url, gobject_url),...] if a parameter is
            not required just provided None
             
            @return: returns either a pytables file handle or the file name when the path is provided     
        """
        url = '%s/features/%s/hdf'%(session.bisque_root,name)
        
        resource = etree.Element('resource')
        for (image, mask, gobject) in resource_list:
            sub = etree.SubElement(resource, 'feature')
            query = [] 
            if image: query.append('image=%s' % image)
            if mask: query.append('mask=%s' % mask)
            if gobject: query.append('gobject=%s' % gobject)
            query = '&'.join(query)            
            sub.attrib['uri'] = '%s?%s'%(url,query)
        
        log.debug('Fetch Feature %s for %s resources'%(name, len(resource_list)))
            
        if path:
            log.debug('Returning feature response to %s' % path)
            return session.c.post(url, content=etree.tostring(resource), headers={'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=path)          
        else:
            f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
            f.close()
            log.debug('Returning feature response to %s' % f.name)
            path = session.c.post(url, content=etree.tostring(resource), headers={'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=f.name)
            return tables.open_file(path, 'r')
    
    
    def fetch_vector(self, session, name, resource_list):
        """
            Requests the feature server to calculate features on provided resources. Designed more for
            requests of very view features. 
            
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            @param: resource_list - list of the resources to extract. format: 
            [(image_url, mask_url, gobject_url),...] if a parameter is
            not required just provided None
            
            @return: a list of features as numpy array
            
            @exception: FeatureCommError - if any part of the request has an error the FeatureCommError will be raised on the
            first error.
            note: You can use fetch and read from the status table for the error. 
            warning: fetch_vector will not return response if an error occurs within the request
        """
        hdf5 = self.fetch(session, name, resource_list)
        status = hdf5.root.status
        index = status.getWhereList('status>=400')
        if index.size>0: #returns the first error that occurs
            status = status[index[0]][0]
            hdf5.close()
            os.remove(hdf5.filename) #remove file from temp directory
            raise FeatureCommError('%s:Error occured during feature calculations' % status, {})
        table = hdf5.root.values
        status_table = hdf5.root.status
        feature_vector = table[:]['feature']
        hdf5.close()
        os.remove(hdf5.filename) #remove file from temp directory
        return feature_vector
    
    @staticmethod
    def length(session, name):
        """
            Returns the length of the feature
            
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            
            @return: feature length
        """
        xml = session.fetchxml('/features/%s'%name)
        return int(xml.xpath('feature/tag[@name="feature_length"]/@value')[0])

class ParallelFeature(Feature):
    
    MaxThread = 4
    MaxChunk = 1000
    MinChunk = 100
    
    def __init__(self):
        super(ParallelFeature, self).__init__()
        

    class BQRequestThread(Thread):
        """
            Single Thread
        """
        def __init__(self, request_queue, errorcb=None):
            """
                @param: requests_queue - a queue of requests functions
                @param: errorcb - a call back that is called if a BQCommError is raised
            """
            self.request_queue = request_queue

            if errorcb is not None:
                self.errorcb = errorcb
            else:
                def error_callback(e):
                    """
                        Default callback function
                        
                        @param: e - BQCommError object
                    """
                    pass
                self.errorcb = error_callback
            super(ParallelFeature.BQRequestThread, self).__init__()
            
            
        def run(self):
            while True:
                if not self.request_queue.empty():
                    request = self.request_queue.get()
                    try:
                        request()
                    except BQCommError as e:
                        self.errorcb(e)
                else:
                    break
        
        
    def request_thread_pool(self, request_queue, errorcb=None, thread_count = MaxThread):
        """
            Runs the BQRequestThread
            
            @param: request_queue - a queue of request functions
            @param: errorcb - is called back when a BQCommError is raised
        """
        jobs = []
        log.debug('Starting Thread Pool')
        for _ in range(thread_count):
            r = self.BQRequestThread(request_queue, errorcb)
            r.daemon = True            
            jobs.append(r)
            r.start()

        for j in jobs:
            j.join()
        log.debug('Rejoining %s threads'%len(jobs))
        return
    
    
    def set_thread_num(self, n):
        """
            Overrides the internal thread parameters, chunk size must also
            be set to override the request parameters
            
            @param: n - the number of requests made at once
        """
        self.thread_num = n
        
        
    def set_chunk_size(self, n):
        """
            Overrides the chunk size, thread num must also
            be set to override the request parameters
            
            @param: n - the size of each request
        """
        self.chunk_size = n
        
    def calculate_request_plan(self, l):
        """
            Tries to figure out the best configuration 
            of concurrent requests and sizes of those 
            requests based on the size of the total request
             and pre-set parameters
            
            @param: l - the list of requests
            
            @return: chunk_size - the amount of resources for request
            @return: thread_num - the amount of concurrent requests
        """
        if len(l)>MaxThread*MaxChunk:
            return (MaxThread,MaxChunk)
        else:
            if len(l)/float(MaxThread)>=MinChunk:
                return (MaxThread, ceil(MaxChunk/float(MaxThread)))
            else:
                t = ceil(len(l)/float(MinChunk))
                return (t, len(l)/float(t))
        
        
    def chunk(self, l, chunk_size):
        """
           @param: l - list  
           @return: list of resource and sets the amount of parallel requests
        """
        for i in xrange(0, len(l), chunk_size):
            yield l[i:i+chunk_size]
        
    def fetch(self, session, name, resource_list, path=None):
        """
            Requests the feature server to calculate provided resources. 
            The request will be boken up according to the chunk size
            and made in parallel depending on the amount of threads.
            
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            @param: resource_list - list of the resources to extract. format: [(image_url, mask_url, gobject_url),...] if a parameter is
            not required just provided None
             
            @return: returns either a pytables file handle or the file name when the path is provided
        """
        if path is None:
            f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
            f.close()
            table_path = f.name
        else:
            table_path = path
        
        stop_write_thread = False #sets a flag to stop the write thread
        # when the requests threads have finished
        
        class WriteHDF5Thread(Thread):
            """
                Copies small hdf5 feature tables
                into one large hdf5 feature table
            """
            
            def __init__(self, h5_filename_queue):
                """
                    param h5_filename_queue: a queue of temporary hdf5 files
                """
                self.h5_filename_queue = h5_filename_queue
                tables.open_file(table_path, 'w').close() #creates a new file
                super(WriteHDF5Thread, self).__init__()
            
            def run(self):
                """
                    While queue is not empty and stop_write_thread
                    has not been set to true, the thread will open
                    temporary hdf5 tables and copy them into the 
                    main hdf5 table and then delete the temporary file.
                """
                while True:
                    if not self.h5_filename_queue.empty():
                        temp_path = self.h5_filename_queue.get()
                        with tables.open_file(temp_path, 'a') as hdf5temp:
                            with tables.open_file(table_path, 'a') as hdf5:
                                temp_table = hdf5temp.root.values
                                temp_status_table = hdf5temp.root.status
                                if not hasattr(hdf5.root, 'values'):
                                    temp_table.copy(hdf5.root,'values')
                                    temp_status_table.copy(hdf5.root,'status')
                                else:
                                    table = hdf5.root.values
                                    status_table = hdf5.root.status
                                    table.append(temp_table[:])
                                    status_table.append(temp_status_table[:])
                                    table.flush()
                                    status_table.flush()
                        os.remove(hdf5temp.filename)
                        continue
                        
                    if stop_write_thread is True:
                        log.debug('Ending HDF5 write thread')
                        break
        
        
        def errorcb(e):
            """
                Returns an error log
            """
            log.warning('%s'%str(e))
        
        write_queue = Queue.Queue()
        request_queue = Queue.Queue()
        
        def request_factory(partial_resource_list):
            def request():
                f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
                f.close()                    
                write_queue.put(super(ParallelFeature, self).fetch(session, name, partial_resource_list, path=f.name))
            return request
        
        if hasattr(self,'thread_num') and hasattr(self,'chunk_size'):
            thread_num = self.thread_num
            chunk_size = self.chunk_size
        else:
            thread_num, chunk_size = calculate_request_plan(resource_list)
        
        for partial_resource_list in self.chunk(resource_list, chunk_size):
            request_queue.put(request_factory(partial_resource_list))          
        
        
        w = WriteHDF5Thread(write_queue)
        log.debug('Starting HDF5 write thread')
        w.daemon = True    
        w.start()

        self.request_thread_pool(request_queue, errorcb=errorcb, thread_count = thread_num)
        stop_write_thread = True
        w.join()

        if path is None:
            log.debug('Returning parallel feature response to %s'%table_path)
            return tables.open_file(table_path, 'r')
        else: 
            log.debug('Returning parallel feature response to %s'%path)
            return path
        
        
    def fetch_vector(self, session, name, resource_list):
        """
            Requests the feature server to calculate provided resources.
            The request will be boken up according to the chunk size
            and made in parallel depending on the amount of threads.
             
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            @param: resource_list - list of the resources to extract. format: 
            [(image_url, mask_url, gobject_url),...] if a parameter is
            not required just provided None
            
            @return: a list of features as numpy array
        """
        return super(ParallelFeature, self).fetch_vector(session, name, resource_list)
    
    