# Install script for NuclearDetector3D
import sys
from bq.setup.module_setup import matlab_setup, read_config, docker_setup

def setup(params, *args, **kw):
    #matlab_setup('NuclearDetector3D', params=params)
    docker_setup('n3d', params=params)
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])

    sys.exit(setup(params))
