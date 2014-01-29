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
import re
import StringIO
from urllib import quote
from urllib import unquote
from urlparse import urlparse
from lxml import etree
import datetime

from tg import config
from pylons.controllers.util import abort

#Project
from bq import blob_service
from bq import data_service
from bq.core import  identity
from bq.util.mkdir import _mkdir
from bq.util.compat import OrderedDict

# Locals
from locks import Locks
import misc

from converter_imgcnv import ConverterImgcnv
from converter_imaris import ConverterImaris
from converter_bioformats import ConverterBioformats


log = logging.getLogger('bq.image_service.server')

default_format = 'bigtiff'

needed_versions = { 'imgcnv'     : '1.65.0',
                    'imaris'     : '7.6.5',
                    'bioformats' : '4.3.0'
                  }

K = 1024
M = K *1000
G = M *1000

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

    def extensions(self):
        exts = []
        for c in self.itervalues():
            for f in c.formats().itervalues():
                exts.extend(f.ext)
        return exts

    def canWriteMultipage(self, formatName):
        formats = []
        for c in self.itervalues():
            for n,f in c.formats().iteritems():
                if f.multipage is True:
                    formats.append[n]
        return formatName.lower() in formats

    def formats(self, readable=True, writable=True, multipage=False):
        fs = []
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
                    fs.append(n)
        return fs

    def byformat(self, fmt):
        for c in self.itervalues():
            if fmt in c.formats():
                return c
        return None


################################################################################
# ProcessToken
################################################################################

class ProcessToken(object):
    'Keep data with correct content type and cache info'

    def __str__(self):
        return '{data: %s, contentType: %s, is_file: %s}'%(self.data, self.contentType, self.is_file)

    def __init__(self):
        self.data        = False
        self.contentType = ''
        self.cacheInfo   = ''
        self.outFileName = ''
        self.httpResponseCode = 200
        self.dims        = None
        self.histogram   = None
        self.is_file     = False

    def setData (self, data_buf, content_type):
        self.data = data_buf
        self.contentType = content_type
        self.cacheInfo = 'max-age=302400' # one week
        return self

    def setHtml (self, text):
        self.data = text
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.is_file = False
        return self

    def setXml (self, xml_str):
        self.data = xml_str
        self.contentType = 'text/xml'
        self.cacheInfo = 'max-age=302400' # one week
        #self.cacheInfo = 'no-cache'
        self.is_file = False
        return self

    def setXmlFile (self, fname):
        self.data = fname
        self.contentType = 'text/xml'
        self.cacheInfo = 'max-age=302400' # one week
        self.is_file = True
        return self

    def setImage (self, fname, format):
        self.data = fname
        self.is_file = True
        if self.dims is not None:
            self.dims['format'] = format
        self.contentType = 'image/' + format.lower()
        #self.cacheInfo = 'max-age=43200' # one day
        #self.cacheInfo = 'max-age=86400' # two days
        self.cacheInfo = 'max-age=302400' # one week
        #self.cacheInfo = 'no-cache'
        if self.contentType.lower() == 'image/flash':
            self.contentType = 'application/x-shockwave-flash'
        if self.contentType.lower() == 'image/flv':
            self.contentType = 'video/x-flv'
        if self.contentType.lower() == 'image/avi':
            self.contentType = 'video/avi'
        if self.contentType.lower() == 'image/quicktime':
            self.contentType = 'video/quicktime'
        if self.contentType.lower() == 'image/wmv':
            self.contentType = 'video/x-ms-wmv'
        if self.contentType.lower().startswith('image/mpeg'):
            self.contentType = 'video/mp4'
        if self.contentType.lower() == 'image/matroska':
            self.contentType = 'video/x-matroska'
        return self

    def setFile (self, fname):
        self.data = fname
        self.is_file = True
        self.contentType = 'application/octet-stream'
        self.cacheInfo = 'max-age=302400' # one week
        return self

    def setNone (self):
        self.data = False
        self.is_file = False
        self.contentType = ''
        return self

    def setHtmlErrorUnauthorized (self):
        self.data = 'Permission denied...'
        self.is_file = False
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 401
        return self

    def setHtmlErrorNotFound (self):
        self.data = 'File not found...'
        self.is_file = False
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 404
        return self

    def setHtmlErrorNotSupported (self):
        self.data = 'File is not in supported image format...'
        self.is_file = False
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 415
        return self

    def isValid (self):
        if self.data:
            return True
        else:
            return False

    def isImage (self):
        if self.contentType.startswith('image/'):
            return True
        elif self.contentType.startswith('video/'):
            return True
        elif self.contentType.lower() == 'application/x-shockwave-flash':
            return True
        else:
            return False

    def isFile (self):
        return self.is_file
        #if self.contentType.startswith('image/') or self.contentType.startswith('application/') or self.contentType.startswith('video/'):
        #    return True
        #else:
        #    return False

    def isText (self):
        return self.contentType.startswith('text/')

    def isHtml (self):
        if self.contentType == 'text/html':
            return True
        else:
            return False

    def isXml (self):
        if self.contentType == 'text/xml':
            return True
        else:
            return False

    def isHttpError (self):
        return (not self.httpResponseCode == 200)

    def hasFileName (self):
        if len(self.outFileName) > 0:
            return True
        else:
            return False

    def testFile (self):
        if self.isFile() and not os.path.exists(self.data):
            self.setHtmlErrorNotFound()

    def getDim (self, key, def_val):
        if self.dims is None:
            return def_val
        if key in self.dims:
            return self.dims[key]
        else:
            return def_val


################################################################################
# Info Services
################################################################################

class ServicesService(object):
    '''Provide services information'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'services: returns XML with services information'

    def dryrun(self, image_id, data_token, arg):
        return data_token.setXml('')

    def action(self, image_id, data_token, arg):
        response = etree.Element ('response')
        servs    = etree.SubElement (response, 'operations', uri='/image_service/operations')
        for name,func in self.server.services.iteritems():
            tag = etree.SubElement(servs, 'tag', name=str(name), value=str(func))
        return data_token.setXml(etree.tostring(response))

class FormatsService(object):
    '''Provide information on supported formats'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'formats: Returns XML with supported formats'

    def dryrun(self, image_id, data_token, arg):
        return data_token.setXml('')

    def action(self, image_id, data_token, arg):
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
        return data_token.setXml(etree.tostring(xml))

class InfoService(object):
    '''Provide image information'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'info: returns XML with image information'

    def dryrun(self, image_id, data_token, arg):
        return data_token.setXml('')

    def action(self, image_id, data_token, arg):

        info = self.server.getImageInfo(ident=image_id)
        info['filename'] = self.server.originalFileName(image_id)

        image = etree.Element ('resource', uri='%s/%s'%(self.server.url,  image_id))
        for k, v in info.iteritems():
            tag = etree.SubElement(image, 'tag', name='%s'%k, value='%s'%v )
        return data_token.setXml(etree.tostring(image))

class DimService(object):
    '''Provide image dimension information'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'dims: returns XML with image dimension information'

    def dryrun(self, image_id, data_token, arg):
        return data_token.setXml('')

    def action(self, image_id, data_token, arg):
        info = data_token.dims
        response = etree.Element ('response')
        if info is not None:
            image = etree.SubElement (response, 'image', resource_uniq='%s'%image_id)
            for k, v in info.iteritems():
                tag = etree.SubElement(image, 'tag', name=str(k), value=str(v))
        return data_token.setXml(etree.tostring(response))

class MetaService(object):
    '''Provide image information'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'meta: returns XML with image meta-data'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName( data_token, image_id )
        metacache = self.server.getOutFileName( ifile, image_id, '.meta' )
        return data_token.setXmlFile(metacache)

    def action(self, image_id, data_token, arg):
        ifile = self.server.getInFileName( data_token, image_id )
        infoname = self.server.getOutFileName( ifile, image_id, '.info' )
        metacache = self.server.getOutFileName( ifile, image_id, '.meta' )

        if not os.path.exists(metacache):
            meta = {}
            if os.path.exists(ifile):
                for c in self.server.converters.itervalues():
                    meta = c.meta(ifile)
                    if len(meta)>0:
                        break

            # overwrite certain fields
            meta['filename'] = self.server.originalFileName(image_id)
            if os.path.exists(infoname):
                info = self.server.getFileInfo(id=image_id)
                meta['image_num_x'] = info.get('image_num_x', meta.get('image_num_x', 0))
                meta['image_num_y'] = info.get('image_num_y', meta.get('image_num_y', 0))
                meta['image_num_z'] = info.get('image_num_z', meta.get('image_num_z', 0))
                meta['image_num_t'] = info.get('image_num_t', meta.get('image_num_t', 0))
                meta['image_num_c'] = info.get('image_num_c', meta.get('image_num_c', 0))
                meta['image_pixel_depth'] = info.get('image_pixel_depth', meta.get('image_pixel_depth', 0))
                meta['image_num_p'] = info['image_num_t']*info['image_num_z']

            # construct an XML tree
            image = etree.Element ('resource', uri='%s/%s?meta'%(self.server.url, image_id))
            tags_map = {}
            for k, v in meta.iteritems():
                k = unicode(str(k), 'latin1')
                v = unicode(str(v), 'latin1')
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

            log.debug('Meta: storing metadata into %s', metacache)
            xmlstr = etree.tostring(image)
            with open(metacache, "w") as f:
                f.write(xmlstr)
            return data_token.setXml(xmlstr)

        log.debug('Meta: reading metadata from %s', metacache)
        return data_token.setXmlFile(metacache)

#class FileNameService(object):
#    '''Provide image filename'''
#
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'FileNameService: Returns XML with image file name'
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#    def action(self, image_id, data_token, arg):
#
#        fileName = self.server.originalFileName(image_id)
#
#        response = etree.Element ('response')
#        image    = etree.SubElement (response, 'image')
#        image.attrib['src'] = '/imgsrv/' + str(image_id)
#        tag = etree.SubElement(image, 'tag')
#        tag.attrib['name'] = 'filename'
#        tag.attrib['type'] = 'string'
#        tag.attrib['value'] = fileName
#
#        data_token.setXml(etree.tostring(response))
#        return data_token

class LocalPathService(object):
    '''Provides local path for response image'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'localpath: returns XML with local path to the processed image'

    def dryrun(self, image_id, data_token, arg):
        return data_token.setXml('')

    def action(self, image_id, data_token, arg):
        ifile = self.server.getInFileName( data_token, image_id )
        ifile = os.path.abspath(ifile)
        log.debug('Localpath: %s'%ifile)

        if os.path.exists(ifile):
            res = etree.Element ('resource', type='file', src='file:%s'%(ifile))
        else:
            res = etree.Element ('resource')

        return data_token.setXml( etree.tostring(res) )


################################################################################
# Main Image Services
################################################################################

class SliceService(object):
    '''Provide a slice of an image :
       arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2
       Each position may be specified as a range
       empty params imply entire available range
       all values are in ranges [1..N]
       0 or empty - means first element
       ex: slice=,,1,'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'slice: returns an image of requested slices, arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2. All values are in ranges [1..N]'

    def dryrun(self, image_id, data_token, arg):
        # parse arguments
        vs = [ [misc.safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return data_token

        imsz = [
            data_token.dims.get('image_num_x', 1),
            data_token.dims.get('image_num_y', 1),
            data_token.dims.get('image_num_z', 1),
            data_token.dims.get('image_num_t', 1)
        ]
        if x1<=1 and x2>=imsz[0]: x1=0; x2=0
        if y1<=1 and y2>=imsz[1]: y1=0; y2=0
        if z1<=1 and z2>=imsz[2]: z1=0; z2=0
        if t1<=1 and t2>=imsz[3]: t1=0; t2=0

        # if input image has only one T and Z skip slice alltogether
        try:
            if not data_token.dims is None:
                skip = True
                if   data_token.dims.get('image_num_z',0)>1: skip = False
                elif data_token.dims.get('image_num_t',0)>1: skip = False
                elif data_token.dims.get('image_num_p',0)>1: skip = False
                if skip: return data_token
        finally:
            pass

        if z1==z2==0: z1=1; z2=data_token.dims['image_num_z']
        if t1==t2==0: t1=1; t2=data_token.dims['image_num_t']

        ifname = self.server.getInFileName( data_token, image_id )
        ofname = self.server.getOutFileName( ifname, image_id, '.%d-%d,%d-%d,%d-%d,%d-%d' % (x1,x2,y1,y2,z1,z2,t1,t2) )
        return data_token.setImage(ofname, format=default_format)

    def action(self, image_id, data_token, arg):
        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''

        # parse arguments
        vs = [ [misc.safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return data_token

        imsz = [
            data_token.dims.get('image_num_x', 1),
            data_token.dims.get('image_num_y', 1),
            data_token.dims.get('image_num_z', 1),
            data_token.dims.get('image_num_t', 1)
        ]
        if x1<=1 and x2>=imsz[0]: x1=0; x2=0
        if y1<=1 and y2>=imsz[1]: y1=0; y2=0
        if z1<=1 and z2>=imsz[2]: z1=0; z2=0
        if t1<=1 and t2>=imsz[3]: t1=0; t2=0

        # if input image has only one T and Z skip slice alltogether
        try:
            if not data_token.dims is None:
                skip = True
                if   data_token.dims.get('image_num_z',0)>1: skip = False
                elif data_token.dims.get('image_num_t',0)>1: skip = False
                elif data_token.dims.get('image_num_p',0)>1: skip = False
                if skip: return data_token
        finally:
            pass

        if z1==z2==0: z1=1; z2=data_token.dims['image_num_z']
        if t1==t2==0: t1=1; t2=data_token.dims['image_num_t']

        # construct a sliced filename
        ifname = self.server.getInFileName( data_token, image_id )
        ofname = self.server.getOutFileName( ifname, image_id, '.%d-%d,%d-%d,%d-%d,%d-%d' % (x1,x2,y1,y2,z1,z2,t1,t2) )
        log.debug('Slice: from [%s] to [%s]', ifname, ofname)

        # slice the image
        if not os.path.exists(ofname):
            intermediate = self.server.getOutFileName( ifname, image_id, '.ome.tif' )
            for c in self.server.converters.itervalues():
                r = c.slice(ifname, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), series=0, info=data_token.dims, format=default_format, intermediate=intermediate)
                if r is not None:
                    break
            if r is None:
                log.error('Slice: could not generate slice for [%s]', ifname)
                abort(415, 'Could not generate slice' )

        try:
            new_w=x2-x1
            new_h=y2-y1
            data_token.dims['image_num_z']  = z2 - z1 + 1
            data_token.dims['image_num_t']  = t2 - t1 + 1
            if new_w>0: data_token.dims['image_num_x'] = new_w+1
            if new_h>0: data_token.dims['image_num_y'] = new_h+1
        finally:
            pass

        return data_token.setImage(ofname, format=default_format)

class FormatService(object):
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

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'format: Returns an Image in the requested format, arg = format[,stream][,OPT1][,OPT2][,...]'

    def dryrun(self, image_id, data_token, arg):
        args = arg.lower().split(',')
        fmt = default_format
        if len(args)>0:
            fmt = args.pop(0).lower()

        stream = False
        if 'stream' in args:
            stream = True
            args.remove('stream')

        name_extra = '' if len(args)<=0 else '.%s'%'.'.join(args)

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.%s%s'%(name_extra, fmt) )
        if stream:
            ext = self.server.converters.defaultExtension(fmt)
            fpath = ofile.split('/')
            filename = '%s_%s.%s'%(self.server.originalFileName(image_id), fpath[len(fpath)-1], ext)
            data_token.setFile(fname=ofile)
            data_token.outFileName = filename
        else:
            data_token.setImage(fname=ofile, format=fmt)
        return data_token

    def action(self, image_id, data_token, arg):
        args = arg.lower().split(',')
        fmt = default_format
        if len(args)>0:
            fmt = args.pop(0).lower()

        stream = False
        if 'stream' in args:
            stream = True
            args.remove('stream')

        # avoid doing anything if requested format is in requested format
        if data_token.dims is not None and data_token.dims.get('format','').lower() == fmt:
            log.debug('Input is in requested format, avoid reconvert...')
            return data_token

        if fmt not in self.server.writable_formats:
            abort(400, 'Requested format [%s] is not writable'%fmt )

        name_extra = '' if len(args)<=0 else '.%s'%'.'.join(args)
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.%s%s'%(name_extra, fmt) )
        log.debug('Format: %s -> %s with %s opts=[%s]', ifile, ofile, fmt, args)

        if not os.path.exists(ofile):
            extra = []
            if len(args) > 0:
                extra.extend( ['-options', (' ').join(args)])
            elif fmt == 'jpg' or fmt == 'jpeg':
                extra.extend(['-options', 'quality 95 progressive yes'])

            c = self.server.converters.byformat(fmt)
            r = c.convert(ifile, ofile, fmt, series=0, extra=extra)
            if r is None:
                log.error('Format: %s could not convert with [%s] format [%s] -> [%s]', c.CONVERTERCOMMAND, fmt, ifile, ofile)
                abort(415, 'Could not convert into %s format'%fmt )

        if stream:
            ext = self.server.converters.defaultExtension(fmt)
            fpath = ofile.split('/')
            filename = '%s_%s.%s'%(self.server.originalFileName(image_id), fpath[len(fpath)-1], ext)
            data_token.setFile(fname=ofile)
            data_token.outFileName = filename
        else:
            data_token.setImage(fname=ofile, format=fmt)

        if (ofile != ifile) and (fmt != 'raw'):
            try:
                info = self.server.getImageInfo(filename=ofile)
                if int(info['image_num_p'])>1:
                    if 'image_num_z' in data_token.dims: info['image_num_z'] = data_token.dims['image_num_z']
                    if 'image_num_t' in data_token.dims: info['image_num_t'] = data_token.dims['image_num_t']
                data_token.dims = info
            except:
                pass

        return data_token

class ResizeService(object):
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

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'resize: returns an Image in requested dimensions, arg = w,h,method[,AR|,MX]'

    def dryrun(self, image_id, data_token, arg):
        ss = arg.split(',')
        size = [0,0]
        method = 'BL'
        textAddition = ''

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2:
            method = ss[2].upper()
        if len(ss)>3:
            textAddition = ss[3].upper()

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.size_%d,%d,%s,%s' % (size[0], size[1], method, textAddition) )
        return data_token.setImage(ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        log.debug('Resize: %s'%arg)

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
        if maxBounding and data_token.dims['image_num_x']<=size[0] and data_token.dims['image_num_y']<=size[1]:
            return data_token

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.size_%d,%d,%s,%s' % (size[0], size[1], method,textAddition) )
        log.debug('Resize: [%s] to [%s]', ifile, ofile)

        if not os.path.exists(ofile):
            args = ['-multi', '-resize', '%s,%s,%s%s'%(size[0], size[1], method,aspectRatio)]
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=args)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
        finally:
            pass

        return data_token.setImage(ofile, format=default_format)

class Resize3DService(object):
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

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'resize3d: returns an image in requested dimensions, arg = w,h,d,method[,AR|,MX]'

    def dryrun(self, image_id, data_token, arg):
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

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.size3d_%d,%d,%d,%s,%s' % (size[0], size[1], size[2], method,textAddition) )
        return data_token.setImage(ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        log.debug('Resize3D: %s'%arg )

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
        w = data_token.dims['image_num_x']
        h = data_token.dims['image_num_y']
        z = data_token.dims['image_num_z']
        t = data_token.dims['image_num_t']
        d = max(z, t)
        if w==size[0] and h==size[1] and d==size[2]:
            return data_token
        if maxBounding and w<=size[0] and h<=size[1] and d<=size[2]:
            return data_token
        if (z>1 and t>1) or (z==1 and t==1):
            abort(400, 'Resize3D: only supports 3D images' )

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.size3d_%d,%d,%d,%s,%s' % (size[0], size[1], size[2], method,textAddition) )
        log.debug('Resize3D: %s to %s'%(ifile, ofile))

        if not os.path.exists(ofile):
            args = ['-multi', '-resize3d', '%s,%s,%s,%s%s'%(size[0], size[1], size[2], method, aspectRatio)]
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=args)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
            if z>0:
                data_token.dims['image_num_z'] = size[2]
            elif t>0:
                data_token.dims['image_num_t'] = size[2]
        finally:
            pass

        return data_token.setImage(ofile, format=default_format)

class Rearrange3DService(object):
    '''Rearranges dimensions of an image
       arg = xzy|yzx
       xz: XYZ -> XZY
       yz: XYZ -> YZX
       ex: rearrange3d=xz'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'rearrange3d: rearrange dimensions of a 3D image, arg = [xzy,yzx]'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.rearrange3d_%s'%arg )
        return data_token.setImage(ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        log.debug('Rearrange3D: %s'%arg )
        arg = arg.lower()

        if arg not in ['xzy', 'yzx']:
            abort(400, 'Rearrange3D: method is unsupported: [%s]'%arg )

        # if the image must be 3D, either z stack or t series
        z = data_token.dims['image_num_z']
        t = data_token.dims['image_num_t']
        if (z>1 and t>1) or (z==1 and t==1):
            abort(400, 'Rearrange3D: only supports 3D images' )

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.rearrange3d_%s'%arg )

        if not os.path.exists(ofile):
            args = ['-multi', '-rearrange3d', '%s'%arg]
            #imgcnv.convert( ifile, ofile, fmt=default_format, extra=args)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=args)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
            if 'image_num_z' in info: data_token.dims['image_num_z'] = info['image_num_z']
            if 'image_num_t' in info: data_token.dims['image_num_t'] = info['image_num_t']
        finally:
            pass

        return data_token.setImage(ofile, format=default_format)

class ThumbnailService(object):
    '''Create and provide thumbnails for images:
       If no arguments are specified then uses: 128,128,BL
       arg = [w,h][,method]
       w - new width
       h - new height
       method - NN or BL, or BC (Nearest neighbor, Bilinear, Bicubic respectively)
       ex: ?thumbnail'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'thumbnail: returns an image as a thumbnail, arg = [w,h][,method]'

    def dryrun(self, image_id, data_token, arg):
        ss = arg.split(',')
        size = [128,128]
        method = 'BC'

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2:
            method = ss[2].upper()

        data_token.dims['image_num_p']  = 1
        data_token.dims['image_num_z']  = 1
        data_token.dims['image_num_t']  = 1
        data_token.dims['image_pixel_depth'] = 8

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.thumb_%s,%s,%s.jpeg'%(size[0],size[1],method) )
        return data_token.setImage(ofile, format='jpeg')

    def action(self, image_id, data_token, arg):

        ss = arg.split(',')
        size = [128,128]
        method = 'BC'

        if len(ss)>0 and ss[0].isdigit():
            size[0] = int(ss[0])
        if len(ss)>1 and ss[1].isdigit():
            size[1] = int(ss[1])
        if len(ss)>2:
            method = ss[2].upper()

        if size[0]<=0 and size[1]<=0:
            abort(400, 'Thumbnail: size is unsupported [%s]'%arg)

        if method not in ['NN', 'BL', 'BC']:
            abort(400, 'Thumbnail: method is unsupported [%s]'%arg)

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.thumb_%s,%s,%s.jpeg'%(size[0],size[1],method) )

        if not os.path.exists(ofile):
            depth = data_token.dims.get('image_pixel_depth', 16)
            intermediate = self.server.getOutFileName( ifile, image_id, '.ome.tif' )
            for c in self.server.converters.itervalues():
                r = c.thumbnail(ifile, ofile, size[0], size[1], series=0, method=method, depth=depth, intermediate=intermediate)
                if r is not None:
                    break
            if r is None:
                log.error('Thumbnail: could not generate thumbnail for [%s]', ifile)
                abort(415, 'Could not generate thumbnail' )

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
            data_token.dims['image_num_p']  = 1
            data_token.dims['image_num_z']  = 1
            data_token.dims['image_num_t']  = 1
            data_token.dims['image_pixel_depth'] = 8
        finally:
            pass

        return data_token.setImage(ofile, format='jpeg')

class RoiService(object):
    '''Provides ROI for requested images
       arg = x1,y1,x2,y2
       x1,y1 - top left corner
       x2,y2 - bottom right
       all values are in ranges [1..N]
       0 or empty - means first/last element
       ex: roi=10,10,100,100'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'roi: returns an image in specified ROI, arg = x1,y1,x2,y2, all values are in ranges [1..N]'

    def dryrun(self, image_id, data_token, arg):
        vs = arg.split(',', 4)
        x1=0; x2=0; y1=0; y2=0
        if len(vs)>0 and vs[0].isdigit(): x1 = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): y1 = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): x2 = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): y2 = int(vs[3])
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.roi_%d,%d,%d,%d'%(x1,y1,x2,y2) )
        return data_token.setImage(ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        vs = arg.split(',', 4)
        x1=0; x2=0; y1=0; y2=0
        if len(vs)>0 and vs[0].isdigit(): x1 = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): y1 = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): x2 = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): y2 = int(vs[3])

        if x1<=0 and x2<=0 and y1<=0 and y2<=0:
            abort(400, 'ROI: region is not provided')

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.roi_%d,%d,%d,%d'%(x1,y1,x2,y2) )
        log.debug('ROI: %s to %s'%(ifile, ofile))

        if not os.path.exists(ofile):
            params = ['-multi', '-roi', '%d,%d,%d,%d' % (x1-1,y1-1,x2-1,y2-1)]
            #imgcnv.convert( ifile, ofile, fmt=default_format, extra=params)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=params)
        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
        finally:
            pass

        return data_token.setImage(ofile, format=default_format)

class RemapService(object):
    """Provide an image with the requested channel mapping
       arg = channel,channel...
       output image will be constructed from channels 1 to n from input image, 0 means black channel
       remap=display - will use preferred mapping found in file's metadata
       remap=gray - will return gray scale image with visual weighted mapping from RGB or equal weights for other nuber of channels
       ex: remap=3,2,1"""

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'remap: returns an image with the requested channel mapping, arg = [channel,channel...]|gray|display'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.map_%s'%arg )
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.map_%s'%arg )
        log.debug('Remap: %s to %s with [%s]'%(ifile, ofile, arg))

        if arg == 'display':
            arg = ['-multi' '-display']
        elif arg=='gray' or arg=='grey':
            arg = ['-multi', '-fusegrey']
        else:
            arg = ['-multi', '-remap', arg]

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=arg)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=arg)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_c' in info: data_token.dims['image_num_c'] = info['image_num_c']
        finally:
            pass

        return data_token.setImage(fname=ofile, format=default_format)

class FuseService(object):
    """Provide an RGB image with the requested channel fusion
       arg = W1R,W1G,W1B;W2R,W2G,W2B;W3R,W3G,W3B;W4R,W4G,W4B
       output image will be constructed from channels 1 to n from input image mapped to RGB components with desired weights
       fuse=display will use preferred mapping found in file's metadata
       ex: fuse=255,0,0;0,255,0;0,0,255;255,255,255:A"""

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'fuse: returns an RGB image with the requested channel fusion, arg = W1R,W1G,W1B;W2R,W2G,W2B;...[:METHOD]'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.fuse_%s'%(argenc) )
        if method != 'a':
            ofile = '%s_%s'%(ofile, method)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.fuse_%s'%(argenc) )
        log.debug('Fuse: %s to %s with [%s:%s]'%(ifile, ofile, arg, method))

        if arg == 'display':
            arg = ['-multi', '-fusemeta']
        else:
            arg = ['-multi', '-fusergb', arg]

        if method != 'a':
            arg.extend(['-fusemethod', method])
            ofile = '%s_%s'%(ofile, method)

        if data_token.histogram is not None:
            arg.extend(['-ihst', data_token.histogram])

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=arg)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=arg)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_c' in info: data_token.dims['image_num_c'] = info['image_num_c']
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        data_token.histogram = None # fusion ideally should not be changing image histogram
        return data_token

class DepthService(object):
    '''Provide an image with converted depth per pixel:
       arg = depth,method[,format]
       depth is in bits per pixel
       method is: f or d or t or e
         f - full range
         d - data range
         t - data range with tolerance
         e - equalized
       format is: u, s or f, if unset keeps image original
         u - unsigned integer
         s - signed integer
         f - floating point
       channel mode is: cs or cc
         cs - channels separate
         cc - channels combined
       ex: depth=8,d'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'depth: returns an image with converted depth per pixel, arg = depth,method[,format][,channelmode]'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.depth_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        ms = 'f|d|t|e|c|n'.split('|')
        ds = '8|16|32|64'.split('|')
        fs = ['u', 's', 'f']
        cm = ['cs', 'cc']
        d=None; m=None; f=None; c=None
        arg = arg.lower()
        args = arg.split(',')
        if len(args)>0: d = args[0]
        if len(args)>1: m = args[1]
        if len(args)>2: f = args[2]
        if len(args)>3: c = args[3]

        if d is None or d not in ds:
            abort(400, 'Depth: depth is unsupported: %s'%d)
        if m is None or m not in ms:
            abort(400, 'Depth: method is unsupported: %s'%m )
        if f is not None and f not in fs:
            abort(400, 'Depth: format is unsupported: %s'%f )
        if c is not None and c not in cm:
            abort(400, 'Depth: channel mode is unsupported: %s'%c )

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.depth_%s'%arg)
        log.debug('Depth: %s to %s with [%s]'%(ifile, ofile, arg))

        if data_token.histogram is not None:
            ohist = self.server.getOutFileName(ifile, image_id, '.histogram_depth_' + arg)

        if not os.path.exists(ofile):
            extra=['-multi', '-depth', arg]
            if data_token.histogram is not None:
                extra.extend([ '-ihst', data_token.histogram, '-ohst', ohist])
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=extra)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=extra)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_pixel_depth'  in info: data_token.dims['image_pixel_depth']  = info['image_pixel_depth']
            if 'image_pixel_format' in info: data_token.dims['image_pixel_format'] = info['image_pixel_format']
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        if data_token.histogram is not None:
            data_token.histogram = ohist
        return data_token



################################################################################
# Tiling Image Services
################################################################################

class TileService(object):
    '''Provides a tile of an image :
       arg = l,tnx,tny,tsz
       l: level of the pyramid, 0 - initial level, 1 - scaled down by a factor of 2
       tnx, tny: x and y tile number on the grid
       tsz: tile size
       All values are in range [0..N]
       ex: tile=0,2,3,512'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'tile: returns a tile, arg = l,tnx,tny,tsz. All values are in range [0..N]'

    def dryrun(self, image_id, data_token, arg):
        tsz=512;
        vs = arg.split(',', 4)
        if len(vs)>0 and vs[0].isdigit():   l = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): tnx = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): tny = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): tsz = int(vs[3])

        try:
            if not data_token.dims is None:
                skip = True
                if   'image_num_x' in data_token.dims and data_token.dims['image_num_x']>tsz: skip = False
                elif 'image_num_y' in data_token.dims and data_token.dims['image_num_y']>tsz: skip = False
                if skip: return data_token
        finally:
            pass

        data_token.dims['image_num_p'] = 1
        data_token.dims['image_num_z'] = 1
        data_token.dims['image_num_t'] = 1

        ifname   = self.server.getInFileName( data_token, image_id )
        base_name = self.server.getOutFileName(ifname, image_id, '' )
        base_name = self.server.getOutFileName(os.path.join('%s.tiles'%(base_name), '%s'%tsz), image_id, '' )
        ofname    = '%s_%.3d_%.3d_%.3d.tif' % (base_name, l, tnx, tny)
        #log.debug('Tiles dryrun: from %s to %s' % (ifname, ofname) )
        return data_token.setImage(ofname, format=default_format)

    def action(self, image_id, data_token, arg):
        '''arg = l,tnx,tny,tsz'''

        l=0; tnx=0; tny=0; tsz=512;
        vs = arg.split(',', 4)
        if len(vs)>0 and vs[0].isdigit():   l = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): tnx = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): tny = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): tsz = int(vs[3])
        log.debug( 'Tile: l:%d, tnx:%d, tny:%d, tsz:%d' % (l, tnx, tny, tsz) )

        # if input image is smaller than the requested tile size
        try:
            if not data_token.dims is None:
                skip = True
                if   'image_num_x' in data_token.dims and data_token.dims['image_num_x']>tsz: skip = False
                elif 'image_num_y' in data_token.dims and data_token.dims['image_num_y']>tsz: skip = False
                if skip: return data_token
        finally:
            pass

        # construct a sliced filename
        ifname   = self.server.getInFileName( data_token, image_id )
        base_name = self.server.getOutFileName(ifname, image_id, '' )
        base_name = self.server.getOutFileName(os.path.join('%s.tiles'%(base_name), '%s'%tsz), image_id, '' )
        ofname    = '%s_%.3d_%.3d_%.3d.tif' % (base_name, l, tnx, tny)
        hist_name = '%s_histogram'%(base_name)
        hstl_name = hist_name

        # tile the image
        tiles_name = '%s.tif' % (base_name)
        if not os.path.exists(hist_name):
            with Locks(ifname, hstl_name) as l:
                if l.locked:
                    params = ['-tile', str(tsz), '-ohst', hist_name]
                    log.debug('Generate tiles: from %s to %s with %s' % (ifname, tiles_name, params) )
                    #imgcnv.convert(ifname, tiles_name, fmt=default_format, extra=params )
                    self.server.imageconvert(image_id, ifname, tiles_name, fmt=default_format, extra=params)
                else:
                    log.debug('Locking failed for %s'%(hist_name) )

        with Locks(hstl_name) as l:
            log.debug("Tile read lock %s"%(hist_name))
            pass
        if os.path.exists(ofname):
            try:
                info = self.server.getImageInfo(filename=ofname)
                if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
                if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
                data_token.dims['image_num_p'] = 1
                data_token.dims['image_num_z'] = 1
                data_token.dims['image_num_t'] = 1
                data_token.setImage(ofname, format=default_format)
                data_token.histogram = hist_name
            finally:
                pass
        else:
            data_token.setHtmlErrorNotFound()

        return data_token



################################################################################
# Misc Image Services
################################################################################

class ProjectMaxService(object):
    '''Provide an image combined of all input planes by MAX
       ex: projectmax'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'projectmax: returns a maximum intensity projection image'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.projectmax')
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.projectmax')
        log.debug('ProjectMax: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-projectmax'])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-projectmax'])

        data_token.dims['image_num_p']  = 1
        data_token.dims['image_num_z']  = 1
        data_token.dims['image_num_t']  = 1
        return data_token.setImage(fname=ofile, format=default_format)

class ProjectMinService(object):
    '''Provide an image combined of all input planes by MIN
       ex: projectmin'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'projectmin: returns a minimum intensity projection image'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.projectmin')
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.projectmin')
        log.debug('Projectmin: %s to %s'%(ifile, ofile))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-projectmin'])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-projectmin'])

        data_token.dims['image_num_p']  = 1
        data_token.dims['image_num_z']  = 1
        data_token.dims['image_num_t']  = 1
        return data_token.setImage(fname=ofile, format=default_format)

class NegativeService(object):
    '''Provide an image negative
       ex: negative'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'negative: returns an image negative'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.negative')
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.negative')
        log.debug('Negative: %s to %s'%(ifile, ofile) )

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-negative', '-multi'])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-negative', '-multi'])

        return data_token.setImage(fname=ofile, format=default_format)

class DeinterlaceService(object):
    '''Provides a deinterlaced image
       ex: deinterlace'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'deinterlace: returns a deinterlaced image'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.deinterlace')
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.deinterlace')
        log.debug('Deinterlace: %s to %s'%(ifile, ofile))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-deinterlace', 'avg', '-multi'])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-deinterlace', 'avg', '-multi'])

        return data_token.setImage(fname=ofile, format=default_format)

class ThresholdService(object):
    '''Threshold an image
       threshold=value[,upper|,lower|,both]
       ex: threshold=128,both'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'threshold: returns a thresholded image, threshold=value[,upper|,lower|,both], ex: threshold=128,both'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        args = arg.split(',')
        if len(args)<1:
            return data_token
        method = 'both'
        if len(args)>1:
            method = args[1]
        arg = '%s,%s'%(args[0], method)
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.threshold_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        arg = arg.lower()
        args = arg.split(',')
        if len(args)<1:
            abort(400, 'Threshold: requires at least one parameter')
        method = 'both'
        if len(args)>1:
            method = args[1]
        arg = '%s,%s'%(args[0], method)
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.threshold_%s'%arg )
        log.debug('Threshold: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-threshold', arg])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-threshold', arg])

        return data_token.setImage(fname=ofile, format=default_format)

class PixelCounterService(object):
    '''Return pixel counts of a thresholded image
       pixelcount=value, where value is a threshold
       ex: pixelcount=128'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'pixelcount: returns a count of pixels in a thresholded image, ex: pixelcount=128'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.pixelcount_%s.xml'%arg)
        return data_token.setXmlFile(fname=ofile)

    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.pixelcount_%s.xml'%arg )
        log.debug('Pixelcount: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, extra=['-pixelcounts', arg])
            self.server.imageconvert(image_id, ifile, ofile, extra=['-pixelcounts', arg])

        return data_token.setXmlFile(fname=ofile)

class HistogramService(object):
    '''Returns histogram of an image
       ex: histogram'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'histogram: returns a histogram of an image, ex: histogram'

    def dryrun(self, image_id, data_token, arg):
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.histogram.xml')
        return data_token.setXmlFile(fname=ofile)

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.histogram.xml' )
        log.debug('Histogram: %s to %s'%(ifile, ofile))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, None, extra=['-ohstxml', ofile])
            self.server.imageconvert(image_id, ifile, None, extra=['-ohstxml', ofile])

        return data_token.setXmlFile(fname=ofile)

class LevelsService(object):
    '''Adjust levels in an image
       levels=minvalue,maxvalue,gamma
       ex: levels=15,200,1.2'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'levels: adjust levels in an image, levels=minvalue,maxvalue,gamma ex: levels=15,200,1.2'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.levels_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.levels_%s'%arg )
        log.debug('Levels: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-levels', arg])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-levels', arg])

        return data_token.setImage(fname=ofile, format=default_format)

class BrightnessContrastService(object):
    '''Adjust brightnesscontrast in an image
       brightnesscontrast=brightness,contrast with both values in range [-100,100]
       ex: brightnesscontrast=0,30'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'brightnesscontrast: Adjust brightness and contrast in an image, brightnesscontrast=brightness,contrast both in range [-100,100] ex: brightnesscontrast=0,30'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.brightnesscontrast_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.brightnesscontrast_%s'%arg )
        log.debug('Brightnesscontrast: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-brightnesscontrast', arg])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-brightnesscontrast', arg])

        return data_token.setImage(fname=ofile, format=default_format)

class TransformService(object):
    """Provide an image transform
       arg = transform
       Available transforms are: fourier, chebyshev, wavelet, radon, edge, wndchrmcolor, rgb2hsv, hsv2rgb, superpixels
       ex: transform=fourier
       superpixels requires two parameters: superpixel size in pixels and shape regularity 0-1, ex: transform=superpixels,32,0.5"""

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'transform: returns a transformed image, transform=fourier|chebyshev|wavelet|radon|edge|wndchrmcolor|rgb2hsv|hsv2rgb|superpixels'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.transform_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        args = arg.split(',')
        transform = args[0]
        params = args[1:]
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.transform_%s'%arg )
        log.debug('Transform: %s to %s with [%s]'%(ifile, ofile, arg))

        extra = ['-multi']
        if not os.path.exists(ofile):
            transforms = {'fourier'      : ['-transform', 'fft'],
                          'chebyshev'    : ['-transform', 'chebyshev'],
                          'wavelet'      : ['-transform', 'wavelet'],
                          'radon'        : ['-transform', 'radon'],
                          'edge'         : ['-filter',    'edge'],
                          'wndchrmcolor' : ['-filter',    'wndchrmcolor'],
                          'rgb2hsv'      : ['-transform_color', 'rgb2hsv'],
                          'hsv2rgb'      : ['-transform_color', 'hsv2rgb'],
                          'superpixels'  : ['-superpixels'], } # requires passing parameters

            if not transform in transforms:
                abort(400, 'transform: requested transform is not yet supported')

            extra.extend(transforms[transform])
            if len(params)>0:
                extra.extend([','.join(params)])
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=extra)
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=extra)

        return data_token.setImage(fname=ofile, format=default_format)

class SampleFramesService(object):
    '''Returns an Image composed of Nth frames form input
       arg = frames_to_skip
       ex: sampleframes=10'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'sampleframes: returns an Image composed of Nth frames form input, arg=n'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.framessampled_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        if not arg:
            abort(400, 'SampleFrames: no frames to skip provided')

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.framessampled_%s'%arg)
        log.debug('SampleFrames: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-multi', '-sampleframes', arg])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-multi', '-sampleframes', arg])

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_p' in info: data_token.dims['image_num_p'] = info['image_num_p']
            data_token.dims['image_num_z'] = 1
            data_token.dims['image_num_t'] = data_token.dims['image_num_p']
        finally:
            pass

        return data_token.setImage(fname=ofile, format=default_format)

class FramesService(object):
    '''Returns an image composed of user defined frames form input
       arg = frames
       ex: frames=1,2,5 or ex: frames=1,-,5 or ex: frames=-,5 or ex: frames=4,-'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'frames: Returns an image composed of user defined frames form input, arg = frames'

    def dryrun(self, image_id, data_token, arg):
        arg = arg.lower()
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.frames_%s'%arg)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):

        if not arg:
            abort(400, 'Frames: no frames provided')

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.frames_%s'%arg)
        log.debug('Frames: %s to %s with [%s]'%(ifile, ofile, arg))

        if not os.path.exists(ofile):
            #imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-multi', '-page', arg])
            self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-multi', '-page', arg])

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_p' in info: data_token.dims['image_num_p'] = info['image_num_p']
            data_token.dims['image_num_z']  = 1
            data_token.dims['image_num_t']  = 1
        finally:
            pass

        return data_token.setImage(fname=ofile, format=default_format)

class RotateService(object):
    '''Provides rotated versions for requested images:
       arg = angle
       At this moment only supported values are 90, -90, 270, 180 and guess
       ex: rotate=90'''

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'rotate: returns an image rotated as requested, arg = 0|90|-90|180|270|guess'

    def dryrun(self, image_id, data_token, arg):
        ang = arg.lower()
        if ang=='270':
            ang='-90'
        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, image_id, '.rotated_%s'%ang)
        return data_token.setImage(fname=ofile, format=default_format)

    def action(self, image_id, data_token, arg):
        ang = arg.lower()
        angles = ['0', '90', '-90', '270', '180', 'guess']
        if ang=='270':
            ang='-90'
        if ang not in angles:
            abort(400, 'rotate: angle value not yet supported' )

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, image_id, '.rotated_%s'%ang )
        log.debug('Rotate service: %s to %s'%(ifile, ofile))
        if ang=='0':
            ofile = ifile

        if not os.path.exists(ofile):
            r = self.server.imageconvert(image_id, ifile, ofile, fmt=default_format, extra=['-multi', '-rotate', ang])
            if r is None:
                return data_token.setHtmlErrorNotSupported()
        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'image_num_x' in info: data_token.dims['image_num_x'] = info['image_num_x']
            if 'image_num_y' in info: data_token.dims['image_num_y'] = info['image_num_y']
        finally:
            pass

        return data_token.setImage(ofile, format=default_format)

################################################################################
# Specific Image Services
################################################################################
#
# class BioFormatsService(object):
#     '''Provides BioFormats conversion to OME-TIFF
#        ex: bioformats'''
#
#     def __init__(self, server):
#         self.server = server
#
#     def __str__(self):
#         return 'bioformats: returns an image in OME-TIFF format'
#
#     def dryrun(self, image_id, data_token, arg):
#         ifile = self.server.getInFileName(data_token, image_id)
#         ofile = self.server.getOutFileName(ifile, image_id, '.ome.tif')
#         return data_token.setImage(fname=ofile, format=default_format)
#
#     def resultFilename(self, image_id, data_token):
#         ifile = self.server.getInFileName( data_token, image_id )
#         ofile = self.server.getOutFileName( ifile, image_id, '.ome.tif' )
#         return ofile
#
#     def action(self, image_id, data_token, arg):
#
#         if not bioformats.installed(): return data_token
#         ifile = self.server.getInFileName( data_token, image_id )
#         ofile = self.server.getOutFileName( ifile, image_id, '.ome.tif' )
#
#         bfinfo = None
#         if not os.path.exists(ofile):
#             log.debug('BioFormats: %s to %s'%(ifile, ofile))
#             try:
#                 original = self.server.originalFileName(image_id)
#                 bioformats.convert( ifile, ofile, original )
#
#                 if os.path.exists(ofile) and imgcnv.supported(ofile):
#                     orig_info = bioformats.info(ifile, original)
#                     bfinfo = imgcnv.info(ofile)
#                     if 'image_num_x' in bfinfo and 'image_num_x' in orig_info:
#                         if 'format' in orig_info: bfinfo['format'] = orig_info['format']
#                     bfinfo['converted_file'] = ofile
#                     self.server.setImageInfo( id=image_id, info=bfinfo )
#
#             except:
#                 log.error('Error running BioFormats: %s'%sys.exc_info()[0])
#
#         if not os.path.exists(ofile) or not imgcnv.supported(ofile):
#             return data_token
#
#         if bfinfo is None:
#             bfinfo = self.server.getImageInfo(ident=image_id)
#         data_token.dims = bfinfo
#         return data_token.setImage(ofile, format='ome-bigtiff')

#class UriService(object):
#    '''Fetches an image from remote URI and passes it from further processing, Note that the URI must be encoded!
#       Example shows encoding for: http://www.google.com/intl/en_ALL/images/logo.gif
#       arg = URI
#       ex: uri=http%3A%2F%2Fwww.google.com%2Fintl%2Fen_ALL%2Fimages%2Flogo.gif'''
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'UriService: Fetches an image from remote URL and passes it from further processing, url=http%3A%2F%2Fwww.google.com%2Fintl%2Fen_ALL%2Fimages%2Flogo.gif.'
#
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#    def action(self, image_id, data_token, arg):
#
#        url = unquote(arg)
#        log.debug('URI service: [' + url +']' )
#        url_filename = quote(url, "")
#        ofile = self.server.getOutFileName( 'url_', url_filename )
#
#        if not os.path.exists(ofile):
#            log.debug('URI service: Fetching to file - ' + str(ofile) )
#            #resp, content = request(url)
#            from bq.util.request import Request
#            content = Request(url).get ()
#            log.debug ("URI service: result header=" + str(resp))
#            if int(resp['status']) >= 400:
#                data_token.setHtml('URI service: requested URI could not be fetched...')
#            else:
#                f = open(ofile, 'wb')
#                f.write(content)
#                f.flush()
#                f.close()
#
#        data_token.setFile( ofile )
#        data_token.outFileName = url_filename
#        #data_token.setImage(fname=ofile, format=default_format)
#
#        if not imgcnv.supported(ofile):
#            #data_token.setHtml('URI service: Downloaded file is not in supported image format...')
#            data_token.setHtmlErrorNotSupported()
#        else:
#            data_token.dims = self.server.getImageInfo(filename=ofile)
#
#        log.debug('URI service: ' + str(data_token) )
#        return data_token
#
#class MaskService(object):
#    '''Provide images with mask preview:
#       arg = mask_id
#       ex: mask=999'''
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'MaskService: Returns an Image with mask superimposed, arg = mask_id'
#
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#
#    def action(self, image_id, data_token, mask_id):
#        #http://localhost:8080/imgsrv/images/4?mask=5
#        log.debug('Service - Mask: ' + mask_id )
#
#        ifname = self.server.getInFileName(data_token, image_id)
#        ofname = self.server.getOutFileName( ifname, '.mask_' + str(mask_id) )
#        mfname = self.server.imagepath(mask_id)
#
##        if not os.path.exists(ofname):
##
##            log.debug( 'Mask service: ' + ifname + ' + ' + mfname )
##
##            # PIL has problems loading 16 bit multiple channel images -> pre convert
##            imgcnv.convert( ifname, ofname, fmt='png', extra='-norm -page 1')
##            im = PILImage.open ( ofname )
##            # convert input image into grayscale and color it with mask
##            im = im.convert("L")
##            im = im.convert("RGB")
##
##            # get the mask image and then color it appropriately
##            im_mask = PILImage.open ( mfname )
##            im_mask = im_mask.convert("L")
##
##            # apply palette with predefined colors
##            im_mask = im_mask.convert("P")
##            mask_pal = im_mask.getpalette()
##            #mask_pal[240:242] = (0,0,255)
##            #mask_pal[480:482] = (0,255,0)
##            #mask_pal[765:767] = (255,0,0)
##            mask_pal[240] = 0
##            mask_pal[241] = 0
##            mask_pal[242] = 255
##            mask_pal[480] = 0
##            mask_pal[481] = 255
##            mask_pal[482] = 0
##            mask_pal[765] = 255
##            mask_pal[766] = 0
##            mask_pal[767] = 0
##            im_mask.putpalette(mask_pal)
##            im_mask = im_mask.convert("RGB")
##
##            # alpha specify the opacity for merging [0,1], 0.5 is 50%-50%
##            im = PILImage.blend(im, im_mask, 0.5 )
##            im.save(ofname, "TIFF")
##
##        data_token.setImage(fname=ofname, format=default_format)
#        return data_token
#
#################################################################################
## New Image Services
#################################################################################
#
#class CreateImageService(object):
#    '''Create new images'''
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'CreateImageService: Create new images, arg = ...'
#
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#
#    def action(self, image_id, data_token, arg):
#        '''arg := w,h,z,t,c,d'''
#        # requires: w,h,z,t,c,d - width,hight,z,t,channles,depth/channel
#        # defaults: -,-,1,1,1,8
#        # this action will create image without consolidated original file
#        # providing later write access to the planes of an image
#
#        if not arg:
#            raise IllegalOperation('Create service: w,h,z,t,c,d are all needed')
#
#        xs,ys,zs,ts,cs,ds = arg.split(',', 5)
#        x=0; y=0; z=0; t=0; c=0; d=0
#        if xs.isdigit(): x = int(xs)
#        if ys.isdigit(): y = int(ys)
#        if zs.isdigit(): z = int(zs)
#        if ts.isdigit(): t = int(ts)
#        if cs.isdigit(): c = int(cs)
#        if ds.isdigit(): d = int(ds)
#
#        if x<=0 or y<=0 or z<=0 or t<=0 or c<=0 or d<=0 :
#            raise IllegalOperation('Create service: w,h,z,t,c,d are all needed')
#
#        image_id = self.server.nextFileId()
#        xmlstr = self.server.setFileInfo( id=image_id, width=x, height=y, zsize=z, tsize=t, channels=c, depth=d )
#
#        response = etree.Element ('response')
#        image    = etree.SubElement (response, 'image')
#        image.attrib['src'] = '/imgsrv/'+str(image_id)
#        image.attrib['x'] = str(x)
#        image.attrib['y'] = str(y)
#        image.attrib['z'] = str(z)
#        image.attrib['t'] = str(t)
#        image.attrib['ch'] = str(c)
#        xmlstr = etree.tostring(response)
#
#        data_token.setXml(xmlstr)
#
#        #now we have to pre-create all the planes
#        ifname = self.server.imagepath(image_id)
#        ofname = self.server.getOutFileName( ifname, '.' )
#        creastr = '%d,%d,1,1,%d,%d'%(x, y, c, d)
#
#        for zi in range(z):
#            for ti in range(t):
#                imgcnv.convert(ifname, ofname+'0-0,0-0,%d-%d,%d-%d'%(zi,zi,ti,ti), fmt=default_format, extra=['-create', creastr] )
#
#        return data_token
#
#class SetSliceService(object):
#    '''Write a slice into an image :
#       arg = x,y,z,t,c
#       Each position may be specified as a range
#       empty params imply entire available range'''
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'SetSliceService: Writes a slice into an image, arg = x,y,z,t,c'
#
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#
#    def action(self, image_id, data_token, arg):
#        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''
#
#        vs = arg.split(',', 4)
#
#        z1=-1; z2=-1
#        if len(vs)>2 and vs[2].isdigit():
#            xs = vs[2].split('-', 2)
#            if len(xs)>0 and xs[0].isdigit(): z1 = int(xs[0])
#            if len(xs)>1 and xs[1].isdigit(): z2 = int(xs[1])
#            if len(xs)==1: z2 = z1
#
#        t1=-1; t2=-1
#        if len(vs)>3 and vs[3].isdigit():
#            xs = vs[3].split('-', 2)
#            if len(xs)>0 and xs[0].isdigit(): t1 = int(xs[0])
#            if len(xs)>1 and xs[1].isdigit(): t2 = int(xs[1])
#            if len(xs)==1: t2 = t1
#
#        x1=-1; x2=-1
#        if len(vs)>0 and vs[0]:
#            xs = vs[0].split('-', 2)
#            if len(xs)>0 and xs[0].isdigit(): x1 = int(xs[0])
#            if len(xs)>1 and xs[1].isdigit(): x2 = int(xs[1])
#
#        y1=-1; y2=-1
#        if len(vs)>1 and vs[1]:
#            xs = vs[1].split('-', 2)
#            if len(xs)>0 and xs[0].isdigit(): y1 = int(xs[0])
#            if len(xs)>1 and xs[1].isdigit(): y2 = int(xs[1])
#
#        if not z1==z2 or not t1==t2:
#            raise IllegalOperation('Set slice service: ranges in z and t are not supported by this service')
#
#        if not x1==-1 or not x2==-1 or not y1==-1 or not y2==-1:
#            raise IllegalOperation('Set slice service: x and y are not supported by this service')
#
#        if not x1==x2 or not y1==y2:
#            raise IllegalOperation('Set slice service: ranges in x and y are not supported by this service')
#
#        if not data_token.isFile():
#            raise IllegalOperation('Set slice service: input image is required')
#
#        # construct a sliced filename
#        gfname = self.server.imagepath(image_id) # this file should not exist, otherwise, exception!
#        if os.path.exists(gfname):
#            raise IllegalOperation('Set slice service: this image is read only')
#
#        ifname = data_token.data
#        ofname = self.server.getOutFileName( gfname, '.%d-%d,%d-%d,%d-%d,%d-%d' % (x1+1,x2+1,y1+1,y2+1,z1+1,z2+1,t1+1,t2+1) )
#
#        log.debug('Slice service: to ' +  ofname )
#        imgcnv.convert(ifname, ofname, fmt=default_format, extra=['-page', '1'] )
#
#        data_token.setImage(ofname, format=default_format)
#        return data_token
#
#
#class CloseImageService(object):
#    '''Create new images'''
#    def __init__(self, server):
#        self.server = server
#    def __str__(self):
#        return 'CloseImageService: Closes requested image, created with CreateImageService'
#
#    def hookInsert(self, data_token, image_id, hookpoint='post'):
#        pass
#
#    def action(self, image_id, data_token, arg):
#        # closes open image (the one without id) creating such an image, composed out of multiple plains
#        # disabling writing into image plains
#
#        ofname = self.server.imagepath(image_id)
#
#        if os.path.exists(ofname):
#            raise IllegalOperation('Close image service: this image is read only')
#
#        # grab all the slices of the image and compose id as tiff
#        ifiles = []
#        #z=0; t=0;
#        params = self.server.getFileInfo(id=image_id)
#        log.debug('Close service: ' +  str(params) )
#        z = int(params['image_num_z'])
#        t = int(params['image_num_t'])
#        for ti in range(t):
#            for zi in range(z):
#                ifname = self.server.getOutFileName( self.server.imagepath(image_id), '.0-0,0-0,%d-%d,%d-%d'%(zi,zi,ti,ti) )
#                log.debug('Close service: ' +  ifname )
#                ifiles.append(ifname)
#        imgcnv.convert_list(ifiles, ofname, fmt=default_format, extra=['-multi'] )
#
#        data_token.setImage(ofname, format=default_format)
#        return data_token


################################################################################
# ImageServer
################################################################################

#
#  /imgsrc/1?thumbnail&equalized
#  imageID | thumbnail | equalized
#  equalize (thumbnail (getimage(1)))
#

class ImageServer(object):
    def __init__(self, work_dir):
        '''Start an image server, using local dir imagedir,
        and loading extensions as methods'''
        #super(ImageServer, self).__init__(image_dir, server_url)
        self.workdir = work_dir
        self.url = "/image_service"

        self.services = {
            'services'     : ServicesService(self),
            'formats'      : FormatsService(self),
            'info'         : InfoService(self),
            'dims'         : DimService(self),
            'meta'         : MetaService(self),
            #'filename'     : FileNameService(self),
            'localpath'    : LocalPathService(self),
            'slice'        : SliceService(self),
            'format'       : FormatService(self),
            'resize'       : ResizeService(self),
            'resize3d'     : Resize3DService(self),
            'rearrange3d'  : Rearrange3DService(self),
            'thumbnail'    : ThumbnailService(self),
            #'default'      : DefaultService(self),
            'roi'          : RoiService(self),
            'remap'        : RemapService(self),
            'fuse'         : FuseService(self),
            'depth'        : DepthService(self),
            'rotate'       : RotateService(self),
            'tile'         : TileService(self),
            #'uri'          : UriService(self),
            'projectmax'   : ProjectMaxService(self),
            'projectmin'   : ProjectMinService(self),
            'negative'     : NegativeService(self),
            'deinterlace'  : DeinterlaceService(self),
            'threshold'    : ThresholdService(self),
            'pixelcounter' : PixelCounterService(self),
            'histogram'    : HistogramService(self),
            'levels'       : LevelsService(self),
            'brightnesscontrast' : BrightnessContrastService(self),
            'transform'    : TransformService(self),
            'sampleframes' : SampleFramesService(self),
            'frames'       : FramesService(self),
            #'mask'         : MaskService(self),
            #'create'       : CreateImageService(self),
            #'setslice'     : SetSliceService(self),
            #'close'        : CloseImageService(self),
            #'bioformats'   : BioFormatsService(self)
        }


        self.converters = ConverterDict([
            ('imgcnv',     ConverterImgcnv()),
            ('imaris',     ConverterImaris()),
            ('bioformats', ConverterBioformats())
        ])

        # image convert is special, we can't proceed without it
        if not self.converters['imgcnv'].get_installed():
            raise Exception('imgcnv is required but not installed')
        if not self.converters['imgcnv'].ensure_version(needed_versions['imgcnv']):
            raise Exception('imgcnv needs update! Has: %s Needs: %s'%(self.converters['imgcnv'].version['full'], needed_versions['imgcnv']))

        # test all the supported command line decoders and remove missing
        missing = []
        for n,c in self.converters.iteritems():
            if not c.get_installed():
                log.debug('%s is not installed, skipping support...', n)
                missing.append(n)
            elif not c.ensure_version(needed_versions[n]):
                log.warning('%s needs update! Has: %s Needs: %s', n, c.version['full'], needed_versions[n])
                missing.append(n)
        for m in missing:
            self.converters.pop(m)

        log.debug('Available converters: %s', self.converters)
        self.writable_formats = self.converters.formats(readable=False, writable=True, multipage=False)


        img_threads = config.get ('bisque.image_service.imgcnv.omp_num_threads', None)
        if img_threads is not None:
            log.info ("Setting OMP_NUM_THREADS = ", img_threads)
            os.environ['OMP_NUM_THREADS'] = "%s" % img_threads


        # check if the imgcnv is properly installed
#         self.image_formats = imgcnv.formats()
#         if not imgcnv.installed():
#             raise Exception('imgcnv not installed')
#         imgcnv.check_version( imgcnv_needed_version)

#         # check the bioformats version if installed
#         if bioformats.installed():
#             if not bioformats.ensure_version( bioformats_needed_version ):
#                 log.debug('Bioformats needs update! Has: '+bioformats.version()['full']+' Needs: '+ bioformats_needed_version)

    def ensureOriginalFile(self, ident):
        return blob_service.localpath(ident) or abort (404, 'File not available from blob service')

    def originalFileName(self, ident):
        return blob_service.original_name(ident)

    def getFileInfo(self, id=None, filename=None):
        if id is None and filename is None:
            return {}
        if filename is None:
            filename = self.ensureOriginalFile(id)
        filename = self.getOutFileName( filename, id, '.info' )
        if not os.path.exists(filename):
            return {}

        image = etree.parse(filename).getroot()
        info = {}
        for k,v in image.attrib.iteritems():
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            info[k] = v
        return info

    def setFileInfo(self, id=None, filename=None, **kw):
        if id is None and filename is None:
            return {}
        if filename is None:
            filename = self.ensureOriginalFile(id)
        filename = self.getOutFileName( filename, id, '.info' )

        image = etree.Element ('image', resource_uniq=str(id))
        for k,v in kw.iteritems():
            image.set(k, '%s'%v)
        etree.ElementTree(image).write(filename)
        return etree.tostring(image)

    def fileInfoCached(self, id=None, filename=None):
        if id==None and filename==None:
            return False
        if filename==None:
            filename = self.ensureOriginalFile(id)
        filename = self.getOutFileName( filename, id, '.info' )
        return os.path.exists(filename)

    def updateFileInfo(self, id=None, filename=None, **kw):
        pars = self.getFileInfo(id=id, filename=filename)
        for k,v in kw.iteritems():
            pars[k] = str(v)
        xmlstr = self.setFileInfo(id=id, filename=filename, **dict(pars))
        return xmlstr

    def getImageInfo(self, ident=None, data_token=None, filename=None):
        if ident==None and filename==None:
            return {}
        if filename is None:
            filename = self.ensureOriginalFile(ident)

        return_token = data_token is not None
        infofile = self.getOutFileName( filename, ident, '.info' )

        info = {}
        if os.path.exists(infofile):
            info = self.getFileInfo(id=ident, filename=filename)
        else:
            # If file info is not cached, get it and cache!
            for c in self.converters.itervalues():
                info = c.info(filename)
                if len(info)>0:
                    break

#             # try imgcnv
#             if imgcnv.supported(filename):
#                 info = imgcnv.info(filename)
#
#             # if not decoded try bioformats
#             if 'image_num_x' not in info and ident is not None:
#                 original = self.originalFileName(ident)
#                 if data_token is None: data_token = ProcessToken()
#                 data_token.setImage(filename, format=default_format)
#                 testfile = self.services['bioformats'].resultFilename(ident, data_token)
#                 if os.path.exists(testfile):
#                     info = self.getImageInfo(filename=testfile)
#                     data_token.setImage(testfile, format='tiff')
#                     data_token.dims = info
#                 elif bioformats.supported(filename, original):
#                     data_token = self.services['bioformats'].action (ident, data_token, '')
#                     if not data_token.dims is None:
#                         info = data_token.dims

            if not 'filesize' in info:
                fsb = os.path.getsize(filename)
                info['filesize'] = fsb

            if 'image_num_x' in info:
                self.setImageInfo( id=ident, filename=filename, info=info )

        if not 'filesize' in info:
            fsb = os.path.getsize(filename)
            info['filesize'] = fsb

        if 'image_num_x' in info:
            if not 'image_num_t' in info: info['image_num_t'] = 1
            if not 'image_num_z' in info: info['image_num_z'] = 1
            if not 'format'      in info: info['format']      = default_format
            if not 'image_num_p' in info: info['image_num_p'] = info['image_num_t'] * info['image_num_z']

        if return_token is True:
            if 'converted_file' in info:
                data_token.setImage(info['converted_file'], format=default_format)
            data_token.dims = info
            return data_token
        return info

    def imageconvert(self, image_id, ifnm, ofnm, fmt=None, extra=[], series=0):
        r = self.converters['imgcnv'].convert( ifnm, ofnm, fmt=fmt, extra=extra)
        if r is not None:
            return r
        # if the conversion failed, convert input to OME-TIFF using other converts
        for n,c in self.converters.iteritems():
            if n=='imgcnv':
                continue
            ometiff = self.getOutFileName( ifnm, image_id, '.ome.tif' )
            if not os.path.exists(ometiff):
                r = c.convertToOmeTiff(ifnm, ometiff, series)
            else:
                r = ometiff
            if r is not None:
                return self.converters['imgcnv'].convert( ometiff, ofnm, fmt=fmt, extra=extra)

    def setImageInfo(self, id=None, data_token=None, info=None, filename=None):
        if info is None: return
        if not 'image_num_t' in info: info['image_num_t'] = 1
        if not 'image_num_z' in info: info['image_num_z'] = 1
        if not 'format'      in info: info['format']      = default_format
        if not 'image_num_p' in info: info['image_num_p'] = info['image_num_t'] * info['image_num_z']
        if 'image_num_x' in info:
            self.setFileInfo( id=id, filename=filename, **info )

    #def fileIsTIFF(self, filename=None, data_token=None):
    #    info = None
    #    if not data_token is None and not data_token.dims is None:
    #        info = data_token.dims
    #    else:
    #        info = self.getImageInfo(filename=filename)
    #
    #    if info is None: return False
    #    if not 'format' in info: return False
    #    if info['format'].lower() == default_format: return True
    #    return False

    def initialWorkPath(self, image_id):
        image = data_service.get_resource(image_id)
        owner = data_service.get_resource(image.get('owner'))
        user_name = owner.get ('name')

        if len(image_id)>3 and image_id[2]=='-':
            subdir = image_id[3]
        else:
            subdir = image_id[0]
        path =  os.path.realpath(os.path.join(self.workdir, user_name, subdir, image_id))
        log.debug ("initialWorkPath %s", path)
        return path

    def ensureWorkPath(self, path, image_id):
        """path may be a workdir path OR an original image path to transformed into
        a workdir path
        """
        # change ./imagedir to ./workdir if needed
        path = os.path.realpath(path)
        workpath = os.path.realpath(self.workdir)
        log.debug ("ensureWorkPath : path=%s image_id=%s wd=%s", path, image_id, workpath)
        if image_id and not path.startswith (workpath):
            path = self.initialWorkPath(image_id)
        # keep paths relative to workdir to reduce file name size
        path = os.path.relpath(path, workpath)
        # make sure that the path directory exists
        _mkdir( os.path.dirname(path) )
        return path

    def getInFileName(self, data_token, image_id):
        # if there is no image file input, request the first slice
        if not data_token.isFile():
            data_token.setFile( self.ensureOriginalFile(image_id) )
        return data_token.data

    def getOutFileName(self, infilename, image_id, appendix):
        ofile = self.ensureWorkPath(infilename, image_id)
        #ofile = os.path.relpath(ofile, self.workdir)
        return '%s%s'%(ofile, appendix)

    def request(self, method, image_id, imgfile, argument):
        '''Apply an image request'''
        if not method:
            #image = self.cache.check(self.imagepath(image_id))
            #return image
            return imgfile

        try:
            service = self.services[method]
        except:
            #do nothing
            service = None

        #if not service:
        #    raise UnknownService(method)
        r = imgfile
        if service is not None:
            r = service.action (image_id, imgfile, argument)
        return r

    def process(self, url, ident, **kw):
        query = getQuery4Url(url)
        log.debug ('STARTING query: %s', query)
        os.chdir(self.workdir)
        log.debug('Current path: %s', self.workdir)

        # init the output to a simple file
        data_token = ProcessToken()
        if ident is not None:

            # pre-compute final filename and check if it exists before starting any other processing
            if len(query)>0:
                data_token.setFile(self.initialWorkPath(ident))
                data_token.dims = self.getFileInfo(id=ident, filename=data_token.data)
                for action, args in query:
                    try:
                        service = self.services[action]
                        log.debug ('DRY run: %s', action)
                        data_token = service.dryrun(ident, data_token, args)
                    except:
                        pass
                    if data_token.isHttpError():
                        break
                localpath = os.path.join(os.path.realpath(self.workdir), data_token.data)
                #localpath = os.path.realpath(data_token.data)
                log.debug('Dryrun result: [%s] [%s]', localpath, data_token)
                if os.path.exists(localpath) and data_token.isFile():
                    log.debug('Returning pre-cached result: %s', data_token.data)
                    with Locks(data_token.data) as l:
                        pass
                    return data_token

            # start the processing
            original_filename = self.ensureOriginalFile(ident)
            data_token.setFile(original_filename)

            #if not blob_service.file_exists(ident):
            if not os.path.exists(original_filename):
                data_token.setHtmlErrorNotFound()
                return data_token

            if len(query)>0:
                # this will pre-convert the image if it's not supported by the imgcnv
                # and also set the proper dimensions info
                data_token = self.getImageInfo(ident=ident, data_token=data_token)
                if not 'image_num_x' in data_token.dims:
                    data_token.setHtmlErrorNotSupported()
                    return data_token

        #process all the requested operations
        for action,args in query:
            log.debug ('ACTION: %s',  action)
            data_token = self.request(action, ident, data_token, args)
            if data_token.isHttpError():
                break

        # test output, if it is a file but it does not exist, set 404 error
        data_token.testFile()

        # if the output is a file but not an image or no processing was done to it
        # set to the original file name
        if data_token.isFile() and not data_token.isImage() and not data_token.isText() and not data_token.hasFileName():
            data_token.contentType = 'application/octet-stream'
            data_token.outFileName = self.originalFileName(ident)

        # if supplied file name overrides filename
        for action,args in query:
            if (action.lower() == 'filename'):
                data_token.outFileName = args
                break

        log.debug ('FINISHED query: %s', query)
        return data_token

