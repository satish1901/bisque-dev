

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


#### 3. Container Errors

```
RunContainerError: failed to start container "9c51eea9f13d6a4cedb61591ca953914ce6396f8e8849116441388605d9f4320": Error response from daemon: OCI runtime create failed: container_linux.go:344: starting container process caused "process_linux.go:424: container init caused \"process_linux.go:407: running prestart hook 0 caused \\\"error running hook: exit status 1, stdout: , stderr: exec command: [/usr/bin/nvidia-container-cli --load-kmods configure --ldconfig=@/sbin/ldconfig.real --device=all --compute --utility --require=cuda>=9.0 --pid=2959531 /var/lib/docker/overlay2/bb9185b9c4dc070c25cac10ae0aad2b991f6dddf8c70f8979e28ec0609c14a21/merged]\\\\nnvidia-container-cli: initialization error: cuda error: no cuda-capable device is detected\\\\n\\\"\"": unknown

```