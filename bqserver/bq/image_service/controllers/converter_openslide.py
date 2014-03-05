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

from . import misc
from .converter_base import ConverterBase, Format
from .converter_imgcnv import ConverterImgcnv
from .locks import Locks

try:
    import openslide
    from openslide import deepzoom
except (ImportError, WindowsError):
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
        except (ImportError, WindowsError):
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
    #######################################

    def supported(self, ifnm):
        '''return True if the input file format is supported'''
        if not self.installed:
            return False
        log.debug('Supported for: %s', ifnm )
        s = openslide.OpenSlide.detect_format(ifnm)
        return (s is not None)

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    def info(self, ifnm, series=0):
        '''returns a dict with file info'''
        if not self.installed:
            return {}
        log.debug('Info for: %s', ifnm )
        with Locks(ifnm):        
            if not os.path.exists(ifnm):
                return {}
            try:
                slide = openslide.OpenSlide(ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                return {}
            info = {
                'format': slide.properties[openslide.PROPERTY_NAME_VENDOR],
                'image_num_series': 0,
                'image_num_x': slide.dimensions[0],
                'image_num_y': slide.dimensions[1],
                'image_num_z': 1,
                'image_num_t': 1,
                'image_num_c': 3,
                'image_num_l': slide.level_count,
                'image_pixel_format': 'unsigned integer', 
                'image_pixel_depth': 8,
                'pixel_resolution_x': slide.properties[openslide.PROPERTY_NAME_MPP_X],
                'pixel_resolution_y': slide.properties[openslide.PROPERTY_NAME_MPP_Y],
                'pixel_resolution_z': 0,
                'pixel_resolution_unit_x': 'microns', 
                'pixel_resolution_unit_y': 'microns', 
                'pixel_resolution_unit_z': 'microns'
            }
            slide.close()
            return info
        return {}

    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    def meta(self, ifnm, series=0):
        if not self.installed:
            return {}
        log.debug('Meta for: %s', ifnm )
        with Locks (ifnm):
            try:
                slide = openslide.OpenSlide(ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                return {}
            rd = {
                'format': slide.properties[openslide.PROPERTY_NAME_VENDOR],
                'image_num_series': 0,
                'image_num_x': slide.dimensions[0],
                'image_num_y': slide.dimensions[1],
                'image_num_z': 1,
                'image_num_t': 1,
                'image_num_c': 3,
                'image_num_l': slide.level_count,
                'image_pixel_format': 'unsigned integer',
                'image_pixel_depth': 8,
                'pixel_resolution_x': slide.properties[openslide.PROPERTY_NAME_MPP_X],
                'pixel_resolution_y': slide.properties[openslide.PROPERTY_NAME_MPP_Y],
                'pixel_resolution_z': 0,
                'pixel_resolution_unit_x': 'microns', 
                'pixel_resolution_unit_y': 'microns', 
                'pixel_resolution_unit_z': 'microns',
                'magnification': slide.properties[openslide.PROPERTY_NAME_OBJECTIVE_POWER],
                'channel_0_name': 'red',
                'channel_1_name': 'green',
                'channel_2_name': 'blue',
                'channel_color_0': '255,0,0',
                'channel_color_1': '0,255,0',
                'channel_color_2': '0,0,255'
            }

            # custom - any other tags in proprietary files should go further prefixed by the custom parent
            for k,v in slide.properties.iteritems():
                rd['custom/%s'%k.replace('.', '/')] = v
            slide.close()
        return rd

    #######################################
    # Conversion
    #######################################

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=[]):
        return None

    @classmethod
    def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=[]):
        return None

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)
        with Locks (ifnm, ofnm):
            try:
                slide = openslide.OpenSlide(ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                return None
            img = slide.get_thumbnail((width, height))
            img.save(ofnm, 'JPEG')
            slide.close()
            return ofnm
        return None

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        return None

    @classmethod
    def tile(cls, ifnm, ofnm, level, x, y, sz, series=0, **kw):
        '''extract Level,X,Y tile from input filename into output in OME-TIFF format'''
        log.debug('Tile: %s %s %s %s %s for [%s]', level, x, y, sz, series, ifnm)
        level = misc.safeint(level, 0)
        x  = misc.safeint(x, 0)
        y  = misc.safeint(y, 0)
        sz = misc.safeint(sz, 0)
        with Locks (ifnm, ofnm):
            try:
                slide = openslide.OpenSlide(ifnm)
            except (openslide.OpenSlideUnsupportedFormatError, openslide.OpenSlideError):
                return None
            dz = deepzoom.DeepZoomGenerator(slide, tile_size=sz, overlap=0)
            img = dz.get_tile(dz.level_count-level-1, (x,y))
            img.save(ofnm, 'TIFF', compression='LZW')
            slide.close()
            return ofnm
        return None

ConverterOpenSlide.init()
