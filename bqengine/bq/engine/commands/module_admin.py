###############################################################################
##  Bisque                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011                                ##
##     by the Regents of the University of California                        ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY         ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE         ##
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR        ##
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR           ##
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,     ##
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,       ##
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR        ##
## PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF    ##
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING      ##
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS        ##
## SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.              ##
##                                                                           ##
## The views and conclusions contained in the software and documentation     ##
## are those of the authors and should not be interpreted as representing    ##
## official policies, either expressed or implied, of <copyright holder>.    ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

"""

import optparse
import os
import logging
import urlparse
from lxml import etree
from paste.deploy import appconfig
from tg import config

from bq.config.environment import load_environment
from bq.util import http
from bq.util.paths import config_path
from bq.util.commands import find_site_cfg
from bq.util.urlnorm import norm

logging.basicConfig(level = logging.DEBUG)

def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

log = logging.getLogger('bq.engine.command.module_admin')

class module_admin(object):
    desc = 'module options'
    def __init__(self, version):
        parser = optparse.OptionParser(
                    usage="%prog module [register|unregister] path/to/Module.xml",
                    version="%prog " + version)
        options, args = parser.parse_args()
        self.args = args
        self.options = options
        self.command = None
        if len(self.args):
            self.command = getattr(self, self.args.pop(0))
        if not self.command:
            parser.error("no command given")

        if len(self.args):
            self.module_path = self.args.pop(0)
            if not os.path.exists(self.module_path):
                parse.error("can't find module at %s" % self.module_path)
        else:
            parser.error('must provide path to module.xml')


    def run(self):
        site_cfg = find_site_cfg('site.cfg')
        load_config(site_cfg)
        self.command()

    def register (self):
        from bq.engine.controllers.engine_service import load_module
        bisque_root = norm(config.get('bisque.root') + '/')
        engine_root = urlparse.urljoin(norm(config.get ('engine.root') + '/'), 'engine_service')+'/'
        module_register = urlparse.urljoin(bisque_root, "module_service/register_engine")

        print "loading ", self.module_path
        module_xml = load_module(self.module_path)
        name = module_xml.get('name')
        if module_xml is not None:
            engine = etree.Element ('engine', uri = engine_root)
            module_xml.set('engine_url', urlparse.urljoin(engine_root, name))
            engine.append(module_xml)
            #####
            log.info ("POSTING %s to %s" % (name, module_register))
            xml =  etree.tostring (engine)
            #print xml
            resp, content = http.xmlrequest (norm(module_register+'/'), method='POST', body=xml)
            if resp['status'] != '200':
                print resp
                return
            print content

            
            
            



