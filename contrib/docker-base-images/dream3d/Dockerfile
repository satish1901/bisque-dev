FROM ubuntu
ENV DEBIAN_FRONTEND none
# RUN apt-get update -y && apt-get install -y libglib2.0 libboost-all-dev libeigen3-dev libxext6
RUN apt-get update -y && apt-get install -y libglib2.0 libxext6 libglu1-mesa-dev
ADD DREAM3D-6.2.327-Linux-x86_64.tar.gz /dream3d/
# dream3d searches for Plugins relative to the bin folder (on Linux); maybe a bug??
RUN ln -s /dream3d/DREAM3D-6.2.327-Linux-x86_64/Plugins /dream3d/DREAM3D-6.2.327-Linux-x86_64/bin
CMD ["/bin/bash"]
