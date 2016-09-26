# imgsrv.py
# Author: Dmitry Fedorov and Kris Kvilekval
# Center for BioImage Informatics, University California, Santa Barbara
""" ImageServer for Bisque system.
"""

from __future__ import with_statement

__module__    = "imgsrv"
__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "1.4"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
import logging
import os.path
import shutil
import re
import StringIO
from urllib import quote
from urllib import unquote
from urlparse import urlparse
from lxml import etree
import datetime
import math

from tg import config
from pylons.controllers.util import abort

#Project
from bq import data_service
from bq import blob_service
from bq.blob_service.controllers.blob_drivers import Blobs

from bq.core import  identity
from bq.util.mkdir import _mkdir
#from collections import OrderedDict
from bq.util.compat import OrderedDict
from bq.util.urlpaths import url2localpath

from bq.util.locks import Locks
from bq.util.io_misc import safetypeparse, safeint


default_format = 'bigtiff'
default_tile_size = 512
min_level_size = 128
converters_preferred_order = ['openslide', 'imgcnv', 'ImarisConvert', 'bioformats']


from .process_token import ProcessToken
from .converter_imgcnv import ConverterImgcnv
from .converter_imaris import ConverterImaris
from .converter_bioformats import ConverterBioformats
from .converter_openslide import ConverterOpenSlide

log = logging.getLogger('bq.image_service.server')

# needed_versions = { 'imgcnv'     : '1.66.0',
#                     'imaris'     : '8.0.0',
#                     'openslide'  : '0.5.1', # python wrapper version
#                     'bioformats' : '5.0.1',
#                   }

################################################################################
# Create a list of querie tuples
################################################################################

def getQuery4Url(url):
    scheme, netloc, url, params, querystring, fragment = urlparse(url)

    #pairs = [s2 for s1 in querystring.split('&') for s2 in s1.split(';')]
    pairs = [s1 for s1 in querystring.split('&')]
    query = []
    for name_value in pairs:
        if not name_value:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            nv.append('')

        name = unquote(nv[0].replace('+', ' '))
        value = unquote(nv[1].replace('+', ' '))
        query.append((name, value))

    return query

def newUrl2Query(url, base):
    query = []
    path = filter(None, url.split('/')) # split and remove empty
    path = path[path.index(base)+1:] # isolate query part
    if path[0].lower() == 'image' or path[0].lower() == 'images':
        path = path[1:]

    resource_id = path[0]
    path = path[1:]
    for p in path:
        v = p.split(':', 1)
        name = unquote(v[0].replace('+', ' '))
        try:
            value = unquote(v[1].replace('+', ' '))
        except IndexError:
            value = ''
        query.append((name, value))
    return resource_id, query


def getOperations(url, base):
    if '?' in url:
        return None, getQuery4Url(url)
    else:
        return newUrl2Query(url, base)


def getFileDateTimeString(filename):

    # retrieves the stats for the current file as a tuple
    # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
    # the tuple element mtime at index 8 is the last-modified-date
    stats = os.stat(filename)
    # create tuple (year yyyy, month(1-12), day(1-31), hour(0-23), minute(0-59), second(0-59),
    # weekday(0-6, 0 is monday), Julian day(1-366), daylight flag(-1,0 or 1)) from seconds since epoch
    # note:  this tuple can be sorted properly by date and time

    #lastmod_date = datetime.fromtimestamp(stats[8])
    #return lastmod_date.isoformat()

    d = time.localtime(stats[8])
    return "%.4d-%.2d-%.2d %.2d:%.2d:%.2d" % ( d[0], d[1], d[2], d[3], d[4], d[5] )


def safeunicode(s):
    if isinstance(s, unicode):
        return s
    if isinstance(s, str) is not True:
        return unicode(s)
    try:
        return unicode(s, 'latin1')
    except (UnicodeEncodeError,UnicodeDecodeError):
        try:
            return unicode(s, 'utf8')
        except (UnicodeEncodeError,UnicodeDecodeError):
            pass
    return unicode(s, 'utf8', errors='ignore')

################################################################################
# ConverterDict
################################################################################

class ConverterDict(OrderedDict):
    'Store items in the order the keys were last added'

#     def __setitem__(self, key, value):
#         if key in self:
#             del self[key]
#         OrderedDict.__setitem__(self, key, value)

    def __str__(self):
        return ', '.join(['%s (%s)'%(n, c.version['full']) for n,c in self.iteritems()])

    def defaultExtension(self, formatName):
        formatName = formatName.lower()
        for c in self.itervalues():
            if formatName in c.formats():
                return c.formats()[formatName].ext[0]

    def extensions(self, name=None):
        exts = []
        if name is None:
            for c in self.itervalues():
                for f in c.formats().itervalues():
                    exts.extend(f.ext)
        else:
            c = self[name]
            for f in c.formats().itervalues():
                exts.extend(f.ext)
        return exts

    def info(self, filename, name=None):

        token = ProcessToken(ifnm=filename)
        if name is None:
            for n,c in self.iteritems():
                info = c.info(token)
                if info is not None and len(info)>0:
                    info['converter'] = n
                    return info
        else:
            c = self[name]
            info = c.info(token)
            if info is not None and len(info)>0:
                info['converter'] = name
                return info
        return None

    def canWriteMultipage(self, formatName):
        formats = []
        for c in self.itervalues():
            for n,f in c.formats().iteritems():
                if f.multipage is True:
                    formats.append[n]
        return formatName.lower() in formats

    def converters(self, readable=True, writable=True, multipage=False):
        fs = {}
        for c in self.itervalues():
            for n,f in c.formats().iteritems():
                ok = True
                if readable is True and f.reading is not True:
                    ok = False
                elif writable is True and f.writing is not True:
                    ok = False
                elif multipage is True and f.multipage is not True:
                    ok = False
                if ok is True:
                    fs.setdefault(n, c)
        return fs

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

        #if 'resource' in r:
        #    return r.get('resource')

        resource = data_service.resource_load (uniq = ident, view='image_meta')
        if resource is not None:
            r['resource'] = resource
        return resource

    def get_blobs(self, ident):
        r = self.get_descriptor(ident)

        #if 'blobs' in r:
        #    blobs = r.get('blobs')
        #    # dima: do file existence check here
        #    # re-request blob service if unavailable
        #    return blobs

        resource = r['resource']
        blobs = blob_service.localpath(ident, resource=resource)
        if blobs is not None:
            r['blobs'] = blobs
        return blobs

################################################################################
# Operations baseclass
################################################################################

class BaseOperation(object):
    '''Provide operations base'''
    name = 'base'

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'base: describe your service and its arguments'

    # optional method, used to generate the final file quickly
    # defined if action does convertions and not only enques its arguments
    #def dryrun(self, token, arg):
    #    return token

    # required method
    def action(self, token, arg):
        return token


################################################################################
# Info Operations
################################################################################

class OperationsOperation(BaseOperation):
    '''Provide operations information'''
    name = 'operations'

    def __str__(self):
        return 'operations: returns XML with operations information'

    def dryrun(self, token, arg):
        return token.setXml('')

    def action(self, token, arg):
        response = etree.Element ('response')
        servs    = etree.SubElement (response, 'operations', uri='/image_service/operations')
        for name,func in self.server.operations.iteritems():
            tag = etree.SubElement(servs, 'tag', name=str(name), value=str(func))
        return token.setXml(etree.tostring(response))

class FormatsOperation(BaseOperation):
    '''Provide information on supported formats'''
    name = 'formats'

    def __str__(self):
        return 'formats: Returns XML with supported formats'

    def dryrun(self, token, arg):
        return token.setXml('')

    def action(self, token, arg):
        xml = etree.Element ('resource', uri='/images_service/formats')
        for nc,c in self.server.converters.iteritems():
            format = etree.SubElement (xml, 'format', name=nc, version=c.version['full'])
            for f in c.formats().itervalues():
                codec = etree.SubElement(format, 'codec', name=f.name )
                etree.SubElement(codec, 'tag', name='fullname', value=f.fullname )
                etree.SubElement(codec, 'tag', name='extensions', value=','.join(f.ext) )
                etree.SubElement(codec, 'tag', name='support', value=f.supportToString() )
                etree.SubElement(codec, 'tag', name='samples_per_pixel_minmax', value='%s,%s'%f.samples_per_pixel_min_max )
                etree.SubElement(codec, 'tag', name='bits_per_sample_minmax',   value='%s,%s'%f.bits_per_sample_min_max )
        return token.setXml(etree.tostring(xml))


class ViewOperation(BaseOperation):
    '''View operation is only needed to ignore view=deep in the request if given'''
    name = 'view'

    def __str__(self):
        return 'view: only needed to ignore view=deep in the request if given'

    def dryrun(self, token, arg):
        return token

    def action(self, token, arg):
        return token

# class InfoOperation(BaseOperation):
#     '''Provide image information'''
#     name = 'operations'

#     def __init__(self, server):
#         self.server = server

#     def __str__(self):
#         return 'info: returns XML with image information'

#     def dryrun(self, token, arg):
#         return token.setXml('')

#     def action(self, token, arg):
#         info = self.server.getImageInfo(ident=token.resource_id)
#         info['filename'] = token.resource_name

#         ifile = token.data
#         infoname = self.server.getOutFileName( ifile, token.resource_id, '.info' )
#         metacache = self.server.getOutFileName( ifile, token.resource_id, '.meta' )


#         image = etree.Element ('resource', uri='/%s/%s'%(self.server.base_url,  token.resource_id))
#         for k, v in info.iteritems():
#             tag = etree.SubElement(image, 'tag', name='%s'%k, value='%s'%v )
#         return token.setXml(etree.tostring(image))

class DimOperation(BaseOperation):
    '''Provide image dimension information'''
    name = 'dims'

    def __str__(self):
        return 'dims: returns XML with image dimension information'

    def dryrun(self, token, arg):
        return token.setXml('')

    def action(self, token, arg):
        info = token.dims
        response = etree.Element ('response')
        if info is not None:
            image = etree.SubElement (response, 'image', resource_uniq='%s'%token.resource_id)
            for k, v in info.iteritems():
                tag = etree.SubElement(image, 'tag', name=str(k), value=str(v))
        return token.setXml(etree.tostring(response))

class MetaOperation(BaseOperation):
    '''Provide image information'''
    name = 'meta'

    def __str__(self):
        return 'meta: returns XML with image meta-data'

    def dryrun(self, token, arg):
        metacache = '%s.meta'%(token.data)
        return token.setXmlFile(metacache)

    def action(self, token, arg):
        ifile = token.first_input_file()
        metacache = '%s.meta'%(token.data)
        log.debug('Meta: %s -> %s', ifile, metacache)

        if not os.path.exists(metacache):
            meta = {}
            if not os.path.exists(ifile):
                abort(404, 'Meta: Input file not found...')

            dims = token.dims or {}
            converter = None
            if dims.get('converter', None) in self.server.converters:
                converter = dims.get('converter')
                meta = self.server.converters[converter].meta(token)

            if meta is None:
                # exhaustively iterate over converters to find supporting one
                for c in self.server.converters.itervalues():
                    if c.name == dims.get('converter'): continue
                    meta = c.meta(token)
                    converter = c.name
                    if meta is not None and len(meta)>0:
                        break

            if meta is None or len(meta)<1:
                abort(415, 'Meta: file format is not supported...')

            # overwrite fileds forced by the fileds stored in the resource image_meta
            if token.meta is not None:
                meta.update(token.meta)
            meta['converter'] = converter
            if token.is_multifile_series() is True:
                meta['file_mode'] = 'multi-file'
            else:
                meta['file_mode'] = 'single-file'

            # construct an XML tree
            image = etree.Element ('resource', uri='/%s/%s?meta'%(self.server.base_url, token.resource_id))
            tags_map = {}
            for k, v in meta.iteritems():
                if k.startswith('DICOM/'): continue
                k = safeunicode(k)
                v = safeunicode(v)
                tl = k.split('/')
                parent = image
                for i in range(0,len(tl)):
                    tn = '/'.join(tl[0:i+1])
                    if not tn in tags_map:
                        tp = etree.SubElement(parent, 'tag', name=tl[i])
                        tags_map[tn] = tp
                        parent = tp
                    else:
                        parent = tags_map[tn]
                try:
                    parent.set('value', v)
                except ValueError:
                    pass

            if meta['format'] == 'DICOM':
                node = etree.SubElement(image, 'tag', name='DICOM')
                ConverterImgcnv.meta_dicom(ifile, series=token.series, token=token, xml=node)

            log.debug('Meta %s: storing metadata into %s', token.resource_id, metacache)
            xmlstr = etree.tostring(image)
            with open(metacache, 'w') as f:
                f.write(xmlstr)
            return token.setXml(xmlstr)

        log.debug('Meta %s: reading metadata from %s', token.resource_id, metacache)
        return token.setXmlFile(metacache)

#class FileNameOperation(BaseOperation):
#    '''Provide image filename'''
#    name = 'operations'
#
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'FileNameService: Returns XML with image file name'
#    def hookInsert(self, token, token.resource_id, hookpoint='post'):
#        pass
#    def action(self, token, arg):
#
#        fileName = token.resource_name
#
#        response = etree.Element ('response')
#        image    = etree.SubElement (response, 'image')
#        image.attrib['src'] = '/imgsrv/' + str(token.resource_id)
#        tag = etree.SubElement(image, 'tag')
#        tag.attrib['name'] = 'filename'
#        tag.attrib['type'] = 'string'
#        tag.attrib['value'] = fileName
#
#        token.setXml(etree.tostring(response))
#        return token

class LocalPathOperation(BaseOperation):
    '''Provides local path for response image'''
    name = 'localpath'

    def __str__(self):
        return 'localpath: returns XML with local path to the processed image'

    def dryrun(self, token, arg):
        return token.setXml('')

    def action(self, token, arg):
        if token.hasQueue():
            ifile = token.data
        else:
            ifile = token.first_input_file()
        ifile = os.path.abspath(ifile)
        log.debug('Localpath %s: %s', token.resource_id, ifile)

        res = etree.Element ('resource', type='file', value=ifile)
        if os.path.exists(ifile):
            etree.SubElement (res, 'tag', name='status', value='requires access for creation')

        #else:
        #    res = etree.Element ('resource')

        return token.setXml( etree.tostring(res) )

class CacheCleanOperation(BaseOperation):
    '''Cleans local cache for a given image'''
    name = 'cleancache'

    def __str__(self):
        return 'cleancache: cleans local cache for a given image'

    def dryrun(self, token, arg):
        return token.setXml('')

    def action(self, token, arg):
        ofname = token.data
        log.debug('Cleaning local cache %s: %s', token.resource_id, ofname)
        path = os.path.dirname(ofname)
        fname = os.path.basename(ofname)
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name.startswith(fname):
                    os.remove(os.path.join(root, name))
            for name in dirs:
                if name.startswith(fname):
                    #os.removedirs(os.path.join(root, name))
                    shutil.rmtree(os.path.join(root, name))
        return token.setHtml( 'Clean' )


################################################################################
# Main Image Operations
################################################################################

class SliceOperation(BaseOperation):
    '''Provide a slice of an image :
       arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2
       Each position may be specified as a range
       empty params imply entire available range
       all values are in ranges [1..N]
       0 or empty - means first element
       ex: slice=,,1,'''
    name = 'slice'

    def __str__(self):
        return 'slice: returns an image of requested slices, arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2. All values are in ranges [1..N]'

    def dryrun(self, token, arg):
        # parse arguments
        vs = [ [safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return token

        dims = token.dims or {}
        if x1<=1 and x2>=dims.get('image_num_x', 1): x1=0; x2=0
        if y1<=1 and y2>=dims.get('image_num_y', 1): y1=0; y2=0
        if z1<=1 and z2>=dims.get('image_num_z', 1): z1=0; z2=0
        if t1<=1 and t2>=dims.get('image_num_t', 1): t1=0; t2=0

        # check image bounds
        if z1>dims.get('image_num_z', 1):
            abort(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z1 )
        if z2>dims.get('image_num_z', 1):
            abort(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z2 )
        if t1>dims.get('image_num_t', 1):
            abort(400, 'Slice: requested T plane outside of image bounds: [%s]'%t1 )
        if t2>dims.get('image_num_t', 1):
            abort(400, 'Slice: requested T plane outside of image bounds: [%s]'%t2 )

        # shortcuts are only possible with no ROIs are requested
        if x1==x2==0 and y1==y2==0:
            # shortcut if input image has only one T and Z
            if dims.get('image_num_z', 1)<=1 and dims.get('image_num_t', 1)<=1:
                #log.debug('Slice: plane requested on image with no T or Z planes, skipping...')
                return token
            # shortcut if asking for all slices with only a specific time point in an image with only one time pont
            if z1==z2==0 and t1<=1 and dims.get('image_num_t', 1)<=1:
                #log.debug('Slice: T plane requested on image with no T planes, skipping...')
                return token
            # shortcut if asking for all time points with only a specific z slice in an image with only one z slice
            if t1==t2==0 and z1<=1 and dims.get('image_num_z', 1)<=1:
                #log.debug('Slice: Z plane requested on image with no Z planes, skipping...')
                return token

        if z1==z2==0: z1=1; z2=dims.get('image_num_z', 1)
        if t1==t2==0: t1=1; t2=dims.get('image_num_t', 1)

        new_w = x2-x1
        new_h = y2-y1
        new_z = max(1, z2 - z1 + 1)
        new_t = max(1, t2 - t1 + 1)
        info = {
            'image_num_z': new_z,
            'image_num_t': new_t,
        }
        if new_w>0: info['image_num_x'] = new_w+1
        if new_h>0: info['image_num_y'] = new_h+1

        ofname = '%s.%d-%d,%d-%d,%d-%d,%d-%d.ome.tif' % (token.data, x1,x2,y1,y2,z1,z2,t1,t2)
        return token.setImage(ofname, fmt=default_format, dims=info)

    def action(self, token, arg):
        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''

        if not token.isFile():
            abort(400, 'Slice: input is not an image...' )

        # parse arguments
        vs = [ [safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return token

        dims = token.dims or {}
        if x1<=1 and x2>=dims.get('image_num_x', 1): x1=0; x2=0
        if y1<=1 and y2>=dims.get('image_num_y', 1): y1=0; y2=0
        if z1<=1 and z2>=dims.get('image_num_z', 1): z1=0; z2=0
        if t1<=1 and t2>=dims.get('image_num_t', 1): t1=0; t2=0

        # check image bounds
        if z1>dims.get('image_num_z', 1):
            abort(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z1 )
        if z2>dims.get('image_num_z', 1):
            abort(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z2 )
        if t1>dims.get('image_num_t', 1):
            abort(400, 'Slice: requested T plane outside of image bounds: [%s]'%t1 )
        if t2>dims.get('image_num_t', 1):
            abort(400, 'Slice: requested T plane outside of image bounds: [%s]'%t2 )

        # shortcuts are only possible with no ROIs are requested
        if x1==x2==0 and y1==y2==0:
            # shortcut if input image has only one T and Z
            if dims.get('image_num_z', 1)<=1 and dims.get('image_num_t', 1)<=1:
                log.debug('Slice: plane requested on image with no T or Z planes, skipping...')
                return token
            # shortcut if asking for all slices with only a specific time point in an image with only one time pont
            if z1==z2==0 and t1<=1 and dims.get('image_num_t', 1)<=1:
                log.debug('Slice: T plane requested on image with no T planes, skipping...')
                return token
            # shortcut if asking for all time points with only a specific z slice in an image with only one z slice
            if t1==t2==0 and z1<=1 and dims.get('image_num_z', 1)<=1:
                log.debug('Slice: Z plane requested on image with no Z planes, skipping...')
                return token

        if z1==z2==0: z1=1; z2=dims.get('image_num_z', 1)
        if t1==t2==0: t1=1; t2=dims.get('image_num_t', 1)

        # construct a sliced filename
        ifname = token.first_input_file()
        ofname = '%s.%d-%d,%d-%d,%d-%d,%d-%d.ome.tif' % (token.data, x1,x2,y1,y2,z1,z2,t1,t2)
        log.debug('Slice %s: from [%s] to [%s]', token.resource_id, ifname, ofname)

        new_w = x2-x1
        new_h = y2-y1
        new_z = max(1, z2 - z1 + 1)
        new_t = max(1, t2 - t1 + 1)
        info = {
            'image_num_z': new_z,
            'image_num_t': new_t,
        }
        if new_w>0: info['image_num_x'] = new_w+1
        if new_h>0: info['image_num_y'] = new_h+1

        meta = token.meta or {}
        unsupported_multifile = False
        if token.is_multifile_series() is True and (z2==0 or z2==z1) and (t2==0 or t2==t1) and x1==x2 and y1==y2 and meta.get('image_num_c', 0)==0:
            unsupported_multifile = True

        if dims.get('converter', '') == ConverterImgcnv.name or unsupported_multifile is True:
            r = ConverterImgcnv.slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format)
            # if decoder returned a list of operations for imgcnv to enqueue
            if isinstance(r, list):
                return self.server.enqueue(token, 'slice', ofname, fmt=default_format, command=r, dims=info)

        # slice the image
        if not os.path.exists(ofname):
            intermediate = '%s.ome.tif'%token.data

            if 'converter' in dims and dims.get('converter') in self.server.converters:
                r = self.server.converters[dims.get('converter')].slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format, intermediate=intermediate)

            # if desired converter failed, perform exhaustive conversion
            if r is None:
                for n,c in self.server.converters.iteritems():
                    if n in [ConverterImgcnv.name, dims.get('converter')]: continue
                    r = c.slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format, intermediate=intermediate)
                    if r is not None:
                        break

            if r is None:
                log.error('Slice %s: could not generate slice for [%s]', token.resource_id, ifname)
                abort(415, 'Could not generate slice' )

            # if decoder returned a list of operations for imgcnv to enqueue
            if isinstance(r, list):
                return self.server.enqueue(token, 'slice', ofname, fmt=default_format, command=r, dims=info)

        return token.setImage(ofname, fmt=default_format, dims=info, input=ofname)

class FormatOperation(BaseOperation):
    '''Provides an image in the requested format
       arg = format[,stream][,OPT1][,OPT2][,...]
       some formats are: tiff, jpeg, png, bmp, raw
       stream sets proper file name and forces browser to show save dialog
       any additional comma separated options are passed directly to the encoder

       for movie formats: fps,R,bitrate,B
       where R is a float number of frames per second and B is the integer bitrate

       for tiff: compression,C
       where C is the compression algorithm: none, packbits, lzw, fax

       for jpeg: quality,V
       where V is quality 0-100, 100 being best

       ex: format=jpeg'''
    name = 'format'

    def __str__(self):
        return 'format: Returns an Image in the requested format, arg = format[,stream][,OPT1][,OPT2][,...]'

    def dryrun(self, token, arg):
        args = arg.lower().split(',')
        fmt = default_format
        if len(args)>0:
            fmt = args.pop(0).lower()

        stream = False
        if 'stream' in args:
            stream = True
            args.remove('stream')

        name_extra = '' if len(args)<=0 else '.%s'%'.'.join(args)
        ext = self.server.converters.defaultExtension(fmt)

        ofile = '%s.%s%s.%s'%(token.data, name_extra, fmt, ext)
        if stream:
            fpath = ofile.split('/')
            filename = '%s_%s.%s'%(token.resource_name, fpath[len(fpath)-1], ext)
            token.setFile(fname=ofile)
            token.outFileName = filename
        else:
            token.setImage(fname=ofile, fmt=fmt)
        return token

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Format: input is not an image...' )

        args = arg.lower().split(',')
        fmt = default_format
        if len(args)>0:
            fmt = args.pop(0).lower()

        stream = False
        if 'stream' in args:
            stream = True
            args.remove('stream')

        # avoid doing anything if requested format is in requested format
        dims = token.dims or {}
        if dims.get('format','').lower() == fmt and not token.hasQueue():
            log.debug('%s: Input is in requested format, avoid reconvert...', token.resource_id)
            return token

        if fmt not in self.server.writable_formats:
            abort(400, 'Requested format [%s] is not writable'%fmt )

        name_extra = '' if len(args)<=0 else '.%s'%'.'.join(args)
        ext = self.server.converters.defaultExtension(fmt)
        ifile = token.first_input_file()
        ofile = '%s.%s%s.%s'%(token.data, name_extra, fmt, ext)
        log.debug('Format %s: %s -> %s with %s opts=[%s]', token.resource_id, ifile, ofile, fmt, args)

        if not os.path.exists(ofile):
            extra = token.drainQueue()
            queue_size = len(extra)
            if len(args) > 0:
                extra.extend( ['-options', (' ').join(args)])
            elif fmt in ['jpg', 'jpeg']:
                extra.extend(['-options', 'quality 95 progressive yes'])

            r = None
            #if dims.get('converter', '') == ConverterImgcnv.name:

            # first try first converter that supports this output format
            c = self.server.writable_formats[fmt]
            first_name = c.name
            # if there are any operations to be run on the output
            if c.name == ConverterImgcnv.name or queue_size < 1:
                r = c.convert(token, ofile, fmt, extra=extra)

            # try using other converters directly
            if r is None:
                log.debug('%s could not convert [%s] to [%s] format'%(first_name, ifile, fmt))
                log.debug('Trying other converters directly')
                for n,c in self.server.converters.iteritems():
                    if n==first_name:
                        continue
                    if n == ConverterImgcnv.name or queue_size < 1:
                        r = c.convert(token, ofile, fmt, extra=extra)
                    if r is not None and os.path.exists(ofile):
                        break

            # using ome-tiff as intermediate if everything failed
            if r is None:
                log.debug('None of converters could connvert [%s] to [%s] format'%(ifile, fmt))
                log.debug('Converting to OME-TIFF and then to desired output')
                r = self.server.imageconvert(token, ifile, ofile, fmt=fmt, extra=extra, try_imgcnv=False)

            if r is None:
                log.error('Format %s: %s could not convert with [%s] format [%s] -> [%s]', token.resource_id, c.CONVERTERCOMMAND, fmt, ifile, ofile)
                abort(415, 'Could not convert into %s format'%fmt )

        if stream:
            fpath = ofile.split('/')
            filename = '%s_%s.%s'%(token.resource_name, fpath[len(fpath)-1], ext)
            token.setFile(fname=ofile)
            token.outFileName = filename
            token.input = ofile
        else:
            token.setImage(fname=ofile, fmt=fmt, input=ofile)

        # if (ofile != ifile) and (fmt != 'raw'):
        #     try:
        #         info = self.server.getImageInfo(filename=ofile)
        #         if int(info['image_num_p'])>1:
        #             if 'image_num_z' in token.dims: info['image_num_z'] = token.dims['image_num_z']
        #             if 'image_num_t' in token.dims: info['image_num_t'] = token.dims['image_num_t']
        #         token.dims = info
        #     except Exception:
        #         pass


        if (ofile != ifile):
            info = {
                'format': fmt,
            }
            if fmt == 'jpeg':
                info.update({
                    'image_pixel_depth': 8,
                    'image_pixel_format': 'unsigned integer',
                    'image_num_c': min(4, int(dims.get('image_num_c', 0))),
                })
            elif fmt not in ['tiff', 'bigtiff', 'ome-tiff', 'ome-bigtiff', 'raw']:
                info = self.server.getImageInfo(filename=ofile)
                info.update({
                    'image_num_z': dims.get('image_num_z', ''),
                    'image_num_t': dims.get('image_num_t', ''),
                })
            token.dims.update(info)

        return token

def compute_new_size(imw, imh, w, h, keep_aspect_ratio, no_upsample):
    if no_upsample is True and imw<=w and imh<=h:
        return (imw, imh)

    if keep_aspect_ratio is True:
        if imw/float(w) >= imh/float(h):
            h = 0
        else:
            w = 0

    # it's allowed to specify only one of the sizes, the other one will be computed
    if w == 0:
        w = int(round(imw / (imh / float(h))))
    if h == 0:
        h = int(round(imh / (imw / float(w))))

    return (w, h)

class ResizeOperation(BaseOperation):
    '''Provide images in requested dimensions
       arg = w,h,method[,AR|,MX]
       w - new width
       h - new height
       method - NN or BL, or BC (Nearest neighbor, Bilinear, Bicubic respectively)
       if either w or h is ommited or 0, it will be computed using aspect ratio of the image
       if ,AR is present then the size will be used as bounding box and aspect ration preserved
       if ,MX is present then the size will be used as maximum bounding box and aspect ratio preserved
       with MX: if image is smaller it will not be resized!
       #size_arg = '-resize 128,128,BC,AR'
       ex: resize=100,100'''
    name = 'resize'

    def __str__(self):
        return 'resize: returns an Image in requested dimensions, arg = w,h,method[,AR|,MX]'

    # def dryrun(self, token, arg):
    #     ss = arg.split(',')
    #     size = [0,0]
    #     method = 'BL'
    #     textAddition = ''

    #     if len(ss)>0 and ss[0].isdigit():
    #         size[0] = int(ss[0])
    #     if len(ss)>1 and ss[1].isdigit():
    #         size[1] = int(ss[1])
    #     if len(ss)>2:
    #         method = ss[2].upper()
    #     if len(ss)>3:
    #         textAddition = ss[3].upper()

    #     if size[0]<=0 and size[1]<=0:
    #         abort(400, 'Resize: size is unsupported: [%s]'%arg )

    #     if method not in ['NN', 'BL', 'BC']:
    #         abort(400, 'Resize: method is unsupported: [%s]'%arg )

    #     # if the image is smaller and MX is used, skip resize
    #     dims = token.dims or {}
    #     if maxBounding and dims.get('image_num_x',0)<=size[0] and dims.get('image_num_y',0)<=size[1]:
    #         log.debug('Resize: Max bounding resize requested on a smaller image, skipping...')
    #         return token

    #     ofile = '%s.size_%d,%d,%s,%s' % (token.data, size[0], size[1], method, textAddition)
    #     return token.setImage(ofile, fmt=default_format)

    def action(self, token, arg):
        log.debug('Resize %s: %s', token.resource_id, arg)

        #size = tuple(map(int, arg.split(',')))
        ss = arg.split(',')
        size = [0,0]
        method = 'BL'
        aspectRatio = ''
        maxBounding = False
        textAddition = ''

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2:
            method = ss[2].upper()
        if len(ss)>3:
            textAddition = ss[3].upper()

        if len(ss)>3 and (textAddition == 'AR'):
            aspectRatio = ',AR'
        if len(ss)>3 and (textAddition == 'MX'):
            maxBounding = True
            aspectRatio = ',AR'

        if size[0]<=0 and size[1]<=0:
            abort(400, 'Resize: size is unsupported: [%s]'%arg )

        if method not in ['NN', 'BL', 'BC']:
            abort(400, 'Resize: method is unsupported: [%s]'%arg )

        # if the image is smaller and MX is used, skip resize
        dims = token.dims or {}
        if maxBounding and dims.get('image_num_x',0)<=size[0] and dims.get('image_num_y',0)<=size[1]:
            log.debug('Resize: Max bounding resize requested on a smaller image, skipping...')
            return token

        ifile = token.first_input_file()
        ofile = '%s.size_%d,%d,%s,%s' % (token.data, size[0], size[1], method, textAddition)
        args = ['-resize', '%s,%s,%s%s'%(size[0], size[1], method,aspectRatio)]
        num_x = int(dims.get('image_num_x', 0))
        num_y = int(dims.get('image_num_y', 0))
        width, height = compute_new_size(num_x, num_y, size[0], size[1], aspectRatio!='', maxBounding)
        log.debug('Resize %s: [%sx%s] to [%sx%s] for [%s] to [%s]', token.resource_id, num_x, num_y, width, height, ifile, ofile)

        # if image has multiple resolution levels find the closest one and request it
        num_l = dims.get('image_num_resolution_levels', 1)
        if num_l>1 and '-res-level' not in token.getQueue():
            try:
                scales = [float(i) for i in dims.get('image_resolution_level_scales', '').split(',')]
                #log.debug('scales: %s',  scales)
                sizes = [(round(num_x*i),round(num_y*i)) for i in scales]
                #log.debug('scales: %s',  sizes)
                relatives = [max(width/float(sz[0]), height/float(sz[1])) for sz in sizes]
                #log.debug('relatives: %s',  relatives)
                relatives = [i if i<=1 else 0 for i in relatives]
                #log.debug('relatives: %s',  relatives)
                level = relatives.index(max(relatives))
                args.extend(['-res-level', str(level)])
            except (Exception):
                pass

        info = {
            'image_num_x': width,
            'image_num_y': height,
            'pixel_resolution_x': dims.get('pixel_resolution_x', 0) * (num_x / float(width)),
            'pixel_resolution_y': dims.get('pixel_resolution_y', 0) * (num_y / float(height)),
        }
        return self.server.enqueue(token, 'resize', ofile, fmt=default_format, command=args, dims=info)


class Resize3DOperation(BaseOperation):
    '''Provide images in requested dimensions
       arg = w,h,d,method[,AR|,MX]
       w - new width
       h - new height
       d - new depth
       method - NN or TL, or TC (Nearest neighbor, Trilinear, Tricubic respectively)
       if either w or h or d are ommited or 0, missing value will be computed using aspect ratio of the image
       if ,AR is present then the size will be used as bounding box and aspect ration preserved
       if ,MX is present then the size will be used as maximum bounding box and aspect ratio preserved
       with MX: if image is smaller it will not be resized!
       ex: resize3d=100,100,100,TC'''
    name = 'resize3d'

    def __str__(self):
        return 'resize3d: returns an image in requested dimensions, arg = w,h,d,method[,AR|,MX]'

    def dryrun(self, token, arg):
        ss = arg.split(',')
        size = [0,0,0]
        method = 'TC'
        textAddition = ''

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2 and ss[2].isdigit():
            size[2] = int(ss[2])
        if len(ss)>3:
            method = ss[3].upper()
        if len(ss)>4:
            textAddition = ss[4].upper()

        ofile = '%s.size3d_%d,%d,%d,%s,%s' % (token.data, size[0], size[1], size[2], method,textAddition)
        return token.setImage(ofile, fmt=default_format)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Resize3D: input is not an image...' )
        log.debug('Resize3D %s: %s', token.resource_id, arg )

        #size = tuple(map(int, arg.split(',')))
        ss = arg.split(',')
        size = [0,0,0]
        method = 'TC'
        aspectRatio = ''
        maxBounding = False
        textAddition = ''

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2 and ss[2].isdigit():
            size[2] = int(ss[2])
        if len(ss)>3:
            method = ss[3].upper()
        if len(ss)>4:
            textAddition = ss[4].upper()

        if len(ss)>4 and (textAddition == 'AR'):
            aspectRatio = ',AR'
        if len(ss)>4 and (textAddition == 'MX'):
            maxBounding = True
            aspectRatio = ',AR'

        if size[0]<=0 and size[1]<=0 and size[2]<=0:
            abort(400, 'Resize3D: size is unsupported: [%s]'%arg )

        if method not in ['NN', 'TL', 'TC']:
            abort(400, 'Resize3D: method is unsupported: [%s]'%arg )

        # if the image is smaller and MX is used, skip resize
        dims = token.dims or {}
        w = dims.get('image_num_x', 0)
        h = dims.get('image_num_y', 0)
        z = dims.get('image_num_z', 1)
        t = dims.get('image_num_t', 1)
        d = max(z, t)
        if w==size[0] and h==size[1] and d==size[2]:
            return token
        if maxBounding and w<=size[0] and h<=size[1] and d<=size[2]:
            return token
        if (z>1 and t>1) or (z==1 and t==1):
            abort(400, 'Resize3D: only supports 3D images' )

        ifile = token.first_input_file()
        ofile = '%s.size3d_%d,%d,%d,%s,%s' % (token.data, size[0], size[1], size[2], method,textAddition)
        log.debug('Resize3D %s: %s to %s', token.resource_id, ifile, ofile)

        width, height = compute_new_size(w, h, size[0], size[1], aspectRatio!='', maxBounding)
        zrestag = 'pixel_resolution_z' if z>1 else 'pixel_resolution_t'
        info = {
            'image_num_x': width,
            'image_num_y': height,
            'image_num_z': size[2] if z>1 else 1,
            'image_num_t': size[2] if t>1 else 1,
            'pixel_resolution_x': dims.get('pixel_resolution_x', 0) * (w / float(width)),
            'pixel_resolution_y': dims.get('pixel_resolution_y', 0) * (h / float(height)),
            zrestag: dims.get(zrestag, 0) * (d / float(size[2])),
        }
        command = token.drainQueue()
        if not os.path.exists(ofile):
            command.extend(['-resize3d', '%s,%s,%s,%s%s'%(size[0], size[1], size[2], method, aspectRatio)])
            self.server.imageconvert(token, ifile, ofile, fmt=default_format, extra=command)

        return token.setImage(ofile, fmt=default_format, dims=info, input=ofile)

class Rearrange3DOperation(BaseOperation):
    '''Rearranges dimensions of an image
       arg = xzy|yzx
       xz: XYZ -> XZY
       yz: XYZ -> YZX
       ex: rearrange3d=xz'''
    name = 'rearrange3d'

    def __str__(self):
        return 'rearrange3d: rearrange dimensions of a 3D image, arg = [xzy,yzx]'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ifile = token.data
        ofile = '%s.rearrange3d_%s'%(token.data, arg)
        return token.setImage(ofile, fmt=default_format)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Rearrange3D: input is not an image...' )
        log.debug('Rearrange3D %s: %s', token.resource_id, arg )
        arg = arg.lower()

        if arg not in ['xzy', 'yzx']:
            abort(400, 'Rearrange3D: method is unsupported: [%s]'%arg )

        # if the image must be 3D, either z stack or t series
        dims = token.dims or {}
        x = dims['image_num_x']
        y = dims['image_num_y']
        z = dims['image_num_z']
        t = dims['image_num_t']
        if (z>1 and t>1) or (z==1 and t==1):
            abort(400, 'Rearrange3D: only supports 3D images' )

        nz = y if arg == 'xzy' else x
        info = {
            'image_num_x': x if arg == 'xzy' else y,
            'image_num_y': z,
            'image_num_z': nz if z>1 else 1,
            'image_num_t': nz if t>1 else 1,
        }
        ifile = token.first_input_file()
        ofile = '%s.rearrange3d_%s'%(token.data, arg)
        command = token.drainQueue()
        if not os.path.exists(ofile):
            command.extend(['-rearrange3d', '%s'%arg])
            self.server.imageconvert(token, ifile, ofile, fmt=default_format, extra=command)

        return token.setImage(ofile, fmt=default_format, dims=info, input=ofile)

class ThumbnailOperation(BaseOperation):
    '''Create and provide thumbnails for images:
       The default values are: 128,128,BL,,jpeg
       arg = [w,h][,method][,preproc][,format]
       w - thumbnail width, width and hight are defined as maximum boundary
       h - thumbnail height, width and hight are defined as maximum boundary
       method - ''|NN|BL|BC - default, Nearest neighbor, Bilinear, Bicubic respectively
       preproc - ''|MID|MIP|NIP - empty (auto), middle slice, maximum intensity projection, minimum intensity projection
       format - output image format, default is JPEG
       ex: ?thumbnail
       ex: ?thumbnail=200,200,BC,,png
       ex: ?thumbnail=200,200,BC,mid,png '''
    name = 'thumbnail'

    def __str__(self):
        return 'thumbnail: returns an image as a thumbnail, arg = [w,h][,method][,preproc][,format]'

    def dryrun(self, token, arg):
        ss = arg.split(',')
        size = [safeint(ss[0], 128) if len(ss)>0 else 128,
                safeint(ss[1], 128) if len(ss)>1 else 128]
        method = ss[2].upper() if len(ss)>2 and len(ss[2])>0 else 'BC'
        preproc = ss[3].lower() if len(ss)>3 and len(ss[3])>0 else ''
        preprocc = ',%s'%preproc if len(preproc)>0 else '' # attempt to keep the filename backward compatible
        fmt = ss[4].lower() if len(ss)>4 and len(ss[4])>0 else 'jpeg'

        dims = token.dims or {}
        num_x = int(dims.get('image_num_x', 0))
        num_y = int(dims.get('image_num_y', 0))
        width, height = compute_new_size(num_x, num_y, size[0], size[1], keep_aspect_ratio=True, no_upsample=True)
        info = {
            'image_num_x': width,
            'image_num_y': height,
            'image_num_c': 3,
            'image_num_z': 1,
            'image_num_t': 1,
            'image_pixel_depth': 8,
            'format': fmt,
        }
        ext = self.server.converters.defaultExtension(fmt)
        ofile = '%s.thumb_%s,%s,%s%s.%s'%(token.data, size[0], size[1], method, preprocc, ext)
        return token.setImage(ofile, fmt=fmt, dims=info)

    def action(self, token, arg):
        ss = arg.split(',')
        size = [safeint(ss[0], 128) if len(ss)>0 else 128,
                safeint(ss[1], 128) if len(ss)>1 else 128]
        method = ss[2].upper() if len(ss)>2 and len(ss[2])>0 else 'BC'
        preproc = ss[3].lower() if len(ss)>3 and len(ss[3])>0 else ''
        preprocc = ',%s'%preproc if len(preproc)>0 else '' # attempt to keep the filename backward compatible
        fmt = ss[4].lower() if len(ss)>4 and len(ss[4])>0 else 'jpeg'

        if size[0]<=0 and size[1]<=0:
            abort(400, 'Thumbnail: size is unsupported [%s]'%arg)

        if method not in ['NN', 'BL', 'BC']:
            abort(400, 'Thumbnail: method is unsupported [%s]'%arg)

        if preproc not in ['', 'mid', 'mip', 'nip']:
            abort(400, 'Thumbnail: method is unsupported [%s]'%arg)

        ext = self.server.converters.defaultExtension(fmt)
        ifile = token.first_input_file()
        ofile = '%s.thumb_%s,%s,%s%s.%s'%(token.data, size[0], size[1], method, preprocc, ext)

        dims = token.dims or {}
        num_x = int(dims.get('image_num_x', 0))
        num_y = int(dims.get('image_num_y', 0))
        width, height = compute_new_size(num_x, num_y, size[0], size[1], keep_aspect_ratio=True, no_upsample=True)
        info = {
            'image_num_x': width,
            'image_num_y': height,
            'image_num_c': 3,
            'image_num_z': 1,
            'image_num_t': 1,
            'image_pixel_depth': 8,
            'format': fmt,
        }

        # if image can be doecoded with imageconvert, enqueue
        if dims.get('converter', '') == ConverterImgcnv.name:
            r = ConverterImgcnv.thumbnail(token, ofile, size[0], size[1], method=method, preproc=preproc, fmt=fmt)
            if isinstance(r, list):
                return self.server.enqueue(token, 'thumbnail', ofile, fmt=fmt, command=r, dims=info)

        # if image requires other decoder
        if not os.path.exists(ofile):
            intermediate = '%s.ome.tif'%(token.data)

            if 'converter' in dims and dims.get('converter') in self.server.converters:
                r = self.server.converters[dims.get('converter')].thumbnail(token, ofile, size[0], size[1], method=method, intermediate=intermediate, preproc=preproc, fmt=fmt)

            # if desired converter failed, perform exhaustive conversion
            if r is None:
                for n,c in self.server.converters.iteritems():
                    if n in [ConverterImgcnv.name, dims.get('converter')]: continue
                    r = c.thumbnail(token, ofile, size[0], size[1], method=method, intermediate=intermediate, preproc=preproc, fmt=fmt)
                    if r is not None:
                        break
            if r is None:
                log.error('Thumbnail %s: could not generate thumbnail for [%s]', token.resource_id, ifile)
                abort(415, 'Could not generate thumbnail' )
            if isinstance(r, list):
                return self.server.enqueue(token, 'thumbnail', ofile, fmt=fmt, command=r, dims=info)

        return token.setImage(ofile, fmt=fmt, dims=info, input=ofile)

class RoiOperation(BaseOperation):
    '''Provides ROI for requested images
       arg = x1,y1,x2,y2
       x1,y1 - top left corner
       x2,y2 - bottom right
       all values are in ranges [1..N]
       0 or empty - means first/last element
       supports multiple ROIs in which case those will be only cached
       ex: roi=10,10,100,100'''
    name = 'roi'

    def __str__(self):
        return 'roi: returns an image in specified ROI, arg = x1,y1,x2,y2[;x1,y1,x2,y2], all values are in ranges [1..N]'

    def dryrun(self, token, arg):
        vs = arg.split(';')[0].split(',', 4)
        x1 = int(vs[0]) if len(vs)>0 and vs[0].isdigit() else 0
        y1 = int(vs[1]) if len(vs)>1 and vs[1].isdigit() else 0
        x2 = int(vs[2]) if len(vs)>2 and vs[2].isdigit() else 0
        y2 = int(vs[3]) if len(vs)>3 and vs[3].isdigit() else 0
        ofile = '%s.roi_%d,%d,%d,%d'%(token.data, x1-1,y1-1,x2-1,y2-1)
        info = {
            'image_num_x': x2-x1,
            'image_num_y': y2-y1,
        }
        return token.setImage(ofile, fmt=default_format, dims=info)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Roi: input is not an image...' )
        rois = []
        for a in arg.split(';'):
            vs = a.split(',', 4)
            x1 = int(vs[0]) if len(vs)>0 and vs[0].isdigit() else 0
            y1 = int(vs[1]) if len(vs)>1 and vs[1].isdigit() else 0
            x2 = int(vs[2]) if len(vs)>2 and vs[2].isdigit() else 0
            y2 = int(vs[3]) if len(vs)>3 and vs[3].isdigit() else 0
            rois.append((x1,y1,x2,y2))
        x1,y1,x2,y2 = rois[0]

        if x1<=0 and x2<=0 and y1<=0 and y2<=0:
            abort(400, 'ROI: region is not provided')

        ifile = token.first_input_file()
        otemp = token.data
        ofile = '%s.roi_%d,%d,%d,%d'%(token.data, x1-1,y1-1,x2-1,y2-1)
        log.debug('ROI %s: %s to %s', token.resource_id, ifile, ofile)

        if len(rois) == 1:
            info = {
                'image_num_x': x2-x1,
                'image_num_y': y2-y1,
            }
            command = ['-roi', '%s,%s,%s,%s'%(x1-1,y1-1,x2-1,y2-1)]
            return self.server.enqueue(token, 'roi', ofile, fmt=default_format, command=command, dims=info)

        # remove pre-computed ROIs
        rois = [(_x1,_y1,_x2,_y2) for _x1,_y1,_x2,_y2 in rois if not os.path.exists('%s.roi_%d,%d,%d,%d'%(otemp,_x1-1,_y1-1,_x2-1,_y2-1))]

        lfile = '%s.rois'%(otemp)
        command = token.drainQueue()
        if not os.path.exists(ofile) or len(rois)>0:
            # global ROI lock on this input since we can't lock on all individual outputs
            with Locks(ifile, lfile, failonexist=True) as l:
                if l.locked: # the file is not being currently written by another process
                    s = ';'.join(['%s,%s,%s,%s'%(x1-1,y1-1,x2-1,y2-1) for x1,y1,x2,y2 in rois])
                    command.extend(['-roi', s])
                    command.extend(['-template', '%s.roi_{x1},{y1},{x2},{y2}'%otemp])
                    self.server.imageconvert(token, ifile, ofile, fmt=default_format, extra=command)
                    # ensure the virtual locking file is not removed
                    with open(lfile, 'wb') as f:
                        f.write('#Temporary locking file')

        # ensure the operation is finished
        if os.path.exists(lfile):
            with Locks(lfile):
                pass

        info = {
            'image_num_x': x2-x1,
            'image_num_y': y2-y1,
        }
        return token.setImage(ofile, fmt=default_format, dims=info, input=ofile)

class RemapOperation(BaseOperation):
    """Provide an image with the requested channel mapping
       arg = channel,channel...
       output image will be constructed from channels 1 to n from input image, 0 means black channel
       remap=display - will use preferred mapping found in file's metadata
       remap=gray - will return gray scale image with visual weighted mapping from RGB or equal weights for other nuber of channels
       ex: remap=3,2,1"""
    name = 'remap'

    def __str__(self):
        return 'remap: returns an image with the requested channel mapping, arg = [channel,channel...]|gray|display'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.map_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        ifile = token.first_input_file()
        ofile = '%s.map_%s'%(token.data, arg)
        log.debug('Remap %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        channels = 0
        if arg == 'display':
            args = ['-fusemeta']
            channels = 3
        elif arg=='gray' or arg=='grey':
            args = ['-fusegrey']
            channels = 1
        else:
            args = ['-remap', arg]
            channels = len(arg.split(','))

        info = {
            'image_num_c': channels,
        }
        return self.server.enqueue(token, 'remap', ofile, fmt=default_format, command=args, dims=info)

class FuseOperation(BaseOperation):
    """Provide an RGB image with the requested channel fusion
       arg = W1R,W1G,W1B;W2R,W2G,W2B;W3R,W3G,W3B;W4R,W4G,W4B
       output image will be constructed from channels 1 to n from input image mapped to RGB components with desired weights
       fuse=display will use preferred mapping found in file's metadata
       ex: fuse=255,0,0;0,255,0;0,0,255;255,255,255:A"""
    name = 'fuse'

    def __str__(self):
        return 'fuse: returns an RGB image with the requested channel fusion, arg = W1R,W1G,W1B;W2R,W2G,W2B;...[:METHOD]'

    def dryrun(self, token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        elif '.' in arg:
            (arg, method) = arg.split('.', 1)
        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])
        ofile = '%s.fuse_%s_%s'%(token.data, argenc, method)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        elif '.' in arg:
            (arg, method) = arg.split('.', 1)

        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])

        ifile = token.first_input_file()
        ofile = '%s.fuse_%s_%s'%(token.data, argenc, method)
        log.debug('Fuse %s: %s to %s with [%s:%s]', token.resource_id, ifile, ofile, arg, method)

        if arg == 'display':
            args = ['-fusemeta']
        else:
            args = ['-fusergb', arg]
        if method != 'a':
            args.extend(['-fusemethod', method])

        info = {
            'image_num_c': 3,
        }
        return self.server.enqueue(token, 'fuse', ofile, fmt=default_format, command=args, dims=info)

class DepthOperation(BaseOperation):
    '''Provide an image with converted depth per pixel:
       arg = depth,method[,format]
       depth is in bits per pixel
       method is: f or d or t or e
         f - full range
         d - data range
         t - data range with tolerance
         e - equalized
         hounsfield - hounsfield space enhancement
       format is: u, s or f, if unset keeps image original
         u - unsigned integer
         s - signed integer
         f - floating point
       channel mode is: cs or cc
         cs - channels separate
         cc - channels combined
       window center, window width - only used for hounsfield enhancement
         ex: depth=8,hounsfield,u,,40,80
       ex: depth=8,d or depth=8,d,u,cc'''
    name = 'depth'

    def __str__(self):
        return 'depth: returns an image with converted depth per pixel, arg = depth,method[,format][,channelmode]'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.depth_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        ms = ['f', 'd', 't', 'e', 'c', 'n', 'hounsfield']
        ds = ['8', '16', '32', '64']
        fs = ['u', 's', 'f']
        fs_map = {
            'u': 'unsigned integer',
            's': 'signed integer',
            'f': 'floating point'
        }
        cm = ['cs', 'cc']
        d='d'; m='8'; f='u'; c='cs'
        arg = arg.lower()
        args = arg.split(',')
        if len(args)>0: d = args[0]
        if len(args)>1: m = args[1]
        if len(args)>2: f = args[2] or 'u'
        if len(args)>3: c = args[3] or 'cs'
        if len(args)>4: window_center = args[4] or None
        if len(args)>5: window_width = args[5] or None

        if d is None or d not in ds:
            abort(400, 'Depth: depth is unsupported: %s'%d)
        if m is None or m not in ms:
            abort(400, 'Depth: method is unsupported: %s'%m )
        if f is not None and f not in fs:
            abort(400, 'Depth: format is unsupported: %s'%f )
        if c is not None and c not in cm:
            abort(400, 'Depth: channel mode is unsupported: %s'%c )
        if m == 'hounsfield' and (window_center is None or window_width is None):
            abort(400, 'Depth: hounsfield enhancement requires window center and width' )

        ifile = token.first_input_file()
        ofile = '%s.depth_%s'%(token.data, arg)
        log.debug('Depth %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        extra=[]
        if m == 'hounsfield':
            extra.extend(['-hounsfield', '%s,%s,%s,%s'%(d,f,window_center,window_width)])
        else:
            extra.extend(['-depth', arg])

        dims = {
            'image_pixel_depth': d,
            'image_pixel_format': fs_map[f],
        }
        return self.server.enqueue(token, 'depth', ofile, fmt=default_format, command=extra, dims=dims)


################################################################################
# Tiling Image Operations
################################################################################

class TileOperation(BaseOperation):
    '''Provides a tile of an image :
       arg = l,tnx,tny,tsz
       l: level of the pyramid, 0 - initial level, 1 - scaled down by a factor of 2
       tnx, tny: x and y tile number on the grid
       tsz: tile size
       All values are in range [0..N]
       ex: tile=0,2,3,512'''
    name = 'tile'

    def __str__(self):
        return 'tile: returns a tile, arg = l,tnx,tny,tsz. All values are in range [0..N]'

    def dryrun(self, token, arg):
        level=0; tnx=0; tny=0; tsz=512;
        vs = arg.split(',', 4)
        if len(vs)>0 and vs[0].isdigit(): level = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): tnx = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): tny = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): tsz = int(vs[3])

        dims = token.dims or {}
        width = dims.get('image_num_x', 0)
        height = dims.get('image_num_y', 0)
        if width<=tsz and height<=tsz:
            log.debug('Dryrun tile: Image is smaller than requested tile size, passing the whole image...')
            return token

        x = tnx * tsz
        y = tny * tsz
        if x>=width or y>=height:
            abort(400, 'Tile: tile position outside of the image: %s,%s'%(tnx, tny))

        # the new tile service does not change the number of z points in the image and if contains all z will perform the operation
        info = {
            'image_num_x': tsz if width-x >= tsz else width-x,
            'image_num_y': tsz if height-y >= tsz else height-y,
            #'image_num_z': 1,
            #'image_num_t': 1,
        }

        base_name = '%s.tiles'%(token.data)
        ofname    = os.path.join(base_name, '%s_%.3d_%.3d_%.3d' % (tsz, level, tnx, tny))
        return token.setImage(ofname, fmt=default_format, dims=info)

    def action(self, token, arg):
        '''arg = l,tnx,tny,tsz'''
        if not token.isFile():
            abort(400, 'Tile: input is not an image...' )
        level=0; tnx=0; tny=0; tsz=512;
        vs = arg.split(',', 4)
        if len(vs)>0 and vs[0].isdigit(): level = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): tnx = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): tny = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): tsz = int(vs[3])
        log.debug( 'Tile: l:%d, tnx:%d, tny:%d, tsz:%d' % (level, tnx, tny, tsz) )

        # if input image is smaller than the requested tile size
        dims = token.dims or {}
        width = dims.get('image_num_x', 0)
        height = dims.get('image_num_y', 0)
        if width<=tsz and height<=tsz:
            log.debug('Image is smaller than requested tile size, passing the whole image...')
            return token

        # construct a sliced filename
        ifname    = token.first_input_file()
        base_name = '%s.tiles'%(token.data)
        _mkdir( base_name )
        ofname    = os.path.join(base_name, '%s_%.3d_%.3d_%.3d' % (tsz, level, tnx, tny))
        hist_name = os.path.join(base_name, '%s_histogram'%(tsz))

        # if input image does not contain tile pyramid, create one and pass it along
        if dims.get('image_num_resolution_levels', 0)<2 or dims.get('tile_num_x', 0)<1:
            pyramid = '%s.pyramid.tif'%(token.data)
            command = token.drainQueue()
            if not os.path.exists(pyramid):
                #command.extend(['-ohst', hist_name])
                command.extend(['-options', 'compression lzw tiles %s pyramid subdirs'%default_tile_size])
                log.debug('Generate tiled pyramid %s: from %s to %s with %s', token.resource_id, ifname, pyramid, command )
                r = self.server.imageconvert(token, ifname, pyramid, fmt=default_format, extra=command)
                if r is None:
                    abort(500, 'Tile: could not generate pyramidal file' )
            # ensure the file was created
            with Locks(pyramid):
                pass

            # compute the number of pyramidal levels
            # sz = max(width, height)
            # num_levels = math.ceil(math.log(sz, 2)) - math.ceil(math.log(min_level_size, 2)) + 1
            # scales = [1/float(pow(2,i)) for i in range(0, num_levels)]
            # info = {
            #     'image_num_resolution_levels': num_levels,
            #     'image_resolution_level_scales': ',',join([str(i) for i in scales]),
            #     'tile_num_x': default_tile_size,
            #     'tile_num_y': default_tile_size,
            #     'converter': ConverterImgcnv.name,
            # }

            # load the number of pyramidal levels from the file
            info2 = self.server.getImageInfo(filename=pyramid)
            info = {
                'image_num_resolution_levels': info2.get('image_num_resolution_levels'),
                'image_resolution_level_scales': info2.get('image_resolution_level_scales'),
                'tile_num_x': info2.get('tile_num_x'),
                'tile_num_y': info2.get('tile_num_y'),
                'converter': info2.get('converter'),
            }
            log.debug('Updating original input to pyramidal version %s: %s -> %s', token.resource_id, ifname, pyramid )
            token.setImage(ofname, fmt=default_format, dims=info, input=pyramid)
            ifname = pyramid


        # compute output tile size
        dims = token.dims or {}
        x = tnx * tsz
        y = tny * tsz
        if x>=width or y>=height:
            abort(400, 'Tile: tile position outside of the image: %s,%s'%(tnx, tny))

        # the new tile service does not change the number of z points in the image and if contains all z will perform the operation
        info = {
            'image_num_x': tsz if width-x >= tsz else width-x,
            'image_num_y': tsz if height-y >= tsz else height-y,
            #'image_num_z': 1,
            #'image_num_t': 1,
        }

        #log.debug('Inside pyramid dims: %s', dims)
        #log.debug('Inside pyramid input: %s', token.first_input_file() )
        #log.debug('Inside pyramid data: %s', token.data )

        # extract individual tile from pyramidal tiled image
        if dims.get('image_num_resolution_levels', 0)>1 and dims.get('tile_num_x', 0)>0:
            # dima: maybe better to test converter, if imgcnv then enqueue, otherwise proceed with the converter path
            if dims.get('converter', '') == ConverterImgcnv.name:
                c = self.server.converters[ConverterImgcnv.name]
                r = c.tile(token, ofname, level, tnx, tny, tsz)
                if r is not None:
                    if not os.path.exists(hist_name):
                        # write the histogram file is missing
                        c.writeHistogram(token, ofnm=hist_name)
                # if decoder returned a list of operations for imgcnv to enqueue
                if isinstance(r, list):
                    r.extend([ '-ihst', hist_name])
                    return self.server.enqueue(token, 'tile', ofname, fmt=default_format, command=r, dims=info)

            # try other decoders to read tiles
            ofname = '%s.tif'%ofname
            if os.path.exists(ofname):
                return token.setImage(ofname, fmt=default_format, dims=info, hist=hist_name, input=ofname)
            else:
                r = None
                for n,c in self.server.converters.iteritems():
                    if n == ConverterImgcnv.name: continue
                    if callable( getattr(c, "tile", None) ):
                        r = c.tile(token, ofname, level, tnx, tny, tsz)
                        if r is not None:
                            if not os.path.exists(hist_name):
                                # write the histogram file if missing
                                c.writeHistogram(token, ofnm=hist_name)
                            return token.setImage(ofname, fmt=default_format, dims=info, hist=hist_name, input=ofname)

        abort(500, 'Tile could not be extracted')


################################################################################
# Misc Image Operations
################################################################################

class IntensityProjectionOperation(BaseOperation):
    '''Provides an intensity projected image with all available plains
       intensityprojection=max|min
       ex: intensityprojection=max'''
    name = 'intensityprojection'

    def __str__(self):
        return 'intensityprojection: returns a maximum intensity projection image, intensityprojection=max|min'

    def dryrun(self, token, arg):
        arg = arg.lower()
        if arg not in ['min', 'max']:
            abort(400, 'IntensityProjection: parameter must be either "max" or "min"')
        ofile = '%s.iproject_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        if arg not in ['min', 'max']:
            abort(400, 'IntensityProjection: parameter must be either "max" or "min"')

        ifile = token.first_input_file()
        ofile = '%s.iproject_%s'%(token.data, arg)
        log.debug('IntensityProjection %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        if arg == 'max':
            command = ['-projectmax']
        else:
            command = ['-projectmin']

        info = {
            'image_num_z': 1,
            'image_num_t': 1,
        }
        return self.server.enqueue(token, 'intensityprojection', ofile, fmt=default_format, command=command, dims=info)

class NegativeOperation(BaseOperation):
    '''Provide an image negative
       ex: negative'''
    name = 'negative'

    def __str__(self):
        return 'negative: returns an image negative'

    def dryrun(self, token, arg):
        ifile = token.data
        ofile = '%s.negative'%(token.data)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        ifile = token.first_input_file()
        ofile = '%s.negative'%(token.data)
        log.debug('Negative %s: %s to %s', token.resource_id, ifile, ofile)

        return self.server.enqueue(token, 'negative', ofile, fmt=default_format, command=['-negative'])

class DeinterlaceOperation(BaseOperation):
    '''Provides a deinterlaced image
       ex: deinterlace'''
    name = 'deinterlace'

    def __str__(self):
        return 'deinterlace: returns a deinterlaced image'

    def dryrun(self, token, arg):
        arg = arg.lower() or 'avg'
        if arg not in ['odd', 'even', 'avg']:
            abort(400, 'Deinterlace: parameter must be either "odd", "even" or "avg"')
        ofile = '%s.deinterlace_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower() or 'avg'
        if arg not in ['odd', 'even', 'avg']:
            abort(400, 'Deinterlace: parameter must be either "odd", "even" or "avg"')
        ifile = token.first_input_file()
        ofile = '%s.deinterlace_%s'%(token.data, arg)
        log.debug('Deinterlace %s: %s to %s', token.resource_id, ifile, ofile)

        return self.server.enqueue(token, 'deinterlace', ofile, fmt=default_format, command=['-deinterlace', arg])

class ThresholdOperation(BaseOperation):
    '''Threshold an image
       threshold=value[,upper|,lower|,both]
       ex: threshold=128,both'''
    name = 'threshold'

    def __str__(self):
        return 'threshold: returns a thresholded image, threshold=value[,upper|,lower|,both], ex: threshold=128,both'

    def dryrun(self, token, arg):
        arg = arg.lower()
        args = arg.split(',')
        if len(args)<1:
            return token
        method = 'both'
        if len(args)>1:
            method = args[1]
        arg = '%s,%s'%(args[0], method)
        ofile = '%s.threshold_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        args = arg.split(',')
        if len(args)<1:
            abort(400, 'Threshold: requires at least one parameter')
        method = 'both'
        if len(args)>1:
            method = args[1]
        arg = '%s,%s'%(args[0], method)
        ifile = token.first_input_file()
        ofile = '%s.threshold_%s'%(token.data, arg)
        log.debug('Threshold %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        return self.server.enqueue(token, 'threshold', ofile, fmt=default_format, command=['-threshold', arg])

class PixelCounterOperation(BaseOperation):
    '''Return pixel counts of a thresholded image
       pixelcount=value, where value is a threshold
       ex: pixelcount=128'''
    name = 'pixelcount'

    def __str__(self):
        return 'pixelcount: returns a count of pixels in a thresholded image, ex: pixelcount=128'

    def dryrun(self, token, arg):
        arg = safeint(arg.lower(), 256)-1
        ofile = '%s.pixelcount_%s.xml'%(token.data, arg)
        return token.setXmlFile(fname=ofile)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Pixelcount: input is not an image...' )
        arg = safeint(arg.lower(), 256)-1
        ifile = token.first_input_file()
        ofile = '%s.pixelcount_%s.xml'%(token.data, arg)
        log.debug('Pixelcount %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        command = token.drainQueue()
        if not os.path.exists(ofile):
            command.extend(['-pixelcounts', str(arg)])
            self.server.imageconvert(token, ifile, ofile, extra=command)

        return token.setXmlFile(fname=ofile)

class HistogramOperation(BaseOperation):
    '''Returns histogram of an image
       ex: histogram'''
    name = 'histogram'

    def __str__(self):
        return 'histogram: returns a histogram of an image, ex: histogram'

    def dryrun(self, token, arg):
        ofile = '%s.histogram.xml'%(token.data)
        return token.setXmlFile(fname=ofile)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Histogram: input is not an image...' )
        ifile = token.first_input_file()
        ofile = '%s.histogram.xml'%(token.data)
        log.debug('Histogram %s: %s to %s', token.resource_id, ifile, ofile)

        command = token.drainQueue()
        if not os.path.exists(ofile):
            # use resolution level if available to find the best estimate for very large images
            command.extend(['-ohstxml', ofile])

            dims = token.dims or {}
            num_x = int(dims.get('image_num_x', 0))
            num_y = int(dims.get('image_num_y', 0))
            width = 1024 # image sizes good enough for histogram estimation
            height = 1024 # image sizes good enough for histogram estimation

            # if image has multiple resolution levels find the closest one and request it
            num_l = dims.get('image_num_resolution_levels', 1)
            if num_l>1 and '-res-level' not in token.getQueue():
                try:
                    scales = [float(i) for i in dims.get('image_resolution_level_scales', '').split(',')]
                    sizes = [(round(num_x*i),round(num_y*i)) for i in scales]
                    relatives = [max(width/float(sz[0]), height/float(sz[1])) for sz in sizes]
                    relatives = [i if i<=1 else 0 for i in relatives]
                    level = relatives.index(max(relatives))
                    command.extend(['-res-level', str(level)])
                except (Exception):
                    pass

            self.server.imageconvert(token, ifile, None, extra=command)

        return token.setXmlFile(fname=ofile)

class LevelsOperation(BaseOperation):
    '''Adjust levels in an image
       levels=minvalue,maxvalue,gamma
       ex: levels=15,200,1.2'''
    name = 'levels'

    def __str__(self):
        return 'levels: adjust levels in an image, levels=minvalue,maxvalue,gamma ex: levels=15,200,1.2'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.levels_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        ifile = token.first_input_file()
        ofile = '%s.levels_%s'%(token.data, arg)
        log.debug('Levels %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        return self.server.enqueue(token, 'levels', ofile, fmt=default_format, command=['-levels', arg])

class BrightnessContrastOperation(BaseOperation):
    '''Adjust brightnesscontrast in an image
       brightnesscontrast=brightness,contrast with both values in range [-100,100]
       ex: brightnesscontrast=0,30'''
    name = 'brightnesscontrast'

    def __str__(self):
        return 'brightnesscontrast: Adjust brightness and contrast in an image, brightnesscontrast=brightness,contrast both in range [-100,100] ex: brightnesscontrast=0,30'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.brightnesscontrast_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        ifile = token.first_input_file()
        ofile = '%s.brightnesscontrast_%s'%(token.data, arg)
        log.debug('Brightnesscontrast %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        return self.server.enqueue(token, 'brightnesscontrast', ofile, fmt=default_format, command=['-brightnesscontrast', arg])


# w: image width
# h: image height
# n: numbe rof image planes, Z stacks or time points
def compute_atlas_size(w, h, n):
    # start with atlas composed of a row of images
    ww = w*n
    hh = h
    ratio = ww / float(hh);
    # optimize side to be as close to ratio of 1.0
    for r in range(2, n):
        ipr = math.ceil(n / float(r))
        aw = w*ipr;
        ah = h*r;
        rr = max(aw, ah) / float(min(aw, ah))
        if rr < ratio:
            ratio = rr
            ww = aw
            hh = ah
        else:
            break

    return (int(round(ww)), int(round(hh)))

class TextureAtlasOperation(BaseOperation):
    '''Returns a 2D texture atlas image for a given 3D input
       ex: textureatlas'''
    name = 'textureatlas'

    def __str__(self):
        return 'textureatlas: returns a 2D texture atlas image for a given 3D input'

    def dryrun(self, token, arg):
        ofile = '%s.textureatlas'%(token.data)
        dims = token.dims or {}
        num_z = int(dims.get('image_num_z', 1))
        num_t = int(dims.get('image_num_t', 1))
        width, height = compute_atlas_size(int(dims.get('image_num_x', 0)), int(dims.get('image_num_y', 0)), num_z*num_t)
        info = {
            'image_num_x': width,
            'image_num_y': height,
            'image_num_z': 1,
            'image_num_t': 1,
        }
        return token.setImage(fname=ofile, fmt=default_format, dims=info)

    def action(self, token, arg):
        #ifile = token.first_input_file()
        ofile = '%s.textureatlas'%(token.data)
        #log.debug('Texture Atlas %s: %s to %s', token.resource_id, ifile, ofile)

        dims = token.dims or {}
        num_z = int(dims.get('image_num_z', 1))
        num_t = int(dims.get('image_num_t', 1))
        width, height = compute_atlas_size(int(dims.get('image_num_x', 0)), int(dims.get('image_num_y', 0)), num_z*num_t)
        info = {
            'image_num_x': width,
            'image_num_y': height,
            'image_num_z': 1,
            'image_num_t': 1,
        }
        #return self.server.enqueue(token, 'textureatlas', ofile, fmt=default_format, command=['-textureatlas'], dims=info)

        if not os.path.exists(ofile):
            if token.hasQueue():
                token = self.server.process_queue(token) # need to process queue first since textureatlas can't deal with all kinds of inputs
            ifile = token.first_input_file()
            ofile = '%s.textureatlas'%(token.data)
            log.debug('Texture Atlas %s: %s to %s', token.resource_id, ifile, ofile)
            self.server.imageconvert(token, ifile, ofile, fmt=default_format, extra=['-textureatlas'], dims=info)
        return token.setImage(ofile, fmt=default_format, dims=info, input=ofile, queue=[])


transforms = {
    'fourier': {
        'command': ['-transform', 'fft'],
        'info': { 'image_pixel_depth': 64, 'image_pixel_format': 'floating point', },
        'require': {},
    },
    'chebyshev': {
        'command': ['-transform', 'chebyshev'],
        'info': { 'image_pixel_depth': 64, 'image_pixel_format': 'floating point', },
        'require': {},
    },
    'wavelet': {
        'command': ['-transform', 'wavelet'],
        'info': { 'image_pixel_depth': 64, 'image_pixel_format': 'floating point', },
        'require': {},
    },
    'radon': {
        'command': ['-transform', 'radon'],
        'info': { 'image_pixel_depth': 64, 'image_pixel_format': 'floating point', },
        'require': {},
    },
    'edge': {
        'command': ['-filter', 'edge'],
        'info': {},
        'require': {},
    },
    'wndchrmcolor': {
        'command': ['-filter', 'wndchrmcolor'],
        'info': {},
        'require': {},
    },
    'rgb2hsv': {
        'command': ['-transform_color', 'rgb2hsv'],
        'info': {},
        'require': { 'image_num_c': 3, },
    },
    'hsv2rgb': {
        'command': ['-transform_color', 'hsv2rgb'],
        'info': {},
        'require': { 'image_num_c': 3, },
    },
    'superpixels': {
        'command': ['-superpixels'],
        'info': { 'image_pixel_depth': 32, 'image_pixel_format': 'unsigned integer', },
        'require': {},
    },
}

class TransformOperation(BaseOperation):
    """Provide an image transform
       arg = transform
       Available transforms are: fourier, chebyshev, wavelet, radon, edge, wndchrmcolor, rgb2hsv, hsv2rgb, superpixels
       ex: transform=fourier
       superpixels requires two parameters: superpixel size in pixels and shape regularity 0-1, ex: transform=superpixels,32,0.5"""
    name = 'transform'

    def __str__(self):
        return 'transform: returns a transformed image, transform=fourier|chebyshev|wavelet|radon|edge|wndchrmcolor|rgb2hsv|hsv2rgb|superpixels'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.transform_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        arg = arg.lower()
        args = arg.split(',')
        transform = args[0]
        params = args[1:]
        ifile = token.first_input_file()
        ofile = '%s.transform_%s'%(token.data, arg)
        log.debug('Transform %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        if not transform in transforms:
            abort(400, 'transform: requested transform is not yet supported')

        dims = token.dims or {}
        for n,v in transforms[transform]['require'].iteritems():
            if v != dims.get(n):
                abort(400, 'transform: input image is incompatible, %s must be %s but is %s'%(n, v, dims.get(n)) )

        extra = transforms[transform]['command']
        if len(params)>0:
            extra.extend([','.join(params)])
        return self.server.enqueue(token, 'transform', ofile, fmt=default_format, command=extra, dims=transforms[transform]['info'])

class SampleFramesOperation(BaseOperation):
    '''Returns an Image composed of Nth frames form input
       arg = frames_to_skip
       ex: sampleframes=10'''
    name = 'sampleframes'

    def __str__(self):
        return 'sampleframes: returns an Image composed of Nth frames form input, arg=n'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.framessampled_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        if not arg:
            abort(400, 'SampleFrames: no frames to skip provided')

        ifile = token.first_input_file()
        ofile = '%s.framessampled_%s'%(token.data, arg)
        log.debug('SampleFrames %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        info = {
            'image_num_z': 1,
            'image_num_t': int(token.dims.get('image_num_p', 0)) / int(arg),
        }
        return self.server.enqueue(token, 'sampleframes', ofile, fmt=default_format, command=['-sampleframes', arg], dims=info)

class FramesOperation(BaseOperation):
    '''Returns an image composed of user defined frames form input
       arg = frames
       ex: frames=1,2,5 or ex: frames=1,-,5 or ex: frames=-,5 or ex: frames=4,-'''
    name = 'frames'

    def __str__(self):
        return 'frames: Returns an image composed of user defined frames form input, arg = frames'

    def dryrun(self, token, arg):
        arg = arg.lower()
        ofile = '%s.frames_%s'%(token.data, arg)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        if not arg:
            abort(400, 'Frames: no frames provided')

        ifile = token.first_input_file()
        ofile = '%s.frames_%s'%(token.data, arg)
        log.debug('Frames %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        info = {
            'image_num_z': 1,
            'image_num_t': 1,
            #if 'image_num_p' in info: token.dims['image_num_p'] = info['image_num_p']
        }
        return self.server.enqueue(token, 'frames', ofile, fmt=default_format, command=['-page', arg], dims=info)

def compute_rotated_size(w, h, arg):
    if arg in ['90', '-90', '270']:
        return (h, w)
    return (w, h)

class RotateOperation(BaseOperation):
    '''Provides rotated versions for requested images:
       arg = angle
       At this moment only supported values are 90, -90, 270, 180 and guess
       ex: rotate=90'''
    name = 'rotate'

    def __str__(self):
        return 'rotate: returns an image rotated as requested, arg = 0|90|-90|180|270|guess'

    def dryrun(self, token, arg):
        ang = arg.lower()
        if ang=='270':
            ang='-90'
        ofile = '%s.rotated_%s'%(token.data, ang)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        ang = arg.lower()
        angles = ['0', '90', '-90', '270', '180', 'guess']
        if ang=='270':
            ang='-90'
        if ang not in angles:
            abort(400, 'rotate: angle value not yet supported' )

        ifile = token.first_input_file()
        ofile = '%s.rotated_%s'%(token.data, ang)
        log.debug('Rotate %s: %s to %s', token.resource_id, ifile, ofile)
        if ang=='0':
            ofile = ifile

        dims = token.dims or {}
        w, h = compute_rotated_size(int(dims.get('image_num_x', 0)), int(dims.get('image_num_y', 0)), ang)
        info = {
            'image_num_x': w,
            'image_num_y': h,
        }
        return self.server.enqueue(token, 'rotate', ofile, fmt=default_format, command=['-rotate', ang], dims=info)


################################################################################
# ImageServer
################################################################################

class ImageServer(object):

    converters = ConverterDict([
        (ConverterOpenSlide.name,   ConverterOpenSlide()),
        (ConverterImgcnv.name,      ConverterImgcnv()),
        (ConverterImaris.name,      ConverterImaris()),
        (ConverterBioformats.name,  ConverterBioformats()),
    ])
    writable_formats = {}

    # cache resources and blob locations
    cache = ResourceCache()

    @classmethod
    def init_converters(cls):
        # test all the supported command line decoders and remove missing
        missing = []
        for n,c in cls.converters.iteritems():
            if not c.get_installed():
                log.debug('%s is not installed, skipping support...', n)
                missing.append(n)
            # elif not c.ensure_version(needed_versions[n]):
            #     log.warning('%s needs update! Has: %s Needs: %s', n, c.version['full'], needed_versions[n])
            #     missing.append(n)
        for m in missing:
            cls.converters.pop(m)


        log.info('Available converters: %s', str(cls.converters))
        if ConverterImgcnv.name not in cls.converters:
            log.warn('imgcnv was not found, it is required for most of image service operations! Make sure to install it!')

        cls.writable_formats = cls.converters.converters(readable=False, writable=True, multipage=False)

    def __init__(self, work_dir):
        '''Start an image server, using local dir imagedir,
        and loading extensions as methods'''
        #super(ImageServer, self).__init__(image_dir, server_url)
        self.workdir = work_dir
        self.base_url = "image_service"

        self.operations = {
            'view'         : ViewOperation(self),
            'operations'   : OperationsOperation(self),
            'formats'      : FormatsOperation(self),
            #'info'         : InfoOperation(self),
            'dims'         : DimOperation(self),
            'meta'         : MetaOperation(self),
            #'filename'     : FileNameOperation(self),
            'localpath'    : LocalPathOperation(self),
            'slice'        : SliceOperation(self),
            'format'       : FormatOperation(self),
            'resize'       : ResizeOperation(self),
            'resize3d'     : Resize3DOperation(self),
            'rearrange3d'  : Rearrange3DOperation(self),
            'thumbnail'    : ThumbnailOperation(self),
            'roi'          : RoiOperation(self),
            'remap'        : RemapOperation(self),
            'fuse'         : FuseOperation(self),
            'depth'        : DepthOperation(self),
            'rotate'       : RotateOperation(self),
            'tile'         : TileOperation(self),
            'intensityprojection'   : IntensityProjectionOperation(self),
            #'projectmax'   : ProjectMaxOperation(self),
            #'projectmin'   : ProjectMinOperation(self),
            'negative'     : NegativeOperation(self),
            'deinterlace'  : DeinterlaceOperation(self),
            'threshold'    : ThresholdOperation(self),
            'pixelcounter' : PixelCounterOperation(self),
            'histogram'    : HistogramOperation(self),
            'levels'       : LevelsOperation(self),
            'brightnesscontrast' : BrightnessContrastOperation(self),
            'textureatlas' : TextureAtlasOperation(self),
            'transform'    : TransformOperation(self),
            'sampleframes' : SampleFramesOperation(self),
            'frames'       : FramesOperation(self),
            'cleancache'   : CacheCleanOperation(self),
        }


        # # test all the supported command line decoders and remove missing
        # missing = []
        # for n,c in self.converters.iteritems():
        #     if not c.get_installed():
        #         log.debug('%s is not installed, skipping support...', n)
        #         missing.append(n)
        #     # elif not c.ensure_version(needed_versions[n]):
        #     #     log.warning('%s needs update! Has: %s Needs: %s', n, c.version['full'], needed_versions[n])
        #     #     missing.append(n)
        # for m in missing:
        #     self.converters.pop(m)


        # log.info('Available converters: %s', str(self.converters))
        # if ConverterImgcnv.name not in self.converters:
        #     log.warn('imgcnv was not found, it is required for most of image service operations! Make sure to install it!')

        # self.writable_formats = self.converters.converters(readable=False, writable=True, multipage=False)

        img_threads = config.get ('bisque.image_service.imgcnv.omp_num_threads', None)
        if img_threads is not None:
            log.info ("Setting OMP_NUM_THREADS = %s", img_threads)
            os.environ['OMP_NUM_THREADS'] = "%s" % img_threads


    def ensureOriginalFile(self, ident, resource=None):
        # if resource is not None:
        #     vs = resource.xpath('value')
        #     if len(vs)>0:
        #         files = [v.text for v in vs]
        #     else:
        #         files = [resource.get('value')]
        #     log.debug('files: %s', files)
        #     if files[0].startswith('file://'):
        #         files = ['path%s'%f.replace('file://', '') for f in files]
        #         log.debug('files: %s', files)
        #         return Blobs(path=files[0], sub=None, files=files if len(files)>1 else None)

        #return blob_service.localpath(ident, resource=resource) or abort (404, 'File not available from blob service')
        blobs = self.cache.get_blobs(ident)
        return blobs or abort (404, 'File not available from blob service')

    def getImageInfo(self, filename, series=0, infofile=None, meta=None):
        if infofile is None:
            infofile = '%s.info'%filename
        info = {}

        # sanity check
        if not os.path.exists(filename):
            return None

        # read image info using converters
        if not os.path.exists(infofile):
            with Locks(filename, infofile, failonexist=True) as l:
                if l.locked: # the file is not being currently written by another process
                    # parse image info from original file
                    for n,c in self.converters.iteritems():
                        info = c.info(ProcessToken(ifnm=filename, series=series))
                        if info is not None and len(info)>0:
                            info['converter'] = n
                            break
                    if info is None or 'image_num_x' not in info:
                        return None

                    info.setdefault('image_num_t', 1)
                    info.setdefault('image_num_z', 1)
                    info.setdefault('image_num_p', info['image_num_t'] * info['image_num_z'])
                    info.setdefault('format', default_format)
                    if not 'filesize' in info:
                        info.setdefault('filesize', os.path.getsize(filename))
                    if meta is not None:
                        info.update(meta)

                    # cache file info into a file
                    image = etree.Element ('image')
                    for k,v in info.iteritems():
                        image.set(k, '%s'%v)
                    with open(infofile, 'w') as f:
                        f.write(etree.tostring(image))
                    return info

        # info file exists
        with Locks(infofile):
            try:
                image = etree.parse(infofile).getroot()
                for k,v in image.attrib.iteritems():
                    info[k] = safetypeparse(v)
                return info
            except  etree.XMLSyntaxError:
                log.debug ("attempt to read empty info file")
        return None

    def process_queue(self, token):
        ofile = token.data
        if token.isFile() and len(token.queue)>0 and not os.path.exists(ofile):
            ifile = token.first_input_file()
            command = token.drainQueue()
            log.debug('Executing enqueued commands %s: %s to %s with %s', token.resource_id, ifile, ofile, command)
            self.imageconvert(token, ifile, ofile, fmt=token.format, extra=command)
            token.input = ofile
        if token.isFile() and len(token.queue)<1 and not os.path.exists(ofile):
            token.data = token.first_input_file()
        return token

    def enqueue(self, token, op_name, ofnm, fmt=None, command=None, dims=None, **kw):
        log.debug('Enqueueing %s for %s with %s', op_name, ofnm, command)
        token.data = ofnm
        if fmt is not None:
            #token.format = fmt
            token.setFormat(fmt=fmt)
        if command is not None:
            #token.queue[op_name] = command
            token.queue.extend(command)
        if dims is not None:
            token.dims.update(dims)
        log.debug('Queue: %s', token.getQueue())
        return token

    def imageconvert(self, token, ifnm, ofnm, fmt=None, extra=None, dims=None, **kw):
        if not token.isFile():
            abort(400, 'Convert: input is not an image...' )
        fmt = fmt or token.format or default_format

        command = []

        # dima: FIXME, extra was being appended before the queue
        if extra is not None:
            command.extend(extra)

        if token.hasQueue():
            command.extend(token.drainQueue())

        # dima: FIXME, extra was being appended before the queue
        #if extra is not None:
        #    command.extend(extra)

        # create pyramid for large images
        dims = dims or token.dims or {}
        if dims.get('image_num_x',0)>4000 and dims.get('image_num_y',0)>4000 and 'tiff' in fmt and '-options' not in command:
            command.extend(['-options', 'compression lzw tiles %s pyramid subdirs'%default_tile_size])

        if token.histogram is not None:
            command.extend(['-ihst', token.histogram])

        if kw.get('try_imgcnv', True) is True:
            r = self.converters[ConverterImgcnv.name].convert( token, ofnm, fmt=fmt, extra=command, respect_command_inputs=True, **kw)
            if r is not None:
                return r

        # if the conversion failed, convert input to OME-TIFF using other converts
        # typically we should be strating from the original file here, if we failed somewhere in the middle, there's a bigger problem
        r = None
        ometiff = '%s.ome.tif'%(token.initial_workpath or token.data)
        if os.path.exists(ometiff) and os.path.getsize(ometiff)>16:
            r = ometiff
        else:
            # try converter used to read info
            n = dims.get('converter')
            if n in self.converters and callable( getattr(self.converters[n], "convertToOmeTiff", None) ) is True:
                r = self.converters[n].convertToOmeTiff(token, ometiff, **kw)

            # if desired converter failed, perform exhaustive conversion
            if r is None:
                for n,c in self.converters.iteritems():
                    if n in [ConverterImgcnv.name, dims.get('converter')]: continue
                    r = c.convertToOmeTiff(token, ometiff, **kw)
                    if r is not None:
                        break

            if r is None or os.path.getsize(ometiff)<16:
                log.error('Convert %s: failed for [%s]', token.resource_id, ifnm)
                abort(415, 'Convert failed' )

        return self.converters[ConverterImgcnv.name].convert( ProcessToken(ifnm=ometiff), ofnm, fmt=fmt, extra=command)

    def initialWorkPath(self, image_id, user_name):
        if len(image_id)>3 and image_id[2]=='-':
            subdir = image_id[3]
        else:
            subdir = image_id[0]
        return os.path.realpath(os.path.join(self.workdir, user_name or '', subdir, image_id))

    def ensureWorkPath(self, path, image_id, user_name):
        """path may be a workdir path OR an original image path to transformed into
        a workdir path
        """
        # change ./imagedir to ./workdir if needed
        path = os.path.realpath(path)
        workpath = os.path.realpath(self.workdir)
        if image_id and not path.startswith (workpath):
            path = self.initialWorkPath(image_id, user_name)
        # keep paths relative to workdir to reduce file name size
        path = os.path.relpath(path, workpath)
        # make sure that the path directory exists
        _mkdir( os.path.dirname(path) )
        return path

    def request(self, method, token, arguments):
        '''Apply an image request'''
        if method not in self.operations:
            abort(400, 'Requested operation does not exist: %s'%method)
        return self.operations[method].action (token, arguments)
        # try:
        #     return self.operations[method].action (token, arguments)
        # except Exception:
        #     log.exception('Exception running: %s', method)
        #     return token

    def process(self, url, ident, resource=None, **kw):
        resource_id, query = getOperations(url, self.base_url)
        log.debug ('STARTING %s: %s', ident, query)
        #os.chdir(self.workdir)
        log.debug('Current path %s: %s', ident, self.workdir)

        if resource is None:
            resource = {}

        # init the output to a simple file
        token = ProcessToken()

        if ident is not None:
            # pre-compute final filename and check if it exists before starting any other processing
            if len(query)>0:
                token.setFile(self.initialWorkPath(ident, user_name=kw.get('user_name', None)))
                token.dims = self.getImageInfo(filename=token.data, series=token.series, infofile='%s.info'%token.data, meta=kw.get('imagemeta', None) )
                token.init(resource_id=ident, ifnm=token.data, imagemeta=kw.get('imagemeta', None), timeout=kw.get('timeout', None), resource_name=resource.get('name'))
                for action, args in query:
                    try:
                        service = self.operations[action]
                        # if the service has a dryrun function, some actions are same as dryrun
                        if callable( getattr(service, "dryrun", None) ):
                            token = service.dryrun(token, args)
                        else:
                            token = service.action(token, args)
                        log.debug ('DRY run: %s producing: %s', action, token.data)
                    except Exception:
                        pass
                    if token.isHttpError():
                        break
                localpath = os.path.join(os.path.realpath(self.workdir), token.data)
                log.debug('Dryrun test %s: [%s] [%s]', ident, localpath, str(token))
                if token.isFile() and os.path.exists(localpath):
                    log.debug('FINISHED %s: returning pre-cached result %s', ident, token.data)
                    with Locks(token.data):
                        pass
                    return token

            log.debug('STARTING full processing %s: with %s', ident, token)

            # ----------------------------------------------
            # start the processing
            b = self.ensureOriginalFile(ident, resource=resource)
            #log.debug('Original %s, %s, %s', b.path, b.sub, b.files)
            workpath = self.ensureWorkPath(b.path, ident, user_name=kw.get('user_name', None))
            token.setFile(workpath, series=(b.sub or 0))
            token.init(resource_id=ident, ifnm=b.path, imagemeta=kw.get('imagemeta', None), files=b.files, timeout=kw.get('timeout', None), resource_name=resource.get('name'), initial_workpath=workpath)

            if not os.path.exists(b.path):
                abort(404, 'File not found...')

            if len(query)>0:
                token.dims = self.getImageInfo(filename=token.first_input_file(), series=token.series, infofile='%s.info'%token.data, meta=token.meta)
                if token.dims is None or 'image_num_x' not in token.dims:
                    abort(415, 'File format is not supported...')
                # overwrite fields from resource image meta
                if token.meta is not None:
                    token.dims.update(token.meta)

        #process all the requested operations
        for action,args in query:
            log.debug ('ACTION %s: %s', ident, action)
            token = self.request(action, token, args)
            if token.isHttpError():
                break
        token = self.process_queue(token)

        # test output, if it is a file but it does not exist, set 404 error
        token.testFile()

        # if the output is a file but not an image or no processing was done to it
        # set to the original file name
        if token.isFile() and not token.isImage() and not token.isText() and not token.hasFileName():
            token.contentType = 'application/octet-stream'
            token.outFileName = token.resource_name

        # if supplied file name overrides filename
        for action,args in query:
            if (action.lower() == 'filename'):
                token.outFileName = args
                break

        log.debug ('FINISHED %s: %s', ident, query)
        return token


try:
    ImageServer.init_converters()
except Exception:
    log.warn("ImageServer is not available")
