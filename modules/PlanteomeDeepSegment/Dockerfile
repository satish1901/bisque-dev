
# +
# docker build:
#   docker build --no-cache -t bisque_uplanteome -f Dockerfile .
#   docker build  -t biodev.ece.ucsb.edu:5000/bisque_uplanteome .
#
# docker run:
#   docker run -it --net=host biodev.ece.ucsb.edu:5000/bisque_uplanteome bash
# 
# test run:
#    python PlanteomeDeepSegment.py http://loup.ece.ucsb.edu:8088/module_service/mex/00-NKpU4CWiHfupgckuXBNFDd admin:00-NKpU4CWiHfupgckuXBNFDd Simple True 3 False
# -

# use ubuntu base image
FROM ubuntu:16.04

# maintenance record
MAINTAINER Phil Daly "pndaly@cyverse.org"

# update the distro
RUN apt-get -y update && apt-get -y upgrade && apt-get -y autoremove &&  \
    apt-get -y --no-install-recommends install build-essential ca-certificates \
    python-pip python-setuptools python-dev \
    cmake net-tools iputils-ping wget byobu curl git htop man unzip vim \
    python-lxml python-tk python-matplotlib python-numpy python-scipy \
    python-skimage python-opencv gcc g++ curl

# fix certificate issue?
RUN curl https://bootstrap.pypa.io/get-pip.py | python

# install python dependencies
RUN pip install --upgrade pip setuptools
RUN pip install --ignore-installed scipy==1.0.1
RUN pip install torch==0.4.0 torchvision==0.2.1 numpy==1.16.1 \
    opencv-python==3.4.0.12 scikit-image==0.14.2 lxml==3.7.3  \  
    matplotlib==2.2.2 cython==0.28.2 PyMaxflow==1.2.9         \
    pillow==4.1.1 requests==2.10.0 libtiff==0.4.0             \
    tifffile==0.14.0 bqapi==0.5.9

# copy code
WORKDIR /module/workdir/PlanteomeDeepSegment
COPY . /module/workdir/PlanteomeDeepSegment

# run command
ENV PYTHONPATH /module/workdir/PlanteomeDeepSegment:/module/workdir
ENV PATH /module/workdir/PlanteomeDeepSegment:/module/workdir:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CMD [ 'python', 'PlanteomeDeepSegment.py' ]
