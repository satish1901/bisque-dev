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

#### Installation Rancher 2.0

Install/Startup Rancher: https://rancher.com/docs/rancher/v2.x/en/installation/single-node/
docker run -d --restart=unless-stopped \
  -p 80:80 -p 443:443 \
  -v /var/log/rancher/auditlog:/var/log/auditlog \
  -e AUDIT_LEVEL=1 \
  rancher/rancher:stable
  
#### Create an access key for command line operations (Doesnt work on self-signed certs)

- endpoint  : https://192.168.1.112/v3
- access-key: token-67rmg
- secret-key: 9qnqxvxpkg5zzm5pj7kkgp985zw4d6dvnf7csxvg7cbvbr5prq4wvt
- bearer-tok: token-67rmg:9qnqxvxpkg5zzm5pj7kkgp985zw4d6dvnf7csxvg7cbvbr5prq4wvt

#### Create the YAML configuration based on docker-compose.yaml

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

### Setup Cluster/Workload [/rke-clusters/custom-nodes](https://rancher.com/docs/rancher/v2.x/en/cluster-provisioning/rke-clusters/custom-nodes/)

- Added a cluster in rancher-ui named "bqdev-cluster" and run the below command for running the rancher-agent 
```
sudo docker run -d --privileged --restart=unless-stopped --net=host \
 -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \
 rancher/rancher-agent:v2.1.5 --server https://192.168.1.112 \
 --token f42lk76lj72qhrm7d6szx6vn6b869mm7kgmmrvjw7tf2gb72hd9wt2 \
 --ca-checksum bc3bb19f279028874626d89515e16a1d5a00f03e7965e64d4c24d9546aba2f27 \
 --etcd --controlplane --worker
```

- Add more nodes as worker only, by running this command on those nodes so that they register with the above main node 
```
sudo docker run -d --privileged --restart=unless-stopped --net=host \
 -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \
 rancher/rancher-agent:v2.1.5 --server https://192.168.1.112 \
 --token f42lk76lj72qhrm7d6szx6vn6b869mm7kgmmrvjw7tf2gb72hd9wt2 \
 --ca-checksum bc3bb19f279028874626d89515e16a1d5a00f03e7965e64d4c24d9546aba2f27 \
 --worker
```

#### Create a namespace bqtest within this cluster
Bisque Test environment where workloads are deployed

Bisque Test environment where workloads are deployed with open NodePort
https://rancher.com/managing-kubernetes-workloads-with-rancher-2-0/

##### Environment Configuration
```
      BISQUE_USER= bisque
      BISQUE_BISQUE_ADMIN_EMAIL= admin@192.168.1.112
      BISQUE_BISQUE_BLOB_SERVICE_STORES= blobs,local
      BISQUE_BISQUE_STORES_BLOBS_MOUNTURL= file://$$datadir/blobdir/$$user/
      BISQUE_BISQUE_STORES_BLOBS_TOP= file://$$datadir/blobdir/
      BISQUE_BISQUE_STORES_LOCAL_MOUNTURL= file://$$datadir/imagedir/$$user/
      BISQUE_BISQUE_STORES_LOCAL_READONLY= 'true'
      BISQUE_BISQUE_STORES_LOCAL_TOP= file://$$datadir/imagedir/
      BISQUE_DOCKER_DOCKER_HUB= biodev.ece.ucsb.edu:5000
      BISQUE_RUNTIME_STAGING_BASE= /tmp/bisque_ranch/data/staging
      BISQUE_SECRET= bq123
      BISQUE_UID= '12027'
      BQ__BISQUE__IMAGE_SERVICE__WORK_DIR= /tmp/bisque_ranch/local/workdir
      BQ__BISQUE__PATHS__DATA= /tmp/bisque_ranch/data
      MAIL_SERVER= dough.ece.ucsb.edu
```

--------------
### Setup Volume

- Mount the host directory for volume using NFS and setup the nfs client access for the cluster
https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nfs-mount-on-ubuntu-16-04
- Or create a persistent volume with local path on the node as /tmp/bisque_ranch
https://www.claudiokuenzler.com/blog/786/rancher-2.0-create-persistent-volume-from-nfs-share


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







