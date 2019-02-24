# Rancher 2 based Jenkins deployment/management guide

- Jenkins LTS Container (jenkins/jenkins:lts) -> [(jenkins/jenkins:2.150.3)](https://hub.docker.com/r/jenkins/jenkins)

- Dockerfile on [jenkinsci/docker](https://github.com/jenkinsci/docker/blob/master/Dockerfile)

- Squid http-proxy for server access: https://help.ubuntu.com/lts/serverguide/squid.html.en

#### Command
- /usr/share/jenkins/rancher/add-docker.sh

#### Volume Mount
Link ~/ws/jenkins_home folder in /var/jenkins_home and change ownership on host 
```
sudo ln -s /home/rahul/ws/jenkins_home /var/jenkins_home

chown -R 1000:1000  ~/ws/jenkins_home
chown 1000 /var/jenkins_home
```
- /var/run/docker.sock
- /usr/bin/docker
- /var/jenkins_home

In case you are using rancher and want to deploy the container on a particular node then make sure that folder is NFS mounted and exists.
```
# bqstage(192.168.1.123) node will be used to deploy jenkins
sudo mount 192.168.1.123:/var/jenkins_home /var/jenkins_home
```
##### Test Run 
docker run -p 8088:8080 -p 50000:50000 -v /var/jenkins_home:/var/jenkins_home jenkins/jenkins:lts

----------------------
### Lets create a deployment in a cluster

- Name: jenkins-bq
- Image: jenkins/jenkins:lts
- Namespace: jenkins
- Port Mapping: 8080-tcp-NodePort-Random
- Environment Variables: No Change
- Node Scheduling: Run all the pods on a particular host with GPU capability
- Health Check: No change
- Volumes: Persistent Volume claim and set the mount point as /var/jenkins_home
- Scaling: No change
- Command: No Change
- Networking: No Change
- Labels: No change
- Security: No change

#### Port
- 8080
