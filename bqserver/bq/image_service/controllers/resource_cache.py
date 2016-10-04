""" 
ResourceCache used to cache resources to speed up retrieval of images without constantly 
asking data service for meta-data view of a resource. It is required to have a fast etag 
lookup on a data service in order to validate the cache state.
"""

__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "1.4"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
import logging

from bq import data_service
from bq import blob_service
from bq.core import identity

import logging
log = logging.getLogger('bq.image_service.cache')

################################################################################
# Resource and Blob caching
################################################################################

class ResourceCache(object):
    '''Provide resource and blob caching'''

    def __init__(self):
        self.d = {}

    def get_descriptor(self, ident):
        user = identity.get_user_id()
        if user not in self.d:
            self.d[user] = {}
        d = self.d[user]
        if ident not in d:
            d[ident] = {}

        #etag = r.get('etag', None)
        #dima: check if etag changed in data_service
        #if too old
        #    d[ident] = {}

        return d[ident]

    def get_resource(self, ident):
        r = self.get_descriptor(ident)

        # load from cache
        # if 'resource' in r:
        #     return r.get('resource')

        resource = data_service.resource_load (uniq = ident, view='image_meta')
        if resource is not None:
            r['resource'] = resource
        return resource

    def get_blobs(self, ident):
        r = self.get_descriptor(ident)

        # load from cache
        # if 'blobs' in r:
        #    blobs = r.get('blobs')
        #    # dima: do file existence check here
        #    # re-request blob service if unavailable
        #    return blobs

        resource = r['resource']
        blobs = blob_service.localpath(ident, resource=resource)
        if blobs is not None:
            r['blobs'] = blobs
        return blobs

