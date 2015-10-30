FROM debian:wheezy
MAINTAINER Kris Kvilekval<kris@cs.ucsb.edu>
RUN apt-get update && apt-get install -yq python  unzip wget libxext6 libxt6

ADD input.txt /mcr-install/input.txt
# Fetch locally
#COPY MCR_R2015b_glnxa64_installer.zip /mcr-install/

RUN cd /mcr-install && \
    wget -nv http://www.mathworks.com/supportfiles/MCR_Runtime/R2015b/MCR_R2015b_glnxa64_installer.zip && \
    unzip MCR_R2015b_glnxa64_installer.zip && \
    mkdir /opt/mcr && \
    ./install -inputFile input.txt && \
    cd / && \
    rm -rf mcr-install

ENV MATLAB_HOME /opt/mcr/v90
ENV LD_LIBRARY_PATH $MATLAB_HOME/runtime/glnxa64:\
$MATLAB_HOME/bin/glnxa64:\
$MATLAB_HOME/sys/os/glnxa64:\
$MATLAB_HOME/sys/java/jre/glnxa64/jre/lib/amd64/native_threads:\
$MATLAB_HOME/sys/java/jre/glnxa64/jre/lib/amd64/server:\
$MATLAB_HOME/sys/java/jre/glnxa64/jre/lib/amd64:
ENV XAPPLRESDIR=$MATLAB_HOME/X11/app-defaults
ENV PATH /module:$PATH
VOLUME /module
WORKDIR /module
CMD [ "bash" ]
