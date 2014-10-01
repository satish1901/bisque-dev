# converter_bioformats.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" BioFormats command line converter
"""

__module__    = "converter_bioformats"
__author__    = "Dmitry Fedorov"
__version__   = "0.6"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os.path
from lxml import etree
#from collections import OrderedDict
from bq.util.compat import OrderedDict

from . import misc
from .converter_base import ConverterBase, Format
from .converter_imgcnv import ConverterImgcnv
from .locks import Locks

import logging
log = logging.getLogger('bq.image_service.converter_bioformats')

################################################################################
# ConverterBase
################################################################################

class ConverterBioformats(ConverterBase):
    installed = False
    version = None
    installed_formats = None
    CONVERTERCOMMAND = 'bfconvert'  if os.name != 'nt' else 'bfconvert.bat'
    BFINFO           = 'showinf'    if os.name != 'nt' else 'showinf.bat'
    BFORMATS         = 'formatlist' if os.name != 'nt' else 'formatlist.bat'

    format_map = {
        'ome-bigtiff' : {
            'name': 'ome-tiff',
            'extra': ['-bigtiff', '-compression', 'LZW']
        },
        'bigtiff' : {
            'name': 'tiff',
            'extra': ['-bigtiff', '-compression', 'LZW']
        },
        'ome-tiff' : {
            'name': 'ome-tiff',
            'extra': ['-compression', 'LZW']
        },
        'tiff' : {
            'name': 'tiff',
            'extra': ['-compression', 'LZW']
        }
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

    #$ ./showinf -version
    #Version: 4.3.2
    #VCS revision: bb54cc7
    #Build date: 14 September 2011

    @classmethod
    def get_version (cls):
        '''returns the version of bioformats'''
        o = misc.run_command( [cls.BFINFO, '-version', '-no-upgrade'] )
        if o is None:
            return None

        v = {}
        for line in o.splitlines():
            if not line: continue
            d = line.split(': ', 1)
            if len(d)<2: continue
            v[d[0]] = d[1]

        if 'Version' in v:
            v['full'] =  v['Version']

        if 'full' in v:
            d = [int(s) for s in v['full'].split('.', 2)]
            if len(d)>2:
                v['numeric']  = d
                v['major']    = d[0]
                v['minor']    = d[1]
                v['build']    = d[2]

        return v

    #######################################
    # Formats
    #######################################

    @classmethod
    def get_formats(cls):
        '''inits supported file formats'''

        if cls.installed_formats is None:
            cls.installed_formats = OrderedDict()

            formats_xml = misc.run_command( [cls.BFORMATS, '-xml'] )
            if formats_xml is None:
                return
            formats = etree.fromstring( formats_xml )

            codecs = formats.xpath('//format')
            for c in codecs:
                try:
                    ext=c.xpath('tag[@name="extensions"]')[0].get('value', '').split('|')
                    name = c.get('name')
                    cls.installed_formats[name.lower()] = Format(
                        name=name,
                        fullname=c.get('name'),
                        ext=ext,
                        reading=len(c.xpath('tag[@name="support" and @value="reading"]'))>0,
                        writing=len(c.xpath('tag[@name="support" and @value="writing"]'))>0,
                        multipage=len(c.xpath('tag[@name="support" and @value="writing multiple pages"]'))>0,
                        metadata=True,
                    )
                except IndexError:
                    continue

    #######################################
    # Supported
    #######################################

    def supported(self, ifnm, **kw):
        '''return True if the input file format is supported'''
        if not self.installed:
            return False
        if self.is_multifile_series(**kw) is True:
            return False # for now we're not using multi-file support of bioformats
        log.debug('Supported for: %s', ifnm )
        return len(self.info(ifnm))>0


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    #$ ./showinf -nopix -omexml "13_1.lsm"
    # Metadata blocks:
    #Reading core metadata
    #Reading global metadata
    #Reading metadata
    # name value fields separated with ":"

    def meta(self, ifnm, series=0, **kw):
        if not self.installed:
            return {}
        if not os.path.exists(ifnm):
            return {}
        if self.is_multifile_series(**kw) is True:
            return {}        
        log.debug('Meta for: %s', ifnm )
        o = self.run_read(ifnm, [self.BFINFO, '-nopix', '-omexml', '-novalid', '-no-upgrade', '-series', '%s'%series, ifnm] )
        if o is None:
            return {}

        # extract the OME-XML part
        try:
            omexml = misc.between('<OME', '</OME>', o)
            omexml = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<OME%s</OME>'%omexml
        except UnboundLocalError:
            return {}

        ########################################
        # Parse non XML parts
        ########################################
        rd = {}
        rd['image_num_series'] = misc.safeint(misc.between('Series count =', '\n', o),1)
        rd['image_series_index'] = series
        rd['format'] = misc.between('Checking file format [', ']', o)

        ########################################
        # Parse Meta XML
        # bioformats defines UTF-8 encoding, but it may be something else, try to recover
        ########################################
        try:
            mee = etree.fromstring(omexml)
        except etree.XMLSyntaxError:
            try:
                mee = etree.fromstring(omexml, parser=etree.XMLParser(encoding='iso-8859-1'))
            except (etree.XMLSyntaxError, LookupError):
                try:
                    mee = etree.fromstring(omexml, parser=etree.XMLParser(encoding='cp1252'))
                except (etree.XMLSyntaxError, LookupError):
                    mee = etree.fromstring(omexml, parser=etree.XMLParser(recover=True))

        imagenodepath = 'ome:Image[@ID="Image:%s"]'%(series)
        namespaces = {
            'ome': misc.between('OME xmlns="', '"', omexml),
            'sa': misc.between('StructuredAnnotations xmlns="', '"', omexml),
            #'om': misc.between('OriginalMetadata xmlns="', '"', o), # dima: v4.x.x
        }

        rd['date_time'] = misc.xpathtextnode(mee, '%s/ome:AcquisitionDate'%imagenodepath, namespaces=namespaces).replace('T', ' ')

        pixels = mee.xpath('ome:Image[@ID="Image:0"]/ome:Pixels', namespaces=namespaces)[0]
        rd['image_num_x'] = misc.safeint(pixels.get('SizeX', '0'))
        rd['image_num_y'] = misc.safeint(pixels.get('SizeY', '0'))
        rd['image_num_z'] = misc.safeint(pixels.get('SizeZ', '0'))
        rd['image_num_c'] = misc.safeint(pixels.get('SizeC', '0'))
        rd['image_num_t'] = misc.safeint(pixels.get('SizeT', '0'))

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
            t = pixeltypes[pixels.get('Type', 0).lower()]
            rd['image_pixel_format'] = t[0]
            rd['image_pixel_depth']  = t[1]
        except KeyError:
            pass

        # resolution
        rd['pixel_resolution_x'] = misc.safefloat(pixels.get('PhysicalSizeX', '0.0'))
        rd['pixel_resolution_y'] = misc.safefloat(pixels.get('PhysicalSizeY', '0.0'))
        rd['pixel_resolution_z'] = misc.safefloat(pixels.get('PhysicalSizeZ', '0.0'))
        rd['pixel_resolution_t'] = misc.safefloat(pixels.get('TimeIncrement', '0.0'))
        rd['pixel_resolution_unit_x'] = 'microns'
        rd['pixel_resolution_unit_y'] = 'microns'
        rd['pixel_resolution_unit_z'] = 'microns'
        rd['pixel_resolution_unit_t'] = 'seconds'

        # channel names
        channels = mee.xpath('ome:Image[@ID="Image:0"]/ome:Pixels/ome:Channel', namespaces=namespaces)
        for c,i in zip(channels, range(len(channels))):
            rd['channel_%s_name'%i] = c.get('Name', 'ch_%s'%i)

        # preferred channel mapping
        if rd['image_num_c']==1:
            rd['channel_color_0'] = '255,255,255'

        # custom - any other tags in proprietary files should go further prefixed by the custom parent
        custom = mee.xpath('sa:StructuredAnnotations/sa:XMLAnnotation', namespaces=namespaces)
        for a in custom:
            #k = misc.xpathtextnode(a, 'sa:Value/om:OriginalMetadata/om:Key', namespaces=namespaces)  # dima: v4.x.x
            #v = misc.xpathtextnode(a, 'sa:Value/om:OriginalMetadata/om:Value', namespaces=namespaces) # dima: v4.x.x
            k = misc.xpathtextnode(a, 'Value/OriginalMetadata/Key', namespaces=namespaces)  # dima: v5.0.0
            v = misc.xpathtextnode(a, 'Value/OriginalMetadata/Value', namespaces=namespaces) # dima: v5.0.0
            rd['custom/%s'%k] = v

        return rd

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################

    #the original metadata as a list of key/value pairs, and the converted OME-XML:
    #showinf -nopix -omexml
    #If you don't want the original metadata to be displayed, add the '-nometa' option.

    #$ ./showinf -nopix -nometa "13_1.lsm"
    #Checking file format [Zeiss Laser-Scanning Microscopy]
    #Initializing reader
    #        Removing thumbnails
    #        Reading LSM metadata
    #Initialization took 0.152s
    #
    #Reading core metadata
    #Filename = 13_1.lsm
    #Series count = 1
    #Series #0 :
    #        Image count = 61
    #        RGB = true (2)
    #        Interleaved = false
    #        Indexed = false
    #        Width = 512
    #        Height = 512
    #        SizeZ = 61
    #        SizeT = 1
    #        SizeC = 2 (effectively 1)
    #        Thumbnail size = 128 x 128
    #        Endianness = motorola (big)
    #        Dimension order = XYCZT (uncertain)
    #        Pixel type = uint16
    #        Metadata complete = false
    #        Thumbnail series = false

    def info(self, ifnm, series=0, **kw):
        '''returns a dict with file info'''
        if not self.installed:
            return {}
        if not os.path.exists(ifnm):
            return {}
        if self.is_multifile_series(**kw) is True:
            return {}        
        log.debug('Info for: %s', ifnm )
        o = self.run_read(ifnm, [self.BFINFO, '-nopix', '-nometa', '-no-upgrade', '-series', '%s'%series, ifnm] )
        if o is None:
            return {}

        bfmap = { 'Image count': 'image_num_p',
                  'Width': 'image_num_x',
                  'Height': 'image_num_y',
                  'SizeZ': 'image_num_z',
                  'SizeT': 'image_num_t',
                  'SizeC': 'image_num_c',
                  'Dimension order': 'dimensions' }

        rd = { 'image_num_z': 1,
               'image_num_t': 1,
               'image_num_p': 1 }

        in_series = False
        for line in o.splitlines():
            if not line: continue
            line = line.strip()

            if line.startswith('Checking file format ['):
                rd['format'] = line.replace('Checking file format [', '').replace(']', '')
                continue

            if line.startswith('Series count = '):
                val = line.replace('Series count = ', '')
                rd['image_num_series'] = misc.safetypeparse(val)
                continue

            if line.startswith('Series #%s'%series):
                rd['image_series_index'] = series
                in_series = True
                continue

            if line.startswith('Series #%s'%(int(series)+1)):
                break

            if not in_series:
                continue

            try:
                tag, val = [ l.strip(' \n') for l in line.split('=',1) ]
            except Exception:
                break
            if not tag in bfmap:
                continue
            rd[bfmap[tag]] = misc.safetypeparse(val)

        if len(rd)<4:
            return {}
        if rd['image_num_p']>1 and rd['image_num_z']<=1 and rd['image_num_t']<=1:
            rd['image_num_t'] = rd['image_num_p']

        return rd


    #######################################
    # Conversion
    #######################################

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=None, **kw):
        '''converts a file and returns output filename'''
        log.debug('convert: [%s] -> [%s] into %s for series %s with [%s]', ifnm, ofnm, fmt, series, extra)
        command = [ifnm, ofnm, '-no-upgrade', '-overwrite']
        tmp = None
        if fmt is not None:
            fmt2 = fmt
            if fmt in cls.format_map:
                fmt2 = cls.format_map[fmt]['name']
            ext = cls.installed_formats[fmt2].ext[0]
            if ofnm.endswith(ext) is False:
                tmp = '%s.%s'%(ofnm, ext)
                command = [ifnm, tmp, '-no-upgrade', '-overwrite']
        if series>=0:
            command.extend(['-series', '%s'%series])

        #if extra is not None:
        #    command.extend(extra)
        if fmt in cls.format_map:
            command.extend(cls.format_map[fmt]['extra'])

        if tmp is None:
            return cls.run(ifnm, ofnm, command )
        else:
            r = cls.run(ifnm, tmp, command )
            os.rename(tmp, ofnm)
            return r

    # '.ome.tiff' or '.ome.tif'.
    #sh bfconvert -bigtiff -compression LZW  ../53676.svs ../output.ome.tiff

    @classmethod
    def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=None, **kw):
        '''converts input filename into output in OME-TIFF format'''
        log.debug('convertToOmeTiff: [%s] -> [%s] for series %s with [%s]', ifnm, ofnm, series, extra)
        if cls.is_multifile_series(**kw) is True:
            return None

        command = [ifnm, ofnm, '-no-upgrade', '-overwrite']
        #if original is not None:
        #    command = ['-map', ifnm, original, ofnm]
        command.extend(['-bigtiff', '-compression', 'LZW'])
        if series>=0:
            command.extend(['-series', '%s'%series])
        if extra is not None:
            command.extend(extra)
        return cls.run(ifnm, ofnm, command, **kw )

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)
        if cls.is_multifile_series(**kw) is True:
            return None        

        # dima: BF has a bug exporting only one channel when -z or -timepoint are requested
        # dima: will run plane extraction only if the image has 1 channel
        # dima: once fixed, remove test and perform plane extraction always
        token = kw.get('token', None)
        info = token.dims if token is not None else {}
        num_channels = info.get('image_num_c', 1)
        if num_channels == 1:
            ometiff = kw['intermediate'].replace('.ome.tif', '.t0.z0.ome.tif')
            # sub point extraction only works for 1 channel and z0 and t0, so, no way to optimizy mid
            if not os.path.exists(ometiff):
                r = cls.convertToOmeTiff(ifnm, ometiff, series=series, extra=['-z', '0', '-timepoint', '0'], nooverwrite=True)
                if r is None:
                    return None
        else:
            # dima: when slices will be supported correctly - remove
            ometiff = kw['intermediate']
            if not os.path.exists(ometiff):
                r = cls.convertToOmeTiff(ifnm, ometiff, series=series, nooverwrite=True)
                if r is None:
                    return None
        
        # extract thumbnail
        #return ConverterImgcnv.thumbnail(ometiff, ofnm=ofnm, width=width, height=height, series=series, **kw)
        return ConverterImgcnv.thumbnail(ometiff, ofnm=ofnm, width=width, height=height, series=series)

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        log.debug('Slice: %s %s %s %s for [%s]', z, t, roi, series, ifnm)
        if cls.is_multifile_series(**kw) is True:
            return None
        
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi

        # dima: BF has a bugs exporting -z or -timepoint, only extracts one image apparently from the beggining
        # dima: will run plane extraction only if the image has 1 channel
        # dima: once fixed, remove test and perform plane extraction always
#         info = kw.get('info', None) or {}
#         num_channels = info.get('image_num_c', 1)
#         if z1>z2 and z2==0 and t1>t2 and t2==0 and x1==0 and x2==0 and y1==0 and y2==0 and num_channels==1:
#             ofnmtmp = '%s.ome.tif'%ofnm
#             r = cls.convertToOmeTiff(ifnm, ofnm=ofnmtmp, series=series, extra=['-z', str(z1-1), '-timepoint', str(t1-1)])
#             if r is None:
#                 return None
#             os.rename(ofnmtmp, ofnm)
#             return ofnm

        # create an intermediate OME-TIFF
        ometiff = kw.get('intermediate', None)
        if not os.path.exists(ometiff):
            r = cls.convertToOmeTiff(ifnm, ometiff, series=series, nooverwrite=True)
            if r is None:
                return None
        # extract slices
        return ConverterImgcnv.slice(ometiff, ofnm=ofnm, z=z, t=t, roi=roi, series=series, **kw)


try:
    ConverterBioformats.init()
except Exception:
    log.warn("Bioformats unavailable")
