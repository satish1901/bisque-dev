


## Openstack @UCSB

We should login to it using our Ucsb NetId credentials(the way you use at gauchospace).

- Link: https://mimic.aristotle.ucsb.edu/
- Authenticate using: Keystone Credentials
- Domain: ucsb
- user: <NETID>
- pass: <NETID_PASSWORD>

##### Notes from Jeff Oakes <oakesj@ucsb.edu> 

1. Create/Launch compute instance
     - Use auto_allocated network (10.0.0.x network)
     - Create the instance (Ubuntu) 
     - Associate the floating IP 
     - Change the deafult security group for access over SSH port 22
     - Create a SSH key and access instance using "ssh -i \*.pem ubuntu@169.\*.\*.\*"

2. Create/Use storage(Ceph based) as attached volume. Format the partition in the instance & mount it (Use GPT label or XFS for TB's of volumes)
     - sudo -i 
     - dmesg | grep vd  
     - mount /dev/vdb1 /mnt
     - df -h
     - help: http://www.darwinbiler.com/openstack-creating-and-attaching-a-volume-into-an-instance/

3. Ansible Playbook for instance configuraiton (Rather than Golden Image or a bash script for installation)

###### Note: Openstack uses 3 KVM instances and try not to launch 3 instances with 32GB RAM at once



## Openstack @CyVerse

Login to Cyverse Openstack using the account created by Chris Martin or Andy Edmond in University of Arizona

- Link: https://tombstone-cloud.cyverse.org
- Domain: cso
- user: vishwakarma
- pass: <SHARED_PASSWORD>

Note: Similar instance and volume creation process as described earlier.