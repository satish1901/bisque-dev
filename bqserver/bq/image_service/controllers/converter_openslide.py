# converter_openslide.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
#
# This converter will not support the full API for now since it would be really inefficient
# trying to create ome-tiff out of pyramidal tiled images, instead it will only provide
# tile and thumbnail access, this will work perfectly for the UI and module access
# if tiles are used, better integration will be looked at later if need arises
#
from __future__ import with_statement

""" Imaris command line converter
"""

__module__    = "converter_openslide"
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
from bq.util.locks import Locks
import bq.util.io_misc as misc

from .converter_base import ConverterBase, Format
from .converter_imgcnv import ConverterImgcnv

try:
    import openslide
    from openslide import deepzoom
except (ImportError, OSError):
    pass

import logging
log = logging.getLogger('bq.image_service.converter_openslide')

################################################################################
# ConverterImaris
################################################################################

class ConverterOpenSlide(ConverterBase):
    installed = False
    version = None
    installed_formats = None
    extensions = None

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
        '''returns the version of openslide python'''
        try:
            import openslide
        except (ImportError, OSError):
            return None

        v = {}
        v['full'] = openslide.__version__

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

        cls.extensions = ['.svs', '.ndpi', '.vms', '.vmu', '.scn', '.mrxs', '.svslide', '.bif']

        # Many extensions may unfortunately be .tif, we'll have to deal with that later
        cls.installed_formats = OrderedDict()
        cls.installed_formats['aperio']    = Format(name='aperio', fullname='Aperio', ext=['svs','tif','tiff'], reading=True, multipage=False, metadata=True) # tif
        cls.installed_formats['hamamatsu'] = Format(name='hamamatsu', fullname='Hamamatsu', ext=['ndpi','vms','vmu'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['leica']     = Format(name='leica', fullname='Leica', ext=['scn'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['mirax']     = Format(name='mirax', fullname='MIRAX', ext=['mrxs'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['sakura']    = Format(name='sakura', fullname='Sakura', ext=['svslide'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['trestle']   = Format(name='trestle', fullname='Trestle', ext=['tif'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['ventana']   = Format(name='ventana', fullname='Ventana', ext=['bif'], reading=True, multipage=False, metadata=True)
        cls.installed_formats['tiff']      = Format(name='tiff', fullname='Generic tiled TIFF', ext=['tif','tiff'], reading=True, multipage=False, metadata=True)

    #######################################
    # Supported
    # we skip generic tiff support from openslide to use imageconvert
    # openslide recognizes OME-TIFF as generic tiff and also does not read >3 channels
    # as well as saves images with >8 bits as 8 bits
    # therefore we skip openslide in favour of imgcnv: it's faster and supports all the aforementioned types
    #######################################

    @classmethod
    def supported(cls, ifnm, **kw):
        '''return True if the input file format is supported'''
        if not cls.installed:
            return False
        log.debug('Supported for: %s', ifnm )
        if cls.is_multifile_series(**kw) is True:
            return False
        s = openslide.OpenSlide.detect_format(ifnm)
        return (s is not None and s != 'generic-tiff')

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################

    @classmethod
    def info(cls, ifnm, series=0, **kw):
        '''returns a dict with file info'''
        if not cls.supported(ifnm):
            return {}
        log.debug('Info for: %s', ifnm )
        with Locks(ifnm):
            if not os.path.exists(ifnm):
                return {}
            try:
                _, tmp = misc.start_nounicode_win(ifnm, [])
                slide = openslide.OpenSlide(tmp or ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                misc.end_nounicode_win(tmp)
                return {}

            info2 = {
                'format': slide.properties[openslide.PROPERTY_NAME_VENDOR],
                'image_num_series': 0,
                'image_series_index': 0,
                'image_num_x': slide.dimensions[0],
                'image_num_y': slide.dimensions[1],
                'image_num_z': 1,
                'image_num_t': 1,
                'image_num_c': 3,
                'image_num_resolution_levels': slide.level_count,
                'image_resolution_level_scales': ','.join([str(1.0/i) for i in slide.level_downsamples]),
                'image_pixel_format': 'unsigned integer',
                'image_pixel_depth': 8
            }

            if slide.properties.get(openslide.PROPERTY_NAME_MPP_X, None) is not None:
                info2.update({
                    'pixel_resolution_x': slide.properties.get(openslide.PROPERTY_NAME_MPP_X, 0),
                    'pixel_resolution_y': slide.properties.get(openslide.PROPERTY_NAME_MPP_Y, 0),
                    'pixel_resolution_unit_x': 'microns',
                    'pixel_resolution_unit_y': 'microns'
                })
            slide.close()

            # read metadata using imgcnv since openslide does not decode all of the info
            info = ConverterImgcnv.info(tmp or ifnm, series=series, **kw)
            misc.end_nounicode_win(tmp)
            info.update(info2)
            return info
        return {}

    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    @classmethod
    def meta(cls, ifnm, series=0, **kw):
        if not cls.supported(ifnm):
            return {}
        log.debug('Meta for: %s', ifnm )
        with Locks (ifnm):
            try:
                _, tmp = misc.start_nounicode_win(ifnm, [])
                slide = openslide.OpenSlide(tmp or ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                misc.end_nounicode_win(tmp)
                return {}
            rd = {
                'format': slide.properties.get(openslide.PROPERTY_NAME_VENDOR),
                'image_num_series': 0,
                'image_num_x': slide.dimensions[0],
                'image_num_y': slide.dimensions[1],
                'image_num_z': 1,
                'image_num_t': 1,
                'image_num_c': 3,
                'image_num_resolution_levels': slide.level_count,
                'image_resolution_level_scales': ','.join([str(1.0/i) for i in slide.level_downsamples]),
                'image_pixel_format': 'unsigned integer',
                'image_pixel_depth': 8,
                'magnification': slide.properties.get(openslide.PROPERTY_NAME_OBJECTIVE_POWER),
                'channel_0_name': 'red',
                'channel_1_name': 'green',
                'channel_2_name': 'blue',
                'channel_color_0': '255,0,0',
                'channel_color_1': '0,255,0',
                'channel_color_2': '0,0,255'
            }

            if slide.properties.get(openslide.PROPERTY_NAME_MPP_X, None) is not None:
                rd.update({
                    'pixel_resolution_x': slide.properties.get(openslide.PROPERTY_NAME_MPP_X, 0),
                    'pixel_resolution_y': slide.properties.get(openslide.PROPERTY_NAME_MPP_Y, 0),
                    'pixel_resolution_unit_x': 'microns',
                    'pixel_resolution_unit_y': 'microns'
                })

            # custom - any other tags in proprietary files should go further prefixed by the custom parent
            for k,v in slide.properties.iteritems():
                rd['custom/%s'%k.replace('.', '/')] = v
            slide.close()

            # read metadata using imgcnv since openslide does not decode all of the info
            meta = ConverterImgcnv.meta(tmp or ifnm, series=series, **kw)
            meta.update(rd)
            rd = meta

            misc.end_nounicode_win(tmp)
        return rd

    #######################################
    # Conversion
    #######################################

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=None, **kw):
        return None

    @classmethod
    def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=None, **kw):
        return None

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        if not cls.supported(ifnm):
            return None
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)

        fmt = kw.get('fmt', 'jpeg').upper()
        with Locks (ifnm, ofnm) as l:
            if l.locked: # the file is not being currently written by another process
                try:
                    _, tmp = misc.start_nounicode_win(ifnm, [])
                    slide = openslide.OpenSlide(tmp or ifnm)
                except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                    misc.end_nounicode_win(tmp)
                    return None
                img = slide.get_thumbnail((width, height))
                try:
                    img.save(ofnm, fmt)
                except IOError:
                    tmp = '%s.tif'%ofnm
                    img.save(tmp, 'TIFF')
                    ConverterImgcnv.thumbnail(tmp, ofnm=ofnm, width=width, height=height, **kw)
                slide.close()
                misc.end_nounicode_win(tmp)

        # make sure the file was written
        with Locks(ofnm):
            pass
        return ofnm

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        return None

    @classmethod
    def tile(cls, ifnm, ofnm, level, x, y, sz, series=0, **kw):
        '''extract Level,X,Y tile from input filename into output in OME-TIFF format'''
        if not cls.supported(ifnm):
            return None
        log.debug('Tile: %s %s %s %s %s for [%s]', level, x, y, sz, series, ifnm)

        level = misc.safeint(level, 0)
        x  = misc.safeint(x, 0)
        y  = misc.safeint(y, 0)
        sz = misc.safeint(sz, 0)
        with Locks (ifnm, ofnm) as l:
            if l.locked: # the file is not being currently written by another process
                try:
                    _, tmp = misc.start_nounicode_win(ifnm, [])
                    slide = openslide.OpenSlide(tmp or ifnm)
                    dz = deepzoom.DeepZoomGenerator(slide, tile_size=sz, overlap=0)
                    img = dz.get_tile(dz.level_count-level-1, (x,y))
                    img.save(ofnm, 'TIFF', compression='LZW')
                    slide.close()
                    misc.end_nounicode_win(tmp)
                except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                    misc.end_nounicode_win(tmp)
                    return None

        # make sure the file was written
        with Locks(ofnm):
            pass
        return ofnm

    @classmethod
    def writeHistogram(cls, ifnm, ofnm, **kw):
        '''writes Histogram in libbioimage format'''
        if not cls.supported(ifnm):
            return None
        log.debug('Writing histogram for %s into: %s', ifnm, ofnm )

        # currently openslide only supports 8 bit 3 channel images
        # need to generate a histogram file uniformely distributed from 0..255
        channels = 3

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
        return ofnm

try:
    ConverterOpenSlide.init()
except Exception:
    log.warn("Openslide Unavailable")
