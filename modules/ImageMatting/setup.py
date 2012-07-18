# Install script for ImageMatting
import sys
from bq.setup.module_setup import matlab_setup, read_config

def setup(params, *args, **kw):
    return matlab_setup(['ImageMatting', '-a', 'vrl_tools'], params=params)
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])

    sys.exit(setup(params))
