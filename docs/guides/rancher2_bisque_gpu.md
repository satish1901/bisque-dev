# Bisque Workload on Rancher 2.0 Setup (with Kubernetes engine)
---------------------------------------------------------------

### Pre-requisite
- [Rancher 2.0 with bq-cluster workload instructions](./rancher2_bisque)
- [Rancher 2.0 with PostgreSql workload instructions](./rancher2_postgresql)

##### General instructions
- Setup Cluster with [/rke-clusters/custom-nodes](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/rke-clusters/custom-nodes/)

##### Note: Assuming we have bq-cluster with postgres and persistent volumes

---------------------------------
### Setup Workload on the bq-cluster

Bisque Test environment where workloads are deployed with open NodePort
https://rancher.com/managing-kubernetes-workloads-with-rancher-2-0/

- We will be using the image at custom registry biodev.ece.ucsb.edu:5000/ucsb-bisque05-svc or another available at [vishwakarmarhl/ucsb-bisque05-svc:dev](https://hub.docker.com/r/vishwakarmarhl/ucsb-bisque05-svc)

##### Bisque Service Workload configuration
- Name: ucsb-bisque05-svc
- Pods: 2
- Docker Image : biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev or [vishwakarmarhl/ucsb-bisque05-svc:dev](https://hub.docker.com/r/vishwakarmarhl/ucsb-bisque05-svc)
- Port Mapping: 8080-tcp-NodePort-Random & 27000-tcp-NodePort-Random 
- Environment Variables: Copy paste the "Environment Configuration" section 
- Node Scheduling: Run all the pods on a particular host
- Health Check: No change
- Volumes: Persistent Volume claim and set the mount point as /run/bisque
- Scaling: No change
- Command: No Change
- Networking: No Change
- Labels: No change
- Security: No change

##### Environment Configuration

- Bisque service variables
```
      BISQUE_USER= bisque
      BISQUE_BISQUE_ADMIN_EMAIL= admin@loup.ece.ucsb.edu
      BISQUE_BISQUE_BLOB_SERVICE_STORES= blobs,local
      BISQUE_BISQUE_STORES_BLOBS_MOUNTURL= file://$$datadir/blobdir/$$user/
      BISQUE_BISQUE_STORES_BLOBS_TOP= file://$$datadir/blobdir/
      BISQUE_BISQUE_STORES_LOCAL_MOUNTURL= file://$$datadir/imagedir/$$user/
      BISQUE_BISQUE_STORES_LOCAL_READONLY= true
      BISQUE_BISQUE_STORES_LOCAL_TOP= file://$$datadir/imagedir/
      BISQUE_DOCKER_DOCKER_HUB= biodev.ece.ucsb.edu:5000
      BISQUE_SECRET= bq123
      BISQUE_UID= 12027
      BISQUE_RUNTIME_STAGING_BASE= /run/bisque/data/staging
      BQ__BISQUE__IMAGE_SERVICE__WORK_DIR= /run/bisque/local/workdir
      BQ__BISQUE__PATHS__DATA= /run/bisque/data
      MAIL_SERVER= dough.ece.ucsb.edu
      BISQUE_DBURL=postgresql://postgres:postgres@10.42.0.15:5432/postgres

      DEBIAN_FRONTEND=noninteractive
      IMGCNV=imgcnv_ubuntu16_2.4.3
```
##### Condor provisioning 

Condor Master 
- Image: biodev.ece.ucsb.edu:5000/condor 
- Ports: 9618, 9886 as HostPort
- Environment
```
CONDOR_DAEMONS = COLLECTOR,MASTER,NEGOTIATOR,SCHEDD,SHARED_PORT
CONDOR_MANAGER_HOST = master
```

Condor Worker
- Same configuration as above
- Ports: 9886 NodePort Random

##### Workload (bq-cluster) Dashboard
![Rancher Workload Dashboard](img/bqranch/workload_bisque_dash.png?raw=true)



--------------------------------------------- 
## Connoisseur/GPU Workload provisioning

- Create a namespace "connoisseur" and deploy everything isolated from the existing bisque-svc
- Create a postgres database for this deployment
  - psql -h 10.42.0.15 -U postgres --password -p 5432 postgres
  - "create database connoissuer;"
  - "grant all privileges on database connoisseur to postgres;"
- Create a volume bqcon-vol mounted at 192.168.1.123:/opt/bisque/connoisseur over NFS 

#### A.) Bisque Client Service Workload configuration
- Name: bq-connoisseur-client-svc
- Pods: 1
- Docker Image : biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev
- Port Mapping: 80-tcp-NodePort-Random & 27000-tcp-NodePort-Random 
- Environment Variables: Copy paste the "Environment Configuration" section 
- Node Scheduling: Run all the pods on a particular host that has GPU, Say "arkady" 
- Health Check: No change
- Volumes: Persistent Volume claim of bqcon-vol and set the mount point as /run/bisque/
- Scaling: No change
- Command: No Change
- Networking: No Change
- Labels: No change
- Security: No change

##### Environment Configuration

- Bisque client service variables
```
      BISQUE_USER= bisque
      BISQUE_BISQUE_ADMIN_EMAIL= admin@loup.ece.ucsb.edu
      BISQUE_BISQUE_BLOB_SERVICE_STORES= blobs,local
      BISQUE_BISQUE_STORES_BLOBS_MOUNTURL= file://$$datadir/blobdir/$$user/
      BISQUE_BISQUE_STORES_BLOBS_TOP= file://$$datadir/blobdir/
      BISQUE_BISQUE_STORES_LOCAL_MOUNTURL= file://$$datadir/imagedir/$$user/
      BISQUE_BISQUE_STORES_LOCAL_READONLY= true
      BISQUE_BISQUE_STORES_LOCAL_TOP= file://$$datadir/imagedir/
      BISQUE_DOCKER_DOCKER_HUB= biodev.ece.ucsb.edu:5000
      BISQUE_SECRET= bq123
      BISQUE_UID= 12027
      BISQUE_RUNTIME_STAGING_BASE= /run/bisque/data/staging
      BQ__BISQUE__IMAGE_SERVICE__WORK_DIR= /run/bisque/local/workdir
      BQ__BISQUE__PATHS__DATA= /run/bisque/data
      MAIL_SERVER= dough.ece.ucsb.edu
      DEBIAN_FRONTEND=noninteractive
      IMGCNV=imgcnv_ubuntu16_2.4.3
      BISQUE_DBURL=postgresql://postgres:postgres@10.42.0.15:5432/connoisseur
      BISQUE_SERVERS_H1_SERVICES_DISABLED = engine_service,connoisseur
```

####  B.) Bisque Engine Service Workload configuration
- All the same configuration as above but skipping one environment variable
- Skip the disable variable --> BISQUE_SERVERS_H1_SERVICES_DISABLED = engine_service,connoisseur

- Verify connoisseur GPU variables 
```
      NVIDIA_REQUIRE_CUDA=cuda>=8.0
      NVIDIA_VISIBLE_DEVICES=all
      NVIDIA_DRIVER_CAPABILITIES=compute,utility
      CUDA_PKG_VERSION=8-0=8.0.61-1
      CAFFE_PKG_VERSION=0.15.13-1ubuntu16.04+cuda8.0
      CAFFE_VERSION=0.15
      CUDA_VERSION=8.0.61

      CONDOR_MANAGER_HOST=master.condor
      CONDOR_DAEMONS=MASTER,SCHEDD,SHARED_PORT

```

##### Workload (bq-cluster) with Namespace Connoissuer
![Rancher Workload Dashboard](img/bqranch/workload_connoisseur.png?raw=true)


-----
TODO:  
- Fix Caffe and CUDA within the image 
- Probably write your own Docker file for a new CUDA/GPU enabled container

```
bisque@bq-connoisseur-engine-svc-74755f798b-6lbgk:/source$ caffe deveice_query -gpu all
E0213 00:36:24.855478  1798 caffe.cpp:77] Available caffe actions:
E0213 00:36:24.856573  1798 caffe.cpp:80]       device_query
E0213 00:36:24.856690  1798 caffe.cpp:80]       test
E0213 00:36:24.856793  1798 caffe.cpp:80]       time
E0213 00:36:24.856899  1798 caffe.cpp:80]       train
F0213 00:36:24.857019  1798 caffe.cpp:82] Unknown action: deveice_query
*** Check failure stack trace: ***
    @     0x7fafbc7c65cd  google::LogMessage::Fail()
    @     0x7fafbc7c8433  google::LogMessage::SendToLog()
    @     0x7fafbc7c615b  google::LogMessage::Flush()
    @     0x7fafbc7c8e1e  google::LogMessageFatal::~LogMessageFatal()
    @           0x40863a  main
    @     0x7fafbb218830  __libc_start_main
    @           0x408dd9  _start
    @              (nil)  (unknown)
Aborted (core dumped)

```