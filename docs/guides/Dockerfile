#
# Ubuntu Bisque Dockerfile
#
# 
#

# ------------------------------------------------------------
# Create a volume 
# docker volume create --name bqvol
# 
# Install Docker Instance
# docker build -t bqdev . -f Dockerfile
#
# Run instance and bash
# docker run -it -p 52080:8080 -v $(pwd):/home/karma/ws --mount source=bqvol,target=/home/karma/bqvol  bqdev
# 
# Delete Images 
# ------------------------------------------------------------
# Pull base image.
FROM ubuntu:16.04
MAINTAINER Rahul Vishwakarma <vishwakarma.rhl@gmail.com>

# Root user installations
RUN echo "Install Bisque System"

RUN \
	DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y software-properties-common
RUN \
	DEBIAN_FRONTEND=noninteractive apt-add-repository multiverse
RUN \
  	DEBIAN_FRONTEND=noninteractive apt-get install -y xubuntu-desktop xvfb firefox
RUN \
  	DEBIAN_FRONTEND=noninteractive apt-get install -y sudo tightvncserver x11vnc xfonts-base vim openssh-server build-essential

# Setup SSH and VNC
RUN service ssh restart
RUN mkdir ~/.vnc
RUN x11vnc -storepasswd vncserver ~/.vnc/passwd

# Packages Pre-requisite
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install -y python python-dev python-pip python-virtualenv python-numpy python-scipy libxml2-dev libxslt1-dev libhdf5-dev git cmake
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install -y libmysqlclient-dev libpq-dev mercurial postgresql postgresql-client libsqlite3-dev
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install -y python-paver python-setuptools graphviz libgraphviz-dev pkg-config openslide-tools  python-openslide libfftw3-dev libbz2-dev libz-dev
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install -y liblcms2-dev  libtiff-dev libpng-dev libgdcm2.6 libopenslide-dev libopenslide0

# Packages source compile 
WORKDIR /var/opt
# Image Convert
RUN wget https://bitbucket.org/dimin/bioimageconvert/downloads/imgcnv_ubuntu16_2.4.3.tar.gz
RUN tar -xvzf imgcnv_ubuntu16_2.4.3.tar.gz
RUN cp imgcnv_ubuntu16_2.4.3/imgcnv /usr/local/bin/
RUN cp imgcnv_ubuntu16_2.4.3/libimgcnv.so.2.4.3 /usr/local/lib/
RUN ln -s /usr/local/lib/libimgcnv.so.2.4.3 /usr/local/lib/libimgcnv.so.2.4
RUN ln -s /usr/local/lib/libimgcnv.so.2.4 /usr/local/lib/libimgcnv.so.2
RUN ln -s /usr/local/lib/libimgcnv.so.2 /usr/local/lib/libimgcnv.so
RUN ldconfig

# OpenJpeg
RUN git clone https://github.com/uclouvain/openjpeg openjpeg
RUN mkdir openjpeg/build
WORKDIR /var/opt/openjpeg/build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release
RUN make -j4 install
RUN ldconfig
RUN easy_install http://biodev.ece.ucsb.edu/binaries/depot/tgext.registration2/tgext.registration2-0.5.2.tar.gz

# Define working directory and user
ENV USER=root
ENV HOME=/root
RUN export USER HOME
USER ${USER}
WORKDIR ${HOME}
RUN echo 'USER=root' >> ${HOME}/.bashrc
RUN echo 'HOME=/root' >> ${HOME}/.bashrc
RUN echo 'export USER HOME' >> ${HOME}/.bashrc

# Additional user for Development
RUN useradd -m karma && echo "karma:karma" | chpasswd && adduser karma sudo

# Install All Bisque Packages
RUN mkdir ${HOME}/bisque 
WORKDIR ${HOME}/bisque
RUN wget http://biodev.ece.ucsb.edu/projects/bisquik/export/tip/bisque-stable/contrib/bootstrap/bisque-bootstrap.py && echo $(pwd)
RUN python bisque-bootstrap.py bqenv

# Fix the requirements file and try installing again
RUN sed -i 's/.*psycopg2==2.6.1.*/psycopg2==2.7.1./' ${HOME}/bisque/requirements.txt
USER ${USER}
RUN easy_install http://biodev.ece.ucsb.edu/binaries/depot/tgext.registration2/tgext.registration2-0.5.2.tar.gz
RUN pip install -i https://biodev.ece.ucsb.edu/py/bisque/dev/+simple -r requirements.txt 

# Paver config/setup
#RUN bqenv/bin/activate && paver setup 

RUN echo "\nNow, configure Bisque using \n1. paver setup => 'sudo bash && source bqenv/bin/activate && paver setup' \n2. bq-admin setup => 'sudo bash && source bqenv/bin/activate && bq-admin setup' \n3. Open Bisque on host system at http://localhost:52080/client_service/"

# Define default command.
CMD ["bash"]

# Expose ports.
EXPOSE 52021:80
EXPOSE 52022:22
EXPOSE 52023:5900
EXPOSE 52080:8080

# Do this manually to run VNC on this machine
# RUN vncserver -geometry 1440x900 -rfbport 5900
RUN echo "\nAccessible Ports \n1. VNC on localhost:52023 \n2. SSH on localhost:52022"