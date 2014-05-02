# converter_imgcnv.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" BioImageConvert command line converter
"""

__module__    = "converter_imgcnv"
__author__    = "Dmitry Fedorov"
__version__   = "1.3"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import logging
import os.path
from lxml import etree
#from subprocess import call
from .locks import Locks

from tg import config
#from collections import OrderedDict
from bq.util.compat import OrderedDict

from . import misc
from .converter_base import ConverterBase, Format


thumbnail_cmd = config.get('bisque.image_service.thumbnail_command', '-depth 8,d -page 1 -display')
log = logging.getLogger('bq.image_service.converter_imgcnv')

################################################################################
# ConverterBase
################################################################################

class ConverterImgcnv(ConverterBase):
    installed = False
    version = None
    installed_formats = None
    CONVERTERCOMMAND = 'imgcnv' if os.name != 'nt' else 'imgcnv.exe'
    info_map = {
        'width'      : 'image_num_x',
        'height'     : 'image_num_y',
        'zsize'      : 'image_num_z',
        'tsize'      : 'image_num_t',
        'channels'   : 'image_num_c',
        'pages'      : 'image_num_p',
        'format'     : 'format',
        'pixelType'  : 'image_pixel_format',
        'depth'      : 'image_pixel_depth',
        'endian'     : 'endian',
        'dimensions' : 'dimensions'
    }

#     #######################################
#     # Init
#     #######################################
#
#     @classmethod
#     def init(cls):
#         #ConverterBase.init.im_func(cls)
#         ConverterBase.init(cls)
#         cls.get_formats()

    #######################################
    # Version and Installed
    #######################################

    @classmethod
    def get_version (cls):
        '''returns the version of command line utility'''
        o = misc.run_command( [cls.CONVERTERCOMMAND, '-v'] )
        try:
            d = [int(s) for s in o.split('.', 1)]
        except ValueError:
            log.error ('imgcnv is too old, cannot proceed')
            raise Exception('imgcnv is too old, cannot proceed')
        d.append(0)
        return {
            'full': '.'.join([str(i) for i in d]),
            'numeric': d,
            'major': d[0],
            'minor': d[1],
            'build': d[2]
        }

    #######################################
    # Formats
    #######################################

    @classmethod
    def get_formats(cls):
        '''inits supported file formats'''
        if cls.installed_formats is None:
            formats_xml = misc.run_command( [cls.CONVERTERCOMMAND, '-fmtxml'] )
            formats = etree.fromstring( '<formats>%s</formats>'%formats_xml )

            cls.installed_formats = OrderedDict()
            codecs = formats.xpath('//codec')
            for c in codecs:
                try:
                    name = c.get('name')
                    fullname = c.xpath('tag[@name="fullname"]')[0].get('value', '')
                    exts = c.xpath('tag[@name="extensions"]')[0].get('value', '').split('|')
                    reading = len(c.xpath('tag[@name="support" and @value="reading"]'))>0
                    writing = len(c.xpath('tag[@name="support" and @value="writing"]'))>0
                    multipage = len(c.xpath('tag[@name="support" and @value="writing multiple pages"]'))>0
                    metadata = len(c.xpath('tag[@name="support" and @value="reading metadata"]'))>0 or len(c.xpath('tag[@name="support" and @value="writing metadata"]'))>0
                    samples_min = misc.safeint(c.xpath('tag[@name="min-samples-per-pixel"]')[0].get('value', '0'))
                    samples_max = misc.safeint(c.xpath('tag[@name="max-samples-per-pixel"]')[0].get('value', '0'))
                    bits_min = misc.safeint(c.xpath('tag[@name="min-bits-per-sample"]')[0].get('value', '0'))
                    bits_max = misc.safeint(c.xpath('tag[@name="max-bits-per-sample"]')[0].get('value', '0'))
                except IndexError:
                    continue
                cls.installed_formats[name.lower()] = Format(
                    name=name,
                    fullname=fullname,
                    ext=exts,
                    reading=reading,
                    writing=writing,
                    multipage=multipage,
                    metadata=metadata,
                    samples=(samples_min,samples_max),
                    bits=(bits_min,bits_max)
                )

    #######################################
    # Supported
    #######################################

    def supported(self, ifnm):
        '''return True if the input file format is supported'''
        log.debug('Supported for: %s', ifnm )
        supported = self.run_read(ifnm, [self.CONVERTERCOMMAND, '-supported', '-i', ifnm]) 
        return supported.startswith('yes')


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    def meta(self, ifnm, series=0):
        '''returns a dict with file metadata'''
        log.debug('Meta for: %s', ifnm)
        if not self.installed:
            return {}

        meta = self.run_read(ifnm, [self.CONVERTERCOMMAND, '-meta', '-i', ifnm] )
        if meta is None:
            return {}
        rd = {}
        for line in meta.splitlines():
            if not line: continue
            try:
                tag, val = [ l.lstrip() for l in line.split(':', 1) ]
            except ValueError:
                continue
            rd[tag] = misc.safetypeparse(val.replace('\n', ''))

        if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
            rd['image_num_t'] = rd['image_num_p']

        return rd

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    def info(self, ifnm, series=0):
        '''returns a dict with file info'''
        log.debug('Info for: %s', ifnm)
        if not self.installed:
            return {}
        if not os.path.exists(ifnm):
            return {}

        info = self.run_read(ifnm, [self.CONVERTERCOMMAND, '-info', '-i', ifnm] )
        if info is None:
            return {}
        rd = {}
        for line in info.splitlines():
            if not line: continue
            try:
                tag, val = [ l.strip() for l in line.split(':',1) ]
            except ValueError:
                continue
            if tag not in self.info_map:
                continue
            rd[self.info_map[tag]] = misc.safetypeparse(val.replace('\n', ''))

        # change the image_pixel_format output, convert numbers to a fully descriptive string
        if isinstance(rd['image_pixel_format'], (long, int)):
            pf_map = {
                1: 'unsigned integer', 
                2: 'signed integer', 
                3: 'floating point'
            }
            rd['image_pixel_format'] = pf_map[rd['image_pixel_format']]

        rd.setdefault('image_num_z', 1)
        rd.setdefault('image_num_t', 1)
        rd.setdefault('image_num_p', 1)
        if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
            rd['image_num_t'] = rd['image_num_p']
        return rd


    #######################################
    # Conversion
    #######################################

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=[]):
        '''converts a file and returns output filename'''
        log.debug('convert: [%s] -> [%s] into %s for series %s with [%s]', ifnm, ofnm, fmt, series, extra)
        command = ['-i', ifnm]
        if ofnm is not None:
            command.extend (['-o', ofnm])
        if fmt is not None:
            command.extend (['-t', fmt])
            if cls.installed_formats[fmt].multipage is True:
                extra.extend(['-multi'])
            else:
                extra.extend(['-page', '1'])
        command.extend (extra)
        return cls.run(ifnm, ofnm, command )

    #def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=[]):
    #    '''converts input filename into output in OME-TIFF format'''
    #    return cls.convert(ifnm, ofnm, ['-input', ifnm, '-output', ofnm, '-format', 'OmeTiff', '-series', '%s'%series] )

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)

        command = ['-i', ifnm, '-o', ofnm, '-t', 'jpeg']
        method = kw.get('method', 'BC')
        depth = kw.get('depth', 16)
        if depth == 8:
            command.extend(thumbnail_cmd.replace('-depth 8,d', '-depth 8,f').split(' '))
        else:
            command.extend(thumbnail_cmd.split(' '))

        command.extend([ '-resize', '%s,%s,%s,AR'%(width,height,method)])
        command.extend([ '-options', 'quality 95 progressive yes'])

        return cls.run(ifnm, ofnm, command )

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        log.debug('Slice: z=%s t=%s roi=%s series=%s for [%s]', z, t, roi, series, ifnm)
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi
        info = kw['info']
        fmt = kw.get('fmt', 'bigtiff')

        command = ['-i', ifnm, '-o', ofnm, '-t', fmt]

        if t2==0: 
            t2=t1
        if z2==0: 
            z2=z1

        pages = []
        for ti in range(t1, t2+1):
            for zi in range(z1, z2+1):
                if info['image_num_t']==1:
                    page_num = zi
                elif info['image_num_z']==1:
                    page_num = ti
                elif info.get('dimensions', 'X Y C Z T').startswith('X Y C Z'):
                    page_num = (ti-1)*info['image_num_z'] + zi
                else:
                    page_num = (zi-1)*info['image_num_t'] + ti
                pages.append(page_num)

        # pages
        command.extend(['-multi', '-page', ','.join([str(p) for p in pages])])

        # roi
        if not x1==x2 or not y1==y2:
            if not x1==x2:
                if x1>0: x1 = x1-1
                if x2>0: x2 = x2-1
            if not y1==y2:
                if y1>0: y1 = y1-1
                if y2>0: y2 = y2-1
            command.extend(['-roi', '%s,%s,%s,%s' % (x1,y1,x2,y2)])

        return cls.run(ifnm, ofnm, command )

    #######################################
    # Special methods
    #######################################

    def writeHistogram(self, channels, ofnm):
        '''writes Histogram in libbioimage format'''
        log.debug('Writing histogram into: %s', ofnm )
        
        import struct
        with open(ofnm, 'wb') as f:
            f.write(struct.pack('<cccc', 'B', 'I', 'M', '1')) # header
            f.write(struct.pack('<cccc', 'I', 'H', 'S', '1')) # spec
            f.write(struct.pack('<L', channels)) # number of histograms
            # write histograms
            for c in range(channels):
                f.write(struct.pack('<cccc', 'B', 'I', 'M', '1')) # header
                f.write(struct.pack('<cccc', 'H', 'S', 'T', '1')) # spec
                
                # write bim::HistogramInternal 
                f.write(struct.pack('<H', 8)) # uint16 data_bpp; // bits per pixel
                f.write(struct.pack('<H', 1)) # uint16 data_fmt; // signed, unsigned, float
                f.write(struct.pack('<d', 0.0)) # double shift;
                f.write(struct.pack('<d', 1.0)) # double scale;
                f.write(struct.pack('<d', 0.0)) # double value_min;
                f.write(struct.pack('<d', 255.0)) # double value_max;
                
                # write data
                f.write(struct.pack('<L', 256)) # histogram size, here 256
                for i in range(256):
                    f.write(struct.pack('<Q', 100)) # histogram data, here each color has freq of 100


ConverterImgcnv.init()

