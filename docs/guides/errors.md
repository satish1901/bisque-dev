

### Errors

Solution to errors encountered during the setup

#### 1. Port in use error
 
  - If you see an error like below it may be due to port not being free
```
    File "/opt/nagare-home/lib/python2.7/site-packages/Paste-1.7.5.1-py2.7.egg/paste/httpserver.py", line 1105, in server_close
    self.thread_pool.shutdown(60)
    AttributeError: 'WSGIThreadPoolServer' object has no attribute 'thread_pool'
```
  - Solution is to kill the process holding the port
```
    sudo kill $(sudo lsof -t -i:8080)
```

#### 2. Import Error on a library
  - Issue: ImportError: libhdf5_serial.so.100: cannot open shared object file: No such file or directory
  - Solution to fix the installed packages
```
    pip uninstall h5py tables
    pip install --no-cache-dir tables
```
