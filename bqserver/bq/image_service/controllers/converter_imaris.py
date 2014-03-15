# converter_imaris.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" Imaris command line converter
"""

__module__    = "converter_imaris"
__author__    = "Dmitry Fedorov"
__version__   = "0.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os.path
from lxml import etree
import re
import tempfile
import cStringIO as StringIO
import ConfigParser
#from collections import OrderedDict
from bq.util.compat import OrderedDict

from . import misc
from .converter_base import ConverterBase, Format
from .converter_imgcnv import ConverterImgcnv
from .locks import Locks

import logging
log = logging.getLogger('bq.image_service.converter_imaris')

################################################################################
# Misc
################################################################################

def parse_format(l):
    l = ' '.join(l.split())
    t = l.split(' ', 1)
    name = t[0]
    t = t[1].split(' - ')
    full = t[0]
    ext = t[1].strip('()').split(';')
    return (name,full,ext)

################################################################################
# ConverterImaris
################################################################################

class ConverterImaris(ConverterBase):
    installed = False
    version = None
    installed_formats = None
    CONVERTERCOMMAND = 'ImarisConvert' if os.name != 'nt' else 'ImarisConvert.exe'

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
        '''returns the version of imaris'''
        o = misc.run_command( [cls.CONVERTERCOMMAND, '-v'] )
        if o is None:
            return None

        v = {}
        for line in o.splitlines():
            if not line and not line.startswith('Imaris Convert'): continue
            m = re.match('Imaris Convert (?P<version>[\d.]+) *', line)
            try:
                v['full'] = m.group('version')
            except IndexError:
                pass

        if 'full' in v:
            d = [int(s) for s in v['full'].split('.', 2)]
            if len(d)>2:
                v['numeric'] = d
                v['major']   = d[0]
                v['minor']   = d[1]
                v['build']   = d[2]
        return v

    #######################################
    # Formats
    #######################################

    @classmethod
    def get_formats(cls):
        '''inits supported file formats'''
        if cls.installed_formats is not None:
            return

        fs = misc.run_command( [cls.CONVERTERCOMMAND, '-h'] )
        if fs is None:
            return ''

        ins = [f.strip(' ') for f in misc.between('Input File Formats are:\r\n\r\n', 'Output File Formats are:', fs).split('\r\n') if f != '']
        # version 8.0.0
        if 'Exit Codes:' in fs:
            ous = [f.strip(' ') for f in misc.between('Output File Formats are:\r\n\r\n', 'Exit Codes:', fs).split('\r\n') if f != '']
        else: # version 7.X
            ous = [f.strip(' ') for f in misc.between('Output File Formats are:\r\n\r\n', 'Examples:', fs).split('\r\n') if f != '']
        ins = [parse_format(f) for f in ins]
        ous = [parse_format(f) for f in ous]

        # join lists
        cls.installed_formats = OrderedDict()
        for name,longname,ext in ins:
            cls.installed_formats[name.lower()] = Format(name=name, fullname=longname, ext=ext, reading=True, multipage=True, metadata=True)
        for name,longname,ext in ous:
            cls.installed_formats[name.lower()] = Format(name=name, fullname=longname, ext=ext, reading=True, writing=True, multipage=True, metadata=True )

    #######################################
    # Supported
    #######################################

    def supported(self, ifnm):
        '''return True if the input file format is supported'''
        if not self.installed:
            return False
        log.debug('Supported for: %s', ifnm )
        return len(self.info(ifnm))>0


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    def meta(self, ifnm, series=0):
        if not self.installed:
            return {}
        log.debug('Meta for: %s', ifnm )
        with Locks (ifnm):
            t = tempfile.mkstemp(suffix='.xml')
            metafile = t[1]
            misc.run_command( [self.CONVERTERCOMMAND, '-i', ifnm, '-m', metafile] )
            with open(metafile, 'r') as f:
                meta = f.read()
            #os.remove(metafile) # felix suggested error


        # fix a bug in Imaris Convert exporting XML with invalid chars
        # by removing the <ImplParameters> tag
        # params is formatted in INI format
        try:
            if '<ImplParameters><![CDATA[' in meta: # v8
                params = misc.between('<ImplParameters><![CDATA[', ']]>\n</ImplParameters>', meta)
            else: # v7
                params = misc.between('<ImplParameters>', '</ImplParameters>', meta)
            # Meta is an XML
            meta = meta.replace(params, '', 1)
        except UnboundLocalError:
            return {}

        ########################################
        # Parse Meta XML
        ########################################
        rd = {}
        mee = etree.fromstring(meta)

        if '<FileInfo2>' in meta: # v7
            rd['image_num_series'] = misc.safeint(misc.xpathtextnode(mee, '/FileInfo2/NumberOfImages'), 1)
            imagenodepath = '/FileInfo2/Image[@mIndex="%s"]'%series
        else: # v8
            rd['image_num_series'] = misc.safeint(misc.xpathtextnode(mee, '/MetaData/NumberOfImages'), 1)
            imagenodepath = '/MetaData/Image[@mIndex="%s"]'%series

        rd['date_time'] = misc.xpathtextnode(mee, '%s/ImplTimeInfo'%imagenodepath).split(';', 1)[0]
        rd['format']    = misc.xpathtextnode(mee, '%s/BaseDescription'%imagenodepath).split(':', 1)[1].strip(' ')

        # dims
        dims = misc.xpathtextnode(mee, '%s/BaseDimension'%imagenodepath).split(' ')
        try:
            rd['image_num_x'] = misc.safeint(dims[0])
            rd['image_num_y'] = misc.safeint(dims[1])
            rd['image_num_z'] = misc.safeint(dims[2])
            rd['image_num_c'] = misc.safeint(dims[3])
            rd['image_num_t'] = misc.safeint(dims[4])
        except IndexError:
            pass

        # pixel format
        pixeltypes = {
            'uint8':  ('unsigned', 8),
            'uint16': ('unsigned', 16),
            'uint32': ('unsigned', 32),
            'uint64': ('unsigned', 64),
            'int8':   ('signed', 8),
            'int16':  ('signed', 16),
            'int32':  ('signed', 32),
            'int64':  ('signed', 64),
            'float':  ('float', 32),
            'double': ('float', 64),
        }
        try:
            t = pixeltypes[misc.xpathtextnode(mee, '%s/ImplDataType'%imagenodepath).lower()]
            rd['image_pixel_format'] = t[0]
            rd['image_pixel_depth']  = t[1]
        except KeyError:
            pass

        # resolution
        extmin = [misc.safefloat(i) for i in misc.xpathtextnode(mee, '%s/ImplExtendMin'%imagenodepath).split(' ')]
        extmax = [misc.safefloat(i) for i in misc.xpathtextnode(mee, '%s/ImplExtendMax'%imagenodepath).split(' ')]
        rd['pixel_resolution_x'] = (extmax[0]-extmin[0])/rd['image_num_x']
        rd['pixel_resolution_y'] = (extmax[1]-extmin[1])/rd['image_num_y']
        rd['pixel_resolution_z'] = (extmax[2]-extmin[2])/rd['image_num_z']
        # Time resolution is apparently missing in Imaris XML
        #rd['pixel_resolution_z'] = (extmax[2]-extmin[2])/rd['image_num_z']

        rd['pixel_resolution_unit_x'] = 'microns'
        rd['pixel_resolution_unit_y'] = 'microns'
        rd['pixel_resolution_unit_z'] = 'microns'

        ########################################
        # Parse params INI
        ########################################

        sp = StringIO.StringIO(params)
        config = ConfigParser.ConfigParser()
        config.readfp(sp)
        sp.close()

        # channel names
        for c in range(rd['image_num_c']):
            try:
                name = config.get('Channel %s'%c, 'Name')
                rd['channel_%s_name'%c] = name
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass

        # channel colors
        for c in range(rd['image_num_c']):
            try:
                rgb = [str(int(misc.safefloat(i)*255)) for i in config.get('Channel %s'%c, 'Color').split(' ')]
                rd['channel_color_%s'%c] = ','.join(rgb)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass

        # custom - any other tags in proprietary files should go further prefixed by the custom parent
        for section in config.sections():
            for option in config.options(section):
                rd['custom/%s/%s'%(section,option)] = config.get(section, option)

        return rd

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    def info(self, ifnm, series=0):
        '''returns a dict with file info'''
        if not self.installed:
            return {}
        log.debug('Info for: %s', ifnm )
        if not os.path.exists(ifnm):
            return {}
        rd = self.meta(ifnm, series)
        core = [ 'image_num_series', 'image_num_x', 'image_num_y', 'image_num_z', 'image_num_c', 'image_num_t',
                 'image_pixel_format', 'image_pixel_depth',
                 'pixel_resolution_x', 'pixel_resolution_y', 'pixel_resolution_z',
                 'pixel_resolution_unit_x', 'pixel_resolution_unit_y', 'pixel_resolution_unit_z' ]

        #return {k:v for k,v in rd.iteritems() if k in core}
        return dict( (k,v)  for k,v in rd.iteritems() if k in core )

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
            command.extend (['-of', fmt])
        if series is not None:
            command.extend (['-ii', str(series)])
        #command.extend (extra)
        return cls.run(ifnm, ofnm, command )

    @classmethod
    def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=[]):
        '''converts input filename into output in OME-TIFF format'''
        log.debug('convertToOmeTiff: [%s] -> [%s] for series %s with [%s]', ifnm, ofnm, series, extra)
        return cls.run(ifnm, ofnm, ['-i', ifnm, '-o', ofnm, '-of', 'OmeTiff', '-ii', '%s'%series] )

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)
        command = ['-i', ifnm, '-t', ofnm, '-tf', 'jpeg', '-ii', '%s'%series]
        #command.extend (['-tl', '%s,%s'%(width, height)]) # does not seem to work
        command.extend (['-ts', '%s,%s'%(width, height)])
        command.extend (['-tb', '#FFFFFF']) # dima: thumbnails are all padded, ask for white right now, before the fix is final
        return cls.run(ifnm, ofnm, command)

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        log.debug('Slice: %s %s %s %s for [%s]', z, t, roi, series, ifnm)
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi
        ometiff = kw['intermediate']

        if z1>z2 and z2==0 and t1>t2 and t2==0 and x1==0 and x2==0 and y1==0 and y2==0:
            # converting one slice z or t, does not support ome-tiff, tiff or jpeg produces an RGBA image
            #return cls.run(ifnm, ofnm, ['-i', ifnm, '-t', ofnm, '-tf', fmt, '-ii', str(series), '-tm', 'Slice', '-tz', str(z1-1), '-th', str(t1-1)])
            r = cls.run(ifnm, ofnm, ['-i', ifnm, '-t', ofnm, '-tf', 'ometiff', '-ii', str(series), '-tz', str(z1-1), '-th', str(t1-1)])
            if r is None:
                return None
            # imaris convert appends .tif extension to the file
            if not os.path.exists(ofnm) and os.path.exists(ofnm+'.tif'):
                os.rename(ofnm+'.tif', ofnm)
            elif not os.path.exists(ofnm) and os.path.exists(ofnm+'.ome.tif'):
                os.rename(ofnm+'.ome.tif', ofnm)
            return ofnm
        else:
            # create an intermediate OME-TIFF
            if not os.path.exists(ometiff):
                cls.convertToOmeTiff(ifnm, ometiff, series=series)
            # extract slices
            return ConverterImgcnv.slice(ometiff, ofnm=ofnm, z=z, t=t, roi=roi, series=series, **kw)


ConverterImaris.init()
