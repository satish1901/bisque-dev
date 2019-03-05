## [Bisque Docker Environment Setup Instructions](https://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions05)

#### Docker/Project Source

- [Docker Hub Image](https://hub.docker.com/r/cbiucsb/bisque05/)
- [Bitbucket CBIucsb/bisque-stable (TODO: Test with Github version!!)](https://bitbucket.org/CBIucsb/bisque-stable)
- [Bique Bioimage Google Groups](https://groups.google.com/forum/#!topic/bisque-bioimage/jwo_5sHFeHU)

#### Pre-requisite

- Install docker (light weight VM) on you laptop:
      https://docs.docker.com/install/linux/docker-ce/ubuntu/
- Instructions on installing bisque using docker
      https://bitbucket.org/CBIucsb/bisque/src/default/README.md

#### Installation

- Use the installer script to setup bisque docker image
```
wget https://bitbucket.org/CBIucsb/bisque-stable/downloads/build_bisque_docker_modules.sh
sh build_bisque_docker_modules.sh
```
- You can modify this script to create a modules folder and mount/load modules from the host machine into docker


#### Run Environment

- Start Docker and mount directories for run

```
# Start
xterm -e \
docker run --name bisque --rm -p 8080:8080 -p 27000:27000 \
-v $(pwd)/container-modules:/source/modules \
-v $(pwd)/container-data:/source/data \
-v $(pwd)/container-config:/source/config \
'cbiucsb/bisque05:stable'
```

- Stop Docker

```
 docker stop $(docker ps -a -q --filter ancestor=cbiucsb/bisque05:stable --format="{{.ID}}")
```

- Advanced environment for working with database URI as,
    - sqlite:///data/bisque.db
    - postgresql://rahul:rahul@localhost/bqmurks58 or postgresql://dbhost:5432/bisque

```
docker run --name bisque --rm -p 8080:8080 \
-v $(pwd)/container-modules:/source/modules \
-v $(pwd)/container-data:/source/data \
-v $(pwd)/container-config:/source/config \
-e BISQUE_DBURL=postgresql://rahul:rahul@localhost/bqmurks58 \
'cbiucsb/bisque05:stable'
```

- This will start the bisque docker/server
    - Client Service http://0.0.0.0:8080
    - Engine Service http://0.0.0.0:8080/engine_service
    - Module Service http://0.0.0.0:8080/module_service
    - Features http://0.0.0.0:8080/features
- Use "admin:admin" to authenticate into this local environment 
- To manipulate and check logs, connect to docker bash 
```
bisque-host$ docker exec -t -i bisque /bin/bash
```

#### Develop in Docker (TODO !!)

- Use the dev docker image [docker vishwakarmarhl/ucsb-bisque05-svc](https://cloud.docker.com/repository/docker/vishwakarmarhl/ucsb-bisque05-svc)

- Create the workspace and prepare the development setup
```
cd ~/ws
git clone https://github.com/UCSB-VRL/bisque
mkdir container-modules container-data container-config
cp -r bisque/modules/* container-modules/
```
- Create the container 

```
docker run --name bisque-dev --rm -p 8080:8080 -p 27000:27000 \
-v $(pwd)/container-modules:/source/modules \
-v $(pwd)/container-data:/source/data \
-v $(pwd)/container-config:/source/config \
'vishwakarmarhl/ucsb-bisque05-svc:dev'
```

- Bash into the docker container and develop

```
docker exec -it bisque-dev /bin/bash

```

- Activate environment and Test/Build a Module (TODO !! python-dev)

```
root@9362d1f8bf12:/source# cd modules/MetaData
root@9362d1f8bf12:/source/modules/MetaData# source /usr/lib/bisque/bin/activate
root@9362d1f8bf12:/source/modules/MetaData# python setup.py

```
- Verify Bisque Services
  - Bisque Client interface at http://0.0.0.0:8080/client_service
  - Bisque Engine service at http://0.0.0.0:8080/engine_service

- Now you can add the Metadata module from the manager interface and run a test

