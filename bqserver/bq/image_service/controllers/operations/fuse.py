"""
Provide an RGB image with the requested channel fusion
       arg = W1R,W1G,W1B;W2R,W2G,W2B;W3R,W3G,W3B;W4R,W4G,W4B
       output image will be constructed from channels 1 to n from input image mapped to RGB components with desired weights
       fuse=display will use preferred mapping found in file's metadata
       ex: fuse=255,0,0;0,255,0;0,0,255;255,255,255:A
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

__all__ = [ 'FuseOperation' ]

from bq.image_service.controllers.operation_base import BaseOperation
from bq.image_service.controllers.process_token import ProcessToken
from bq.image_service.controllers.converters.converter_imgcnv import ConverterImgcnv
from bq.image_service.controllers.imgsrv import default_format

log = logging.getLogger("bq.image_service.operations.fuse")

class FuseOperation(BaseOperation):
    """Provide an RGB image with the requested channel fusion
       arg = W1R,W1G,W1B;W2R,W2G,W2B;W3R,W3G,W3B;W4R,W4G,W4B
       output image will be constructed from channels 1 to n from input image mapped to RGB components with desired weights
       fuse=display will use preferred mapping found in file's metadata
       ex: fuse=255,0,0;0,255,0;0,0,255;255,255,255:A"""
    name = 'fuse'

    def __str__(self):
        return 'fuse: returns an RGB image with the requested channel fusion, arg = W1R,W1G,W1B;W2R,W2G,W2B;...[:METHOD]'

    def dryrun(self, token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        elif '.' in arg:
            (arg, method) = arg.split('.', 1)
        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])
        ofile = '%s.fuse_%s_%s'%(token.data, argenc, method)
        return token.setImage(fname=ofile, fmt=default_format)

    def action(self, token, arg):
        method = 'a'
        arg = arg.lower()
        if ':' in arg:
            (arg, method) = arg.split(':', 1)
        elif '.' in arg:
            (arg, method) = arg.split('.', 1)

        argenc = ''.join([hex(int(i)).replace('0x', '') for i in arg.replace(';', ',').split(',') if i is not ''])

        ifile = token.first_input_file()
        ofile = '%s.fuse_%s_%s'%(token.data, argenc, method)
        log.debug('Fuse %s: %s to %s with [%s:%s]', token.resource_id, ifile, ofile, arg, method)

        if arg == 'display':
            args = ['-fusemeta']
        else:
            args = ['-fusergb', arg]
        if method != 'a':
            args.extend(['-fusemethod', method])

        info = {
            'image_num_c': 3,
        }
        return self.server.enqueue(token, 'fuse', ofile, fmt=default_format, command=args, dims=info)
