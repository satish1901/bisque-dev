""" Setup the environment for a docker execution.
"""

from __future__ import with_statement

import os,sys
import string
from module_env import BaseEnvironment, ModuleEnvironmentError



DOCKER_RUN="""#!/bin/bash

exec docker run --rm  -v $(pwd):/module ${DOCKER_IMAGE} $@
"""

class DockerEnvironment(BaseEnvironment):
    '''Docker Environment

    This script environment prepares an execution script to run docker


    Enable  the matlab environment by adding to your module.cfg::
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
        self.docker_hub = runner.config['docker.hub']
        self.docker_image = runner.config.get ('docker.image', '')
        #self.matlab_launcher = runner.config.get('runtime.matlab_launcher', None)
        #if self.matlab_launcher is not None and not os.path.exists(self.matlab_launcher):
        #    raise ModuleEnvironmentError("Can't find matlab script %s" % self.matlab_launcher)
        #if runner.named_args.has_key('matlab_home'):
        #    self.matlab_home = runner.named_args['matlab_home']

    def setup_environment(self, runner):
        # Construct a special environment script
        for mex in runner.mexes:
            #if mex.executable:
            docker_image = "%s" % (self.docker_image)
            if '/' not in docker_image:
                docker_image = "%s/%s" % (self.docker_hub , docker_image)
            docker = self.create_docker_launcher(mex.rundir, docker_image)
            docker = os.path.join('.', os.path.basename(docker))
            if mex.executable:
                mex.executable.insert(0, docker)

    def create_docker_launcher(self, dest, docker_image):
        docker_run = DOCKER_RUN
        #if self.matlab_launcher and os.path.exists(self.matlab_launcher):
        #    matlab_launcher = open(self.matlab_launcher).read()
        content = string.Template(docker_run)
        content = content.safe_substitute(DOCKER_IMAGE=docker_image)
        if os.name == 'nt':
            path = os.path.join(dest, 'docker_run.bat' )
        else:
            path = os.path.join(dest, 'docker_run' )
        with open(path, 'w') as f:
            f.write (content)
        os.chmod (path, 0744)
        return path


