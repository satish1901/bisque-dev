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



#### Run Environment

- Setup folders & pull code 

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
 'vishwakarmarhl/ucsb-bisque05-svc:dev'

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

- Advanced environment for working with database URI as,
    - sqlite:///data/bisque.db
    - postgresql://rahul:rahul@localhost/bqmurks58 or postgresql://dbhost:5432/bisque

```
docker run --name bisque-dev --rm -p 8080:8080 -p 27000:27000 \
 -v $(pwd)/container-modules:/source/modules \
 -v $(pwd)/container-data:/source/data \
 -v $(pwd)/container-config:/source/config \
 -e BISQUE_DBURL=postgresql://rahul:rahul@localhost/bqmurks58 \
 'vishwakarmarhl/ucsb-bisque05-svc:dev'
```

- This will start the bisque docker/server
    - Client Service http://0.0.0.0:8080
    - Engine Service http://0.0.0.0:8080/engine_service
    - Module Service http://0.0.0.0:8080/module_service
    - Features http://0.0.0.0:8080/features
- Use "admin:admin" to authenticate into this local environment 
- To manipulate and check logs, connect to docker bash 
```
bisque-host$ docker exec -t -i bisque-dev /bin/bash
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

