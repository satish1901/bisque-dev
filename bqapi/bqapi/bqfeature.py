from lxml import etree
from threading import Thread
import threading
import tempfile
import tables
import os
import Queue
from bqapi.comm import BQCommError
import numpy as np

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
            if image is not None:
                sub.attrib['image'] = image
            if mask is not None:
                sub.attrib['mask'] = mask
            if gobject is not None:
                sub.attrib['gobject'] = gobject            
            
        if path:
            return session.c.post(url, content=etree.tostring(resource), headers={'Content-Type':'text/xml', 'Accept':'application/x-bag'}, path=path)          
        else:
            f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
            f.close()
            path = session.c.post(url, content=etree.tostring(resource), headers={'Content-Type':'text/xml',  'Accept':'application/x-bag'}, path=f.name)
            return tables.open_file(path, 'r')
    
    
    def fetch_vector(self, session, name, resource_list):
        """
            Requests the feature server to calculate features on provided resources.
             
            @param: session - the local session
            @param: name - the name of the feature one wishes to extract
            @param: resource_list - list of the resources to extract. format: 
            [(image_url, mask_url, gobject_url),...] if a parameter is
            not required just provided None
            
            @return: a list of features as numpy array
        """
        hdf5 = self.fetch(session, name, resource_list)
        table = hdf5.root.values
        feature_vector = table[:]['feature']
        hdf5.close()
        os.remove(hdf5.filename) #remove file from temp directory
        return feature_vector



class threadsafe_iter(object):
    """
        Takes an iterator/generator and makes it thread-safe by
        serializing call to the `next` method of given iterator/generator.
    """
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            return self.it.next()


def threadsafe_generator(func):
    """
        A decorator that takes a generator function and makes it thread-safe.
    """
    def gen(*a, **kw):
        return threadsafe_iter(func(*a, **kw))
    return gen



class ParallelFeature(Feature):
    
    def __init__(self):
        self.thread_num = 1
        self.chunk_size = 500
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
            for request in self.request_queue:
                try:
                   request() #run request
                except BQCommError as e:
                    self.errorcb(e)
        
        
    def request_thread_pool(self, request_queue, errorcb=None):
        """
            Runs the BQRequestThread
            
            @param: request_queue - a queue of request functions
            @param: errorcb - is called back when a BQCommError is raised
        """
        rq = request_queue()
        
        jobs = []
        for _ in range(self.thread_num):
            r = self.BQRequestThread(rq, errorcb)
            jobs.append(r)
            r.start()

        for j in jobs:
            j.join()
        print 'Joins Threads'
        return
    
    
    def set_thread_num(self, n):
        """
            @param: n - the number of requests made at once
        """
        self.thread_num = n
        
        
    def set_chunk_size(self, n):
        """
            @param: n - the size of each request
        """
        self.chunk_size = n
        
        
    def chunk(self, l):
        for i in xrange(0,len(l),self.chunk_size):
            yield l[i:i+self.chunk_size]
        
        
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
                super(WriteThread, self).__init__()
            
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
                                if not hasattr(hdf5.root, 'values'):
                                    temp_table.copy(hdf5.root,'values')
                                else:
                                    table = hdf5.root.values
                                    table.append(temp_table[:])
                                    table.flush()
                        os.remove(hdf5temp.filename)
                        continue
                        
                    if stop_write_thread is True:
                        break
        
        write_queue = Queue.Queue()
        
        @threadsafe_generator
        def request_queue():
            """
                A generator of request functions.
            """
            for partial_resource_list in self.chunk(resource_list):
                
                def request():
                    f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
                    f.close()                    
                    write_queue.put(super(ParallelFeature, self).fetch(session, name, partial_resource_list, path=f.name))
                    return
                
                yield request
        
        
        w = WriteThread(write_queue)
        w.start()
        self.request_thread_pool(request_queue)
        stop_write_thread = True
        w.join()

        if path is None:
            return tables.open_file(table_path, 'r')
        else: 
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
    
    
                yield request
                
        self.thread_pool(request_queue)
        
        response_list = []
        while not response_queue.empty():
            response_list.append(response_queue.get())
        return np.concatenate(response_list)        
    
    