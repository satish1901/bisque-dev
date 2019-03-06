# Rancher 2.0 (with Kubernetes engine) Openstack
------------------------------------------------

#### Pre-requisite

- [Packages list](resources/dpackages.dump) on bisquesvc production (xenial-caffe) env
- [Custom Registry](https://docs.docker.com/registry/) is available and active at https://biodev.ece.ucsb.edu:5000/v2/_catalog
- [Dev Pi Packages](https://biodev.ece.ucsb.edu/py/bisque/stretch/+simple/) are acccessible 

##### Nvidia-docker

Since there is a GPU requirement in Bisque Connoisseur.
- Install [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu)
- Install [Nvidia-Docker](https://github.com/nvidia/nvidia-docker/), 
- Configure default nvidia-runtime: https://github.com/NVIDIA/k8s-device-plugin#preparing-your-gpu-nodes

```
sudo cat /etc/docker/daemon.json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```
- Check whethere you can execute without the runtime flag 

  ```docker run  --rm nvidia/cuda:9.0-base nvidia-smi ```

##### PostgreSQL server
- [Setup PostgreSql 10.4 on Rancher workload](../rancher2_postgresql)
- Verify the connectivity to this database

```
psql -h postgres.prod -U postgres --password -p 5432 postgres
```
- This is used in the Bisque configuration as environment variable 

```BISQUE_DBURL=postgresql://postgres:postgres@10.42.0.15:5432/postgres```

--------------------------
#### A. Cluster Description
- Deployment [Google Slides](https://docs.google.com/presentation/d/1E6f6BR5sj5g3WPc_uRV01ZPbAjezZuUAvidUwZbbthQ/edit#slide=id.g4f74d0d960_0_58)

![Rancher Deployment Diagram](img/bqranch/)


==Cluster==
- bisque-dev-01.cyverse.org , ubuntu@128.196.65.71
- bisque-dev-02.cyverse.org , ubuntu@128.196.65.100
- bisque-dev-gpu-01.cyverse.org , ubuntu@128.196.65.142


#### B. Lets Encrypt on [Ubuntu 16.04](https://certbot.eff.org/lets-encrypt/ubuntuxenial-other)

- Bind the hostname to the IP address by creating an A record in DNS 
- Letsencrypt ACME challenge at TCP/80 on host 
- Open up firewall for this "sudo ufw allow 80 && sudo ufw allow 80 443"
- Verify the port 80 availability

``` 
sudo netstat -peanut | grep ":80" 
```
- Setup certificates at /etc/letsencrypt on each node

```
sudo certbot certonly --standalone --dry-run \
   --agree-tos -m vishwakarma@ucsb.edu \
   --cert-name bisque-dev-01.cyverse.org \
   -d bisque-dev-01.cyverse.org 
```
```
sudo certbot certonly --standalone --dry-run \
   --agree-tos -m vishwakarma@ucsb.edu \
   --cert-name bisque-dev-02.cyverse.org \
   -d bisque-dev-02.cyverse.org 
```
```
sudo certbot certonly --standalone --dry-run \
   --agree-tos -m vishwakarma@ucsb.edu \
   --cert-name bisque-dev-gpu-01.cyverse.org \
   -d bisque-dev-gpu-01.cyverse.org 
```


--------------------------
#### C. Master Rancher 2.0

Install/Startup Rancher: https://rancher.com/docs/rancher/v2.x/en/installation/single-node/
- Rancher etcd data persisted at /var/lib/rancher
- Since port 80 is occupied by rancher/rancher, a rancher/rancher-agent cannot be run on this node.

```
docker run -d --restart=unless-stopped \
  -p 8080:80 -p 8443:443 \
  -v /var/log/rancher/auditlog:/var/log/auditlog \
  -v /host/rancher:/var/lib/rancher \
  -e AUDIT_LEVEL=1 \
  rancher/rancher:stable 
```
- You will have rancher accessible at https://bisque-dev-01.cyverse.org:8443 if everything goes fine

------------------------

#### D. Setup Cluster [RKE/custom-nodes](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/rke-clusters/custom-nodes/)

- Create a cluster and name it "bq-cluster"
- Use Calico for the CNI network layer
- Choose custom cloud provider leveraging k8s
- Make this server as etcd, controlplane and worker

```
 sudo docker run -d --privileged --restart=unless-stopped --net=host \
  -v /etc/kubernetes:/etc/kubernetes \
  -v /var/run:/var/run \
  rancher/rancher-agent:v2.1.6 \
  --server https://bisque-dev-01.cyverse.org:8443 \
  --token 2s7gbd8gj9vx4pv4vgsq899gkkxdfrxc8j8wh8njgcgwdmtfkt7gd8 \
  --ca-checksum cf2f54c1837a5d9e1f8cc7db35efdb9a497c16b4ea9022b52b877a7cc94be505 \
  --node-name bisque-dev-gpu-01.cyverse.org \
  --address 128.196.65.142 \
  --etcd --controlplane --worker \
  --label type=gpu
 
```

- You will see a green bar below saying a particular node has registered.

> You can add more nodes to the cluster by editing the cluster and running another command as below

```
sudo docker run -d --privileged --restart=unless-stopped --net=host \
  -v /etc/kubernetes:/etc/kubernetes \
  -v /var/run:/var/run \
  rancher/rancher-agent:v2.1.6 \
  --server https://bisque-dev-01.cyverse.org:8443 \
  --token 2sw5pb6nv2vqhrb8hrkbc6dgbn9k9lmw9kv6h8qzgmncxg9bfz6qpl \
  --ca-checksum cf2f54c1837a5d9e1f8cc7db35efdb9a497c16b4ea9022b52b877a7cc94be505 \
  --node-name bisque-dev-02.cyverse.org \
  --address 128.196.65.100 \
  --controlplane --worker \
  --label type=cpu
```

##### Port requirements

Open up ports based on the [CNI provider requirements](https://rancher.com/docs/rancher/v2.x/en/installation/references/)
- See requirements for Calico as the provider in this case

##### Service Discovery
- This [Service Discovery](https://rancher.com/docs/rancher/v2.x/en/k8s-in-rancher/service-discovery) entry enables DNS resolution for the workload’s pods using the following naming convention: ```<workload>.<namespace>.svc.cluster.local```

--------------
#### E. Setup Volume

- Mount the host directory for volume using NFS and setup the nfs client access for the cluster
https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nfs-mount-on-ubuntu-16-04
- Setup folders

```
# Create the path on host system
sudo mkdir /etc/letsencrypt/ -p && \
sudo mkdir /run/bisque/ -p && \
sudo mkdir /run/bisque/data -p && \
sudo mkdir /run/bisque/local/workdir -p

# Allow other users to edit this
sudo chown -R nobody:nogroup /run/bisque/
sudo chmod 0777 -R /run/bisque
```

- Now add NFS host configuration at /etc/exports

```
/run/bisque     128.196.65.100(rw,sync,no_root_squash,no_subtree_check)
/run/bisque     128.196.65.142(rw,sync,no_root_squash,no_subtree_check)
/run/postgres     128.196.65.100(rw,sync,no_root_squash,no_subtree_check)
/run/postgres     128.196.65.142(rw,sync,no_root_squash,no_subtree_check)
```
- restart the nfs server on the NFS host machine

```
sudo systemctl restart nfs-kernel-server
```
- Mount the NFS folder on the client machine

```
sudo apt-get install nfs-common
sudo mount 128.196.65.71:/run/bisque/ /run/bisque/
sudo mount 128.196.65.71:/run/postgres/ /run/postgres/
```
- Verify the mount on a client system using df -h

> AND
https://www.claudiokuenzler.com/blog/786/rancher-2.0-create-persistent-volume-from-nfs-share

- Create a persistent volume in the cluster 
- Set NFS-Share option on the node as /run/bisque 

![Rancher NFS persistent volume addition](img/bqranch/rancher_volume_nfs?raw=true)

- We can see all the volumes that are created in the Volumes section of the "bq-cluster" workload

![Rancher workload volumes](img/bqranch/workload_vol?raw=true)

---------------------------------
#### F. Setup Workload (on the cluster)

Bisque Test environment where workloads are deployed with open NodePort
https://rancher.com/managing-kubernetes-workloads-with-rancher-2-0/

##### Condor Setup
Installation & Configuration
- [HT Condor install instructions](https://research.cs.wisc.edu/htcondor/instructions/ubuntu/16/stable/)

###### Condor Master Node Deployment. This service will be discoverable at master.condor.svc.cluster.local
- Name: master
- Namespace: condor
- Pods: 1
- Docker Image: biodev.ece.ucsb.edu:5000/condor
- Port Mapping: 
  - 9618 	  	TCP 	  	HostPort 	  	9618
  - 9886 	  	TCP 	  	HostPort 	  	9886 
- Environment

```
CONDOR_MANAGER_HOST =	master.condor
CONDOR_DAEMONS =	COLLECTOR,MASTER,NEGOTIATOR,SCHEDD,SHARED_PORT
```

Also, verify the /etc/condor/condor_config.local has property

```
DAEMON_LIST = COLLECTOR,MASTER,NEGOTIATOR,SCHEDD,SHARED_PORT

```

###### Condor Worker Node Deployment
- Name: worker
- Namespace: condor
- Pods: 2
- Docker Image: biodev.ece.ucsb.edu:5000/condor
- Port Mapping: 
  - 9886 	  	TCP 	  	ClusterIP(Internal) 	  	9886 
- Volumes
  - Persistent Volume from Node path /var/run/docker.sock (enables docker run)
- Node Scheduling: Run all the pods on a particular host (GPU based bisque-dev-gpu-01.cyverse.org due to caffe engine requirements)

- Environment

```
CONDOR_MANAGER_HOST =	master.condor
CONDOR_DAEMONS =	MASTER,SCHEDD,STARTD,SHARED_PORT
```

###### Condor Configuration: [Advanced Setup Instructions](../rancher2_condor) 

- Configuration is needed to make sure the pool is discoverable, functional and collecting jobs.

##### Bisque workload configuration

We will be using the image at custom registry [biodev.ece.ucsb.edu:5000](https://biodev.ece.ucsb.edu:5000/v2/_catalog) or we can use any publicly deployed image at [https://hub.docker.com](https://hub.docker.com)

- Name: bisquesvc
- Pods: 1
- Docker Image: biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev
- Port Mapping: 
  - 80-TCP-NodePort-Random 
  - 27000-TCP-NodePort-Random

- Environment Variables: Copy paste the "Environment Configuration" section 
- Node Scheduling: Run all the pods on a particular host (GPU based bisque-dev-gpu-01.cyverse.org due to caffe engine)
- Health Check: No change
- Volumes
  - Persistent Volume claim and set the mount point as /run/bisque
  - Persistent Volume from Node path /etc/letsencrypt
  - Persistent Volume from Node path /var/run/docker.sock
- Scaling: No change
- Command: (Only, in case needed. Not used with the current Image)
  - Entrypoint: /builder/run-bisque.sh
  - Command: bootstrap start
  - Working Dir: /source
  - Console: Interactive & TTY (-i -t)
- Networking: No Change
- Labels: No change
- Security & Host: Privileged is True

> Finally we can see the overall state of pods in the workload within the clusters. Also view logs to track the Bisque initialization 
![Workload pods](img/bqranch/workload_pod?raw=true)
##### Environment Configuration

- Bisque service variables
```
      BISQUE_USER= bisque
      BISQUE_BISQUE_ADMIN_EMAIL= admin@bisque-dev-gpu-01.cyverse.org
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
      BISQUE_DBURL=postgresql://postgres:postgres@postgres.prod:5432/postgres
      CONDOR_DAEMONS= MASTER,SCHEDD,SHARED_PORT	
      CONDOR_MANAGER_HOST= master.condor
      DEBIAN_FRONTEND=noninteractive
      IMGCNV=imgcnv_ubuntu16_2.4.3
```

We should see the overview of workloads deployed as below
![Workload Dashboard](img/bqranch/workloads.png?raw=true)

Service should be running at http://bisque-dev-gpu-01.cyverse.org:31274

##### Bisque GPU Verification (nvidia-docker should be default runtime)
- Connect into the container and verify ```nvidia-smi``` state
- Caffe can be tested with ```caffe device_query --gpu all```

You should be able to tail the log on the node where you have deployed the container.
``` sudo tail -f /var/log/containers/prod_bisquecon-*.log ```

#### G. Load Balancing (using L7 Ingress)
- Add Ingress configuration for load balancing with name "bq-website" 
- Configure the target(bisquesvc) pods so that the port 80 is used

