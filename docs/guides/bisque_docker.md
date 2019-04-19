## [Bisque Docker Environment Setup Instructions](https://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions05)

#### Docker/Project Source

- [Docker Hub Bisque Dev Image](https://cloud.docker.com/u/vishwakarmarhl/repository/docker/vishwakarmarhl/ucsb-bisque05-svc)
- [UCSB-VRL/bisque-stable Github](https://github.com/UCSB-VRL/bisque)
- [Bique Bioimage Google Groups](https://groups.google.com/forum/#!topic/bisque-bioimage/jwo_5sHFeHU)

#### Installation
#### Pre-requisite

- Install docker (light weight VM) on you laptop:
      https://docs.docker.com/install/linux/docker-ce/ubuntu/
- Instructions on installing bisque using docker
      https://github.com/UCSB-VRL/bisque/README.md

#### Create the Docker Image

> Look into the [UCSB-VRL/bisque-build](https://github.com/UCSB-VRL/bisque-build) repository on how to create Docker container images for development

- The container image has bisque server, docker & virtual environment pre-installed
- The child containers that will run modules, will use the host network since we are working with local IP addresses which are not resolved on development network environments.


#### Run Environment

- Setup folders & pull code (Only for modules since Bisque server codebase is already part of the container image being used in next step)

```
mkdir ws && cd ws && git clone https://github.com/UCSB-VRL/bisque
mkdir container-modules container-data container-config && cp -r bisque/modules/* container-modules/
```

- Start Docker and mount directories for run

```
# Docker Run
docker run --name bisque-dev --rm -p 8080:8080 -p 27000:27000 \
 -v $(pwd)/container-modules:/source/modules \
 -v $(pwd)/container-data:/source/data \
 -v $(pwd)/container-config:/source/config \
 -v /var/run/docker.sock:/var/run/docker.sock \
 --ipc=host \
 --net=host \
 'vishwakarmarhl/ucsb-bisque05-svc:dev'
```

Alternately if you want an interactive log for docker run use the below command
```
docker run -it -p 8080:8080 -p 27000:27000 \
 -v $(pwd):/ws \
 -v /var/run/docker.sock:/var/run/docker.sock \
 --mount source=bqvol,target=/ws/bqvol \
 --ipc=host \
 --net=host \
 ucsb-bisque05-svc:dev
 
```

- Check Container state 

```
bisque@ubuntu:~$ docker ps
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS              PORTS                                              NAMES
a1162677d66a        vishwakarmarhl/ucsb-bisque05-svc:dev   "/builder/run-bisque…"   13 minutes ago      Up 13 minutes       0.0.0.0:8080->8080/tcp, 0.0.0.0:27000->27000/tcp   bisque-dev

```

- Stop Docker

```
docker stop $(docker ps -a -q --filter ancestor=vishwakarmarhl/ucsb-bisque05-svc:dev --format="{{.ID}}")
```

- This will start the bisque docker/server
    - Client Service http://0.0.0.0:8080
    - Engine Service http://0.0.0.0:8080/engine_service
    - Module Service http://0.0.0.0:8080/module_service
    - Features http://0.0.0.0:8080/features
- Since we want to develop we should use the local IP address for all accesses
    - Client Service http://192.168.0.14:8080/
    - Engine Service http://192.168.0.14:8080/engine_service

- Use "admin:admin" to authenticate into this local environment 
- To manipulate and check logs, connect to docker bash 

```
bisque-host$ docker exec -t -i bisque-dev /bin/bash
```

- Advanced environment for working with database URI as
    - sqlite:///data/bisque.db
    - postgresql://rahul:rahul@localhost/bqmurks58 or postgresql://dbhost:5432/bisque

```
docker run --name bisque-dev --rm -p 8080:8080 -p 27000:27000 \
-e BISQUE_DBURL=postgresql://rahul:rahul@localhost/bqmurks58 \
'vishwakarmarhl/ucsb-bisque05-svc:dev'
```


#### Develop in Docker (Work In Progress !!)

Run the containerized bisque server as described in the first half of this document

- Use the dev docker image [docker vishwakarmarhl/ucsb-bisque05-svc](https://cloud.docker.com/repository/docker/vishwakarmarhl/ucsb-bisque05-svc)
- Bash into the docker container and develop

```
docker exec -it bisque-dev /bin/bash

```

- Activate environment and Test/Build a Module

```
root@9362d1f8bf12:/source# cd modules/MaskRCNN
root@9362d1f8bf12:/source/modules/MaskRCNN# source /usr/lib/bisque/bin/activate
root@9362d1f8bf12:/source/modules/MaskRCNN# python setup.py

```
- Verify Bisque Services
- Now you can add the MaskRCNN module from the manager interface and run a test
- In this test a MEX-ID will be assigned to this module run and corresponding code will be dumped in the staging folder
- Look for "docker_run" script in the "staging/<mex_id>" folder. It has the following commands which you can use to run and debug your codebase
  - Script first creates the parameterized container command 

```
docker pull biodev.ece.ucsb.edu:5000/tflow-mrcnn-mod-v1
CONTAINER=$(docker create --ipc=host biodev.ece.ucsb.edu:5000/tflow-mrcnn-mod-v1  python PythonScriptWrapper.py http://192.168.0.14:8080/data_service/00-s3KxZhuvBt8vhER5RD7wdX 15 0.05 http://192.168.0.14:8080/module_service/mex/00-wRq68hGv5HTtr6mBsfM4CG admin:00-wRq68hGv5HTtr6mBsfM4CG)
```

  - Thereafter it executes the parameterized container command
    
```
docker start $CONTAINER
MODULE_RETURN=$(docker wait  $CONTAINER)
docker logs $CONTAINER
```

  - In your test, while still in the staging folder you can directly use the "docker_run" script to run your module as follows
    
```
sh docker_run python PythonScriptWrapper.py \
  http://192.168.0.14:8080/data_service/00-s3KxZhuvBt8vhER5RD7wdX \
  15 0.05 \
  http://192.168.0.14:8080/module_service/mex/00-wRq68hGv5HTtr6mBsfM4CG \
  admin:00-wRq68hGv5HTtr6mBsfM4CG)
```

Notes: Look into the README files on the modules for more commands on test/debug

- MaskRCNN - [README from Github](https://github.com/UCSB-VRL/bisque-dev/blob/master/modules/MaskRCNN/README.md)
- Deep Planteome - [Module Instructions](../bisque_module_planteome)