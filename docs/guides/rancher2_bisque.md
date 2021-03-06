# Rancher 2.0 Setup (with Kubernetes engine)
---------------------------------------------------


#### Introduction

- [Why Docker Container](https://www.docker.com/why-docker) ??
  - A container is a standard unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings.
  - [Container vs. Virtual Machine](https://www.docker.com/resources/what-container)
  ![What is Container](img/bqranch/container-vs-vm.png)

- [Why Kubernetes](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/#why-do-i-need-kubernetes-and-what-can-it-do) ?? [K8s](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/#what-does-kubernetes-mean-k8s) ??
  - Kubernetes provides a container-centric management environment. It orchestrates computing, networking, and storage infrastructure on behalf of user workloads. 
- [Why Rancher](https://rancher.com/what-is-rancher/what-rancher-adds-to-kubernetes/) ??
  - Rancher combines everything an organization needs to run containers in production and centrally manage multiple Kubernetes clusters
  - Rancher includes a full Kubernetes distribution, but adds value around Kubernetes in three key areas: Cluster Operations and Management, Intuitive Workload Management, and Enterprise Support.

#### Nomenclature (Kubernetes like)
--------------------------------

Rancher 2.0 [Guide to provisioning a Kubernetes cluster](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/) which uses the Kubernetes container-orchestration system to  

| Name | Kubernetes concepts  |
| :---          | :---        |
| Container		| 	Pod (Simplest Kubernetes object representing a set of containers on the cluster) |
| Services		|	Workload (Units of work that are running on the cluster, these can be pods or deployments) |
| Load Balancer	|	Ingress |
| Stack			|	Namespace (A virtual cluster) |
| Environment		|	Project (Administration)/Cluster (Compute machines that run containerized applications) |
| Host			|	Node (Physical or virtual machines making up the cluster) |
| Catalog			|	Helm |

--------------------------
#### A. Cluster Description
- Deployment [Google Slides](https://docs.google.com/presentation/d/1E6f6BR5sj5g3WPc_uRV01ZPbAjezZuUAvidUwZbbthQ/edit#slide=id.g4f74d0d960_0_58)

![Rancher Deployment Diagram](img/bqranch/Rancher2-deployment.png?raw=true)


#### B. Lets Encrypt on [Ubuntu 16.04](https://certbot.eff.org/lets-encrypt/ubuntuxenial-other)

- Bind the hostname to the IP address by creating an A record in DNS 
- Letsencrypt ACME challenge at TCP/80 on host 
- Open up firewall for this "sudo ufw allow 80 && sudo ufw allow 80 443"
- Verify the port 80 availability
``` 
sudo netstat -peanut | grep ":80" 
```
- Setup certificates at /etc/letsencrypt
```
sudo certbot certonly --standalone --dry-run \
   --cert-name loup.ece.ucsb.edu -d loup.ece.ucsb.edu
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

![Rancher main Container](img/bqranch/rancher_main_container.png?raw=true)

- You will have rancher accessible at https://loup.ece.ucsb.edu:8443 if everything goes fine


------------------------

- Create the YAML configuration based on docker-compose.yaml (In case of migration)
- Create an access key for [Rancher CLI](https://rancher.com/docs/rancher/v2.x/en/cli/) operations (Doesnt work on self-signed certs)
    - endpoint  : https://loup.ece.ucsb.edu:8443/v3
    - access-key: token-xt47w
    - secret-key: < >
    - bearer-tok: token-xt47w: < >

##### Migration CLI 
- Download the docker-compose and rancher-compose.yml files from existing rancher user interface for migration 
https://rancher.com/docs/rancher/v2.x/en/v1.6-migration
- Migration using CLI tools

```
migration-tools export --url <RANCHER_URL> --access-key <RANCHER_ACCESS_KEY> \
 --secret-key <RANCHER_SECRET_KEY> --export-dir <EXPORT_DIR>
```
```
./migration-tools parse --docker-file compose/docker-compose.yml \
 --rancher-file compose/rancher-compose.yml 
```

------------------------

#### D. Setup Cluster [RKE/custom-nodes](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/rke-clusters/custom-nodes/)

##### Port requirements

Open up ports based on the [CNI provider requirements](https://rancher.com/docs/rancher/v2.x/en/installation/references/)
- Use Canal as the provider in this case
```
# API/UI Clients
sudo ufw allow 22,80,443/tcp
# Etcd Plane Nodes
sudo ufw allow 2379,2380,9099,6443/tcp && sudo ufw allow 8472/udp
# Control Plane Nodes
sudo ufw allow 2379,2380,10250,6443,9099,10254/tcp && sudo ufw allow 8472/udp
# Worker Plane Nodes
sudo ufw allow 6443,9099,10254/tcp && sudo ufw allow 8472/udp
# Workload
sudo ufw allow 30000:32767/tcp && sudo ufw allow 30000:32767/udp
# Others 
sudo ufw allow  2376/tcp
```
![Ubuntu ufw status](img/bqranch/rancher_ufw_status.png?raw=true)


##### Create cluster 

- Create a cluster in rancher-ui named "bq-cluster"
- Select "custom" local/remote nodes option to create this cluster
- Run the below command for running the rancher-agent/workers
```
sudo docker run -d --privileged --restart=unless-stopped --net=host \
 -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \
  rancher/rancher-agent:v2.1.6 --server https://loup.ece.ucsb.edu:8443 \
  --token 7z2ncgjj4482m48fpsj7xjmc8lc9n6bsxh7qcjrsr6rcxrzhzl6prz \
  --ca-checksum d522680b13d7aabe4dc57bb2776e28759852c336d0cf0e0f9fed5d3fb7b495e8 \
  --etcd --controlplane --worker
```
- The final "bq-cluster" state can be visualized upon creation 
![Rancher cluster created state](img/bqranch/rancher_cluster.png?raw=true)

- A docker ps on a node of the cluster (as created above) would look like below screenshot
![Rancher cluster node addition](img/bqranch/rancher_worker_control_plane.png?raw=true)

- Add more nodes as worker, by running above command on those nodes so that they register with the rancher2 and become part of this cluster. The nodes on a cluster can be visualized in rancher cluster -> nodes menu.
![Rancher cluster node view](img/bqranch/rancher_cluster_nodes.png?raw=true)

##### Create a namespace bqdev within this cluster
Bisque Development environment where workloads are deployed and tested

--------------
#### E. Setup Volume

- Mount the host directory for volume using NFS and setup the nfs client access for the cluster
https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nfs-mount-on-ubuntu-16-04
- Setup folders
```
# Create the path on host system
sudo mkdir /opt/bisque/ -p && \
sudo mkdir /opt/bisque/data -p && \
sudo mkdir /opt/bisque/local/workdir -p

# Allow other users to edit this
sudo chown -R nobody:nogroup /opt/bisque/
```
- Open up the ports used by NFS
```
# Access from specific machines
sudo ufw allow from 192.168.1.129 to any port nfs
sudo ufw allow from 192.168.1.133 to any port nfs

# Specific ports in case above doesnt work
sudo ufw allow 32768:65535/tcp && sudo ufw allow 32768:65535/udp
sudo ufw allow 2049/tcp && sudo ufw allow 2049/udp
sudo ufw allow 111/tcp && sudo ufw allow 111/udp
```
- Now add NFS host configuration at /etc/exports
```
/opt/bisque     192.168.1.129(rw,sync,no_root_squash,no_subtree_check)
/opt/bisque     192.168.1.133(rw,sync,no_root_squash,no_subtree_check)
```
- restart the nfs server on the NFS host machine
```
sudo systemctl restart nfs-kernel-server
```
- Mount the NFS folder on the client machine
```
sudo mount 192.168.1.123:/opt/bisque/ /run/bisque/
```
- Verify the mount on a client system using df -h


> AND
https://www.claudiokuenzler.com/blog/786/rancher-2.0-create-persistent-volume-from-nfs-share

- Create a persistent volume in the cluster 
- Set local path option on the node as /run/bisque

![Rancher NFS persistent volume addition](img/bqranch/rancher_volume_nfs.png?raw=true)

- We can see all the volumes that are created in the Volumes section of the "bq-cluster" workload

![Rancher workload volumes](img/bqranch/workload_volumes.png?raw=true)

---------------------------------
#### F. Setup Workload (on the cluster)

Bisque Test environment where workloads are deployed with open NodePort
https://rancher.com/managing-kubernetes-workloads-with-rancher-2-0/

- We will be using the image at custom registry [biodev.ece.ucsb.edu:5000/ucsb-bisque05-svc](https://biodev.ece.ucsb.edu:5000/v2/_catalog) or we can use a publicly deployed image at [https://hub.docker.com](https://hub.docker.com)

##### Test workload configuration
- Name: ucsb-bisque05-svc
- Pods: 2
- Docker Image : biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev or vishwakarmarhl/ucsb-bisque05-svc:dev
  ![Workload name](img/bqranch/workload_head.png?raw=true)
- Port Mapping: 
  - 8080-tcp-NodePort-Random & 27000-tcp-NodePort-Random
  - Alternately, we can use 8080-tcp-ClusterIP(Internal)-Same & 27000-tcp-ClusterIP(Internal)-Same

  ![Workload ports](img/bqranch/workload_ports.png?raw=true)

- Environment Variables: Copy paste the "Environment Configuration" section 
- Node Scheduling: Run all the pods on a particular host
- Health Check: No change
- Volumes: Persistent Volume claim and set the mount point as /tmp/bisque
- Scaling: No change
- Command: (Only, in case needed. Not used with the current Image)
  - Entrypoint: /builder/run-bisque.sh
  - Command: bootstrap start
  - Working Dir: /source
  - Console: Interactive & TTY (-i -t)
- Networking: No Change
- Labels: No change
- Security: No change

> Finally we can see the overall state of pods in the workload within the clusters
![Workload pods](img/bqranch/workload_pods.png?raw=true)
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

We should see the overview of workloads deployed as below
![Workload Dashboard](img/bqranch/workloads.png?raw=true)

#### G. Load Balancing (using L7 Ingress)
- Add Ingress configuration for load balancing with name "bq-website" 
- Configure the target(ucsb-bisque05-svc) pods so that the port 8080 is exposed through the ingress controller
![Ingress Ctrl Configuration ](img/bqranch/workload_ingress_ctrl.png?raw=true)

- Load Balancing section of the workload will showcase the list of ingress controllers along with the mapping
![Ingress Ctrl dashboard ](img/bqranch/workload_ingress_dash.png?raw=true)

#### H. Monitoring/Debugging 
- Using cluster kubectl shell from the cluster web UI
```
# Fetch namespaces
kubectl get pods --all-namespaces
kubectl get pods -n bqdev 

# Fetch logs on a pod/container
kubectl logs postgres-564d9f79d5-z2sxl  -n bqdev 
```
- Use Cluster dashboard for all cluster monitoring and configuration

    ![Cluster Dashboard](img/bqranch/cluster_dash.png?raw=true)


-------------------------
#### I. [Uninstall](https://rancher.com/docs/rancher/v2.x/en/admin-settings/removing-rancher/user-cluster-nodes/) Rancher

- Stop Rancher Containers 
```
# Master: for the rancher server container
docker stop $(docker ps -a -q --filter ancestor=rancher/rancher:stable --format="{{.ID}}")
# Workers: for all k8s containers 
docker stop $(docker ps -f name=k* --format="{{.ID}}")
```
- Clean the container, images and volumes
```
docker rm -f $(docker ps -a -f name=k* --format="{{.ID}}")
docker rmi -f $(docker images -q "rancher/*")
docker volume rm $(docker volume ls -q)
```
- Unmount and remove data (/var/lib/kubelet/pods/XXX, /var/lib/kubelet, /var/lib/rancher)
```
# Unmount directories
for mount in $(mount | grep tmpfs | grep '/var/lib/kubelet' | awk '{ print $3 }') /var/lib/kubelet /var/lib/rancher; do sudo umount $mount; done

# Clean the directories
sudo rm -rf /etc/ceph \
       /etc/cni \
       /etc/kubernetes \
       /opt/cni \
       /opt/rke \
       /run/secrets/kubernetes.io \
       /run/calico \
       /run/flannel \
       /var/lib/calico \
       /var/lib/etcd \
       /var/lib/cni \
       /var/lib/kubelet \
       /var/lib/rancher/rke/log \
       /var/log/containers \
       /var/log/pods \
       /var/run/calico
# Mounted host directories
sudo rm -rf /host/rancher/
sudo rm -rf /var/log/rancher/auditlog
```

- Remove the existing network interface
```
ip address show
ip link delete <interface_name>
```

---------------------
Additional References
---------------------

==TODO==

#### 1.) Mail server setup 
https://www.linuxbabe.com/mail-server/ubuntu-16-04-iredmail-server-installation

#### 2.) Migration from Rancher 1.x to 2.x
- individual workload/containers to rancher-kubernetes using rancher-cli (doesnt work with self-signed certificates)
https://rancher.com/blog/2018/2018-08-02-journey-from-cattle-to-k8s/


#### 3.) Reference on Ingress Controllers

- Load Balancers add in workloads [/k8s-in-rancher/load-balancers-and-ingress](https://www.cnrancher.com/docs/rancher/v2.x/en/k8s-in-rancher/load-balancers-and-ingress/load-balancers/)
> Tried using built in Ingress for  	
bq-website.bqdev.192.168.1.129.xip.io but failed to work for engine service

- If you want to expose the workload container to outside world then use NodePort otherwise work with ClusterIp(Internal Only) port configuration 
- https://rancher.com/blog/2018/2018-08-14-expose-and-monitor-workloads/

#### 4.) PostgreSQL server
- [Setup PostgreSql 10.4 on Rancher workload](../rancher2_postgresql)
- This is used in the Bisque configuration as environment variable BISQUE_DBURL=postgresql://postgres:postgres@10.42.0.15:5432/postgres