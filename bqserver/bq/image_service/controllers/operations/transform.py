"""
Provide an image transform
       arg = transform
       Available transforms are: fourier, chebyshev, wavelet, radon, edge, wndchrmcolor, rgb2hsv, hsv2rgb, superpixels
       ex: transform=fourier
       superpixels requires two parameters: superpixel size in pixels and shape regularity 0-1, ex: transform=superpixels,32,0.5
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

import os
import sys
import math
import logging
import pkg_resources
from lxml import etree
from pylons.controllers.util import abort

__all__ = [ 'TransformOperation' ]

from bq.image_service.controllers.operation_base import BaseOperation
from bq.image_service.controllers.process_token import ProcessToken
from bq.image_service.controllers.converters.imgcnv import ConverterImgcnv
from bq.image_service.controllers.imgsrv import default_format

log = logging.getLogger("bq.image_service.operations.transform")

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
