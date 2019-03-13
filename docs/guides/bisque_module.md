
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
docker tag $(docker images -q "biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest") biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest
docker push biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest


#### Run container and bash
nvidia-docker run -it --ipc=host -v $(pwd):/module biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2:latest bash

- The docker run, creates a container and then connect to its bash



## B.) Module Deploy/Execution

- Extracts from the ~/staging/**/docker_run.log execution log
- Updated engine service to include --ipc=host parameter in the launcher template (DOCKER_RUN) at bq.engine.controllers/docker_env.py

```
docker create --ipc=host biodev.ece.ucsb.edu:5000/torch-cellseg-3dunet-v2 \
python PythonScriptWrapper.py \
http://drishti.ece.ucsb.edu:8080/data_service/00-GFmjehgjqfqQi5CdXsAbiC \
15 0.05 \
http://drishti.ece.ucsb.edu:8080/module_service/mex/00-ZRwn68oz8CRhf2n9oXA9za \
admin:00-ZRwn68oz8CRhf2n9oXA9za

9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9 (Returns an identifier for this instance)
```

- Eventually this is the code that is running inside the container at runtime

```
python PythonScriptWrapper.py \
http://drishti.ece.ucsb.edu:8080/data_service/00-kDwj3vQq83vJA6SvVvVVh8 \
15 0.05 \
http://drishti.ece.ucsb.edu:8080/module_service/mex/00-RNeG4KEKJUQPXboPEbt63S \
admin:00-RNeG4KEKJUQPXboPEbt63S


tail -f PythonScript.log

```

#### Run based on the identifier for that instance

```
docker start 9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9
docker wait 9eb7d1be403ca77b6cdc5c2140d289c2ee1692e736fe39abc0bf1fd798a530f9
```




## C.) Integrate with Python 3 codebase/module or external clients
  - Use a Python 3 wheels build of the bisque-api==0.5.9 package
  - BQAPI https://setuptools.readthedocs.io/en/latest/setuptools.html#distributing-a-setuptools-based-project
  ```
  cd ~/bisque/bqapi
  python3 -m pip install --user --upgrade setuptools wheel
  python3 setup.py sdist bdist_wheel
  ```
  - This will create the whl file in dist folder which can be installed using
  ```
  python3 -m pip install dist/bisque_api-0.5.9-py2.py3-none-any.whl 
  ```
  - In case the bqapi code is not portable to Python 3 easily. We can use the 2to3.5 CLI for migration. This will update the files with Python 3 syntax in place and move the legacy code to a *.bak file upon update
  ```
  2to3.5 -w *.py  
  ```
  - Ideally we should be able to create a new bisque-api-py3 and push it to the packages respository at https://biodev.ece.ucsb.edu/py/bisque/prod