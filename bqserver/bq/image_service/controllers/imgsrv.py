# imgsrv.py
# Author: Dmitry Fedorov and Kris Kvilekval
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" ImageServer for Bisque system.
"""

__module__    = "imgsrv"
__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "1.3"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
#import web
import shutil
#import fcntl
import logging
import os
import os.path
import subprocess
import datetime
import StringIO
import time
import shutil
import urllib
from urllib import quote
from urllib import unquote
from urlparse import urlparse
from lxml import etree
from datetime import datetime

import tg
from tg import config
from pylons.controllers.util import abort

#Project
from bq import blob_service
from bq.util.http import request
from bq.util.mkdir import _mkdir

# Locals
from exceptions import *
import imgcnv
import bioformats

log = logging.getLogger('bq.image_service.server')

default_format = 'bigtiff'

imgsrv_thumbnail_cmd = config.get('bisque.image_service.thumbnail_command', '-depth 8,d -page 1 -display')
imgsrv_default_cmd = config.get('bisque.image_service.default_command', '-depth 8,d')

imgcnv_needed_version = '1.60' # dima: upcoming 1.54
bioformats_needed_version = '4.3.0' # dima: upcoming 4.4.4

# ImageServer
#
#
#
#  /datasrv/blob/1

#  /datasrv/image/(\d+)[?format=(jpg,tiff,raw)]
#  htpp://datasrv/image/(\d+)/t/1-10/z/1/
#  /datasrv/thumbnail[/(\d+)]
#  /datasrv/blob/(\d)
#  htpp://datasrv/image/methods
#  http://datasrv/image/(\d+)[?(method)(&method)*]
#
#     method = thumbnail
#              x=100&y=100
#              equalize
#              dimensions
#              binarize
#              t=1&z=1&c=1&format=jpg

#  /datasev/feature

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
# ProcessToken
################################################################################

class ProcessToken(object):
    'Keep data with correct content type and cache info'
    def __init__(self):
        self.data        = False
        self.contentType = ''
        self.cacheInfo   = ''
        self.outFileName = ''
        self.httpResponseCode = 200
        self.dims        = None
        self.histogram   = None

    def setData (self, data_buf, content_type):
        self.data = data_buf
        self.contentType = content_type
        self.cacheInfo = 'max-age=302400' # one week

    def setHtml (self, text):
        self.data = text
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'

    def setXml (self, xml_str):
        self.data = xml_str
        self.contentType = 'text/xml'
        self.cacheInfo = 'max-age=302400' # one week
        #self.cacheInfo = 'no-cache'

    def setImage (self, fname, format):
        self.data = fname
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


    def setFile (self, fname):
        self.data = fname
        self.contentType = 'application/octet-stream'
        self.cacheInfo = 'max-age=302400' # one week

    def setNone (self):
        self.data = False
        self.contentType = ''

      #Status-Code    = "200"   ; OK
      #| "201"   ; Created
      #| "202"   ; Accepted
      #| "204"   ; No Content
      #| "301"   ; Moved Permanently
      #| "302"   ; Moved Temporarily
      #| "304"   ; Not Modified
      #| "400"   ; Bad Request
      #| "401"   ; Unauthorized
      #| "403"   ; Forbidden
      #| "404"   ; Not Found
      #| "500"   ; Internal Server Error
      #| "501"   ; Not Implemented
      #| "502"   ; Bad Gateway
      #| "503"   ; Service Unavailable

    def setHtmlErrorUnauthorized (self):
        self.data = 'Permission denied...'
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 401

    def setHtmlErrorNotFound (self):
        self.data = 'File not found...'
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 404

    def setHtmlErrorNotSupported (self):
        self.data = 'File is not in supported image format...'
        self.contentType = 'text/html'
        self.cacheInfo = 'no-cache'
        self.httpResponseCode = 415

    def isValid (self):
        if self.data:
            return True
        else:
            return False

    def isImage (self):
        if self.contentType.startswith('image/'):
            return True
        if self.contentType.startswith('video/'):
            return True
        elif self.contentType.lower() == 'application/x-shockwave-flash':
            return True
        else:
            return False

    def isFile (self):
        if self.contentType.startswith('image/') or self.contentType.startswith('application/') or self.contentType.startswith('video/'):
            return True
        else:
            return False

    def isText (self):
        if self.contentType.startswith('text/'):
            return True
        else:
            return False

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
# FileCache
################################################################################

class FileCache(object):
    'Keep recently served files in memory for speedier delivery'
    def __init__(self, timeout = 3600, maxmem = 20*M):
        self.cache = {}
        self.timeout = timeout
        self.maxmem = maxmem
        self.current_mem = 0

    def add (self, path, mem):
        if not isinstance(mem, StringIO.StringIO):
            mem = StringIO.StringIO (mem)
        self.cache[path] = (mem, datetime.datetime.now())
        return mem

    def filecheck(self, path):
        if not self.check(path) and os.path.exists(path):
            self.add(path, open(path,'rb').read())
        return self.check(path)

    def check (self, path):
        file, ts = self.cache.get (path, (None, None))
        if file:
            file.seek(0)
        return file

################################################################################
# Info Services
################################################################################

class ServicesService(object):
    '''Provide services information'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'ServicesService: Returns XML with services information'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        response = etree.Element ('response')
        servs    = etree.SubElement (response, 'services')
        servs.attrib['src'] = '/imgsrv/'

        for name,func in self.server.services.items():
            tag = etree.SubElement(servs, 'tag')
            tag.attrib['name'] = str(name)
            tag.attrib['type'] = 'string'
            tag.attrib['value'] = str(func)

        data_token.setXml(etree.tostring(response))
        return data_token

class FormatsService(object):
    '''Provide information on supported formats'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'FormatsService: Returns XML with supported formats'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):
        xmlout = '<response>\n' + imgcnv.installed_formats()
        if bioformats.installed():
            xmlout += bioformats.installed_formats()
        xmlout += '\n</response>\n'
        data_token.setXml( xmlout )
        return data_token

class InfoService(object):
    '''Provide image information'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'InfoService: Returns XML with image information'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        info = self.server.getImageInfo(ident=image_id)

        #response = etree.Element ('response')
        image    = etree.Element ('resource')
        image.attrib['uri'] = '%s/%s' % (self.server.url,  image_id)
        for k, v in info.iteritems():
            tag = etree.SubElement(image, 'tag')
            tag.attrib['name'] = str(k)
            tag.attrib['type'] = 'string'
            tag.attrib['value'] = str(v)

        # append original file name
        fileName = self.server.originalFileName(image_id)
        if len(fileName)>0:
            tag = etree.SubElement(image, 'tag')
            tag.attrib['name'] = 'filename'
            tag.attrib['type'] = 'string'
            tag.attrib['value'] = fileName

        data_token.setXml(etree.tostring(image))
        return data_token

class DimService(object):
    '''Provide image dimension information'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'DimService: Returns XML with image dimension information'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        info = data_token.dims
        response = etree.Element ('response')
        if not info is None:
            image    = etree.SubElement (response, 'image')
            image.attrib['src'] = '/imgsrv/' + str(image_id)
            for k, v in info.iteritems():
                tag = etree.SubElement(image, 'tag')
                tag.attrib['name'] = str(k)
                tag.attrib['type'] = 'string'
                tag.attrib['value'] = str(v)

        data_token.setXml(etree.tostring(response))
        return data_token

class MetaService(object):
    '''Provide image information'''

    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'MetaService: Returns XML with image meta-data'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):
        ifile = self.server.imagepath(image_id)
        #infoname = self.server.imagepath(image_id)+'.info'
        infoname = self.server.getOutFileName( ifile, '.info' )
        metacache = self.server.getOutFileName( self.server.imagepath(image_id), '.meta' )

        if not os.path.exists(metacache):
            if not imgcnv.supported(ifile):
                ifile = self.server.getInFileName( data_token, image_id )

            info = {}
            if os.path.exists(ifile):
                info = imgcnv.meta(ifile)
            else:
                info['format']      = default_format
                info['pixel_resolution_x'] = str( '0.0' )
                info['pixel_resolution_y'] = str( '0.0' )
                info['pixel_resolution_z'] = str( '0.0' )
                info['pixel_resolution_t'] = str( '0.0' )
                info['date_time'] = str( getFileDateTimeString(infoname) )

            if os.path.exists(infoname):
                info2 = self.server.getFileInfo(id=image_id)
                if 'width'    in info2: info['image_num_x'] = str( info2['width'] )
                if 'height'   in info2: info['image_num_y'] = str( info2['height'] )
                if 'zsize'    in info2: info['image_num_z'] = str( info2['zsize'] )
                if 'tsize'    in info2: info['image_num_t'] = str( info2['tsize'] )
                if 'channels' in info2: info['image_num_c'] = str( info2['channels'] )
                if 'depth'    in info2: info['image_pixel_depth'] = str( info2['depth'] )
                info['image_num_p'] = str( int(info2['tsize']) * int(info2['zsize']) )

            #response = etree.Element ('response')
            #response.set('uri', '%s/%s?meta'%(self.server.url, image_id))
            #response.set('src', '%s/%s'%(self.server.url, image_id))
            image    = etree.Element ('resource')
            #image.set('src', '%s/%s'%(self.server.url, image_id))
            image.set('uri', '%s/%s?meta'%(self.server.url, image_id))
            planes = None

            # append original file name
            fileName = self.server.originalFileName(image_id)
            if len(fileName)>0:
                tag = etree.SubElement(image, 'tag')
                tag.set('name', 'filename')
                tag.set('value', fileName)

            tags_map = {}
            for k, v in info.items():
                k = unicode(str(k), 'latin1')
                v = unicode(str(v), 'latin1')
                #log.debug('meta %s: %s'%(k, v))
                
                tl = k.split('/')
                parent = image
                for i in range(0,len(tl)):
                    tn = '/'.join(tl[0:i+1])
                    if not tn in tags_map:
                        tp = etree.SubElement(parent, 'tag')
                        tp.attrib['name'] = tl[i]
                        tags_map[tn] = tp
                        parent = tp
                    else:
                        parent = tags_map[tn]
                try:
                    parent.set('value', v)
                except ValueError:
                    pass

            log.debug("MetaService: storing metadata into " + str(metacache))
            xmlstr = etree.tostring(image)
            f = open(metacache, "w")
            try:
                f.write(xmlstr)
            finally:
                f.close()

            #etree.ElementTree(response).write(metacache)
            #data_token.setXml(etree.tostring(response))
            data_token.setXml(xmlstr)
            return data_token

        log.debug("MetaService: reading metadata from " + str(metacache))
        xmlstr = ""
        f = open(metacache, "r")
        try:
            xmlstr = f.read()
        finally:
            f.close()

        data_token.setXml(xmlstr)
        return data_token

class FileNameService(object):
    '''Provide image filename'''

    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'FileNameService: Returns XML with image file name'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        fileName = self.server.originalFileName(image_id)

        response = etree.Element ('response')
        image    = etree.SubElement (response, 'image')
        image.attrib['src'] = '/imgsrv/' + str(image_id)
        tag = etree.SubElement(image, 'tag')
        tag.attrib['name'] = 'filename'
        tag.attrib['type'] = 'string'
        tag.attrib['value'] = fileName

        data_token.setXml(etree.tostring(response))
        return data_token

class LocalPathService(object):
    '''Provides local path for responce image'''

    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'LocalPathService: Returns XML with local path to the procesed image'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):
        ifile = self.server.getInFileName( data_token, image_id )
        ifile = os.path.abspath(ifile)
        res = etree.Element ('resource')
        if os.path.exists(ifile):
            res.attrib['type'] = 'file'
            #res.attrib['src'] = 'file:%s'%( urllib.pathname2url(ifile) )
            # This urlencode a filepath in an xml file, which to me doesn't make sense.
            # maybe needs XML encoding, but not url
            res.attrib['src'] = 'file:%s'%( ifile )

        log.debug("LocalPathService: local path: " + str(ifile))
        data_token.setXml( etree.tostring(res) )
        return data_token


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
    def __repr__(self):
        return 'SliceService: Returns an Image of requested slices, arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2. All values are in ranges [1..N]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''

        vs = arg.split(',', 4)

        x1=0; x2=0
        if len(vs)>0 and vs[0]:
            xs = vs[0].split('-', 1)
            if len(xs)>0 and xs[0].isdigit(): x1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): x2 = int(xs[1])

        y1=0; y2=0
        if len(vs)>1 and vs[1]:
            xs = vs[1].split('-', 1)
            if len(xs)>0 and xs[0].isdigit(): y1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): y2 = int(xs[1])

        z1=0; z2=0
        if len(vs)>2 and vs[2]:
            xs = vs[2].split('-', 1)
            if len(xs)>0 and xs[0].isdigit(): z1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): z2 = int(xs[1])
            if len(xs)==1: z2 = z1

        t1=0; t2=0
        if len(vs)>3 and vs[3]:
            xs = vs[3].split('-', 1)
            if len(xs)>0 and xs[0].isdigit(): t1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): t2 = int(xs[1])
            if len(xs)==1: t2 = t1

        # construct a sliced filename
        ifname = self.server.getInFileName( data_token, image_id )
        ofname = self.server.getOutFileName( ifname, '.%d-%d,%d-%d,%d-%d,%d-%d' % (x1,x2,y1,y2,z1,z2,t1,t2) )
        log.debug('Slice service: from ' + ifname + ' to ' +  ofname )

        # if input image has only one T and Z skip slice alltogether
        try:
            if not data_token.dims is None:
                skip = True
                if   'zsize' in data_token.dims and int(data_token.dims['zsize'])>1: skip = False
                elif 'tsize' in data_token.dims and int(data_token.dims['tsize'])>1: skip = False
                elif 'pages' in data_token.dims and int(data_token.dims['pages'])>1: skip = False
                if skip: return data_token
        finally:
            pass

        # hack fix, this whole image info thing should be rewritten along with the image service
        if z1==z2==0: z1=1; z2=int(data_token.dims['zsize'])
        if t1==t2==0: t1=1; t2=int(data_token.dims['tsize'])

        # slice the image
        if not os.path.exists(ofname):
            if not imgcnv.supported(ifname):
                #data_token.setHtml('Slice service: input file is not in supported image format...')
                data_token.setHtmlErrorNotSupported()
                return data_token

            info = self.server.getImageInfo(ident=image_id)

            # extract pages from 5D image
            if z1==z2==0: z1=1; z2=int(info['zsize'])
            if t1==t2==0: t1=1; t2=int(info['tsize'])
            pages = []
            for ti in range(t1, t2+1):
                for zi in range(z1, z2+1):
                     if int(info['tsize'])==1:
                         page_num = zi
                     elif int(info['zsize'])==1:
                         page_num = ti
                     elif info['dimensions'].startswith('X Y C Z'):
                         page_num = (ti-1)*int(info['zsize']) + zi
                     else:
                         page_num = (zi-1)*int(info['tsize']) + ti

                     pages.append(page_num)

            pages_str = ",".join([str(p) for p in pages])

            # init parameters
            params = ['-multi', '-page', '%d'%pages_str]

            if not (x1==x2) or not (y1==y2):
                x1s = ''; y1s = ''; x2s = ''; y2s = ''
                if not (x1==x2):
                    if x1 > 0: x1s = str(x1-1)
                    if x2 > 0: x2s = str(x2-1)
                if not (y1==y2):
                    if y1 > 0: y1s = str(y1-1)
                    if y2 > 0: y2s = str(y2-1)
                params.extend(['-roi', '%s,%s,%s,%s' % (x1s,y1s,x2s,y2s)])
            log.debug( 'Slice service params: %s'%params )
            imgcnv.convert(ifname, ofname, fmt=default_format, extra=params )

        try:
            new_num_z = z2 - z1 + 1;
            new_num_t = t2 - t1 + 1;
            new_w=x2-x1;
            new_h=y2-y1;
            data_token.dims['zsize']  = str(new_num_z)
            data_token.dims['tsize']  = str(new_num_t)
            data_token.dims['pages']  = str(new_num_z*new_num_t)
            if new_w>0: data_token.dims['width']  = str(new_w)
            if new_h>0: data_token.dims['height'] = str(new_h)
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(ofname, format=default_format)
        return data_token


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
    def __repr__(self):
        return 'FormatService: Returns an Image in the requested format, arg = format[,stream][,OPT1][,OPT2][,...]'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        fmt = default_format
        stream = False
        args = arg.split(',')
        if len(args)>0:
            fmt = args[0].lower()
            args.pop(0)

        if 'stream' in args:
            stream = True
            args.remove('stream')

        if fmt in imgcnv.formats():
            name_extra = ''
            if len(args) > 0:
                name_extra = (".").join(args) + '.'

            ifile = self.server.getInFileName( data_token, image_id )
            ofile = self.server.getOutFileName( ifile, '.' + name_extra + fmt.lower() )
            log.debug('Format service: ' + ifile +'->'+ofile+' with ' + fmt + ' opts= ' + str(args))

            # avoid doing anything if requested format is tiff and input file is already tiff
            # Altough this might give us back one of the proprietary tiff-based images, in that case, recode
            if (fmt == default_format or fmt == 'tif') and self.server.fileIsTIFF(filename=ifile, data_token=data_token) and (ifile != self.server.imagepath(image_id)):
                log.debug('Result is standard TIFF, avoid reconvert')
                ofile = ifile

            if not os.path.exists(ofile):
                # allow multiple pages to be saved in MP format
                extra_opt = ['-page', '1']
                if imgcnv.canWriteMultipage( fmt ):
                    extra_opt = ['-multi']

                if len(args) > 0:
                    extra_opt.extend( ['-options', (" ").join(args)])
                else:
                    if fmt == 'jpg' or fmt == 'jpeg':
                      extra_opt.extend(['-options', 'quality 95 progressive yes'])

                imgcnv.convert(ifile, ofile, fmt, extra=extra_opt)

            if stream:
              ext = imgcnv.defaultExtension(fmt)
              fpath = ofile.split('/')
              filename = self.server.originalFileName(image_id) +'_'+ fpath[len(fpath)-1] +'.'+ext
              data_token.setFile(fname=ofile)
              data_token.outFileName = filename
            else:
              data_token.setImage(fname=ofile, format=fmt)

            if (ofile != ifile) and (fmt != 'raw'):
                try:
                    info = self.server.getImageInfo(filename=ofile)
                    if int(info['pages'])>1:
                        if 'zsize' in data_token.dims: info['zsize'] = data_token.dims['zsize']
                        if 'tsize' in data_token.dims: info['tsize'] = data_token.dims['tsize']
                    data_token.dims = info
                except:
                    pass

            return data_token

        data_token.setNone()
        return data_token

class ResizeService(object):
    '''Provide images in requested dimensions
       arg = w,h,method[,AR]
       w - new width
       h - new height
       method - NN or BL, or BC (Nearest neighbor, Bilinear, Bicubic respectively)
       if either w or h is ommited or 0, it will be computed using aspect ratio of the image
       if ,AR is present then the size will be used as bounding box and aspect ration preserved
       if ,MX is present then the size will be used as maximum bounding box and aspect ration preserved
       with MX: if image is smaller it will not be resized!
       #size_arg = '-resize 128,128,BC,AR'
       ex: resize=100,100'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'ResizeService: Returns an Image in requested dimensions, arg = w,h,method[,AR|,MX]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        log.debug('Service - Resize: ' + arg )

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
            raise IllegalOperation('Resize service: size is unsupported ['+ arg + ']' )

        if not (method=='NN' or method=='BL' or method=='BC'):
            raise IllegalOperation('Resize service: method is unsupported ['+ arg + ']' )

        # if the image is smaller and MX is used, skip resize
        if maxBounding and int(data_token.dims['width'])<=size[0] and int(data_token.dims['height'])<=size[1]:
            return data_token

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.size_%d,%d,%s,%s' % (size[0], size[1], method,textAddition) )
        log.debug('Resize service: ' + ifile + ' to ' + ofile)

        if not os.path.exists(ofile):
            args = ['-multi', '-resize', '%s,%s,%s%s'%(size[0], size[1], method,aspectRatio)]
            imgcnv.convert( ifile, ofile, fmt=default_format, extra=args)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'width' in info:  data_token.dims['width']  = str(info['width'])
            if 'height' in info: data_token.dims['height'] = str(info['height'])
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(ofile, format=default_format)
        return data_token

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
    def __repr__(self):
        return 'ThumbnailService: Returns an Image as a thumbnail, arg = [w,h][,method]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        #thm = self._insertThumb (data_token, image_id)
        #self.server.cache.add (thm, thm.read())
        pass

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
            raise IllegalOperation('Thumbnail service: size is unsupported ['+ arg + ']' )

        if not (method=='NN' or method=='BL' or method=='BC'):
            raise IllegalOperation('Thumbnail service: method is unsupported ['+ arg + ']' )


        ifile = self.server.getInFileName( data_token, image_id )
        if size[0]==128 and size[1]==128:
          ofile = self.server.getOutFileName( ifile, '.thumb' )
        else:
          ofile = self.server.getOutFileName( ifile, '.thumb'+'_'+str(size[0])+'x'+str(size[1]) )

        if not os.path.exists(ofile):
            log.debug('Service - Thumbnail: ' + ofile)
            conv_arg = imgsrv_thumbnail_cmd.split(' ')
#            try:
#                if int(data_token.dims['depth']) == 8:
#                    conv_arg = conv_arg.replace('-depth 8,d ', '')
#            except (KeyError, ValueError):
#                    pass
            conv_arg.extend([ '-resize', '%s,%s,%s,AR'%(size[0],size[1],method)])
            conv_arg.extend([ '-options', 'quality 95 progressive yes'])
            imgcnv.convert( ifile, ofile, fmt='jpeg', extra=conv_arg)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'width' in info:  data_token.dims['width']  = str(info['width'])
            if 'height' in info: data_token.dims['height'] = str(info['height'])
            data_token.dims['pages']  = '1'
            data_token.dims['zsize']  = '1'
            data_token.dims['tsize']  = '1'
            data_token.dims['format'] = 'JPEG'
        finally:
            pass

        data_token.setImage(ofile, format='jpeg')
        return data_token

class DefaultService(object):
    '''Provide a default RGB preview of the image
       ex: default'''
    def __init__(self, server):
        self.server = server

    def __repr__(self):
        return 'DefaultService: Returns a default RGB preview of the image'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def getTagValue(self, elem, name, def_val):
        t = elem.find('tag[@name="%s"]'%(name) )
        if t is None:
            return def_val
        return t.get( 'value', def_val )

    def getTagValueInt(self, elem, name, def_val):
        v = self.getTagValue(elem, name, def_val)
        if v.isdigit():
            return int(v)
        else:
            return def_val

    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.default')
        log.debug('Default Preview service: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            extra = imgsrv_default_cmd.split(' ')
            try:
                # define channels in C form and then add 1 to start at 1
                chan_r = 0; chan_g = 1; chan_b = 2
                #if ( data_token.getDim('channels', 0) == 1 ):
                #    chan_r = 0; chan_g = 0; chan_b = 0
                #if ( data_token.getDim('channels', 0) == 2 ):
                #    chan_r = 0; chan_g = 1; chan_b = -1

                self.server.services['meta'].action (image_id, data_token, '')
                meta_str = data_token.data
                root = etree.fromstring( meta_str )
                image = root.find('image')
                if not image is None:
                    #chan_num = self.getTagValueInt( image, 'image_num_c', 0)
                    chan_r = self.getTagValueInt( image, 'display_channel_red', -1)
                    chan_g = self.getTagValueInt( image, 'display_channel_green', -1)
                    chan_b = self.getTagValueInt( image, 'display_channel_blue', -1)
                extra.extend(['-remap', '%d,%d,%d'%(chan_r+1, chan_g+1, chan_b+1)])
                imgcnv.convert( ifile, ofile, fmt=default_format, extra=extra )
            except:
                extra.extend(['-display'])
                imgcnv.convert( ifile, ofile, fmt=default_format, extra=extra)

        data_token.dims['format'] = default_format
        data_token.setImage(fname=ofile, format=default_format)
        return data_token

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
    def __repr__(self):
        return 'RoiService: Returns an Image in specified ROI, arg = x1,y1,x2,y2, all values are in ranges [1..N]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        log.debug('Service - Resize: ' + arg )

        vs = arg.split(',', 4)

        x1=0; x2=0; y1=0; y2=0
        if len(vs)>0 and vs[0].isdigit(): x1 = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): y1 = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): x2 = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): y2 = int(vs[3])

        if x1<=0 and x2<=0 and y1<=0 and y2<=0:
            raise IllegalOperation('ROI service: region is not provided' )

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, ('.roi_%d,%d,%d,%d' % (x1,y1,x2,y2)) )
        log.debug('ROI service: ' + ifile + ' to ' + ofile)

        if not os.path.exists(ofile):
            params = ['-multi', '-roi', '%d,%d,%d,%d' % (x1-1,y1-1,x2-1,y2-1)]
            imgcnv.convert( ifile, ofile, fmt=default_format, extra=params)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'width' in info:  data_token.dims['width']  = str(info['width'])
            if 'height' in info: data_token.dims['height'] = str(info['height'])
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(ofile, format=default_format)
        return data_token

class RemapService(object):
    """Provide an image with the requested channel mapping
       arg = channel,channel...
       output image will be constructed from channels 1 to n from input image, 0 means black channel
       remap=display - will use preferred mapping found in file's metadata
       remap=gray - will return gray scale image with visual weighted mapping from RGB or equal weights for other nuber of channels
       ex: remap=3,2,1"""
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'RemapService: Returns an Image with the requested channel mapping, arg = [channel,channel...]|gray|display'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.map_' + arg )
        log.debug('Remap service: ' + ifile + ' to '+ ofile +' with [' + arg + ']')

        if arg == 'display':
            arg = ['-multi' '-display']
        elif arg=='gray' or arg=='grey':
            arg = ['-multi', '-fusegrey']
        else:
            arg = ['-multi', '-remap', arg]

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=arg)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'channels' in info: data_token.dims['channels'] = str(info['channels'])
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        return data_token
        
class FuseService(object):
    """Provide an RGB image with the requested channel fusion
       arg = W1R,W1G,W1B;W2R,W2G,W2B;W3R,W3G,W3B;W4R,W4G,W4B
       output image will be constructed from channels 1 to n from input image mapped to RGB components with desired weights
       fuse=display will use preferred mapping found in file's metadata
       ex: fuse=255,0,0;0,255,0;0,0,255;255,255,255:A"""
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'FuseService: Returns an RGB image with the requested channel fusion, arg = W1R,W1G,W1B;W2R,W2G,W2B;...[:METHOD]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])
        
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.fuse_%s'%(argenc) )
        log.debug('Fuse service: %s to %s with [%s:%s]'%(ifile, ofile, arg, method))

        if arg == 'display':
            arg = ['-multi', '-fusemeta']
        else:
            arg = ['-multi', '-fusergb', arg]
            
        if method != 'a':
            arg.extend(['-fusemethod', method])
            ofile += '_%s'%(method)
            
        if data_token.histogram is not None:
            arg.extend(['-ihst', data_token.histogram])            

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=arg)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'channels' in info: data_token.dims['channels'] = str(info['channels'])
            data_token.dims['format'] = default_format
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
       ex: depth=8,d'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'DepthService: Returns an Image with converted depth per pixel, arg = depth,method[,format]'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):
        ms = 'f|F|d|D|t|T|e|E'.split('|')
        ds = '8|16|32|64'.split('|')
        fs = ['u', 's', 'f']
        f=None
        try: 
            d,m,f = arg.lower().split(',', 2)
        except ValueError:
            d,m = arg.lower().split(',', 1)

        if not d in ds:
            raise IllegalOperation('Depth service: depth is unsupported: %s'%d )

        if not m in ms:
            raise IllegalOperation('Depth service: method is unsupported: %s'%m )

        if f is not None and f not in fs:
            raise IllegalOperation('Depth service: format is unsupported: %s'%f )


        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.depth_' + arg)
        log.debug('Depth service: ' + ifile + ' to '+ ofile +' with [' + arg + ']')
        
        if data_token.histogram is not None:
            ohist = self.server.getOutFileName(ifile, '.histogram_depth_' + arg)

        if not os.path.exists(ofile):
            extra=['-multi', '-depth', arg]
            if data_token.histogram is not None:
                extra.extend([ '-ihst', data_token.histogram, '-ohst', ohist])
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=extra)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'depth'     in info: data_token.dims['depth']     = str(info['depth'])
            if 'pixelType' in info: data_token.dims['pixelType'] = str(info['pixelType'])
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        if data_token.histogram is not None:
            data_token.histogram = ohist                    
        #else:
        #    data_token.histogram = None
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
    def __repr__(self):
        return 'TileService: Returns a tile, arg = l,tnx,tny,tsz. All values are in range [0..N]'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        '''arg = l,tnx,tny,tsz'''

        l=0; tnx=0; tny=0; tsz=512;
        vs = arg.split(',', 4)
        if len(vs)>0 and vs[0].isdigit():   l = int(vs[0])
        if len(vs)>1 and vs[1].isdigit(): tnx = int(vs[1])
        if len(vs)>2 and vs[2].isdigit(): tny = int(vs[2])
        if len(vs)>3 and vs[3].isdigit(): tsz = int(vs[3])
        log.debug( 'TileService: l:%d, tnx:%d, tny:%d, tsz:%d' % (l, tnx, tny, tsz) )

        # if input image is smaller than the requested tile size
        try:
            if not data_token.dims is None:
                skip = True
                if   'width'  in data_token.dims and int(data_token.dims['width'])>tsz:  skip = False
                elif 'height' in data_token.dims and int(data_token.dims['height'])>tsz: skip = False
                if skip: return data_token
        finally:
            pass

        # construct a sliced filename
        ifname    = self.server.getInFileName( data_token, image_id )
        base_name = self.server.getOutFileName( '%s.tiles/%d'%(ifname, tsz), '' )
        ofname    = '%s_%.3d_%.3d_%.3d.tif' % (base_name, l, tnx, tny)
        test_tile = '%s_%.3d_%.3d_%.3d.tif' % (base_name, 0, 0, 0)
        hist_name = self.server.getOutFileName( '%s.tiles/%s_histogram'%(ifname, tsz), '' )
        #hstl_name = '%s_lock'%(hist_name)
        hstl_name = hist_name

        # tile the image
        tiles_name = '%s.tif' % (base_name)
        if not os.path.exists(hist_name):
            with imgcnv.Locks(ifname, hstl_name) as l:
                if l.locked:
                    params = ['-tile', str(tsz), '-ohst', hist_name]
                    log.debug('Generate tiles: from %s to %s with %s' % (ifname, tiles_name, params) )
                    imgcnv.convert(ifname, tiles_name, fmt=default_format, extra=params )
                else:
                    log.debug('IS locking failed for %s'%(hist_name) )

        with imgcnv.Locks(hstl_name) as l:
            log.debug("IS Tile RL %s"%(hist_name))
            pass
        if os.path.exists(ofname):
            try:
                info = self.server.getImageInfo(filename=ofname)
                if 'width'  in info: data_token.dims['width']  = str(info['width'])
                if 'height' in info: data_token.dims['height'] = str(info['height'])
                data_token.dims['pages'] = '1'
                data_token.dims['zsize'] = '1'
                data_token.dims['tsize'] = '1'
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
    def __repr__(self):
        return 'ProjectMaxService: Returns an Image composed of all input planes by MAX'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.projectmax')
        log.debug('ProjectMax service: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-projectmax'])

        data_token.dims['pages']  = '1'
        data_token.dims['zsize']  = '1'
        data_token.dims['tsize']  = '1'
        data_token.dims['format'] = default_format

        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class ProjectMinService(object):
    '''Provide an image combined of all input planes by MIN
       ex: projectmin'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'ProjectMinService: Returns an Image composed of all input planes by MIN'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.projectmin')
        log.debug('ProjectMin service: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-projectmin'])

        data_token.dims['pages']  = '1'
        data_token.dims['zsize']  = '1'
        data_token.dims['tsize']  = '1'
        data_token.dims['format'] = default_format

        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class NegativeService(object):
    '''Provide an image negative
       ex: negative'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'NegativeService: Returns an Image negative'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.negative')
        log.debug('NegativeService service: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-negative', '-multi'])

        data_token.dims['format'] = default_format
        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class DeinterlaceService(object):
    '''Provides a deinterlaced image
       ex: deinterlace'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'DeinterlaceService: Returns a deinterlaced image'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.deinterlace')
        log.debug('DeinterlaceService service: ' + ifile + ' to '+ ofile )

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-deinterlace', 'avg', '-multi'])

        data_token.dims['format'] = default_format
        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class TransformService(object):
    """Provide an image transform
       arg = transform
       Available transforms are: fourier, chebyshev, wavelet, radon, edge, wndchrmcolor, rgb2hsv, hsv2rgb
       ex: transform=fourier"""
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'TransformService: Returns a transformed image, transform=fourier|chebyshev|wavelet|radon|edge|wndchrmcolor|rgb2hsv|hsv2rgb'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        arg = arg.lower()
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.transform_' + arg )
        log.debug('Transform service: ' + ifile + ' to '+ ofile +' with [' + arg + ']')

        extra = ['-multi']
        if not os.path.exists(ofile):
            transforms = {'fourier'      : ['-transform', 'fft'], 
                          'chebyshev'    : ['-transform', 'chebyshev'], 
                          'wavelet'      : ['-transform', 'wavelet'],
                          'radon'        : ['-transform', 'radon'], 
                          'edge'         : ['-filter',    'edge'],
                          'wndchrmcolor' : ['-filter',    'wndchrmcolor'], 
                          'rgb2hsv'      : ['-transform_color', 'rgb2hsv'],
                          'hsv2rgb'      : ['-transform_color', 'hsv2rgb'] }            
            
            if not arg in transforms:
                abort(400)
            
            extra.extend(transforms[arg])
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=extra)

        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class SampleFramesService(object):
    '''Returns an Image composed of Nth frames form input
       arg = frames_to_skip
       ex: sampleframes=10'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'SampleFrames: Returns an Image composed of Nth frames form input, arg=n'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        if not arg:
            raise IllegalOperation('SampleFramesService srvice: no frames to skip provided' )

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.framessampled_' + arg)
        log.debug('SampleFramesService: ' + ifile + ' to '+ ofile +' with [' + arg + ']')

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-multi', '-sampleframes', arg])

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'pages' in info: data_token.dims['pages']  = str(info['pages'])
            data_token.dims['zsize']  = '1'
            data_token.dims['tsize']  = data_token.dims['pages']
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class FramesService(object):
    '''Returns an image composed of user defined frames form input
       arg = frames
       ex: frames=1,2,5 or ex: frames=1,-,5 or ex: frames=-,5 or ex: frames=4,-'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'FramesService: Returns an image composed of user defined frames form input, arg = frames'
    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        if not arg:
            raise IllegalOperation('FramesService srvice: no frames provided' )

        ifile = self.server.getInFileName(data_token, image_id)
        ofile = self.server.getOutFileName(ifile, '.frames_' + arg)
        log.debug('FramesService: ' + ifile + ' to '+ ofile +' with [' + arg + ']')

        if not os.path.exists(ofile):
            imgcnv.convert(ifile, ofile, fmt=default_format, extra=['-multi', '-page', arg])

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'pages' in info: data_token.dims['pages']  = str(info['pages'])
            data_token.dims['zsize']  = '1'
            data_token.dims['tsize']  = '1'
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(fname=ofile, format=default_format)
        return data_token

class RotateService(object):
    '''Provides rotated versions for requested images:
       arg = angle
       At this moment only supported values are 90, -90, 270 and 180
       ex: rotate=90'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'RotateService: Returns an Image rotated as requested, arg = angle'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        log.debug('Service - Rotate: ' + arg )

        ang = 0
        try:
            ang = int(arg)
        except:
            raise IllegalOperation('Rotate service: argument is incorrect' )

        if not (ang==90 or ang==-90 or ang==270 or ang==180):
            raise IllegalOperation('Rotate service: angle value not yet supported' )

        if ang==270: ang=-90

        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, ('.rotated_%d' % (ang)) )
        log.debug('Rotate service: ' + ifile + ' to ' + ofile)
        if ang==0: ofile = ifile

        if not os.path.exists(ofile):
            if not imgcnv.supported(ifile):
                data_token.setHtmlErrorNotSupported()
                return data_token
            params = ['-multi', '-rotate', '%d'%ang]
            imgcnv.convert( ifile, ofile, fmt=default_format, extra=params)

        try:
            info = self.server.getImageInfo(filename=ofile)
            if 'width' in info:  data_token.dims['width']  = str(info['width'])
            if 'height' in info: data_token.dims['height'] = str(info['height'])
            data_token.dims['format'] = default_format
        finally:
            pass

        data_token.setImage(ofile, format=default_format)
        return data_token

################################################################################
# Specific Image Services
################################################################################

class BioFormatsService(object):
    '''Provides BioFormats conversion to OMETIFF
       ex: bioformats'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'BioFormatsService: Returns an Image in OME TIFF format'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    
    def resultFilename(self, image_id, data_token):
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.ome.tif' )
        return ofile        

    def action(self, image_id, data_token, arg):

        if not bioformats.installed(): return data_token
        ifile = self.server.getInFileName( data_token, image_id )
        ofile = self.server.getOutFileName( ifile, '.ome.tif' )

        bfinfo = None
        if not os.path.exists(ofile):
            log.debug('BioFormats service: ' + ifile + ' to ' + ofile)
            try:
                original = self.server.originalFileName(image_id)
                bioformats.convert( ifile, ofile, original )

                if os.path.exists(ofile) and imgcnv.supported(ofile):
                    orig_info = bioformats.info(ifile, original)
                    bfinfo = imgcnv.info(ofile)
                    if 'width' in bfinfo and 'width' in orig_info:
                        if 'format' in orig_info: bfinfo['format'] = orig_info['format']
                    bfinfo['converted_file'] = ofile
                    self.server.setImageInfo( id=image_id, info=bfinfo )

            except:
                log.error ('Error running BioFormats'+ str( sys.exc_info()[0] ) )

        if not os.path.exists(ofile) or not imgcnv.supported(ofile):
            return data_token

        if bfinfo is None: bfinfo = self.server.getImageInfo(ident=image_id)
        data_token.dims = bfinfo
        data_token.setImage(ofile, format=default_format)
        return data_token

class UriService(object):
    '''Fetches an image from remote URI and passes it from further processing, Note that the URI must be encoded!
       Example shows encoding for: http://www.google.com/intl/en_ALL/images/logo.gif
       arg = URI
       ex: uri=http%3A%2F%2Fwww.google.com%2Fintl%2Fen_ALL%2Fimages%2Flogo.gif'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'UriService: Fetches an image from remote URL and passes it from further processing, url=http%3A%2F%2Fwww.google.com%2Fintl%2Fen_ALL%2Fimages%2Flogo.gif.'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass
    def action(self, image_id, data_token, arg):

        url = unquote(arg)
        log.debug('URI service: [' + url +']' )
        url_filename = quote(url, "")
        ofile = self.server.getOutFileName( 'url_', url_filename )

        if not os.path.exists(ofile):
            log.debug('URI service: Fetching to file - ' + str(ofile) )
            #resp, content = request(url)
            from bq.util.request import Request
            content = Request(url).get ()
            log.debug ("URI service: result header=" + str(resp))
            if int(resp['status']) >= 400:
                data_token.setHtml('URI service: requested URI could not be fetched...')
            else:
                f = open(ofile, 'wb')
                f.write(content)
                f.flush()
                f.close()

        data_token.setFile( ofile )
        data_token.outFileName = url_filename
        #data_token.setImage(fname=ofile, format=default_format)

        if not imgcnv.supported(ofile):
            #data_token.setHtml('URI service: Downloaded file is not in supported image format...')
            data_token.setHtmlErrorNotSupported()
        else:
            data_token.dims = self.server.getImageInfo(filename=ofile)

        log.debug('URI service: ' + str(data_token) )
        return data_token

class MaskService(object):
    '''Provide images with mask preview:
       arg = mask_id
       ex: mask=999'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'MaskService: Returns an Image with mask superimposed, arg = mask_id'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, mask_id):
        #http://localhost:8080/imgsrv/images/4?mask=5
        log.debug('Service - Mask: ' + mask_id )

        ifname = self.server.getInFileName(data_token, image_id)
        ofname = self.server.getOutFileName( ifname, '.mask_' + str(mask_id) )
        mfname = self.server.imagepath(mask_id)

#        if not os.path.exists(ofname):
#
#            log.debug( 'Mask service: ' + ifname + ' + ' + mfname )
#
#            # PIL has problems loading 16 bit multiple channel images -> pre convert
#            imgcnv.convert( ifname, ofname, fmt='png', extra='-norm -page 1')
#            im = PILImage.open ( ofname )
#            # convert input image into grayscale and color it with mask
#            im = im.convert("L")
#            im = im.convert("RGB")
#
#            # get the mask image and then color it appropriately
#            im_mask = PILImage.open ( mfname )
#            im_mask = im_mask.convert("L")
#
#            # apply palette with predefined colors
#            im_mask = im_mask.convert("P")
#            mask_pal = im_mask.getpalette()
#            #mask_pal[240:242] = (0,0,255)
#            #mask_pal[480:482] = (0,255,0)
#            #mask_pal[765:767] = (255,0,0)
#            mask_pal[240] = 0
#            mask_pal[241] = 0
#            mask_pal[242] = 255
#            mask_pal[480] = 0
#            mask_pal[481] = 255
#            mask_pal[482] = 0
#            mask_pal[765] = 255
#            mask_pal[766] = 0
#            mask_pal[767] = 0
#            im_mask.putpalette(mask_pal)
#            im_mask = im_mask.convert("RGB")
#
#            # alpha specify the opacity for merging [0,1], 0.5 is 50%-50%
#            im = PILImage.blend(im, im_mask, 0.5 )
#            im.save(ofname, "TIFF")
#
#        data_token.setImage(fname=ofname, format=default_format)
        return data_token

################################################################################
# New Image Services
################################################################################

class CreateImageService(object):
    '''Create new images'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'CreateImageService: Create new images, arg = ...'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        '''arg := w,h,z,t,c,d'''
        # requires: w,h,z,t,c,d - width,hight,z,t,channles,depth/channel
        # defaults: -,-,1,1,1,8
        # this action will create image without consolidated original file
        # providing later write access to the planes of an image

        if not arg:
            raise IllegalOperation('Create service: w,h,z,t,c,d are all needed')

        xs,ys,zs,ts,cs,ds = arg.split(',', 5)
        x=0; y=0; z=0; t=0; c=0; d=0
        if xs.isdigit(): x = int(xs)
        if ys.isdigit(): y = int(ys)
        if zs.isdigit(): z = int(zs)
        if ts.isdigit(): t = int(ts)
        if cs.isdigit(): c = int(cs)
        if ds.isdigit(): d = int(ds)

        if x<=0 or y<=0 or z<=0 or t<=0 or c<=0 or d<=0 :
            raise IllegalOperation('Create service: w,h,z,t,c,d are all needed')

        image_id = self.server.nextFileId()
        xmlstr = self.server.setFileInfo( id=image_id, width=x, height=y, zsize=z, tsize=t, channels=c, depth=d )

        response = etree.Element ('response')
        image    = etree.SubElement (response, 'image')
        image.attrib['src'] = '/imgsrv/'+str(image_id)
        image.attrib['x'] = str(x)
        image.attrib['y'] = str(y)
        image.attrib['z'] = str(z)
        image.attrib['t'] = str(t)
        image.attrib['ch'] = str(c)
        xmlstr = etree.tostring(response)

        data_token.setXml(xmlstr)

        #now we have to pre-create all the planes
        ifname = self.server.imagepath(image_id)
        ofname = self.server.getOutFileName( ifname, '.' )
        creastr = '%d,%d,1,1,%d,%d'%(x, y, c, d)

        for zi in range(z):
            for ti in range(t):
                imgcnv.convert(ifname, ofname+'0-0,0-0,%d-%d,%d-%d'%(zi,zi,ti,ti), fmt=default_format, extra=['-create', creastr] )

        return data_token

class SetSliceService(object):
    '''Write a slice into an image :
       arg = x,y,z,t,c
       Each position may be specified as a range
       empty params imply entire available range'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'SetSliceService: Writes a slice into an image, arg = x,y,z,t,c'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''

        vs = arg.split(',', 4)

        z1=-1; z2=-1
        if len(vs)>2 and vs[2].isdigit():
            xs = vs[2].split('-', 2)
            if len(xs)>0 and xs[0].isdigit(): z1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): z2 = int(xs[1])
            if len(xs)==1: z2 = z1

        t1=-1; t2=-1
        if len(vs)>3 and vs[3].isdigit():
            xs = vs[3].split('-', 2)
            if len(xs)>0 and xs[0].isdigit(): t1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): t2 = int(xs[1])
            if len(xs)==1: t2 = t1

        x1=-1; x2=-1
        if len(vs)>0 and vs[0]:
            xs = vs[0].split('-', 2)
            if len(xs)>0 and xs[0].isdigit(): x1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): x2 = int(xs[1])

        y1=-1; y2=-1
        if len(vs)>1 and vs[1]:
            xs = vs[1].split('-', 2)
            if len(xs)>0 and xs[0].isdigit(): y1 = int(xs[0])
            if len(xs)>1 and xs[1].isdigit(): y2 = int(xs[1])

        if not z1==z2 or not t1==t2:
            raise IllegalOperation('Set slice service: ranges in z and t are not supported by this service')

        if not x1==-1 or not x2==-1 or not y1==-1 or not y2==-1:
            raise IllegalOperation('Set slice service: x and y are not supported by this service')

        if not x1==x2 or not y1==y2:
            raise IllegalOperation('Set slice service: ranges in x and y are not supported by this service')

        if not data_token.isFile():
            raise IllegalOperation('Set slice service: input image is required')

        # construct a sliced filename
        gfname = self.server.imagepath(image_id) # this file should not exist, otherwise, exception!
        if os.path.exists(gfname):
            raise IllegalOperation('Set slice service: this image is read only')

        ifname = data_token.data
        ofname = self.server.getOutFileName( gfname, '.%d-%d,%d-%d,%d-%d,%d-%d' % (x1+1,x2+1,y1+1,y2+1,z1+1,z2+1,t1+1,t2+1) )

        log.debug('Slice service: to ' +  ofname )
        imgcnv.convert(ifname, ofname, fmt=default_format, extra=['-page', '1'] )

        data_token.setImage(ofname, format=default_format)
        return data_token


class CloseImageService(object):
    '''Create new images'''
    def __init__(self, server):
        self.server = server
    def __repr__(self):
        return 'CloseImageService: Closes requested image, created with CreateImageService'

    def hookInsert(self, data_token, image_id, hookpoint='post'):
        pass

    def action(self, image_id, data_token, arg):
        # closes open image (the one without id) creating such an image, composed out of multiple plains
        # disabling writing into image plains

        ofname = self.server.imagepath(image_id)

        if os.path.exists(ofname):
            raise IllegalOperation('Close image service: this image is read only')

        # grab all the slices of the image and compose id as tiff
        ifiles = []
        z=0; t=0;
        params = self.server.getFileInfo(id=image_id)
        log.debug('Close service: ' +  str(params) )
        z = int(params['zsize'])
        t = int(params['tsize'])
        for ti in range(t):
            for zi in range(z):
                ifname = self.server.getOutFileName( self.server.imagepath(image_id), '.0-0,0-0,%d-%d,%d-%d'%(zi,zi,ti,ti) )
                log.debug('Close service: ' +  ifname )
                ifiles.append(ifname)
        imgcnv.convert_list(ifiles, ofname, fmt=default_format, extra=['-multi'] )

        data_token.setImage(ofname, format=default_format)
        return data_token


################################################################################
# ImageServer
################################################################################

#
#  /imgsrc/1?thumbnail&equalized
#  imageID | thumbnail | equalized
#  equalize (thumbnail (getimage(1)))
#

class ImageServer(object):
    def __init__(self, image_dir, work_dir, data_dir, server_url):
        '''Start an image server, using local dir imagedir,
        and loading extensions as methods'''
        #super(ImageServer, self).__init__(image_dir, server_url)
        self.imagedir = image_dir
        self.workdir = work_dir
        self.datadir = data_dir
        self.cache = FileCache()
        self.url = server_url

        self.services = {}
        self.services = { 'services'     : ServicesService(self),
                          'formats'      : FormatsService(self),
                          'info'         : InfoService(self),
                          'dims'         : DimService(self),
                          'meta'         : MetaService(self),
                          'filename'     : FileNameService(self),
                          'localpath'    : LocalPathService(self),
                          'slice'        : SliceService(self),
                          'format'       : FormatService(self),
                          'resize'       : ResizeService(self),
                          'thumbnail'    : ThumbnailService(self),
                          'default'      : DefaultService(self),
                          'roi'          : RoiService(self),
                          'remap'        : RemapService(self),
                          'fuse'         : FuseService(self),
                          'depth'        : DepthService(self),
                          'rotate'       : RotateService(self),
                          'tile'         : TileService(self),
                          'uri'          : UriService(self),
                          'projectmax'   : ProjectMaxService(self),
                          'projectmin'   : ProjectMinService(self),
                          'negative'     : NegativeService(self),
                          'deinterlace'  : DeinterlaceService(self),
                          'transform'    : TransformService(self),
                          'sampleframes' : SampleFramesService(self),
                          'frames'       : FramesService(self),
                          'mask'         : MaskService(self),
                          'create'       : CreateImageService(self),
                          'setslice'     : SetSliceService(self),
                          'close'        : CloseImageService(self),
                          'bioformats'   : BioFormatsService(self)
                        }

        # check if the imgcnv is properly installed
        self.image_formats = imgcnv.formats()
        if not imgcnv.installed():
            raise Exception('imgcnv not installed')
        imgcnv.check_version( imgcnv_needed_version )

        # check the bioformats version if installed
        if bioformats.installed():
            if not bioformats.ensure_version( bioformats_needed_version ):
                log.debug('Bioformats needs update! Has: '+bioformats.version()['full']+' Needs: '+ bioformats_needed_version)
                #raise Exception('Bioformats needs update! Has: '+bioformats.version()['full']+' Needs: '+ bioformats_needed_version)

    def tmpnam(ext):
        'create a tmp filename with ext'
        pass

    def imagepath(self, ident):
        return blob_service.localpath(ident)

    def originalFileName(self, ident):
        return blob_service.original_name(ident)

    def getFileInfo(self, id=None, filename=None):
        if id==None and filename==None: return {}
        if filename==None: filename = self.imagepath(id)
        #filename += '.info'
        filename = self.getOutFileName( filename, '.info' )
        if not os.path.exists(filename): return {}

        tree = etree.parse(filename)
        elem = tree.getroot()
        image = elem.find('image')
        return image.attrib

    def setFileInfo(self, id=None, filename=None, **kw):
        if id==None and filename==None: return {}
        if filename==None: filename = self.imagepath(id)
        #filename += '.info'
        filename = self.getOutFileName( filename, '.info' )

        response = etree.Element ('response')
        image    = etree.SubElement (response, 'image')

        image.attrib['src'] = '/imgsrv/'+str(id)
        for attr,val in kw.items():
          image.attrib[attr] = str(val)

        etree.ElementTree(response).write(filename)
        return etree.tostring(response)

    def fileInfoCached(self, id=None, filename=None):
        if id==None and filename==None: return False
        if filename==None: filename = self.imagepath(id)
        #filename += '.info'
        filename = self.getOutFileName( filename, '.info' )
        return os.path.exists(filename)

    def updateFileInfo(self, id=None, filename=None, **kw):
        pars = self.getFileInfo(id=id, filename=filename)
        for attr,val in kw.items():
          pars[attr] = str(val)
        xmlstr = self.setFileInfo(id=id, filename=filename, **dict(pars))
        return xmlstr

    def getImageInfo(self, ident=None, data_token=None, filename=None):
        if ident==None and filename==None: return {}
        if filename==None: filename = self.imagepath(ident)

        return_token = data_token is not None
        infofile = self.getOutFileName( filename, '.info' )

        info = {}
        if os.path.exists(infofile):
            info = self.getFileInfo(id=ident, filename=filename)
        else:
            # If file info is not cached, get it and cache!

            # try imgcnv
            if imgcnv.supported(filename):
                info = imgcnv.info(filename)

            # if not decoded try bioformats
            if 'width' not in info and ident is not None:
                original = self.originalFileName(ident)
                if data_token is None: data_token = ProcessToken()
                data_token.setImage(filename, format=default_format)
                testfile = self.services['bioformats'].resultFilename(ident, data_token)                    
                if os.path.exists(testfile): 
                    info = self.getImageInfo(filename=testfile)
                    data_token.setImage(testfile, format='tiff')
                    data_token.dims = info
                elif bioformats.supported(filename, original):
                    data_token = self.services['bioformats'].action (ident, data_token, '')
                    if not data_token.dims is None:
                        info = data_token.dims

            if not 'filesize' in info:
                fsb = os.path.getsize(filename)
                info['filesize'] = str(fsb)

            if 'width' in info:
                self.setImageInfo( id=ident, filename=filename, info=info )

        if not 'filesize' in info:
            fsb = os.path.getsize(filename)
            info['filesize'] = str(fsb)

        if 'width' in info:
            if not 'tsize'      in info: info['tsize']      = '1'
            if not 'zsize'      in info: info['zsize']      = '1'
            if not 'dimensions' in info: info['dimensions'] = 'X Y C Z T'
            if not 'format'     in info: info['format']     = default_format
            if not 'pages'      in info: info['pages']      = str( int(info['tsize']) * int(info['zsize']) )

        if not 'pixelFormat' in info and 'pixelType' in info and 'depth' in info:
            ppd = int(info['depth'])
            ppt = int(info['pixelType'])
            pxtypes = { 0: 'unknown', 1: 'unsigned', 2:'signed', 3:'float' }
            pxdepths = { 8 : ['unknown8',  'uint8',  'int8',  'unknown8'],
                         16: ['unknown16', 'uint16', 'int16', 'unknown16'],
                         32: ['unknown32', 'uint32', 'int32', 'single'],
                         64: ['unknown64', 'uint64', 'int64', 'double'] }
            info['pixelType'] = pxtypes[ppt]
            pxf = '%s%d'%(pxtypes[ppt], ppd)
            if ppd in pxdepths:
                pxf = pxdepths[ppd][ppt]
            info['pixelFormat'] = pxf
            # backwards compatibility, store pixelFormat if it was not found
            #self.setImageInfo( id=id, filename=filename, info=info )

        if return_token is True:
            if 'converted_file' in info:
                data_token.setImage(info['converted_file'], format=default_format)
            data_token.dims = info
            return data_token
        return info


    def setImageInfo(self, id=None, data_token=None, info=None, filename=None):
        if info is None: return
        if not 'tsize'      in info: info['tsize']      = '1'
        if not 'zsize'      in info: info['zsize']      = '1'
        if not 'dimensions' in info: info['dimensions'] = 'X Y C Z T'
        if not 'format'     in info: info['format']     = default_format
        if not 'pages'      in info: info['pages']      = str( int(info['tsize']) * int(info['zsize']) )
        if 'width' in info:
            self.setFileInfo( id=id, filename=filename, **info )

    def fileIsTIFF(self, filename=None, data_token=None):
        info = None
        if not data_token is None and not data_token.dims is None:
            info = data_token.dims
        else:
            info = self.getImageInfo(filename=filename)

        if info is None: return False
        if not 'format' in info: return False
        if info['format'].lower() == default_format: return True
        return False

    def ensureWorkPath(self, path):
        # change ./imagedir to ./workdir if needed
        #drv, path = os.path.splitdrive(path) # dima: does not seem necessary?
        if path.find( self.workdir ) == -1:
            if path.find (self.imagedir)>=0:
                path = path.replace(self.imagedir, self.workdir, 1)
            elif path.find(self.datadir)>=0:
                path = path.replace(self.datadir, self.workdir, 1)
            else:
                if path[0]=='/' or path=='\\':
                    path=path[1:]
                path = os.path.join(self.workdir , path)
        #make sure that the path directory exists
        _mkdir( os.path.dirname(path) )
        return path

    def getInFileName(self, data_token, image_id):
        # if there is no image file input, request the first slice
        if not data_token.isFile():
            data_token.setFile( self.imagepath(image_id) )
        return data_token.data

    def getOutFileName(self, infilename, appendix):
        ofile = self.ensureWorkPath(infilename)
        ofile = os.path.relpath(ofile, self.workdir)
        log.debug('Output filename: %s'%ofile)
        return ofile + appendix

    # def addImage(self, src, name, ownerId = None, permission = None, **kw):
    #     """Add image:
    #         1. Store original in unique ID ending in .orig
    #         2. Store canonical format i.e. raw (use link)
    #         3. Store preprocessed image:
    #              a) thumbnail
    #     """
    #     #log.debug('IMGSRV: Adding image: ' + str(src.name) + ' ' + str(name) )
    #     info = {}

    #     if 'format' in kw and kw['format'] == 'raw':
    #         image_id, origpath = self.nextEmptyBlob()

    #         tmppath = self.ensureWorkPath(origpath)
    #         workfile = open(tmppath, "wb")
    #         shutil.copyfileobj(src, workfile)
    #         workfile.close()

    #         #-raw     - reads RAW image with w,h,c,d,p,e,t, ex: -raw 100,100,3,8,10,0,uint8\n
    #         num_pages = int(kw['zsize'])*int(kw['tsize'])
    #         rawargs = '%s,%s,%s,%s,%s,%s,%s'%( kw['width'], kw['height'], kw['channels'], kw['depth'], num_pages, kw['endian'], kw['type'] )
    #         imgcnv.convert(tmppath, origpath, fmt=default_format, extra='-multi -raw '+rawargs)
    #         self.loginfo (name, image_id)

    #         sha1 = file_hash_SHA1( origpath )
    #         imgtype = default_format
    #         flocal = origpath[len(self.imagedir)+1:]

    #         blobdb.updateFile (dbid = image_id, original = name, uri = self.geturi(image_id), owner = ownerId, perm = permission, fhash=sha1, ftype=imgtype, flocal=flocal)

    #     else:
    #         image_id, origpath = self.storeBlob(src, name, ownerId, permission)

    #     # if it's not supported, fail
    #     info = self.getImageInfo(id=image_id)
    #     if info is None or not hasattr(info, '__iter__') or not 'width' in info:
    #         log.debug('############################################')
    #         log.debug('Image format is NOT SUPPORTED!!!!!!!!!!!!!!!')
    #         log.debug('############################################')
    #         return None, None, None, None, None, None, None

    #     # in case the user supplied image physical parameters, store them and use over the embedded
    #     if 'width'      in kw: info['width']      = kw['width']
    #     if 'height'     in kw: info['height']     = kw['height']
    #     if 'channels'   in kw: info['channels']   = kw['channels']
    #     if 'zsize'      in kw: info['zsize']      = kw['zsize']
    #     if 'tsize'      in kw: info['tsize']      = kw['tsize']
    #     if 'dimensions' in kw: info['dimensions'] = kw['dimensions']

    #     self.setImageInfo( id=image_id, info=info )
    #     image_path = self.imagepath(image_id)
    #     log.debug( 'New image: %d %s %s,%s,%s,%s,%s'%( image_id, image_path, info['width'], info['height'], info['channels'], info['zsize'], info['tsize'] )  )
    #     return image_id, image_path, info['width'], info['height'], info['channels'], info['zsize'], info['tsize'
#                                                                                                          ]

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
            service = False

        #if not service:
        #    raise UnknownService(method)
        r = imgfile
        if service:
            r = service.action (image_id, imgfile, argument)
        return r

    def process(self, url, ident, userId, **kw):
        log.debug ('')
        #log.debug ('headers:'+ str(cherrypy.request.headers))
        log.debug ('')
        log.debug ('--------------------------------------------------')
        log.debug (">>>> Request url: %s" % url)
        query = getQuery4Url(url)
        log.debug (">>>> Query: %s by %s" % (query, userId)  )
        
        os.chdir(self.workdir)
        log.debug('Current path: %s'%(self.workdir))

        # init the output to a simple file
        data_token = ProcessToken()

        if id != -1:
            try:
                #intid = int(id)
                pass
            except:
                data_token.setHtmlErrorNotFound()
                return data_token

            #if not self.accessPermission(id, userId):
            #    data_token.setHtmlErrorUnauthorized()
            #    return data_token

            if not blob_service.file_exists(ident):
                data_token.setHtmlErrorNotFound()
                return data_token

            data_token.setFile( self.imagepath(ident) )

            if len(query)>0:
                # this will pre-convert the image if it's not supported by the imgcnv
                # and also set the proper dimensions info
                data_token = self.getImageInfo(ident=ident, data_token=data_token)

                # dima: this call seems ambiguous now, but some bugs appeared, call it anyways with a small test
                #if 'width' not in data_token.dims:
                #    if not imgcnv.supported( data_token.data ):
                #        data_token = self.services['bioformats'].action (ident, data_token, '')

            if len(query)>0 and (not 'width' in data_token.dims):
                #data_token.setHtml('File is not in supported image format...')
                data_token.setHtmlErrorNotSupported()
                return data_token

        try:
            #process all the requested operations
            for action,args in query:
                data_token = self.request(action, ident, data_token, args)
                if data_token.isHttpError():
                    break

            # test output, if it is a file but it does not exist, set 404 error
            data_token.testFile()

            # if the output is a file but not an image or no processing was done to it
            # set to the original file name
            if data_token.isFile() and not data_token.isImage() and not data_token.hasFileName():
                data_token.contentType = 'application/octet-stream'
                data_token.outFileName = self.originalFileName(ident)

            # if supplied file name overrides filename
            for action,args in query:
                if (action.lower() == 'filename'):
                    data_token.outFileName = args
                    break

            return data_token

        except DataSrvException, e:
            log.error ('error while handling actions'+ str(e))

        return data_token

#    def execute(self, method, image_id, userId, arg):
#        '''Directly execute a method on an image id'''
#        data_token = ProcessToken()
#
#        if (self.accessPermission(image_id, userId) == False):
#            data_token.setHtmlErrorUnauthorized()
#            return data_token
#
#        if (blob_service.file_exists(image_id) == False):
#            data_token.setHtmlErrorNotFound()
#            return data_token
#
#        data_token.setImage( self.imagepath(image_id), default_format )
#
#        # this will pre-convert the image if it's not supported by the imgcnv
#        # and also set the proper dimensions info
#        data_token = self.getImageInfo(id=image_id, data_token=data_token)
#        if not imgcnv.supported( data_token.data ):
#            data_token = self.services['bioformats'].action (image_id, data_token, '')
#
#        if not 'width' in data_token.dims:
#            data_token.setHtml('File is not in supported image format...')
#            return data_token
#
#        service = self.services[method]
#        if not service:
#            raise UnknownService(method)
#        r =  service.action (image_id, data_token, arg)
#        return data_token.data
#
#
#    def upload_file(self):
#        pass
