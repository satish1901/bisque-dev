""" Setup the environment for a docker execution.
"""

from __future__ import with_statement

import os,sys
import string
from module_env import BaseEnvironment, ModuleEnvironmentError

from bq.util.converters import asbool


DOCKER_RUN="""#!/bin/bash

${DOCKER_LOGIN}
docker create  --name ${STAGING_ID} ${DOCKER_IMAGE}  $@
${DOCKER_CP}
docker start ${STAGING_ID}
docker wait  ${STAGING_ID}
docker cp ${STAGING_ID}:/module/ .
docker rm ${STAGING_ID}
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

    def setup_environment(self, runner):
        # Construct a special environment script
        if not self.enabled:
            return

        docker_login=""
        if self.docker_user and self.docker_pass:
            docker_login = "docker login -u %s -p %s -e %s %s" % (self.docker_user, self.docker_pass, self.docker_email, self.docker_hub)

        for mex in runner.mexes:
            #if mex.executable:
            docker_image = "/".join (filter (lambda x:x, [ self.docker_hub, self.docker_user, self.docker_image ]))
            #docker = os.path.join('.', os.path.basename(docker))

            module_vars =  runner.module_cfg.get ('command', asdict=True)
            module_files = [x.strip () for x in module_vars.get ('files', '').split (',') ]
            runner.log ("docker files setup %s" % module_vars.get ('files') )

            copylist = list(module_files)
            if mex.executable:
                # if there are additional executable wrappers needed in the environment, add them to copylist
                # (e.g., "matlab_run python mymodule")
                for p in mex.executable:
                    pexec = os.path.join(mex.rundir, p)
                    runner.log ("Checking exec %s->%s" % (pexec, os.path.exists (pexec)))
                    if os.path.exists (pexec) and p not in module_files:
                        copylist.append (p)
            #runner.log ("docker setup: %s"% mex.files)
            docker = self.create_docker_launcher(mex.rundir, docker_image, docker_login, mex.staging_id, copylist)
            if mex.executable:
                mex.executable.insert(0, docker)

    def create_docker_launcher(self, dest, docker_image, docker_login, staging_id, copylist):
        docker_run = DOCKER_RUN
        #if self.matlab_launcher and os.path.exists(self.matlab_launcher):
        #    matlab_launcher = open(self.matlab_launcher).read()
        content = string.Template(docker_run)
        content = content.safe_substitute(DOCKER_IMAGE=docker_image,
                                          DOCKER_LOGIN = docker_login,
                                          STAGING_ID = staging_id,
                                          DOCKER_CP="\n".join ( "docker cp %s %s:/module/%s" % (f, staging_id, f) for f in copylist )
                                          )
        if os.name == 'nt':
            path = os.path.join(dest, 'docker_run.bat' )
        else:
            path = os.path.join(dest, 'docker_run' )
        with open(path, 'w') as f:
            f.write (content)
        os.chmod (path, 0744)
        return path
