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

import os
import os.path
from lxml import etree
import re
import tempfile
import cStringIO as StringIO
import ConfigParser
#from collections import OrderedDict
from bq.util.compat import OrderedDict
import bq.util.io_misc as misc

from .converter_base import ConverterBase, Format
from .converter_imgcnv import ConverterImgcnv
from bq.util.locks import Locks

import logging
log = logging.getLogger('bq.image_service.converter_imaris')

BLOCK_START='<ImplParameters><![CDATA['
BLOCK_END  = ']]>' + os.linesep + '</ImplParameters>'


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
    CONVERTERCOMMAND = 'ImarisConvert' if os.name != 'nt' else 'ImarisConvert/ImarisConvert.exe'

    format_map = {
        'ome-bigtiff' : 'OmeTiff',
        'ome-tiff' : 'OmeTiff',
        'bigtiff' : 'OmeTiff',
        'tiff' : 'OmeTiff',
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

        ins = [f.strip(' ') for f in misc.between('Input File Formats are:%s' % (os.linesep*2) , 'Output File Formats are:', fs).split(os.linesep) if f != '']
        # version 8.0.0
        if 'Exit Codes:' in fs:
            ous = [f.strip(' ') for f in misc.between('Output File Formats are:%s' % (os.linesep*2), 'Exit Codes:', fs).split(os.linesep) if f != '']
        else: # version 7.X
            ous = [f.strip(' ') for f in misc.between('Output File Formats are:%s' % (os.linesep*2), 'Examples:', fs).split(os.linesep) if f != '']
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

    @classmethod
    def supported(cls, ifnm, **kw):
        '''return True if the input file format is supported'''
        if not cls.installed:
            return False
        log.debug('Supported for: %s', ifnm )
        return len(cls.info(ifnm, **kw))>0


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    @classmethod
    def meta(cls, ifnm, series=0, **kw):
        if not cls.installed:
            return {}
        series = int(series)        
        log.debug('Meta for: %s', ifnm )
        
        if os.name == 'nt':
            nulldevice = 'NUL'
        elif os.name == 'posix':
            nulldevice = '/dev/null'
        
        command = [cls.CONVERTERCOMMAND, '-i', ifnm, '-m', '-l', nulldevice, '-ii', '%s'%series]    
        command.extend( cls.extention(**kw) ) # extend if timeout or meta are present
        meta = cls.run_read(ifnm, command)
        
        if meta is None:
            return {}

        # fix a bug in Imaris Convert exporting XML with invalid chars
        # by removing the <ImplParameters> tag
        # params is formatted in INI format
        params = ''    
        try:
            p = misc.between(BLOCK_START, BLOCK_END, meta)
            meta = meta.replace('%s%s%s'%(BLOCK_START, p, BLOCK_END), '', 1)
            params = p
        except UnboundLocalError:
            return {}

        ########################################
        # Parse Meta XML
        # most files have improper encodings, try to recover
        ########################################
        rd = {}
        try:
            mee = etree.fromstring(meta)
        except etree.XMLSyntaxError:
            try:
                mee = etree.fromstring(meta, parser=etree.XMLParser(encoding='iso-8859-1'))
            except (etree.XMLSyntaxError, LookupError):
                try:
                    mee = etree.fromstring(meta, parser=etree.XMLParser(encoding='utf-16'))
                except (etree.XMLSyntaxError, LookupError):
                    try:
                        mee = etree.fromstring(meta, parser=etree.XMLParser(recover=True))
                    except etree.XMLSyntaxError:
                        log.error ("Unparsable %s", meta)
                        return {}

        if '<FileInfo2>' in meta: # v7
            rd['image_num_series'] = misc.safeint(misc.xpathtextnode(mee, '/FileInfo2/NumberOfImages'), 1)
            imagenodepath = '/FileInfo2/Image[@mIndex="%s"]'%series
        else: # v8
            rd['image_num_series'] = misc.safeint(misc.xpathtextnode(mee, '/MetaData/NumberOfImages'), 1)
            imagenodepath = '/MetaData/Image[@mIndex="%s"]'%series

        rd['image_series_index'] = series
        rd['date_time'] = misc.xpathtextnode(mee, '%s/ImplTimeInfo'%imagenodepath).split(';', 1)[0]
        #rd['format']    = misc.xpathtextnode(mee, '%s/BaseDescription'%imagenodepath).split(':', 1)[1].strip(' ')
        rd['format']    = misc.xpathtextnode(mee, '%s/BaseDescription'%imagenodepath) #.split(':', 1)[1].strip(' ')

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
            'uint8':  ('unsigned integer', 8),
            'uint16': ('unsigned integer', 16),
            'uint32': ('unsigned integer', 32),
            'uint64': ('unsigned integer', 64),
            'int8':   ('signed integer', 8),
            'int16':  ('signed integer', 16),
            'int32':  ('signed integer', 32),
            'int64':  ('signed integer', 64),
            'float':  ('floating point', 32),
            'double': ('floating point', 64),
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
        #params = misc.xpathtextnode(mee, '%s/ImplParameters'%imagenodepath)
        # use index 0 since we fetch meta data with imageindex argument
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

        # preferred channel mapping
        #if rd['image_num_c']==1:
        #    rd['channel_color_0'] = '255,255,255'

        # custom - any other tags in proprietary files should go further prefixed by the custom parent
        for section in config.sections():
            for option in config.options(section):
                rd['custom/%s/%s'%(section,option)] = config.get(section, option)

        return rd

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    
    @classmethod    
    def info(cls, ifnm, series=0, **kw):
        '''returns a dict with file info'''
        if not cls.installed:
            return {}
        log.debug('Info for: %s', ifnm )
        if not os.path.exists(ifnm):
            return {}
        rd = cls.meta(ifnm, series, **kw)
        core = [ 'image_num_series', 'image_num_x', 'image_num_y', 'image_num_z', 'image_num_c', 'image_num_t',
                 'image_pixel_format', 'image_pixel_depth', 'image_series_index',
                 'pixel_resolution_x', 'pixel_resolution_y', 'pixel_resolution_z',
                 'pixel_resolution_unit_x', 'pixel_resolution_unit_y', 'pixel_resolution_unit_z' ]

        #return {k:v for k,v in rd.iteritems() if k in core}
        return dict( (k,v)  for k,v in rd.iteritems() if k in core )

    #######################################
    # Conversion
    #######################################
    
    @classmethod
    def extention(cls, ofnm=None, **kw):
        c = []
        try:
            token = kw['token']
            timeout = token.timeout
        except (KeyError, TypeError, AttributeError):
            return c
        
        # add timeout if exists
        if timeout is not None:
            c.extend (['-to', '%s'%timeout])
        
        # add multi-file series geometry if exists
        try:
            meta = token.meta
        except (TypeError, AttributeError):
            return c

        if meta is None:
            return c
        try:
            if ofnm is not None:            
                tempSeriesFileName = '%s.serieslayout'%ofnm
            else:
                fd,tempSeriesFileName = tempfile.mkstemp(suffix='.serieslayout')
                os.close(fd)
            
            seriesLayoutXml = meta['SeriesLayout'] 
            with open(tempSeriesFileName, 'wb') as f:
                f.write(seriesLayoutXml)
            
            # felix: should we delete this file afterwards or since it is a temp file the OS takes care of it?
            c.extend(['-il', '%s'%tempSeriesFileName])
        except (TypeError, KeyError, ValueError, OSError):
            log.debug("Could not extend command with series layout")
            pass
            
        return c

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=None, **kw):
        '''converts a file and returns output filename'''
        log.debug('convert: [%s] -> [%s] into %s for series %s with [%s]', ifnm, ofnm, fmt, series, extra)
        if fmt in cls.format_map:
            fmt = cls.format_map[fmt]
        command = ['-i', ifnm]
        if ofnm is not None:
            command.extend (['-o', ofnm])
        if fmt is not None:
            command.extend (['-of', fmt])
        if series is not None:
            command.extend (['-ii', str(series)])
        #if extra is not None:
        #    command.extend (extra)
        return cls.run(ifnm, ofnm, command )

    @classmethod
    def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=None, **kw):
        '''converts input filename into output in OME-TIFF format'''
        log.debug('convertToOmeTiff: [%s] -> [%s] for series %s with [%s]', ifnm, ofnm, series, extra)
        command = ['-i', ifnm, '-o', ofnm, '-of', 'OmeTiff', '-ii', '%s'%series]
        command.extend( cls.extention(ofnm=ofnm, **kw) ) # extend if timeout or meta are present
        return cls.run(ifnm, ofnm, command, **kw )

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)
        fmt = kw.get('fmt', 'jpeg')
        if fmt in cls.format_map:
            fmt = cls.format_map[fmt]
        command = ['-i', ifnm, '-t', ofnm, '-tf', fmt, '-ii', '%s'%series]
        command.extend (['-tl', '%s'%width]) # bitplane

        preproc = kw.get('preproc', '')
        if preproc == 'mid':
            command.extend('-tm', 'MiddleSlice')
        elif preproc == 'mip':
            command.extend('-tm', 'MaxIntensity')
        elif preproc == 'nip':
            command.extend('-tm', 'MinIntensity')
                    
                    
        command.extend( cls.extention(ofnm=ofnm, **kw) ) # extend if timeout or meta are present
        
        return cls.run(ifnm, ofnm, command)

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        log.debug('Slice: %s %s %s %s for [%s]', z, t, roi, series, ifnm)
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi

        ometiff = kw.get('intermediate', None)

        if z1>z2 and z2==0 and t1>t2 and t2==0 and x1==0 and x2==0 and y1==0 and y2==0:
            # converting one slice z or t, does not support ome-tiff, tiff or jpeg produces an RGBA image
            command = ['-i', ifnm, '-o', ofnm, '-of', 'OmeTiff', '-ii', str(series), '-ic', '0,0,0,0,%s,%s,0,0,%s,%s'%(z1-1,z1,t1-1,t1)]
            command.extend( cls.extention(ofnm=ofnm, **kw) ) # extend if timeout or meta are present
            r = cls.run(ifnm, ofnm, command)
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
                token = kw.get('token', None)
                r = cls.convertToOmeTiff(ifnm, ometiff, series=series, nooverwrite=True, token=token)
                if r is None:
                    return None
            # extract slices
            return ConverterImgcnv.slice(ometiff, ofnm=ofnm, z=z, t=t, roi=roi, series=0, **kw)


try:
    ConverterImaris.init()
except Exception:
    log.warn("ImarisConvert unavailable")
