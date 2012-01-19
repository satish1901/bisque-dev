# Install script for RootTip
import sys
from bq.util.module_setup import matlab_setup, require, read_config

def setup(*args, **kw):
    return matlab_setup('matlab/araGT.m', bisque_deps = False, params=params)
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])
    sys.exit(setup(params))
