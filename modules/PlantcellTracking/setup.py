# Install script for NuclearDetector3D
import sys
from bq.setup.module_setup import matlab_setup, read_config, docker_setup

def setup(params, *args, **kw):
    matlab_setup('PlantcellTracking', params=params)
    docker_setup('plantcelltracking', 'PlantcellTracking', 'matlab_runtime', params=params)
    
if __name__ =="__main__":
    params = read_config('runtime-bisque.cfg')
    if len(sys.argv)>1:
        params = eval (sys.argv[1])

    sys.exit(setup(params))
