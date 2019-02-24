## [Bisque Development Environment Setup Instructions](https://biodev.ece.ucsb.edu/projects/bisquik/wiki/InstallationInstructions05)

Project Source
- https://bitbucket.org/CBIucsb/bisque
- http://biodev.ece.ucsb.edu/projects/bisquik/export/tip/bisque-stable

Reference
- [Bique Bioimage Google Groups](https://groups.google.com/forum/#!topic/bisque-bioimage/jwo_5sHFeHU)
- [Instructions on installing bisque using docker](https://bitbucket.org/CBIucsb/bisque/src/default/README.md)

##### Setup for Ubuntu 16.04 
---
##### Pre-requisites 
```
sudo apt-get install -y python python-dev python-virtualenv python-numpy python-scipy 
sudo apt-get install -y libxml2-dev libxslt1-dev libhdf5-dev
sudo apt-get install -y libmysqlclient-dev libpq-dev mercurial git cmake
sudo apt-get install -y postgresql postgresql-client libsqlite3-dev
sudo apt-get install -y python-paver python-setuptools
sudo apt-get install -y graphviz libgraphviz-dev pkg-config
sudo apt-get install -y openslide-tools  python-openslide
sudo apt-get install -y libfftw3-dev libbz2-dev libz-dev
sudo apt-get install -y liblcms2-dev libtiff-dev libpng-dev
sudo apt-get install -y libgdcm2.6 libopenslide-dev libopenslide0

```

Install Openjpeg
```
git clone https://github.com/uclouvain/openjpeg
cd openjpeg && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
sudo make -j4 install
sudo ldconfig
```

Install BioImageConvert
- [BioImageConvert Source Repository](https://biodev.ece.ucsb.edu/projects/imgcnv)
- [Prebuilt Binaries Repository](https://bitbucket.org/dimin/bioimageconvert/downloads/)
- Setup for pre-built binaries (below)
```
# Ubuntu 18 version
wget https://bitbucket.org/dimin/bioimageconvert/downloads/imgcnv_ubuntu18_2.5.0.tar.gz

# Ubuntu 16 version
wget https://bitbucket.org/dimin/bioimageconvert/downloads/imgcnv_ubuntu16_2.4.3.tar.gz
tar -xvzf imgcnv_ubuntu16_2.4.3.tar.gz

sudo cp imgcnv_ubuntu16_2.4.3/imgcnv /usr/local/bin/
sudo cp imgcnv_ubuntu16_2.4.3/libimgcnv.so.2.4.3 /usr/local/lib/
sudo ln -s /usr/local/lib/libimgcnv.so.2.4.3 /usr/local/lib/libimgcnv.so.2.4
sudo ln -s /usr/local/lib/libimgcnv.so.2.4 /usr/local/lib/libimgcnv.so.2
sudo ln -s /usr/local/lib/libimgcnv.so.2 /usr/local/lib/libimgcnv.so
sudo ldconfig
```
Alternately, Compile by source and Install 
```
hg clone --insecure http://biodev.ece.ucsb.edu/hg/imgcnv
cd imgcnv && make -j6 
sudo make install
```

---
##### A. Download the Bootstrap installer (Use Python 2.7)
```
$ mkdir bisque && cd bisque
$ wget http://biodev.ece.ucsb.edu/projects/bisquik/export/tip/bisque-stable/contrib/bootstrap/bisque-bootstrap.py
$ python bisque-bootstrap.py bqenv

# Activate Virtualenv
bisque$ source bqenv/bin/activate

```

Fix the requirements.txt
```
#Fix the requirements.txt file using sed -i 's/.*psycopg2==2.6.1.*/psycopg2==2.7.1./' requirements.txt
psycopg2==2.7.1
Minimatic==1.0
Paste==1.7.5.1
httplib2==0.7.3
#tgext.registration==0.1dev

Install separately since packages may be deprecated in PyPi
easy_install http://biodev.ece.ucsb.edu/binaries/depot/tgext.registration2/tgext.registration2-0.5.2.tar.gz

```
Now Install requirements
```
pip install -i https://biodev.ece.ucsb.edu/py/bisque/stretch/+simple/ -r requirements.txt

Alternate Index Url for Development: https://biodev.ece.ucsb.edu/py/bisque/dev/+simple

```

---

##### B. Configure Bisque Environment
```
$ paver setup
```
Expected log tail
```
Installing collected packages: bqengine
  Running setup.py develop for bqengine
Successfully installed bqengine

Now run:
bq-admin setup 
```
```
$ bq-admin setup
```
Expected log tail
```
  ...

Found imgcnv version 2.4.3

    Imgcnv is installed and no-precompiled version exists. Using installed version

Top level site variables are:
  bisque.admin_email=YourEmail@YourOrganization
  bisque.admin_id=admin
  bisque.organization=Your Organization
  bisque.paths.root=.
  bisque.server=http://0.0.0.0:8080
  bisque.title=Image Repository
Change a site variable [Y]? N

  ...

Running setup_config() from bq.websetup
CALLING  <function install_preferences at 0x7f47f191f848>

Initialize your database with:
   $ bq-admin setup createdb

You can start bisque with:
   $ bq-admin server start
then point your browser to:
    http://0.0.0.0:8080
If you need to shutdown the servers, then use:
   $ bq-admin server stop
You can login as admin and change the default password.

Send Installation/Registration report [Y]? N

```

Add "config/runtime-bisque.cfg" for module configuration and docker image registry
- Edit and add run config from config-defaults/runtime-bisque.defaults to config/runtime-bisque.cfg

---

##### C. Run Bisque

Start/Stop the server
```
$ bq-admin server start
$ bq-admin server stop
```

Overview of Installation (Just for review)
```
source bqenv/bin/activate
paver setup    [server|engine]
bq-admin setup [server|engine]
bq-admin deploy public
```

Open in browser
![Browser Client](img/BisqueClientScreen.png?raw=true)

---
#### RUN
Local Bisque Dev setup
###### Load Module Workflow 
- Login using admin:admin 
- Update the email address in the users context menu item (This is important)
- Open Module Manager from the admin user context menu
- Paste the following URL in the Module->Engine Module
```
http://0.0.0.0:8080/engine_service/
```
- List of engine modules could be seen
- ![Bisque Module](img/ModulesBisque.png?raw=true)
- ![Register Module](img/RegisterModule.png?raw=true)
- Drag-n-Drop say Dream3D from the list to the left window and close the window
- Go to Analyse and select Dream3D there
- ![Launch Dream 3D](img/OpenModuleDream3d.png?raw=true)

---
### Further 


###### Load Dream 3D data

==> TODO

- Manually create a virtualenv for development and install dependencies
  ```
  python -m virtualenv bqenv --no-setuptools
  source bqenv/bin/activate
  pip install -r requirements.txt --trusted-host=biodev.ece.ucsb.edu -i https://biodev.ece.ucsb.edu/py/bisque/dev/+simple

  ```

- Install Docker (https://docs.docker.com/install/linux/docker-ce/ubuntu/)
  - Also go through the post-installation steps

- Install Condor (https://research.cs.wisc.edu/htcondor/ubuntu/)
```
rahul@bqdev:~$ /etc/init.d/condor restart
[ ok ] Restarting condor (via systemctl): condor.service.
rahul@bqdev:~$ ps -ef | grep condor
```


