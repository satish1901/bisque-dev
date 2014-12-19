###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
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
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========

DESCRIPTION
===========

TODO
===========

  1. Accept metadata as XML file along with packed image files
  1.

"""

__module__    = "export_service"
__author__    = "Dmitry Fedorov, Kris Kvilekval, Santhoshkumar Sunderrajan"
__version__   = "1.3"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

# -*- mode: python -*-

# default includes
import os
import logging
import pkg_resources
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates



# additional includes
import sys
import traceback
import datetime
import time
import re
import threading
import shutil
import tarfile
import zipfile
import logging
import gdata.docs
import gdata.docs.service

try:
    from cStringIO import StringIO
except Exception:
    from StringIO import StringIO

from urllib import quote
from lxml import etree

import tg
from tg import request, response, session, flash, require, abort
from repoze.what import predicates

from bq.core.service import ServiceController
from bq import data_service
from bq import image_service

from bqapi.bqclass import gobject_primitives

from bq.export_service.controllers.archive_streamer import ArchiveStreamer


# export plugins
try:
    import pyproj
except ImportError:
    pass

#---------------------------------------------------------------------------------------
# inits
#---------------------------------------------------------------------------------------

NO_BYTES=16*1024
max_size=1024*1024*1024*2
CHARREGEX=re.compile("\W+")
log  = logging.getLogger('bq.export_service')

#---------------------------------------------------------------------------------------
# controller
#---------------------------------------------------------------------------------------

log = logging.getLogger("bq.export_service")
class export_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "export"

    def __init__(self, server_url):
        super(export_serviceController, self).__init__(server_url)
        self.exporters = {}
        if 'pyproj' in sys.modules:
            self.exporters['kml'] = ExporterKML()

    @expose('bq.export_service.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from export_service'))

    def check_access(self, ident):
        resource = data_service.resource_load (uniq = ident)
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    @expose()
    def _default(self, *path, **kw):
        """find export plugin and run export"""
        uniq = path[0] if len(path)>0 else None
        format = path[1] if len(path)>1 else None
        if format is None:
            format = kw.get('format')
        
        # check permissions
        self.check_access(uniq)
        
        # export
        if format in self.exporters:
            return self.exporters[format].export(uniq)
       
        abort(400, 'Requested export format (%s) is not supported'%format )

#------------------------------------------------------------------------------
# Google Docs Export
#------------------------------------------------------------------------------

    @expose(template='bq.export_service.templates.to_gdocs')
    @require(predicates.not_anonymous())
    def to_gdocs (self, **kw):
        return { 'opts': kw }

    @expose(template='bq.export_service.templates.to_gdocs_send')
    @require(predicates.not_anonymous())
    def to_gdocs_send (self, **kw):
        if not 'google_id' in kw: return 'Google e-mail is needed'
        if not 'google_password' in kw: return 'Google password is needed'
        if not 'document_url' in kw: return 'Document to be exported is not provided'

        # get the document
        google_id = str(kw['google_id'])
        google_pass = str(kw['google_password'])
        url = str(kw['document_url'])

        s = data_service.load(url+'?view=deep&format=csv')
        #s = data_service.get_resource(url, view='deep', format='csv')

        input_file = StringIO(s)
        #log.debug('Google Docs input: ' + s )

        # upload to google docs
        gd_client = gdata.docs.service.DocsService()
        gd_client.email = str(google_id)
        gd_client.password = str(google_pass)
        gd_client.source = 'CBI_UCSB-Bisque-1'
        try:
            gd_client.ProgrammaticLogin()
        except Exception:
            return dict(error= str(sys.exc_value) )

        m_file_handle = input_file
        m_content_type = 'text/csv'
        m_content_length = len(s)
        m_file_name = quote(url)
        m_title = 'Bisque data - '+url

        ms = gdata.MediaSource(file_handle = m_file_handle, content_type = m_content_type, content_length = m_content_length, file_name = m_file_name )
        entry = gd_client.UploadSpreadsheet(ms, m_title)
        return dict(error=None, google_url=str(entry.GetAlternateLink().href))


    #------------------------------------------------------------------
    # new ArchiveStreamer - Utkarsh
    #------------------------------------------------------------------

    @expose()
    def stream(self, **kw):
        """Create and return a streaming archive

        :param compression: tar, zip, gzip, bz2
        :param files: a comma separated list of resource URIs to include in the archive
        :param datasets: a comma separated list of dataset resource URIs to include in the archive
        :param urls: a comma separated list of any url accessible over HTTP to include in the archive

        ------------------------------------
        Sample XML when POSTing to this app
        ------------------------------------

        <resource>
            <value type="FILE">    ...    </value>
            <value type="URL">     ...    </value>
            <value type="DATASET"> ...    </value>
        </resource>

        """

        files    = []
        datasets = []
        urls     = []
        dirs     = []

        if (tg.request.method.upper()=='POST' and tg.request.body):
            try:
                data = etree.XML(tg.request.body)
            except etree.ParseError:
                data = []
            for resource in data:
                type = resource.get('type', 'url').lower()
                if (type == 'file'):
                    files.append(resource.text)
                elif (type == 'dataset'):
                    datasets.append(resource.text)
                elif (type == 'dir'):
                    dirs.append(resource.text)
                elif (type == 'url'):
                    urls.append(resource.text)
                else:
                    urls.append(resource.text)

        compression = kw.pop('compression', '')
        
        def extractData(kw, field):
            if field in kw:
                vals = kw.pop(field)
                if vals:
                    return vals.split(',')
            return []
        
        jsbool   = {'true': True, 'false': False}
        export_meta = jsbool.get(kw.get('metadata', 'true'), True);
        export_mexs = jsbool.get(kw.get('analysis', 'false'), True);
        
        files.extend(extractData(kw, 'files'))
        datasets.extend(extractData(kw, 'datasets'))
        urls.extend(extractData(kw, 'urls'))
        dirs.extend(extractData(kw, 'dirs'))

        filename = kw.pop('filename', 'bisque-'+time.strftime("%Y%m%d.%H%M%S"))

        archiveStreamer = ArchiveStreamer(compression)
        archiveStreamer.init(archiveName=filename, fileList=files, datasetList=datasets, urlList=urls, dirList=dirs, export_meta=export_meta, export_mexs=export_mexs)
        return archiveStreamer.stream()

    def export(self, **kw):
        compression = kw.pop('compression', 'gzip')
        files       = kw.pop('files', None)
        datasets    = kw.pop('datasets', None)
        urls        = kw.pop('urls', None)
        dirs        = kw.pop('dirs', None)
        export_meta = kw.pop('export_meta', None)
        export_mexs = kw.pop('export_mexs', None)
        filename    = kw.pop('filename', 'bisque-'+time.strftime("%Y%m%d.%H%M%S"))

        archiveStreamer = ArchiveStreamer(compression)
        archiveStreamer.init(archiveName=filename, fileList=files, datasetList=datasets, urlList=urls, dirList=dirs, export_meta=export_meta, export_mexs=export_mexs)
        return archiveStreamer.stream()


#---------------------------------------------------------------------------------------
# exporters
#---------------------------------------------------------------------------------------

class ExporterKML():

    def __init__(self):
        #self.primitives = {}
        
        pass

    def export(self, uniq):
        """Add your first page here.. """
        resource = data_service.resource_load (uniq = uniq, view='deep')
        #resource = data_service.get_resource(url, view='deep')
        meta = image_service.meta(uniq)
        
        # if the resource is a dataset, fetch contents of documents linked in it
        #if resource.tag == 'dataset': 
        #    resource = data_service.get_resource('%s/value'%resource.get('uri'), view='deep')        
        
        #response.headers['Content-Type'] = 'text/xml'
        response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        
        fname = '%s.kml' % resource.get('name')
        try:
            fname.encode('ascii')
            disposition = 'filename="%s"'%(fname)
        except UnicodeEncodeError:
            disposition = 'filename="%s"; filename*="%s"'%(fname.encode('utf8'), fname.encode('utf8'))
        response.headers['Content-Disposition'] = disposition
        
        return self.bq2kml(resource, meta)

    def bq2kml(self, resource, meta):
        """ converts BisqueXML into KML """
        
        # get proj4
        q = meta.xpath('tag[@name="Geo"]/tag[@name="Model"]/tag[@name="proj4_definition"]')
        prj = q[0].get('value', None) if len(q)>0 else None 
        
        # get top_left
        q = meta.xpath('tag[@name="Geo"]/tag[@name="Coordinates"]/tag[@name="upper_left_model"]')
        top_left = q[0].get('value', None) if len(q)>0 else None
        if top_left is None:
            q = meta.xpath('tag[@name="Geo"]/tag[@name="Coordinates"]/tag[@name="upper_left"]')
            top_left = q[0].get('value', None) if len(q)>0 else None               
        if top_left:
            top_left = [float(v) for v in top_left.split(',')]
        
        # get pixel res
        q = meta.xpath('tag[@name="Geo"]/tag[@name="Tags"]/tag[@name="ModelPixelScaleTag"]')
        res = q[0].get('value', None) if len(q)>0 else None
        if res:
            res = [float(v) for v in res.split(',')]         
        
        # define transformation
        transform = {
            'proj_from': pyproj.Proj(prj),
            'proj_to': pyproj.Proj(init='EPSG:4326'),
            'offset': top_left,
            'res': res
        }
        log.debug('Transform: %s', str(transform))

        # closure with current transform
        def transform_coord(c):
            if transform['offset'] is None or transform['res'] is None:
                return c
            cc = ( transform['offset'][0] + c[0]*transform['res'][0], transform['offset'][1] - c[1]*transform['res'][1] )
            ccc = pyproj.transform(transform['proj_from'], transform['proj_to'], cc[0], cc[1])
            #log.debug('Converting coordinate: %s -> %s -> %s', c, cc, ccc)
            return (ccc[0], ccc[1])

        
        kml = etree.Element ('kml', xmlns='http://www.opengis.net/kml/2.2')
        doc = etree.SubElement (kml, 'Document')
        
        # per image
        folder = etree.SubElement (doc, 'Folder')
        name = etree.SubElement (folder, 'name') # type of gobject
        name.text = resource.get('name')
        descr = etree.SubElement (folder, 'description') # name of gobject
        descr.text = 'Annotations contained within image: %s'%resource.get('name')
        
        self.convert_node(resource, folder, transform_coord)
        return etree.tostring(kml)

    def convert_node(self, node, kml, cnvf):
        for n in node:
            if n.tag == 'gobject':
                if len(n) > 1:
                    folder = etree.SubElement (kml, 'Folder')
                    name = etree.SubElement (folder, 'name') # type of gobject
                    name.text = n.get('type')
                    descr = etree.SubElement (folder, 'description') # name of gobject
                    descr.text = n.get('name')
                    self.convert_node(n, folder, cnvf=cnvf)
                else:
                    self.render(n[0], kml, n.get('type'), n.get('name'), cnvf=cnvf)
                    #self.convert_node(n, kml)
            
            if n.tag in gobject_primitives:
                self.render(n, kml, n.tag, cnvf=cnvf)

    def render(self, node, kml, type=None, _val=None, cnvf=None): 
        vrtx = node.xpath('vertex')       
        f = getattr(self, node.tag, None)
        if len(vrtx)>0 and callable(f):
            
            vrtx = [(float(v.get('x')), float(v.get('y'))) for v in vrtx]
            if cnvf is not None:
                vrtx = [cnvf(v) for v in vrtx]                
            
            f(node, kml, vrtx, type or node.tag, _val)

    def point(self, node, kml, vrtx, type=None, val=None):
        pm = etree.SubElement (kml, 'Placemark')
        name = etree.SubElement (pm, 'name') # type of gobject
        name.text = type or node.get('name')

        if val is not None:
            descr = etree.SubElement (pm, 'description') # name of gobject
            descr.text = val

        point = etree.SubElement (pm, 'Point')
        coord = etree.SubElement (point, 'coordinates')
        
        x = vrtx[0][0]
        y = vrtx[0][1]
        coord.text = '%s,%s'%(x,y)

    def line(self, node, kml, vrtx, type=None, val=None):
        pm = etree.SubElement (kml, 'Placemark')
        name = etree.SubElement (pm, 'name') # type of gobject
        name.text = type or node.get('name')

        if val is not None:
            descr = etree.SubElement (pm, 'description') # name of gobject
            descr.text = val

        point = etree.SubElement (pm, 'LineString')
        coord = etree.SubElement (point, 'coordinates')
        
        x1 = vrtx[0][0]
        y1 = vrtx[0][1]
        x2 = vrtx[1][0]
        y2 = vrtx[1][1]
        coord.text = '%s,%s %s,%s'%(x1,y1, x2,y2)

    def polygon(self, node, kml, vrtx, type=None, val=None):
        pm = etree.SubElement (kml, 'Placemark')
        name = etree.SubElement (pm, 'name') # type of gobject
        name.text = type or node.get('name')

        if val is not None:
            descr = etree.SubElement (pm, 'description') # name of gobject
            descr.text = val

        g = etree.SubElement (pm, 'Polygon')
        g1 = etree.SubElement (g, 'outerBoundaryIs')
        g2 = etree.SubElement (g1, 'LinearRing')
        coord = etree.SubElement (g2, 'coordinates')
        
        coord.text = ' '.join( ['%s,%s'%(v[0], v[1]) for v in vrtx ] )

    def polyline(self, node, kml, vrtx, type=None, val=None):
        pm = etree.SubElement (kml, 'Placemark')
        name = etree.SubElement (pm, 'name') # type of gobject
        name.text = type or node.get('name')

        if val is not None:
            descr = etree.SubElement (pm, 'description') # name of gobject
            descr.text = val

        g = etree.SubElement (pm, 'LineString')
        coord = etree.SubElement (g, 'coordinates')
        
        coord.text = ' '.join( ['%s,%s'%(v[0], v[1]) for v in vrtx ] )

    def label(self, node, kml, vrtx, type=None, val=None):
        pm = etree.SubElement (kml, 'Placemark')
        name = etree.SubElement (pm, 'name') # type of gobject
        name.text = type or node.get('name')

        if val is not None:
            descr = etree.SubElement (pm, 'description') # name of gobject
            descr.text = val

        point = etree.SubElement (pm, 'Point')
        coord = etree.SubElement (point, 'coordinates')
        
        x = vrtx[0][0]
        y = vrtx[0][1]
        coord.text = '%s,%s'%(x,y)

#set(['circle', 'ellipse', 'rectangle', 'square'])

#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------
def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  export_serviceController(uri)
    #directory.register_service ('export_service', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'export_service', 'public'))]

__controller__ =  export_serviceController
