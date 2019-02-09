# Bisque Rancher 2.0 Setup (with Kubernetes engine)
---------------------------------------------------

#### Nomenclature (Kubernetes like)
--------------------------------

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
#### Cluster Description

#### Lets Encrypt on [Ubuntu 16.04](https://certbot.eff.org/lets-encrypt/ubuntuxenial-other)

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
#### Installation Rancher 2.0

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
- You will have rancher accessible at https://loup.ece.ucsb.edu:8443

------------------------
#### Create the YAML configuration based on docker-compose.yaml (In case of migration)

##### Create an access key for [Rancher CLI](https://rancher.com/docs/rancher/v2.x/en/cli/) operations (Doesnt work on self-signed certs)
- endpoint  : https://loup.ece.ucsb.edu/v3
- access-key: token-xt47w
- secret-key: < >
- bearer-tok: token-xt47w: < >

##### Migration CLI 
- Download the docker-compose and rancher-compose.yml files from existing rancher user interface for migration 
https://rancher.com/docs/rancher/v2.x/en/v1.6-migration
- Migration using CLI tools
```
# migration-tools export --url <RANCHER_URL> --access-key <RANCHER_ACCESS_KEY> \
# --secret-key <RANCHER_SECRET_KEY> --export-dir <EXPORT_DIR>

./migration-tools parse --docker-file compose/docker-compose.yml \
 --rancher-file compose/rancher-compose.yml 
```

------------------------

### Setup Cluster [/rke-clusters/custom-nodes](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/rke-clusters/custom-nodes/)

#### Port requirements

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

#### Create cluster 

- Added a cluster in rancher-ui named "bqdev-cluster" and run the below command for running the rancher-agent 
```

sudo docker run -d --privileged --restart=unless-stopped --net=host \
 -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \
  rancher/rancher-agent:v2.1.6 --server https://loup.ece.ucsb.edu:8443 \
  --token 7z2ncgjj4482m48fpsj7xjmc8lc9n6bsxh7qcjrsr6rcxrzhzl6prz \
  --ca-checksum d522680b13d7aabe4dc57bb2776e28759852c336d0cf0e0f9fed5d3fb7b495e8 \
  --etcd --controlplane --worker
  
```

- Add more nodes as worker only, by running this command on those nodes so that they register with the above main control node 
```
sudo docker run -d --privileged --restart=unless-stopped --net=host \
  -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \ 
  rancher/rancher-agent:v2.1.6 --server https://arkady.ece.ucsb.edu \ 
  --token 298vqgm9fs6kfd8n5rbmwq6mx87g6vdbmr26c7xbf4bgb6t9z4bcjt \ 
  --worker
```

#### Create a namespace bqdev within this cluster
Bisque Test environment where workloads are deployed

--------------
#### Setup Volume

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
- restart the nfs server
```
sudo systemctl restart nfs-kernel-server
```
- Mount the NFS folder on the client
```
sudo mount 192.168.1.123:/opt/bisque/ /run/bisque/
```
- Verify the mount on a client system using df -h


> OR 
https://www.claudiokuenzler.com/blog/786/rancher-2.0-create-persistent-volume-from-nfs-share
- Create a persistent volume in the cluster 
- Set local path option on the node as /run/bisque

---------------------------------
### Setup Workload on the cluster

Bisque Test environment where workloads are deployed with open NodePort
https://rancher.com/managing-kubernetes-workloads-with-rancher-2-0/

- We will be using the image at registry biodev.ece.ucsb.edu:5000/ucsb-bisque05-svc

##### Workload configuration
- Name: ucsb-bisque05-svc-wl
- Pods: 1
- Docker Image : biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev or vishwakarmarhl/ucsb-bisque05-svc:dev
- Port Mapping: 80-tcp-ClusterIP(Internal)-Same & 27000-tcp-ClusterIP(Internal)-Same 
- Environment Variables: Copy paste the "Environment Configuration" section 
- Node Scheduling: Run all the pods on a particular host
- Health Check: No change
- Volumes: Persistent Volume claim and set the mount point as /tmp/bisque
- Scaling: No change
- Command: 
  - Entrypoint: /builder/run-bisque.sh
  - Command: bootstrap start
  - Working Dir: /source
  - Console: Interactive & TTY (-i -t)
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
- Connoisseur GPU variables
```
NVIDIA_REQUIRE_CUDA=cuda>=8.0
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility
CUDA_PKG_VERSION=8-0=8.0.61-1
CAFFE_PKG_VERSION=0.15.13-1ubuntu16.04+cuda8.0
CAFFE_VERSION=0.15
CUDA_VERSION=8.0.61

IMGCNV=imgcnv_ubuntu16_2.4.3
CONDOR_MANAGER_HOST=master.condor
CONDOR_DAEMONS=MASTER,SCHEDD,SHARED_PORT

```

##### Debugging the cluster/pods 
- Using cluster kubectl shell from the cluster web UI
```
# Fetch namespaces
kubectl get pods --all-namespaces
kubectl get pods -n bqdev 

# Fetch logs on a pod/container
kubectl logs postgres-564d9f79d5-z2sxl  -n bqdev 

```

--------------
#### Mail server setup 
https://www.linuxbabe.com/mail-server/ubuntu-16-04-iredmail-server-installation

#### Move individual workload/containers to rancher-kubernetes using rancher-cli (doesnt work with self-signed certificates)
https://rancher.com/blog/2018/2018-08-02-journey-from-cattle-to-k8s/

-------------------------
### Run Bisque on two nodes 

- Load Balancers add in workloads [/k8s-in-rancher/load-balancers-and-ingress](https://www.cnrancher.com/docs/rancher/v2.x/en/k8s-in-rancher/load-balancers-and-ingress/load-balancers/)
> Tried using built in Ingress for bisque-test.bqtest.192.168.1.112.xip.io but failed to work

- If you want to expose the workload container to outside world then use NodePort otherwise work with ClusterIp(Internal Only) port configuration 
- https://rancher.com/blog/2018/2018-08-14-expose-and-monitor-workloads/

-------------------------
### [Remove/Cleanup Rancher](https://rancher.com/docs/rancher/v2.x/en/admin-settings/removing-rancher/user-cluster-nodes/)

- Stop Rancher Containers 
```
# Master: for the rancher server container
docker stop $(docker ps -a -q --filter ancestor=rancher/rancher:stable --format="{{.ID}}")
# Workers: for all k8s containers 
docker stop $(docker ps -f name=k8s* --format="{{.ID}}")
```
- Clean the container, images and volumes
```
docker rm -f $(docker ps -a -f name=k8s* --format="{{.ID}}")
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