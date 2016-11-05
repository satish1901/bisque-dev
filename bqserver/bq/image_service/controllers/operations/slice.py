"""
Provide a slice of an image :
       arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2
       Each position may be specified as a range
       empty params imply entire available range
       all values are in ranges [1..N]
       0 or empty - means first element
       ex: slice=,,1,
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

__all__ = [ 'SliceOperation' ]

from bq.image_service.controllers.exceptions import ImageServiceException
from bq.image_service.controllers.operation_base import BaseOperation
from bq.image_service.controllers.process_token import ProcessToken
from bq.image_service.controllers.converters.converter_imgcnv import ConverterImgcnv
from bq.util.io_misc import safeint
from bq.image_service.controllers.imgsrv import default_format

log = logging.getLogger("bq.image_service.operations.slice")

class SliceOperation(BaseOperation):
    '''Provide a slice of an image :
       arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2
       Each position may be specified as a range
       empty params imply entire available range
       all values are in ranges [1..N]
       0 or empty - means first element
       ex: slice=,,1,'''
    name = 'slice'

    def __str__(self):
        return 'slice: returns an image of requested slices, arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2. All values are in ranges [1..N]'

    def dryrun(self, token, arg):
        # parse arguments
        vs = [ [safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return token

        dims = token.dims or {}
        if x1<=1 and x2>=dims.get('image_num_x', 1): x1=0; x2=0
        if y1<=1 and y2>=dims.get('image_num_y', 1): y1=0; y2=0
        if z1<=1 and z2>=dims.get('image_num_z', 1): z1=0; z2=0
        if t1<=1 and t2>=dims.get('image_num_t', 1): t1=0; t2=0

        # check image bounds
        if z1>dims.get('image_num_z', 1):
            raise ImageServiceException(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z1 )
        if z2>dims.get('image_num_z', 1):
            raise ImageServiceException(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z2 )
        if t1>dims.get('image_num_t', 1):
            raise ImageServiceException(400, 'Slice: requested T plane outside of image bounds: [%s]'%t1 )
        if t2>dims.get('image_num_t', 1):
            raise ImageServiceException(400, 'Slice: requested T plane outside of image bounds: [%s]'%t2 )

        # shortcuts are only possible with no ROIs are requested
        if x1==x2==0 and y1==y2==0 and len(dims)>0:
            # shortcut if input image has only one T and Z
            if dims.get('image_num_z', 1)<=1 and dims.get('image_num_t', 1)<=1:
                #log.debug('Slice: plane requested on image with no T or Z planes, skipping...')
                return token
            # shortcut if asking for all slices with only a specific time point in an image with only one time pont
            if z1==z2==0 and t1<=1 and dims.get('image_num_t', 1)<=1:
                #log.debug('Slice: T plane requested on image with no T planes, skipping...')
                return token
            # shortcut if asking for all time points with only a specific z slice in an image with only one z slice
            if t1==t2==0 and z1<=1 and dims.get('image_num_z', 1)<=1:
                #log.debug('Slice: Z plane requested on image with no Z planes, skipping...')
                return token

        if z1==z2==0: z1=1; z2=dims.get('image_num_z', 1)
        if t1==t2==0: t1=1; t2=dims.get('image_num_t', 1)

        new_w = x2-x1
        new_h = y2-y1
        new_z = max(1, z2 - z1 + 1)
        new_t = max(1, t2 - t1 + 1)
        info = {
            'image_num_z': new_z,
            'image_num_t': new_t,
        }
        if new_w>0: info['image_num_x'] = new_w+1
        if new_h>0: info['image_num_y'] = new_h+1

        ofname = '%s.%d-%d,%d-%d,%d-%d,%d-%d.ome.tif' % (token.data, x1,x2,y1,y2,z1,z2,t1,t2)
        return token.setImage(ofname, fmt=default_format, dims=info, input=ofname)

    def action(self, token, arg):
        '''arg = x1-x2,y1-y2,z|z1-z2,t|t1-t2'''

        if not token.isFile():
            raise ImageServiceException(400, 'Slice: input is not an image...' )

        # parse arguments
        vs = [ [safeint(i, 0) for i in vs.split('-', 1)] for vs in arg.split(',')]
        for v in vs:
            if len(v)<2: v.append(0)
        for v in range(len(vs)-4):
            vs.append([0,0])
        x1,x2 = vs[0]; y1,y2 = vs[1]; z1,z2 = vs[2]; t1,t2 = vs[3]

        # in case slices request an exact copy, skip
        if x1==0 and x2==0 and y1==0 and y2==0 and z1==0 and z2==0 and t1==0 and t2==0:
            return token

        dims = token.dims or {}
        if x1<=1 and x2>=dims.get('image_num_x', 1): x1=0; x2=0
        if y1<=1 and y2>=dims.get('image_num_y', 1): y1=0; y2=0
        if z1<=1 and z2>=dims.get('image_num_z', 1): z1=0; z2=0
        if t1<=1 and t2>=dims.get('image_num_t', 1): t1=0; t2=0

        # check image bounds
        if z1>dims.get('image_num_z', 1):
            raise ImageServiceException(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z1 )
        if z2>dims.get('image_num_z', 1):
            raise ImageServiceException(400, 'Slice: requested Z slice outside of image bounds: [%s]'%z2 )
        if t1>dims.get('image_num_t', 1):
            raise ImageServiceException(400, 'Slice: requested T plane outside of image bounds: [%s]'%t1 )
        if t2>dims.get('image_num_t', 1):
            raise ImageServiceException(400, 'Slice: requested T plane outside of image bounds: [%s]'%t2 )

        # shortcuts are only possible with no ROIs are requested
        if x1==x2==0 and y1==y2==0:
            # shortcut if input image has only one T and Z
            if dims.get('image_num_z', 1)<=1 and dims.get('image_num_t', 1)<=1:
                log.debug('Slice: plane requested on image with no T or Z planes, skipping...')
                return token
            # shortcut if asking for all slices with only a specific time point in an image with only one time pont
            if z1==z2==0 and t1<=1 and dims.get('image_num_t', 1)<=1:
                log.debug('Slice: T plane requested on image with no T planes, skipping...')
                return token
            # shortcut if asking for all time points with only a specific z slice in an image with only one z slice
            if t1==t2==0 and z1<=1 and dims.get('image_num_z', 1)<=1:
                log.debug('Slice: Z plane requested on image with no Z planes, skipping...')
                return token

        if z1==z2==0: z1=1; z2=dims.get('image_num_z', 1)
        if t1==t2==0: t1=1; t2=dims.get('image_num_t', 1)

        # construct a sliced filename
        ifname = token.first_input_file()
        ofname = '%s.%d-%d,%d-%d,%d-%d,%d-%d.ome.tif' % (token.data, x1,x2,y1,y2,z1,z2,t1,t2)
        log.debug('Slice %s: from [%s] to [%s]', token.resource_id, ifname, ofname)

        new_w = x2-x1
        new_h = y2-y1
        new_z = max(1, z2 - z1 + 1)
        new_t = max(1, t2 - t1 + 1)
        info = {
            'image_num_z': new_z,
            'image_num_t': new_t,
        }
        if new_w>0: info['image_num_x'] = new_w+1
        if new_h>0: info['image_num_y'] = new_h+1

        meta = token.meta or {}
        unsupported_multifile = False
        if token.is_multifile_series() is True and (z2==0 or z2==z1) and (t2==0 or t2==t1) and x1==x2 and y1==y2 and meta.get('image_num_c', 0)==0:
            unsupported_multifile = True

        if dims.get('converter', '') == ConverterImgcnv.name or unsupported_multifile is True:
            r = ConverterImgcnv.slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format)
            # if decoder returned a list of operations for imgcnv to enqueue
            if isinstance(r, list):
                return self.server.enqueue(token, 'slice', ofname, fmt=default_format, command=r, dims=info)

        # slice the image
        if not os.path.exists(ofname):
            intermediate = '%s.ome.tif'%token.data

            if 'converter' in dims and dims.get('converter') in self.server.converters:
                r = self.server.converters[dims.get('converter')].slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format, intermediate=intermediate)

            # if desired converter failed, perform exhaustive conversion
            if r is None:
                for n,c in self.server.converters.iteritems():
                    if n in [ConverterImgcnv.name, dims.get('converter')]: continue
                    r = c.slice(token, ofname, z=(z1,z2), t=(t1,t2), roi=(x1,x2,y1,y2), fmt=default_format, intermediate=intermediate)
                    if r is not None:
                        break

            if r is None:
                log.error('Slice %s: could not generate slice for [%s]', token.resource_id, ifname)
                raise ImageServiceException(415, 'Could not generate slice' )

            # if decoder returned a list of operations for imgcnv to enqueue
            if isinstance(r, list):
                return self.server.enqueue(token, 'slice', ofname, fmt=default_format, command=r, dims=info)

        return token.setImage(ofname, fmt=default_format, dims=info, input=ofname)
