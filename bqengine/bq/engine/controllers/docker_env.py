""" Setup the environment for a docker execution.
"""

from __future__ import with_statement

import os
import string

from bq.util.converters import asbool
from .base_env import strtolist
from .module_env import BaseEnvironment, ModuleEnvironmentError


DOCKER_RUN="""#!/bin/bash
set -x

#mkdir -p ./output_files
${DOCKER_LOGIN}
${DOCKER_PULL}
CONTAINER=$$(docker create ${DOCKER_IMAGE}  $@)
${DOCKER_INPUTS}
docker start $CONTAINER
docker wait  $CONTAINER
${DOCKER_OUTPUTS}
# docker will not copy to existing directory .. so create a new one and copy from that
docker cp $CONTAINER:/module/ output_files
mv ./output_files/* .
#docker rm $CONTAINER
"""

class DockerEnvironment(BaseEnvironment):
    '''Docker Environment

    This Docker environment prepares an execution script to run docker


    Enable  the Docker environment by adding to your module.cfg::
       environments = ..., Docker, ...

    The output file "docker.run" will be placed in the staging directory
    and used as the executable for any processing and will be called with
    matlab_launch executable argument argument argument

    The script will be generated based on internal template which can
    be overriden with (in runtime-module.cfg)::
       matlab_launcher = mymatlab_launcher.txt

    '''

    name = "Docker"
    config = { }
    matlab_launcher = ""

    def process_config (self, runner, **kw):
        runner.load_section ('docker', runner.bisque_cfg)
        runner.load_section ('docker', runner.module_cfg)
        self.enabled = asbool(runner.config.get ('docker.enabled', False))
        self.docker_hub = runner.config.get('docker.hub', '')
        self.docker_image = runner.config.get('docker.image', '')
        self.docker_user = runner.config.get ('docker.hub.user', '')
        self.docker_pass = runner.config.get('docker.hub.password', '')
        self.docker_email = runner.config.get('docker.hub.email', '')
        #self.matlab_launcher = runner.config.get('runtime.matlab_launcher', None)
        #if self.matlab_launcher is not None and not os.path.exists(self.matlab_launcher):
        #    raise ModuleEnvironmentError("Can't find matlab script %s" % self.matlab_launcher)
        #if runner.named_args.has_key('matlab_home'):
        #    self.matlab_home = runner.named_args['matlab_home']

    def setup_environment(self, runner, build=False):
        # Construct a special environment script
        runner.info ("docker environment setup")
        if not self.enabled:
            runner.info ("docker disabled")
            return


        if build:
            #docker_outputs = [ "." ]
            #module_vars =  runner.module_cfg.get ('command', asdict=True)
            #docker_inputs = [x.strip () for x in module_vars.get ('files', '').split (',') ]
            runner.mexes[0].files = strtolist (runner.mexes[0].files)
            runner.mexes[0].outputs = [ ]
            return


        docker_login=""
        if self.docker_user and self.docker_pass:
            docker_login = "docker login -u %s -p %s -e %s %s" % (self.docker_user, self.docker_pass, self.docker_email, self.docker_hub)


        for mex in runner.mexes:
            docker_pull =""
            #if mex.executable:
            docker_image = "/".join ([x for x in  [ self.docker_hub, self.docker_user, self.docker_image ] if x ])
            #docker = os.path.join('.', os.path.basename(docker))

            # always pull an image
            if self.docker_hub:
                docker_pull = "docker pull %s" % docker_image


            docker_outputs = [ ]
            docker_inputs  = []
            #module_vars =  runner.module_cfg.get ('command', asdict=True)
            #docker_inputs = [x.strip () for x in module_vars.get ('files', '').split (',') ]

            #runner.log ("docker files setup %s" % mex.get ('files') )

            # Static files will already be inside container (created during build)

            # if there are additional executable wrappers needed in the environment, add them to copylist
            # (e.g., "matlab_run python mymodule")
            if  mex.executable:
                for p in mex.executable:
                    pexec = os.path.join(mex.rundir, p)
                    #runner.debug ("Checking exec %s->%s" % (pexec, os.path.exists (pexec)))
                    #if os.path.exists (pexec) and p not in docker_inputs:
                    if os.path.exists (pexec) and p not in mex.files:
                        docker_inputs.append (p)

            docker = self.create_docker_launcher(mex.rundir, mex.mex_id,
                                                 docker_image, docker_login, docker_pull, docker_inputs, docker_outputs)
            if mex.executable:
                mex.executable.insert(0, docker)
                #mex.files = ",".join (docker_inputs)
                #mex.output_files = ",".join (docker_outputs)
                mex.files = docker_inputs
                mex.output_files = docker_outputs +  ['output_files/']

                runner.debug ("mex files %s outputs %s", mex.files, mex.output_files)

    def create_docker_launcher(self, dest, mex_id,
                               docker_image,
                               docker_login,
                               docker_pull,
                               docker_inputs,
                               docker_outputs,):
        docker_run = DOCKER_RUN
        #if self.matlab_launcher and os.path.exists(self.matlab_launcher):
        #    matlab_launcher = open(self.matlab_launcher).read()
        content = string.Template(docker_run)
        content = content.safe_substitute(
            MEX_ID = mex_id,
            DOCKER_IMAGE = docker_image,
            DOCKER_LOGIN = docker_login,
            DOCKER_PULL  = docker_pull,
            DOCKER_INPUTS="\n".join("docker cp %s %s:/module/%s" % (f, mex_id, f) for f in docker_inputs),
            DOCKER_OUTPUTS="\n".join("docker cp %s:/module/%s %s" % (mex_id, f,f) for f in docker_outputs),
        )
        if os.name == 'nt':
            path = os.path.join(dest, 'docker_run.bat' )
        else:
            path = os.path.join(dest, 'docker_run' )
        with open(path, 'w') as f:
            f.write (content)
        os.chmod (path, 0744)
        return path
