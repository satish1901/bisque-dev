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
            @param: session - 
            @param: name - 
            @param: resource_list - 
            @param: path -
            
            @return:            
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
            @param: session - 
            @param: name - 
            @param: resource_list - 
            
            @return:
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
        def __init__(self, request_queue, error_func=None):
            self.request_queue = request_queue
            
            if error_func is not None:
                self.error_func = error_func
            else:
                def error_func(e):
                    pass
                self.error_func = error_func
            super(ParallelFeature.BQRequestThread, self).__init__()
            
            
        def run(self):
            for request in self.request_queue:
                try:
                   request() #run request
                except BQCommError as e:
                    errorcb(e)
        
        
    def thread_pool(self, request_queue, error_func=None):
        """
            Runs the threads
        """
        rq = request_queue()
        
        jobs = []
        for _ in range(self.thread_num):
            r = self.BQRequestThread(rq, error_func)
            jobs.append(r)
            r.start()

        for j in jobs:
            j.join()
        print 'Joins Threads'
        return
    
    
    def set_thread_num(self, n):
        self.thread_num = n
        
        
    def set_chunk_size(self, n):
        self.chunk_size = n
        
        
    def chunk(self, l):
        for i in xrange(0,len(l),self.chunk_size):
            yield l[i:i+self.chunk_size]
        
        
    def fetch(self, session, name, resource_list, path=None):
        """
         @param: session - 
         @param: name - 
         @param: resource_list - 
         @param: path - 
         
         @return:
        """
        if path is None:
            f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
            f.close()
            table_path = f.name
        else:
            table_path = path
        
        stop_write_thread = False
        class WriteThread(Thread):
            
            def __init__(self, queue):
                self.queue = queue
                super(WriteThread, self).__init__()
            
            def run(self):
                while True:
                    if not self.queue.empty():
                        temp_path = self.queue.get()
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
            for partial_resource_list in self.chunk(resource_list):
                
                def request():
                    f = tempfile.TemporaryFile(suffix='.h5', dir=tempfile.gettempdir())
                    f.close()                    
                    write_queue.put(super(ParallelFeature, self).fetch(session, name, partial_resource_list, path=f.name))
                    return
                yield request
        
        
        w = WriteThread(write_queue)
        w.start()
        self.thread_pool(request_queue)
        stop_write_thread = True
        w.join()

        if path is None:
            return tables.open_file(table_path, 'r')
        else: 
            return path
        
        
    def fetch_vector(self, session, name, resource_list):
        """
         @param: session - 
         @param: name - 
         @param: resource_list - 
         
         @return: 
        """
        response_queue = Queue.Queue()
        
        @threadsafe_generator
        def request_queue():
            for partial_resource_list in self.chunk(resource_list):
                
                def request():
                    response_queue.put(super(ParallelFeature, self).fetch_vector(session, name, partial_resource_list))
                    return
                
                yield request
                
        self.thread_pool(request_queue)
        
        response_list = []
        while not response_queue.empty():
            response_list.append(response_queue.get())
        return np.concatenate(response_list)        
    
    