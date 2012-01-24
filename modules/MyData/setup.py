# Install script for Metalab
import sys
from bq.util.module_setup import matlab_setup, require, read_config

from bbfreeze import Freezer

def setup(params, *args, **kw):
    f = Freezer("dist")
    f.addScript('MyData.py')
    f()
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])
    sys.exit(setup(params))
    
