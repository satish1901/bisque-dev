# -*- mode: python -*-
"""Main server for image_service}
"""
import os
import logging
import pkg_resources
import tg
import urlparse
import re

from hashlib import md5
from datetime import datetime
from lxml import etree
from pylons.controllers.util import etag_cache
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash, config, abort
from repoze.what import predicates
from bq.core.service import ServiceController
from paste.fileapp import FileApp
from pylons.controllers.util import forward
from bq import data_service

from bq.core import permission, identity
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq import data_service
from bq import export_service
from .process_token import ProcessToken
from .imgsrv import ImageServer, getOperations
import bq.util.io_misc as misc

log = logging.getLogger("bq.image_service")

# extensions not usually associated with image files
extensions_ignore = set(['', 'amiramesh', 'cfg', 'csv', 'dat', 'grey', 'htm', 'html', 'hx', 'inf', 'labels', 'log', 'lut', 'mdb', 'pst', 'pty', 'rec', 'tim', 'txt', 'xlog', 'xml', 'zip', 'zpo'])

# confirmed extensions of header files in some proprietary series
extensions_series = set(['cfg', 'xml'])

# confirmed fixed series header names
series_header_files = ['DiskInfo5.kinetic']

def get_image_id(url):
    path = urlparse.urlsplit(url)[2]
    if path[-1]=='/':
        path =path[:-1]

    id = path.split('/')[-1]
    return id

def cache_control (value):
    tg.response.headers.pop('Pragma', None)
    tg.response.headers['Cache-Control'] = value

class ImageServiceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "image_service"
    format_exts = None

    def __init__(self, server_url):
        super(ImageServiceController, self).__init__(server_url)
        workdir= config.get('bisque.image_service.work_dir', data_path('workdir'))

        _mkdir (workdir)
        log.info('ROOT=%s work=%s' , config.get('bisque.root'),  workdir)

        self.user_map = {}
        # users = data_service.query('user', wpublic=1)
        # for u in users.xpath('user'):
        #     self.user_map[u.get('uri')] = u.get('name')

        self.srv = ImageServer(work_dir = workdir)

    def meta (self, uniq, **kw):
        ''' returns etree metadata element'''
        url = '/image_service/%s?meta'%uniq

        # check for access permission
        resource = self.check_access(uniq, view='image_meta')
        user_name = self.get_user_name(resource.get('owner'))

        # fetch image meta from a resource if any, has to have a name and a type as "image_meta"
        meta = None
        try:
            meta = resource.xpath('tag[@type="image_meta"]')[0]
            meta = dict((i.get('name'), misc.safetypeparse(i.get('value'))) for i in meta.xpath('tag'))
            log.debug('images meta: %s', meta)
            if len(meta)==0:
                meta=None
        except (AttributeError, IndexError):
            meta = None

        # Run processing
        token = self.srv.process(url, uniq, imagemeta=meta, resource=resource, user_name=user_name)
        if token.isHttpError():
            return None

        return etree.parse(token.data)

    # we use URL here in order to give access to derived computed results as local files
    def local_file (self, url, **kw):
        ''' returns local path if it exists otherwise None'''
        m = re.search(r'(\/image_service\/(image[s]?\/|))(?P<id>[\w-]+)', url) #includes cases without image(s) in the url

        if m is None: #url did not match the regex
            return None

        uniq = m.group('id')

        # check for access permission
        resource = self.check_access(uniq, view='image_meta')
        user_name = self.get_user_name(resource.get('owner'))

        # fetch image meta from a resource if any, has to have a name and a type as "image_meta"
        meta = None
        try:
            meta = resource.xpath('tag[@type="image_meta"]')[0]
            meta = dict((i.get('name'), misc.safetypeparse(i.get('value'))) for i in meta.xpath('tag'))
            log.debug('images meta: %s', meta)
            if len(meta)==0:
                meta=None
        except (AttributeError, IndexError):
            meta = None

        # Run processing
        token = self.srv.process(url, uniq, imagemeta=meta, resource=resource, user_name=user_name)
        if token.isHttpError():
            return None

        return token.data

    @classmethod
    def is_image_type (cls, filename):
        """guess whether the file is an image based on the filename
        and whether we think we can decode
        """
        if cls.format_exts is None:
            cls.format_exts = set(ImageServer.converters.extensions()) - extensions_ignore

        ext = os.path.splitext(filename.strip())[1][1:].lower()
        return ext in cls.format_exts

    @classmethod
    def proprietary_series_extensions (cls):
        """ return all extensions that can be proprietary series
        """
        non_series_cnv = ['imgcnv', 'openslide']
        exts = []
        ignore = []
        for n in ImageServer.converters.iterkeys():
            if n in non_series_cnv:
                ignore.extend(ImageServer.converters.extensions(n))
            else:
                exts.extend(ImageServer.converters.extensions(n))
        return list(((set(exts) - set(ignore)) - extensions_ignore) | extensions_series)

    @classmethod
    def proprietary_series_headers (cls):
        """ get fixed file names that could be series headers
        """
        return series_header_files

    @classmethod
    def get_info (cls, filename):
        """ read file info
        """
        return ImageServer.converters.info(filename)




    @expose()
    def _default(self, *path, **kw):
        id = path[0]
        return self.images(id, **kw)

    @expose(content_type='text/xml')
    def index(self, **kw):
        service_path = '/image_service'
        response = etree.Element ('resource', uri=service_path)
        etree.SubElement(response, 'method', name='%s/operations'%service_path, value='Returns a list of supported operations in XML')
        etree.SubElement(response, 'method', name='%s/formats'%service_path, value='Returns a list of supported formats in XML')
        etree.SubElement(response, 'method', name='%s/ID'%service_path, value='Returns a file for this ID')
        etree.SubElement(response, 'method', name='%s/ID?OPERATION1=PAR1&OPERATION2=PAR2'%service_path, value='Executes operations for give image ID. Call /operations to check available')
        etree.SubElement(response, 'method', name='%s/ID/OPERATION1:PAR1/OPERATION2:PAR2'%service_path, value='Executes operations for give image ID. Call /operations to check available')
        etree.SubElement(response, 'method', name='%s/image/ID'%service_path, value='same as /ID')
        etree.SubElement(response, 'method', name='%s/images/ID'%service_path, value='same as /ID, deprecated and will be removed in the future')
        return etree.tostring(response)

    @expose()
    def operations(self, **kw):
        token = self.srv.request( 'operations', ProcessToken(), None )
        tg.response.headers['Content-Type']  = token.contentType
        cache_control( token.cacheInfo )
        return token.data

    @expose(content_type="application/xml")
    #@identity.require(identity.not_anonymous())
    def formats(self, **kw):
        token = self.srv.request( 'formats', ProcessToken(), None )
        tg.response.headers['Content-Type']  = token.contentType
        cache_control( token.cacheInfo )
        return token.data

    # @expose()
    # #@identity.require(identity.not_anonymous())
    # def remote(self, **kw):
    #     return self.images(-1, **kw)

    # @expose()
    # def blobs(self):
    #     pass

    def check_access(self, ident, view=None):
        resource = data_service.resource_load (uniq = ident, view=view)
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    # try to find user name in the map otherwise will query the database
    def get_user_name(self, uri):
        if uri in self.user_map:
            return self.user_map[uri]
        owner = data_service.get_resource(uri)
        self.user_map[uri] = owner.get ('name')
        return owner.get ('name')

    @expose()
    def image(self, *path, **kw):
        id = path[0]
        return self.images(id, **kw)

    @expose()
    #@identity.require(identity.not_anonymous())
    def images(self, ident, **kw):
        request = tg.request
        response = tg.response

        #url = request.path+'?'+request.query_string if len(request.query_string)>0 else request.path
        url = request.url
        resource_id, query = getOperations(url, self.srv.base_url)
        ident = resource_id or ident
        log.info ('STARTING %s: %s', ident, url)

        # dima: patch for incorrect /auth requests for image service
        if '/auth' in url:
            tg.response.headers['Content-Type'] = 'text/xml'
            return '<resource />'


        # check for access permission
        resource = self.check_access(ident, view='image_meta')
        user_name = self.get_user_name(resource.get('owner'))

        # extract requested timeout: BQ-Operation-Timeout: 30
        timeout = request.headers.get('BQ-Operation-Timeout', None)


        # fetch image meta from a resource if any, has to have a name and a type as "image_meta"
        meta = None
        try:
            meta = resource.xpath('tag[@type="image_meta"]')[0]
            meta = dict((i.get('name'), misc.safetypeparse(i.get('value'))) for i in meta.xpath('tag'))
            log.debug('images meta: %s', meta)
            if len(meta)==0:
                meta=None
        except (AttributeError, IndexError):
            meta = None

        # if the image is multi-blob and blob is requested, use export service
        try:
            values = resource.xpath('value')
            if len(query)<1 and len(values)>1:
                return export_service.export(files=[resource.get('uri')], filename=resource.get('name'))
        except (AttributeError, IndexError):
            pass

        # Run processing
        token = self.srv.process(url, ident, timeout=timeout, imagemeta=meta, resource=resource, user_name=user_name, **kw)
        tg.response.headers['Content-Type']  = token.contentType
        #tg.response.content_type  = token.contentType
        #tg.response.headers['Cache-Control'] = ",".join ([token.cacheInfo, "public"])
        cache_control( ",".join ([token.cacheInfo, "public"]))

        #first check if the output is an error
        if token.isHttpError():
            log.error('Responce Code: %s for %s: %s ' % (token.httpResponseCode, ident, token.data))
            tg.response.status_int = token.httpResponseCode
            tg.response.content_type = token.contentType
            tg.response.charset = 'utf8'
            return token.data.encode('utf8')

        #second check if the output is TEXT/HTML/XML
        if token.isText() and not token.isFile():
            return token.data

        #third check if the output is actually a file
        if token.isFile():
            #modified =  datetime.fromtimestamp(os.stat(token.data).st_mtime)
            #etag_cache(md5(str(modified) + str(id)).hexdigest())

            fpath = token.data.split('/')
            fname = fpath[len(fpath)-1]

            if token.hasFileName():
                fname = token.outFileName

            #Content-Disposition: attachment; filename=genome.jpeg;
            disposition = ''
            if token.isImage() is not True and token.isText() is not True:
                disposition = 'attachment; '

            try:
                fname.encode('ascii')
                disposition = '%sfilename="%s"'%(disposition, fname)
            except UnicodeEncodeError:
                # dima: encode the filename in utf-8
                disposition = '%sfilename="%s"; filename*="%s"'%(disposition, fname.encode('utf8'), fname.encode('utf8'))
                #disposition = '%sfilename="%s"; filename*="%s"'%(disposition, fname.encode('ascii', errors='ignore'), fname.encode('utf8'))

            # fix for the cherrypy error 10055 "No buffer space available" on windows
            # by streaming the contents of the files as opposite to sendall the whole thing
            log.info ("%s: returning %s with mime %s"%(ident, token.data, token.contentType ))
            return forward(FileApp(token.data,
                                   content_type=token.contentType,
                                   content_disposition=disposition,
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks

        log.error ("%s: unknown image issue"%ident)
        tg.response.status_int = 404
        return "File not found"

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  ImageServiceController(uri)
    #directory.register_service ('image_service', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'image_service', 'public'))]

__controller__ =  ImageServiceController
