The Condor instructions are based out of custom image(biodev.ece.ucsb.edu:5000/condor)


Official Docs: https://research.cs.wisc.edu/htcondor/manual/v8.8

###### References:
- Condor [Submit Jobs (Official Docs)](https://research.cs.wisc.edu/htcondor/manual/v8.2/2_5Submitting_Job.html)
  - Multi Node [Condor Pool (Blog)](https://spinningmatt.wordpress.com/2011/06/12/getting-started-creating-a-multiple-node-condor-pool/)
  - Simple [Condor Cluster (Blog)](https://www.linux.com/news/setting-condor-cluster)
- Condor [Examples of Security Configurations (Official Docs)](https://research.cs.wisc.edu/htcondor/manual/v8.8/Security.html)
- Install Docker Community Edition https://docs.docker.com/install/linux/docker-ce/ubuntu/

### Topology

The condor image available at the registry has ```htcondor==8.4.2~dfsg.1-1build1``` pre-installed.

- Submit Node   (host = bisquesvc.prod)
- Master node   (host = master.condor)
- Worker Nodes  (host = worker*.condor) 
  - Docker typically runs at worker and on the Bisque submit node for cases where we dont use condor at all
  - Test this using ```docker ps``` on the worker nodes

> Now on each node we should start Condor and also make sure that the hostname "master.condor" is reachable from all the nodes in the pool, including the bisque submit node.

```
$ ping master.condor
    PING master.condor.svc.cluster.local (10.43.55.33) 56(84) bytes of data.
$ service condor start
```

### Master/Worker Condor Config

#### Initiate startd at master and workers

``` 
condor_startd 
```

#### Condor config ``` vim /etc/condor/condor_config.local ```

Add the following in the section where you see ALLOW_READ/WRITE keys

```
ALLOW_ADMINISTRATOR = $(CONDOR_HOST)
ALLOW_OWNER = $(FULL_HOSTNAME), $(ALLOW_ADMINISTRATOR)
ALLOW_READ = *
ALLOW_WRITE = *
ALLOW_NEGOTIATOR = *
ALLOW_NEGOTIATOR_SCHEDD = *
ALLOW_WRITE_COLLECTOR = $(ALLOW_WRITE), $(FLOCK_FROM)
ALLOW_WRITE_STARTD    = $(ALLOW_WRITE), $(FLOCK_FROM)
ALLOW_READ_COLLECTOR  = $(ALLOW_READ), $(FLOCK_FROM)
ALLOW_READ_STARTD     = $(ALLOW_READ), $(FLOCK_FROM)
ALLOW_CLIENT = *
ALLOW_ADVERTISE_STARTD = *

SEC_DEFAULT_NEGOTIATION = NEVER
SEC_DEFAULT_AUTHENTICATION = NEVER

```

#### Reconfig & Restart Condor

```
condor_reconfig
service condor restart
```

### BisqueSvc Submit Node Condor Config

Here is contents of the production configuration ``` /etc/condor/condor_config.local ``` file

```
CONDOR_HOST = master.condor
COLLECTOR_NAME = CBIUCSB
DAEMON_LIST = MASTER,SCHEDD,SHARED_PORT
CONDOR_ADMIN          = admin@biodev.ece.ucsb.edu
##  Do you want to use NFS for file access instead of remote system calls
ALLOW_READ  = $(ALLOW_READ), 172.*, 10.*, 128.111.*, *.ece.ucsb.edu, *.cs.ucsb.edu
ALLOW_WRITE = $(ALLOW_WRITE), 172.*, 10.*, 128.111.*, *.ece.ucsb.edu, *.cs.ucsb.edu
ALLOW_NEGOTIATOR      = 172.*, 10.*, 128.111.*

#https://lists.cs.wisc.edu/archive/htcondor-users/2016-December/msg00046.shtml
DISCARD_SESSION_KEYRING_ON_STARTUP = false

# Use CCB with shared port so outside units can talk to
USE_SHARED_PORT = TRUE
SHARED_PORT_ARGS = -p 9886
UPDATE_COLLECTOR_WITH_TCP = TRUE
BIND_ALL_INTERFACES = TRUE

# Slots for multi-cpu machines
NUM_SLOTS = 1
NUM_SLOTS_TYPE_1 = 1
SLOT_TYPE_1 = 100%
SLOT_TYPE_1_PARTITIONABLE = true

START = True
PREEMPT = False
SUSPEND = False
KILL = False
WANT_SUSPEND = False
WANT_VACATE= False
CONTINUE= True
```

### State & logs

- condor_status for the state of the pool

```
root@bisquevc:/source# condor_status

Name               OpSys      Arch   State     Activity LoadAv Mem    ActvtyTime
slot1@master-7b988 LINUX      X86_64 Unclaimed Idle     -1.000 64423  0+13:07:28
slot1@worker-6c6cc LINUX      X86_64 Unclaimed Idle     -1.000 64423  0+13:04:24
                     Total Owner Claimed Unclaimed Matched Preempting Backfill
        X86_64/LINUX     2     0       0         2       0          0        0
               Total     2     0       0         2       0          0        0
```

- condor_q for the schedule of the queue. You can use "-analyse" to get additional details on the jobs.

```
root@bisquesvc:/source# condor_q
-- Schedd: bisquesvc : <10.42.0.15:40007>
 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD

0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
```

### Test Condor 

Condor is configured to be run as a user and not root. So we will change user (su bisque) to bisque and operate with a regular user level privileges for job submittion purposes.

##### Create a file dock.sh with the following commands

```
#!/bin/bash
echo "Hello HTCondor from Job $1 running on `whoami`@`hostname`"
docker --version
sleep 10s
```

##### Create a dock.submit file with the following paramaters

```
executable = dock.sh
arguments = $(Process)
universe = vanilla
output = dock_$(Cluster)_$(Process).out
error= dock_$(Cluster)_$(Process).error
log = dock_$(Cluster)_$(Process).log
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
queue 2
```

##### Now execute  

```
bisque@bisquesvc:~/condor_dock_test$ condor_submit dock.submit
Submitting job(s)..
2 job(s) submitted to cluster 10.
```

- Here we also observe the status of condor queue which should have the jobs running

```
bisque@bisquesvc:~/condor_dock_test$ condor_q
-- Schedd: bisquesvc : <10.42.0.15:9886?...
 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD
  11.0   bisque          3/5  22:37   0+00:00:00 I  0   0.0  dock.sh 0
  11.1   bisque          3/5  22:37   0+00:00:00 I  0   0.0  dock.sh 1

2 jobs; 0 completed, 0 removed, 2 idle, 0 running, 0 held, 0 suspended
```

- When the Master/worker nodes executes the job we see the following state

```
bisque@bisquesvc:~/condor_dock_test$ condor_status
Name               OpSys      Arch   State     Activity LoadAv Mem    ActvtyTime

slot1@master-7b988 LINUX      X86_64 Unclaimed Idle      0.000 64295  0+00:00:04
slot1_1@master-7b9 LINUX      X86_64 Claimed   Busy     -1.000  128  0+00:00:04
slot1@worker-6c6cc LINUX      X86_64 Unclaimed Idle      0.000 64295  0+00:00:04
slot1_1@worker-6c6 LINUX      X86_64 Claimed   Busy     -1.000  128  0+00:00:04
                     Total Owner Claimed Unclaimed Matched Preempting Backfill
        X86_64/LINUX     4     0       2         2       0          0        0
               Total     4     0       2         2       0          0        0
```

- In about 10 seconds this execution will terminate and dump the results in corresponding log files

```
bisque@bisquesvc:~/condor_dock_test$ condor_status
Name               OpSys      Arch   State     Activity LoadAv Mem    ActvtyTime
slot1@master-7b988 LINUX      X86_64 Unclaimed Idle      0.000 64295  0+00:00:04
slot1@worker-6c6cc LINUX      X86_64 Unclaimed Idle      0.000 64295  0+00:00:04
                     Total Owner Claimed Unclaimed Matched Preempting Backfill
        X86_64/LINUX     2     0       0         2       0          0        0
               Total     2     0       0         2       0          0        0

bisque@bisquesvc:~/condor_dock_test$ condor_q
-- Schedd: bisquesvc : <10.42.0.15:9886?...
 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD

0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
```

- To verify the execution at worker/master we can take a look at the /var/log/condor/StartLog

```
# Logs at the master condor node

03/05/19 22:37:54 slot1_1: Request accepted.
03/05/19 22:37:54 slot1_1: Remote owner is bisque@bisquesvc
03/05/19 22:37:54 slot1_1: State change: claiming protocol successful
03/05/19 22:37:54 slot1_1: Changing state: Owner -> Claimed
03/05/19 22:37:54 slot1_1: Got activate_claim request from shadow (10.42.0.15)
03/05/19 22:37:54 /proc format unknown for kernel version 4.15.0
03/05/19 22:37:54 slot1_1: Remote job ID is 11.0
03/05/19 22:37:54 slot1_1: Got universe "VANILLA" (5) from request classad
03/05/19 22:37:54 slot1_1: State change: claim-activation protocol successful
03/05/19 22:37:54 slot1_1: Changing activity: Idle -> Busy
03/05/19 22:37:59 /proc format unknown for kernel version 4.15.0
03/05/19 22:38:04 /proc format unknown for kernel version 4.15.0
03/05/19 22:38:09 /proc format unknown for kernel version 4.15.0
03/05/19 22:38:09 slot1_1: Called deactivate_claim_forcibly()
03/05/19 22:38:09 Starter pid 1141 exited with status 0
03/05/19 22:38:09 slot1_1: State change: starter exited
03/05/19 22:38:09 slot1_1: Changing activity: Busy -> Idle
03/05/19 22:38:09 slot1_1: State change: received RELEASE_CLAIM command
03/05/19 22:38:09 slot1_1: Changing state and activity: Claimed/Idle -> Preempting/Vacating
03/05/19 22:38:09 slot1_1: State change: No preempting claim, returning to owner
03/05/19 22:38:09 slot1_1: Changing state and activity: Preempting/Vacating -> Owner/Idle
03/05/19 22:38:09 slot1_1: State change: IS_OWNER is false
03/05/19 22:38:09 slot1_1: Changing state: Owner -> Unclaimed
03/05/19 22:38:09 slot1_1: Changing state: Unclaimed -> Delete
03/05/19 22:38:09 slot1_1: Resource no longer needed, deleting
```

- Final results of the output could be seen in the dock_11_*.out result files which represents the Job Id = 11

```
bisque@bisquesvc:~/condor_dock_test$ ll
total 36
drwxrwxr-x 2 bisque bisque 4096 Mar  5 22:37 ./
drwxr-xr-x 1 bisque bisque 4096 Mar  5 22:34 ../
-rw-r--r-- 1 bisque bisque    0 Mar  5 22:37 dock_11_0.error
-rw-rw-r-- 1 bisque bisque 1021 Mar  5 22:38 dock_11_0.log
-rw-r--r-- 1 bisque bisque  132 Mar  5 22:38 dock_11_0.out
-rw-r--r-- 1 bisque bisque    0 Mar  5 22:37 dock_11_1.error
-rw-rw-r-- 1 bisque bisque 1021 Mar  5 22:38 dock_11_1.log
-rw-r--r-- 1 bisque bisque  132 Mar  5 22:38 dock_11_1.out
-rw-r--r-- 1 bisque bisque  163 Mar  5 22:34 dock.sh
-rw-r--r-- 1 bisque bisque  253 Mar  5 09:07 dock.submit
```

- Output Result

```
bisque@bisquesvc:~/condor_dock_test$ cat dock_11_1.out
Hello HTCondor from Job 1 running on nobody@master-7b988ddb7d-hnspj
Docker version 17.03.0-ce, build 60ccb22
Completed my first job
```

- Output Log

```
bisque@bisquesvc:~/condor_dock_test$ cat dock_11_1.log
000 (011.001.000) 03/05 22:37:44 Job submitted from host: <10.42.0.15:9886?addrs=10.42.0.15-9886&noUDP&sock=6207_60d7_3>
...
001 (011.001.000) 03/05 22:37:57 Job executing on host: <10.42.0.8:9886?sock=30363_868c>
...
006 (011.001.000) 03/05 22:38:07 Image size of job updated: 1
        8  -  MemoryUsage of job (MB)
        7560  -  ResidentSetSize of job (KB)
...
005 (011.001.000) 03/05 22:38:09 Job terminated.
        (1) Normal termination (return value 0)
                Usr 0 00:00:00, Sys 0 00:00:00  -  Run Remote Usage
                Usr 0 00:00:00, Sys 0 00:00:00  -  Run Local Usage
                Usr 0 00:00:00, Sys 0 00:00:00  -  Total Remote Usage
                Usr 0 00:00:00, Sys 0 00:00:00  -  Total Local Usage
        132  -  Run Bytes Sent By Job
        163  -  Run Bytes Received By Job
        132  -  Total Bytes Sent By Job
        163  -  Total Bytes Received By Job
        Partitionable Resources :    Usage  Request Allocated
           Cpus                 :                 1         1
           Disk (KB)            :        9        1    893677
           Memory (MB)          :        8        1         1
...

```
