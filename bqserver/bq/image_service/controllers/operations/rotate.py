"""
Provides rotated versions for requested images:
       arg = angle
       At this moment only supported values are 90, -90, 270, 180 and guess
       ex: rotate=90
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

__all__ = [ 'RotateOperation' ]

from bq.image_service.controllers.operation_base import BaseOperation
from bq.image_service.controllers.process_token import ProcessToken
from bq.image_service.controllers.converters.converter_imgcnv import ConverterImgcnv
from bq.image_service.controllers.imgsrv import default_format

log = logging.getLogger("bq.image_service.operations.rotate")

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
