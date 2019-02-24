
##### Rancher: http://saw.ece.ucsb.edu:8080

Container organization and plan for rancher setup

##### Main Containers
| Instance Name | Host or IP  | Image Name | Remarks    |
| :---          | :---        | :---       | :---       |
| condor-nodes | IP ADDR     | biodev.ece.ucsb.edu:5000/condor      | One master and 4 worker nodes |
| elasticsearch 2 | IP ADDR     | rancher/elasticsearch-conf:v0.5.0     | One container each elasticsearch-[clients, datanodes & masters] |
| elasticsearch base/data | IP ADDR     | elasticsearch:2.4.3-alpine     | Two containers(base & data volume) for each elasticsearch-[clients, datanodes & masters] |
| elasticsearch kopf | IP ADDR     | rancher/kopf:v0.4.0     | One container |
| healthcheck | IP ADDR     | rancher/healthcheck:v0.3.6     | One on each instance |
| ipsec cni-driver, connectivity-check, router | IP ADDR     | rancher/net:v0.13.11     | One on each instance for executing start-cni-driver, connectivity-check, and start-ipsec |
| ipsec-ipsec | IP ADDR     | rancher/net:holder     | One on each instance |
| network-services-meta | IP ADDR     | rancher/metadata:v0.10.2     | One on each instance start.sh,rancher-metadata,-reload-interval-limit=1000,-subscribe |
| network-services-meta-dns | IP ADDR     | rancher/dns:v0.17.3     | One on each instance rancher-dns,--listen,169.254.169.250:53,--metadata-server=localhost |
| network-services-manager | IP ADDR     | rancher/network-manager:v0.7.20    | One on each instance plugin-manager,--disable-cni-setup,--metadata-address,169.254.169.250 |
| nfs-driver | IP ADDR     | rancher/storage-nfs:v0.9.1     | One on each instance |
| rancher-agent | IP ADDR     | rancher/agent:v1.2.10      | One on each instance |
| scheduler | IP ADDR     | rancher/scheduler:v0.8.3     | One instance  scheduler,--metadata-address,169.254.169.250 |
| janitor-cleanup | IP ADDR     | meltwater/docker-cleanup:1.8.0     | One on each instance |
| kibana | IP ADDR     | kibana:5.3.0      | One instance |
| kibana rancher | IP ADDR     | rancher/lb-service-haproxy:v0.7.9, rancher/nginx:v1.9.4-3, rancher/nginx-conf:v0.2.0      | One instance |
| production logsvc | IP ADDR     | biodev.ece.ucsb.edu:5000/logger_ucsb:dev      | One instance |
| LetsEncrypt | IP ADDR     | janeczku/rancher-letsencrypt:v0.4.0     | One instance |
| jenkins | IP ADDR     | jenkins/jenkins:lts     | One instance |
| jenkins plugins | IP ADDR     | biodev.ece.ucsb.edu:5000/jenkins-cbi-plugins:v0.1.1     | One instance |



##### Modules Containers
| Instance Name | Host or IP  | Image Name | Remarks    |
| :---          | :---        | :---       | :---       |
| Dream3D       | IP ADDR     | biodev.ece.ucsb.edu:5000/bisque_dream3d    | Dream3D Module |
| Predict Strength | IP ADDR     | biodev.ece.ucsb.edu:5000/predict_strength   | Predict Strength Module |
| Connoisseur | IP ADDR     | biodev.ece.ucsb.edu:5000/bisque-caffe-xenial:dev   | Predict Strength Module |




### [Reference](https://github.com/pndaly/BisQue_Platform_Guide): https://github.com/pndaly/BisQue_Platform_Guide

- Sample Deep Learning Module: [Planteome Deep Segment Analysis](https://github.com/Planteome/planteome-deep-segmenter-dockerized)
- 