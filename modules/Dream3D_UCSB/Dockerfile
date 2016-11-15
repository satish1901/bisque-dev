FROM dream3d_ucsb
MAINTAINER nobody@example.com
# dream3d searches for Plugins relative to the bin folder (on Linux); maybe a bug??
RUN ln -s /build/Plugins/* /build/Bin/Plugins/
WORKDIR /module
COPY Dream3D /module/
COPY pydist /module/pydist/
CMD  [ "Dream3D" ]
