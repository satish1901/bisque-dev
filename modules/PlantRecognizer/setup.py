# Install script for PlantRecognizer
import sys
from bq.util.module_setup import matlab_setup, require, read_config

def setup(params, *args, **kw):

    if not require (['matlab_home'], params):
        print "Skipping.. no matlab_home", params
        return 1
    
    return matlab_setup('PlantRecognizer', params=params)
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])

    sys.exit(setup(params))
