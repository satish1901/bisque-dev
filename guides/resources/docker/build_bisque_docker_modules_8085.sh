#!/bin/bash


# +
#
# Name:           build_bisque_docker_modules.sh
# Description:    instructions for building and running a docker container for BisQue modules
# Author(s):      Phil Daly (pndaly@email.arizona.edu), Rahul Vishwakarma (vishwakarma@ucsb.edu)
# Version:        v0.3
# History:        2018-05-11: based on https://bitbucket.org/CBIucsb/bisque/src/default/README.md
#                 2018-05-14: added mounted volumes mapped to local sub-directories
#                 2018-05-15: change flag from --use-x11 to --use-linux or --use-mac
#		  2019-01-14: modified the script to expose configuration <vishwakarma@ucsb.edu>
# Usage:          % bash build_bisque_docker_modules.sh [--use-linux | --use-mac]
# Pre-Requisites: docker (linux, macosx), firefox (linux)
#
# -


# +
# get command line argument(s)
# -
USE_LINUX=1
while test $# -gt 0; do
  case "${1}" in
    --help|--HELP)
      echo "$0 [--use-linux | --use-mac]"
      exit 0
      ;;
    --use-linux|--USE-LINUX)
      USE_LINUX=1
      shift
      ;;
    --use-mac|--USE-MAC)
      USE_LINUX=0
      shift
      ;;
    *)
      break
      ;;
  esac
done


# +
# function(s): write_cmd(), write_err(), write_info(), write_next(), isDockerRunning()
# -
write_cmd () {
  YELLOW='\033[0;33m'
  NCOL='\033[0m'
  printf "${YELLOW}<<EXEC>> ${1}${NCOL}\n"
}

write_err () {
  RED='\033[0;31m'
  NCOL='\033[0m'
  printf "${RED}<<ERROR>> ${1}${NCOL}\n"
}

write_info () {
  BLUE='\033[0;34m'
  NCOL='\033[0m'
  printf "${BLUE}<<INFO>> ${1}${NCOL}\n"
}

write_next () {
  CYAN='\033[0;36m'
  NCOL='\033[0m'
  printf "${CYAN}<<NEXT>> ${1}${NCOL}\n"
}

isDockerRunning () {
  if [ ${1} -eq 1 ]; then
    echo `ps -ef | grep 'dockerd'`
  else
    echo `ps -ef | grep 'com[.]docker[.]hyperkit'`
  fi
}


# +
# check docker is running
# -
check_docker=`isDockerRunning ${USE_LINUX}`
if [ -z "${check_docker}" ]; then
  write_err "docker daemon is not running"
  exit 0
else
  write_info "docker daemon is running"
fi


# +
# create sub-directories
# -
STEP="1/8"
write_info "Step ${STEP}: creating sub-directories ..."
if [ ! -d ~/bisque-docker ]; then
  write_cmd "mkdir ~/bisque-docker"
  mkdir ~/bisque-docker
else
  write_info "Step ${STEP}: using existing ~/bisque-docker"
fi

if [ ! -d ~/bisque-docker/container-data ]; then
  write_cmd "mkdir ~/bisque-docker/container-data"
  mkdir ~/bisque-docker/container-data
else
  write_info "Step ${STEP}: using existing ~/bisque-docker/container-data"
fi

if [ ! -d ~/bisque-docker/container-config ]; then
  # create sub-directory
  write_cmd "mkdir ~/bisque-docker/container-config"
  mkdir ~/bisque-docker/container-config
else
  write_info "Step ${STEP}: using existing ~/bisque-docker/container-config"
fi



# +
# different paths depending on if we have already downloaded the modules before
# -
cd ~/bisque-docker
if [ ! -d ~/bisque-docker/container-modules ]; then

  # create sub-directory
  write_cmd "mkdir ~/bisque-docker/container-modules"
  mkdir ~/bisque-docker/container-modules

  # start local bisque container
  STEP="2/8"
  write_info "Step ${STEP}: start local bisque container ..."
  if [ ${USE_LINUX} -eq 1 ]; then
    write_cmd "xterm -e docker run --name bisque --rm -p 8080:8080 cbiucsb/bisque05:stable &"
    xterm -e docker run --name bisque --rm -p 8080:8080 cbiucsb/bisque05:stable &
  else
    write_cmd "osascript -e 'tell app \"Terminal\" to do script \"docker run --name bisque --rm -p 8080:8080 cbiucsb/bisque05:stable\"'"
    osascript -e 'tell app "Terminal" to do script "docker run --name bisque --rm -p 8080:8080 cbiucsb/bisque05:stable"'
  fi

  # wait for local bisque server to become ready
  STEP="3/8"
  until [ "`docker inspect -f {{.State.Running}} bisque 2> /dev/null`" == "true" ]; do
    write_info "Step ${STEP}: waiting for container to become available ..."
    sleep 1
  done
  write_info "Step ${STEP}: container is available ..."

  while ! curl http://localhost:8080/ 2> /dev/null; do
    write_info "Step ${STEP}: waiting for bisque on localhost to become available ..."
    sleep 1
  done
  write_info "Step ${STEP}: bisque on localhost is available ..."

  # copy module directory out of container
  STEP="4/8"
  write_info "Step ${STEP}: copying modules from local bisque container ..."
  write_cmd "docker cp bisque:/source/modules ~/bisque-docker/container-modules"
  docker cp bisque:/source/modules ~/bisque-docker/container-modules

  # Copy the configuration files out of container
  STEP="4.5/8"
  write_info "Step ${STEP}: copying configs from local bisque container ..."
  write_cmd "docker cp bisque:/source/config ~/bisque-docker/container-config"
  docker cp bisque:/source/config ~/bisque-docker/container-config

  # stop the docker container
  STEP="5/8"
  write_info "Step ${STEP}: stopping local bisque container ..."
  write_cmd "docker stop bisque"
  docker stop bisque

else
  write_info "Step ${STEP}: using existing ~/bisque-docker/container-modules"
  STEP="2/8"
  write_info "Step ${STEP}: skipping ..."
  STEP="3/8"
  write_info "Step ${STEP}: skipping ..."
  STEP="4/8"
  write_info "Step ${STEP}: skipping ..."
  STEP="5/8"
  write_info "Step ${STEP}: skipping ..."
fi


# +
# re-start container with host mounted modules and data directory
# -
STEP="6/8"
write_info "Step ${STEP}: re-start local bisque container with local modules and data stores ..."
if [ ${USE_LINUX} -eq 1 ]; then
  write_cmd "xterm -e docker run --name bisque --rm -p 8080:8080 -v ~/bisque-docker/container-modules:/source/modules -v $(pwd)/container-config:/source/config -v ~/bisque-docker/container-data:/source/data cbiucsb/bisque05:stable &"
  xterm -e docker run --name bisque --rm -p 8080:8080 -v ~/bisque-docker/container-modules:/source/modules -v $(pwd)/container-config:/source/config -v ~/bisque-docker/container-data:/source/data cbiucsb/bisque05:stable &
else
  write_cmd "osascript -e 'tell app \"Terminal\" to do script \"docker run --name bisque --rm -p 8080:8080 -v ~/bisque-docker/container-modules:/source/modules -v ~/bisque-docker/container-data:/source/data cbiucsb/bisque05:stable\"'"
  osascript -e 'tell app "Terminal" to do script "docker run --name bisque --rm -p 8080:8080 -v ~/bisque-docker/container-modules:/source/modules -v ~/bisque-docker/container-data:/source/data cbiucsb/bisque05:stable"'
fi


# +
# wait for local bisque server to become ready
# -
STEP="7/8"
until [ "`docker inspect -f {{.State.Running}} bisque 2> /dev/null`" == "true" ]; do
  write_info "Step ${STEP}: waiting for container to become available ..."
  sleep 1
done
write_info "Step ${STEP}: container is available ..."


# +
# open browser to it
# -
STEP="8/8"
while ! curl http://localhost:8080/ 2> /dev/null; do
  write_info "Step ${STEP}: waiting for bisque on localhost to become available ..."
  sleep 1
done
write_info "Step ${STEP}: bisque on localhost is available ..."

write_info "Step ${STEP}: opening bisque on local container ..."
if [ ${USE_LINUX} -eq 1 ]; then
  write_cmd "firefox http://localhost:8080 2>&1 /dev/null &"
  firefox http://localhost:8080 2>&1 /dev/null &
else
  write_cmd "open http://localhost:8080 2>&1 /dev/null &"
  open http://localhost:8080 2>&1 /dev/null &
fi


# +
# next (interactive) step(s)
# -
write_next "\nLogin using admin:admin credentials"
write_next "Navigate to module manager under the admin account\n"
write_next "If your local hostname is resolved via DNS, do the following:"
write_next "  in the left-hand panel, insert http://<hostname>:8080/engine_service\n"
write_next "If your local hostname is not resolved via DNS, do the following:"
write_next "  in the left-hand panel, insert http://localhost:8080/engine_service\n"
write_next "Press the 'Load' button"

