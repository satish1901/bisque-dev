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
except:
    from StringIO import StringIO

from urllib import quote
from lxml import etree

import tg
from tg import request, response, session, flash, require
from repoze.what import predicates

from bq.core.service import ServiceController
from bq import data_service


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

    @expose('bq.export_service.templates.index')
    def index(self, **kw):
        """Add your first page here.. """
        return dict(msg=_('Hello from export_service'))


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
        except:
            return dict(error= str(sys.exc_value) )

        m_file_handle = input_file
        m_content_type = 'text/csv'
        m_content_length = len(s)
        m_file_name = quote(url)
        m_title = 'Bisque data - '+url

        ms = gdata.MediaSource(file_handle = m_file_handle, content_type = m_content_type, content_length = m_content_length, file_name = m_file_name )
        entry = gd_client.UploadSpreadsheet(ms, m_title)
        return dict(error=None, google_url=str(entry.GetAlternateLink().href))


    @expose()
    def exportString(self, **kw):
        value = kw.pop('value', '')
        return value

    #------------------------------------------------------------------
    # new ArchiveStreamer - Utkarsh
    #------------------------------------------------------------------

    @expose()
    def initStream(self, **kw):
        """Create and return a streaming archive

        :param compressionType: tar, zip, gzip, bz2
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

        from bq.export_service.controllers.archive_streamer import ArchiveStreamer
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

        compressionType = kw.pop('compressionType', '')
        
        def extractData(kw, field):
            if field in kw:
                vals = kw.pop(field)
                if vals:
                    return vals.split(',')
            return []
        
        jsbool   = {'true': True, 'false': False}
        export_meta = jsbool.get(kw.get('metadata', 'true'), True);
        
        files    = files + extractData(kw, 'files')
        datasets = datasets + extractData(kw, 'datasets')
        urls     = urls + extractData(kw, 'urls')
        dirs     = dirs + extractData(kw, 'dirs')

        filename = kw.pop('filename', None) or 'bisque-'+time.strftime("%Y%m%d.%H%M%S")

        archiveStreamer = ArchiveStreamer(compressionType)
        archiveStreamer.init(archiveName=filename, fileList=files, datasetList=datasets, urlList=urls, dirList=dirs, export_meta=export_meta)
        return archiveStreamer.stream()


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
