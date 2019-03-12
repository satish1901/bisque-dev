
## Module Development Guide/Resources

- Developer Reference: https://biodev.ece.ucsb.edu/projects/bisquik/wiki/Developer
- Module Reference: https://biodev.ece.ucsb.edu/projects/bisquik/wiki/Developer/ModuleSystem

##### Container organization and plan for rancher setup

- Bisque Production Rancher: http://saw.ece.ucsb.edu:8080

##### Server Containers
| Instance Name | Host or IP  | Image Name | Remarks    |
| :---          | :---        | :---       | :---       |
| BisQue Server | http://dough.ece.ucsb.edu  | biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev   | Main BisQue service with Connoisseur |
| condor-nodes | condor.master     | biodev.ece.ucsb.edu:5000/condor      | One master and 4 worker nodes |


##### Module Containers
| Instance Name | Host or IP  | Image Name | Remarks    |
| :---          | :---        | :---       | :---       |
| Dream3D       | IP ADDR     | biodev.ece.ucsb.edu:5000/bisque_dream3d    | Dream3D Module |
| Predict Strength | IP ADDR     | biodev.ece.ucsb.edu:5000/predict_strength   | Predict Strength Module |
| Cell Segment 3D Unet | IP ADDR     | biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2  | 3D Cell Segmentation |

- There is another load balancer or haproxy to route the traffic based on IP rules
- LetsEncrypt certificates are used for encrypted traffic

## A.) Develop Module CellSegment3DUnet (PyTorch)
We describe the module which takes a 3D cell image in TIFF format as input and generates segmentation mask for it.

### Overall Module code 

```
root@karma:/module# tree -L 1  
.
|-- CellSegment3DUnet.xml
|-- Dockerfile
|-- PythonScript.log
|-- PythonScriptWrapper
|-- PythonScriptWrapper.py
|-- PythonScriptWrapper.spec
|-- README.md
|-- build/
|-- module.log
|-- public/
|-- pydist/
|-- runtime-module.cfg
|-- scriptrun.log
|-- setup.py
`-- source/
```

- Describe each section of the module

### Developing the Module in Docker

This module is used for segmenting the 3D image using UNet Pytorch based model. We  will build a container to test, develop and deploy the module.

#### Build Docker Image
docker build -t biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest . -f Dockerfile

#### Run container and bash
nvidia-docker run -it --ipc=host -v $(pwd):/module biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest bash

- The docker run, creates a container and then connect to its bash



## B.) Module Deploy/Execution

- Extracts from the ~/staging/**/docker_run.log execution log
- Updated engine service to include --ipc=host parameter in the launcher template (DOCKER_RUN) at bq.engine.controllers/docker_env.py

```
docker create --ipc=host biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2 \
python PythonScriptWrapper.py \
http://drishti.ece.ucsb.edu:8080/data_service/00-kDwj3vQq83vJA6SvVvVVh8 \
15 0.05 \
http://drishti.ece.ucsb.edu:8080/module_service/mex/00-XW6DsZR9puKj76Ezn9Mi79 \
admin:00-XW6DsZR9puKj76Ezn9Mi79

9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9 (Returns an identifier for this instance)
```

- Eventually this is the code that is running inside the container at runtime

```
python PythonScriptWrapper.py \
http://drishti.ece.ucsb.edu:8080/data_service/00-kDwj3vQq83vJA6SvVvVVh8 \
15 0.05 \
http://drishti.ece.ucsb.edu:8080/module_service/mex/00-XW6DsZR9puKj76Ezn9Mi79 \
admin:00-XW6DsZR9puKj76Ezn9Mi79


tail -f PythonScript.log

```

#### Run based on the identifier for that instance

```
docker start 9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9
docker wait 9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9
```




### Issues:

- Fix for the network issues. cannot reach/connect to external/host address
  - Error: Network
    ```
    requests.exceptions.ConnectionError: HTTPConnectionPool
    (host='loup.ece.ucsb.edu', port=8088): Max retries exceeded with url
    ```
  - Error: PyTorch 
    ```
    ERROR: Unexpected bus error encountered in worker. This might be caused by insufficient shared memory (shm).
    File "/usr/local/lib/python2.7/dist-packages/torch/utils/data/dataloader.py", line 274, in handler
    _error_if_any_worker_fails()
    RuntimeError: DataLoader worker (pid 277) is killed by signal: Bus error.
    ```
  - [Common Fix](https://github.com/tengshaofeng/ResidualAttentionNetwork-pytorch/issues/2): mount the docker container using --ipc=host flag
 
    ```
    docker create --ipc=host biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2 \
    python PythonScriptWrapper.py \ 
    http://bisque-dev-gpu-01.cyverse.org:8080/data_service/00-ZeBjryEbutgnpKFWvFDx38 \
    15 0.05 \
    http://bisque-dev-gpu-01.cyverse.org:8080/module_service/mex/00-g5rHg7NyujuUmPzLLb2M78 \
    admin:00-g5rHg7NyujuUmPzLLb2M78
    ```
