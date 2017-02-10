import os
import inspect
from datetime import datetime
#from itertools import *
import logging

#import pkg_resources
from tg import expose, request
#from repoze.what import predicates
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from pylons.controllers.util import abort

# imports for pipeline server
from lxml import etree
#from bqapi import *

from bq.core.service import ServiceController
from bq.core import identity
from bq import data_service

from .plugin_manager import PluginManager
from .pipeline_base import PipelineBase
from .pipeline_exporter import PipelineExporter

log = logging.getLogger("bq.pipeline")

################################################################################
# PipelineController
################################################################################

class PipelineController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "pipeline"

    def __init__(self, server_url):
        super(PipelineController, self).__init__(server_url)
        #self.baseuri = server_url
        self.basepath = os.path.dirname(inspect.getfile(inspect.currentframe()))

        self.importers = PluginManager('import', os.path.join(self.basepath, 'importers'), PipelineBase)
        self.exporters = PluginManager('export', os.path.join(self.basepath, 'exporters'), PipelineExporter)

        log.info('Pipeline service started...')

    @expose(content_type='text/xml')
    def index(self, **kw):
        """Add your service description here """
        response = etree.Element ('resource', uri=self.baseuri)
        etree.SubElement(response, 'method', name='%sID'%self.baseuri, value='Return pipeline with ID.')
        return etree.tostring(response)

    def check_access(self, uniq):
        resource = data_service.resource_load (uniq = uniq)
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    @expose()
    def _default(self, *path, **kw):
        """find export plugin and run export"""
        log.info ("STARTING pipeline (%s): %s", datetime.now().isoformat(), request.url)
        path = list(path)
        log.debug("Path: %s", path)

        # /pipeline/ID
        if len(path)<1:
            abort(400, 'Element ID is required as a first parameter, ex: /pipeline/00-XXXXX?format=xml' )
        uniq = path.pop(0)

        # check permissions
        resource = self.check_access(uniq)
        log.debug('Resource: %s', etree.tostring(resource))

        # load pipeline
        pipeline = None
        try:
            for n, r in self.importers.plugins.iteritems():
                if '.' in resource.get('value', '') and resource.get('value').split('.')[-1].lower() not in r.ext:
                    # resource has filename with extension and extension does not match plugins supported extensions
                    continue
                try:
                    log.debug("trying format %s", str(n))
                    pipeline = r(uniq, resource, path, url=request.url)
                except Exception as ex:
                    log.debug("failed with error %s", str(ex))
                    pipeline = None
                    pass # continue with next format # TODO: continue?
                if pipeline is not None and pipeline.isloaded() == True:
                    break
            if pipeline is None:
                abort(500, 'Pipeline cannot be read')
            log.debug('Read pipeline: %s',str(pipeline))

            # export
            out_format = kw.get('format', 'json')
            log.debug('Format: %s', out_format)
            if out_format in self.exporters.plugins:
                r = self.exporters.plugins[out_format]().export(pipeline)
                return r
            abort(400, 'Requested export format (%s) is not supported'%out_format )
        finally:
            log.info ("FINISHED (%s): %s", datetime.now().isoformat(), request.url)


#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  PipelineController(uri)
    #directory.register_service ('table', service)
    return service

__controller__ =  PipelineController
