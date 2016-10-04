"""
Return pixel counts of a thresholded image
       pixelcount=value, where value is a threshold
       ex: pixelcount=128
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

__all__ = [ 'PixelCounterOperation' ]

from bq.image_service.controllers.operation_base import BaseOperation
from bq.image_service.controllers.process_token import ProcessToken
from bq.image_service.controllers.converters.converter_imgcnv import ConverterImgcnv
from bq.util.io_misc import safeint
from bq.image_service.controllers.imgsrv import default_format

log = logging.getLogger("bq.image_service.operations.pixelcount")

class PixelCounterOperation(BaseOperation):
    '''Return pixel counts of a thresholded image
       pixelcount=value, where value is a threshold
       ex: pixelcount=128'''
    name = 'pixelcount'

    def __str__(self):
        return 'pixelcount: returns a count of pixels in a thresholded image, ex: pixelcount=128'

    def dryrun(self, token, arg):
        arg = safeint(arg.lower(), 256)-1
        ofile = '%s.pixelcount_%s.xml'%(token.data, arg)
        return token.setXmlFile(fname=ofile)

    def action(self, token, arg):
        if not token.isFile():
            abort(400, 'Pixelcount: input is not an image...' )
        arg = safeint(arg.lower(), 256)-1
        ifile = token.first_input_file()
        ofile = '%s.pixelcount_%s.xml'%(token.data, arg)
        log.debug('Pixelcount %s: %s to %s with [%s]', token.resource_id, ifile, ofile, arg)

        command = token.drainQueue()
        if not os.path.exists(ofile):
            command.extend(['-pixelcounts', str(arg)])
            self.server.imageconvert(token, ifile, ofile, extra=command)

        return token.setXmlFile(fname=ofile)
