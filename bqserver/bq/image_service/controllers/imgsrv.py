""" ImageServer for Bisque system.
"""

__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "2.0.9"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
import logging
import os.path
import shutil
import re
import StringIO
from urllib import quote
from urllib import unquote
from urlparse import urlparse
from lxml import etree
import datetime
import math

from tg import config
from pylons.controllers.util import abort

#Project
from bq import data_service
from bq import blob_service
from bq.blob_service.controllers.blob_drivers import Blobs

from bq.core import  identity
from bq.util.mkdir import _mkdir
#from collections import OrderedDict
from bq.util.compat import OrderedDict
from bq.util.urlpaths import url2localpath

from bq.util.locks import Locks
from bq.util.io_misc import safetypeparse, safeint


default_format = 'bigtiff'
default_tile_size = 512
min_level_size = 128
converters_preferred_order = ['openslide', 'imgcnv', 'ImarisConvert', 'bioformats']


from .process_token import ProcessToken
from .operation_base import BaseOperation
from .converter_dict import ConverterDict
from .resource_cache import ResourceCache

from .converters.imgcnv import ConverterImgcnv
from .converters.imaris import ConverterImaris
from .converters.bioformats import ConverterBioformats
from .converters.openslide import ConverterOpenSlide

from .operations.operations import OperationsOperation
from .operations.formats import FormatsOperation
from .operations.view import ViewOperation
from .operations.dims import DimsOperation
from .operations.meta import MetaOperation
from .operations.localpath import LocalPathOperation
from .operations.cleancache import CacheCleanOperation
from .operations.slice import SliceOperation
from .operations.format import FormatOperation
from .operations.resize import ResizeOperation, Resize3DOperation
from .operations.rearrange3d import Rearrange3DOperation
from .operations.thumbnail import ThumbnailOperation
from .operations.roi import RoiOperation
from .operations.remap import RemapOperation
from .operations.fuse import FuseOperation
from .operations.depth import DepthOperation
from .operations.tile import TileOperation
from .operations.intensityprojection import IntensityProjectionOperation
from .operations.negative import NegativeOperation
from .operations.deinterlace import DeinterlaceOperation
from .operations.threshold import ThresholdOperation
from .operations.pixelcount import PixelCounterOperation
from .operations.histogram import HistogramOperation
from .operations.levels import LevelsOperation
from .operations.brightnesscontrast import BrightnessContrastOperation
from .operations.textureatlas import TextureAtlasOperation
from .operations.transform import TransformOperation
from .operations.sampleframes import SampleFramesOperation
from .operations.frames import FramesOperation
from .operations.rotate import RotateOperation


log = logging.getLogger('bq.image_service.server')


################################################################################
# Create a list of querie tuples
################################################################################

def getQuery4Url(url):
    scheme, netloc, url, params, querystring, fragment = urlparse(url)

    #pairs = [s2 for s1 in querystring.split('&') for s2 in s1.split(';')]
    pairs = [s1 for s1 in querystring.split('&')]
    query = []
    for name_value in pairs:
        if not name_value:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            nv.append('')

        name = unquote(nv[0].replace('+', ' '))
        value = unquote(nv[1].replace('+', ' '))
        query.append((name, value))

    return query

def newUrl2Query(url, base):
    query = []
    path = filter(None, url.split('/')) # split and remove empty
    path = path[path.index(base)+1:] # isolate query part
    if path[0].lower() == 'image' or path[0].lower() == 'images':
        path = path[1:]

    resource_id = path[0]
    path = path[1:]
    for p in path:
        v = p.split(':', 1)
        name = unquote(v[0].replace('+', ' '))
        try:
            value = unquote(v[1].replace('+', ' '))
        except IndexError:
            value = ''
        query.append((name, value))
    return resource_id, query


def getOperations(url, base):
    if '?' in url:
        return None, getQuery4Url(url)
    else:
        return newUrl2Query(url, base)

################################################################################
# ImageServer
################################################################################

class ImageServer(object):

    converters = ConverterDict([
        (ConverterOpenSlide.name,   ConverterOpenSlide()),
        (ConverterImgcnv.name,      ConverterImgcnv()),
        (ConverterImaris.name,      ConverterImaris()),
        (ConverterBioformats.name,  ConverterBioformats()),
    ])
    writable_formats = {}

    # cache resources and blob locations
    cache = ResourceCache()

    @classmethod
    def init_converters(cls):
        # test all the supported command line decoders and remove missing
        missing = []
        for n,c in cls.converters.iteritems():
            if not c.get_installed():
                log.debug('%s is not installed, skipping support...', n)
                missing.append(n)
            # elif not c.ensure_version(needed_versions[n]):
            #     log.warning('%s needs update! Has: %s Needs: %s', n, c.version['full'], needed_versions[n])
            #     missing.append(n)
        for m in missing:
            cls.converters.pop(m)


        log.info('Available converters: %s', str(cls.converters))
        if ConverterImgcnv.name not in cls.converters:
            log.warn('imgcnv was not found, it is required for most of image service operations! Make sure to install it!')

        cls.writable_formats = cls.converters.converters(readable=False, writable=True, multipage=False)

    def __init__(self, work_dir, run_dir):
        '''Start an image server, using local dir imagedir,
        and loading extensions as methods'''
        #super(ImageServer, self).__init__(image_dir, server_url)
        self.workdir = work_dir
        self.rundir = run_dir
        self.base_url = "image_service"

        self.operations = {
            'view'         : ViewOperation(self),
            'operations'   : OperationsOperation(self),
            'formats'      : FormatsOperation(self),
            #'info'         : InfoOperation(self),
            'dims'         : DimsOperation(self),
            'meta'         : MetaOperation(self),
            #'filename'     : FileNameOperation(self),
            'localpath'    : LocalPathOperation(self),
            'slice'        : SliceOperation(self),
            'format'       : FormatOperation(self),
            'resize'       : ResizeOperation(self),
            'resize3d'     : Resize3DOperation(self),
            'rearrange3d'  : Rearrange3DOperation(self),
            'thumbnail'    : ThumbnailOperation(self),
            'roi'          : RoiOperation(self),
            'remap'        : RemapOperation(self),
            'fuse'         : FuseOperation(self),
            'depth'        : DepthOperation(self),
            'rotate'       : RotateOperation(self),
            'tile'         : TileOperation(self),
            'intensityprojection'   : IntensityProjectionOperation(self),
            #'projectmax'   : ProjectMaxOperation(self),
            #'projectmin'   : ProjectMinOperation(self),
            'negative'     : NegativeOperation(self),
            'deinterlace'  : DeinterlaceOperation(self),
            'threshold'    : ThresholdOperation(self),
            'pixelcounter' : PixelCounterOperation(self),
            'histogram'    : HistogramOperation(self),
            'levels'       : LevelsOperation(self),
            'brightnesscontrast' : BrightnessContrastOperation(self),
            'textureatlas' : TextureAtlasOperation(self),
            'transform'    : TransformOperation(self),
            'sampleframes' : SampleFramesOperation(self),
            'frames'       : FramesOperation(self),
            'cleancache'   : CacheCleanOperation(self),
        }


        # # test all the supported command line decoders and remove missing
        # missing = []
        # for n,c in self.converters.iteritems():
        #     if not c.get_installed():
        #         log.debug('%s is not installed, skipping support...', n)
        #         missing.append(n)
        #     # elif not c.ensure_version(needed_versions[n]):
        #     #     log.warning('%s needs update! Has: %s Needs: %s', n, c.version['full'], needed_versions[n])
        #     #     missing.append(n)
        # for m in missing:
        #     self.converters.pop(m)


        # log.info('Available converters: %s', str(self.converters))
        # if ConverterImgcnv.name not in self.converters:
        #     log.warn('imgcnv was not found, it is required for most of image service operations! Make sure to install it!')

        # self.writable_formats = self.converters.converters(readable=False, writable=True, multipage=False)

        img_threads = config.get ('bisque.image_service.imgcnv.omp_num_threads', None)
        if img_threads is not None:
            log.info ("Setting OMP_NUM_THREADS = %s", img_threads)
            os.environ['OMP_NUM_THREADS'] = "%s" % img_threads


    def ensureOriginalFile(self, ident, resource=None):
        # if resource is not None:
        #     vs = resource.xpath('value')
        #     if len(vs)>0:
        #         files = [v.text for v in vs]
        #     else:
        #         files = [resource.get('value')]
        #     log.debug('files: %s', files)
        #     if files[0].startswith('file://'):
        #         files = ['path%s'%f.replace('file://', '') for f in files]
        #         log.debug('files: %s', files)
        #         return Blobs(path=files[0], sub=None, files=files if len(files)>1 else None)

        #return blob_service.localpath(ident, resource=resource) or abort (404, 'File not available from blob service')
        blobs = self.cache.get_blobs(ident)
        return blobs or abort (404, 'File not available from blob service')

    def getImageInfo(self, filename, series=0, infofile=None, meta=None):
        if infofile is None:
            infofile = '%s.info'%filename
        info = {}

        # sanity check
        if not os.path.exists(filename):
            return None

        # read image info using converters
        if not os.path.exists(infofile):
            with Locks(filename, infofile, failonexist=True) as l:
                if l.locked: # the file is not being currently written by another process
                    # parse image info from original file
                    for n,c in self.converters.iteritems():
                        info = c.info(ProcessToken(ifnm=filename, series=series))
                        if info is not None and len(info)>0:
                            info['converter'] = n
                            break
                    if info is None or 'image_num_x' not in info:
                        return None

                    info.setdefault('image_num_t', 1)
                    info.setdefault('image_num_z', 1)
                    info.setdefault('image_num_p', info['image_num_t'] * info['image_num_z'])
                    info.setdefault('format', default_format)
                    if not 'filesize' in info:
                        info.setdefault('filesize', os.path.getsize(filename))
                    if meta is not None:
                        info.update(meta)

                    # cache file info into a file
                    image = etree.Element ('image')
                    for k,v in info.iteritems():
                        image.set(k, '%s'%v)
                    with open(infofile, 'w') as f:
                        f.write(etree.tostring(image))
                    return info

        # info file exists
        with Locks(infofile):
            try:
                image = etree.parse(infofile).getroot()
                for k,v in image.attrib.iteritems():
                    info[k] = safetypeparse(v)
                return info
            except  etree.XMLSyntaxError:
                log.debug ("attempt to read empty info file")
        return None

    def process_queue(self, token):
        ofile = token.data
        if token.isFile() and len(token.queue)>0 and not os.path.exists(ofile):
            ifile = token.first_input_file()
            command = token.drainQueue()
            log.debug('Executing enqueued commands %s: %s to %s with %s', token.resource_id, ifile, ofile, command)
            self.imageconvert(token, ifile, ofile, fmt=token.format, extra=command)
            token.input = ofile
        if token.isFile() and len(token.queue)<1 and not os.path.exists(ofile):
            token.data = token.first_input_file()
        return token

    def enqueue(self, token, op_name, ofnm, fmt=None, command=None, dims=None, **kw):
        log.debug('Enqueueing %s for %s with %s', op_name, ofnm, command)
        token.data = ofnm
        if fmt is not None:
            #token.format = fmt
            token.setFormat(fmt=fmt)
        if command is not None:
            #token.queue[op_name] = command
            token.queue.extend(command)
        if dims is not None:
            token.dims.update(dims)
        log.debug('Queue: %s', token.getQueue())
        return token

    def imageconvert(self, token, ifnm, ofnm, fmt=None, extra=None, dims=None, **kw):
        if not token.isFile():
            abort(400, 'Convert: input is not an image...' )
        fmt = fmt or token.format or default_format

        command = []

        # dima: FIXME, extra was being appended before the queue
        if extra is not None:
            command.extend(extra)

        if token.hasQueue():
            command.extend(token.drainQueue())

        # dima: FIXME, extra was being appended before the queue
        #if extra is not None:
        #    command.extend(extra)

        # create pyramid for large images
        dims = dims or token.dims or {}
        if dims.get('image_num_x',0)>4000 and dims.get('image_num_y',0)>4000 and 'tiff' in fmt and '-options' not in command:
            command.extend(['-options', 'compression lzw tiles %s pyramid subdirs'%default_tile_size])

        if token.histogram is not None:
            command.extend(['-ihst', token.histogram])

        if kw.get('try_imgcnv', True) is True:
            r = self.converters[ConverterImgcnv.name].convert( token, ofnm, fmt=fmt, extra=command, respect_command_inputs=True, **kw)
            if r is not None:
                return r

        # if the conversion failed, convert input to OME-TIFF using other converts
        # typically we should be strating from the original file here, if we failed somewhere in the middle, there's a bigger problem
        r = None
        ometiff = '%s.ome.tif'%(token.initial_workpath or token.data)
        if os.path.exists(ometiff) and os.path.getsize(ometiff)>16:
            r = ometiff
        else:
            # try converter used to read info
            n = dims.get('converter')
            if n in self.converters and callable( getattr(self.converters[n], "convertToOmeTiff", None) ) is True:
                r = self.converters[n].convertToOmeTiff(token, ometiff, **kw)

            # if desired converter failed, perform exhaustive conversion
            if r is None:
                for n,c in self.converters.iteritems():
                    if n in [ConverterImgcnv.name, dims.get('converter')]: continue
                    r = c.convertToOmeTiff(token, ometiff, **kw)
                    if r is not None:
                        break

            if r is None or os.path.getsize(ometiff)<16:
                log.error('Convert %s: failed for [%s]', token.resource_id, ifnm)
                abort(415, 'Convert failed' )

        return self.converters[ConverterImgcnv.name].convert( ProcessToken(ifnm=ometiff), ofnm, fmt=fmt, extra=command)

    def initialWorkPath(self, image_id, user_name):
        if len(image_id)>3 and image_id[2]=='-':
            subdir = image_id[3]
        else:
            subdir = image_id[0]
        return os.path.realpath(os.path.join(self.workdir, user_name or '', subdir, image_id))

    def ensureWorkPath(self, path, image_id, user_name):
        """path may be a workdir path OR an original image path to transformed into
        a workdir path
        """
        # change ./imagedir to ./workdir if needed
        path = os.path.realpath(path)
        workpath = os.path.realpath(self.workdir)
        if image_id and not path.startswith (workpath):
            path = self.initialWorkPath(image_id, user_name)
        # keep paths relative to running dir to reduce file name size
        path = os.path.relpath(path, self.rundir)
        # make sure that the path directory exists
        _mkdir( os.path.dirname(path) )
        return path

    def request(self, method, token, arguments):
        '''Apply an image request'''
        if method not in self.operations:
            abort(400, 'Requested operation does not exist: %s'%method)
        return self.operations[method].action (token, arguments)
        # try:
        #     return self.operations[method].action (token, arguments)
        # except Exception:
        #     log.exception('Exception running: %s', method)
        #     return token

    def process(self, url, ident, resource=None, **kw):
        resource_id, query = getOperations(url, self.base_url)
        log.debug ('STARTING %s: %s', ident, query)
        #os.chdir(self.workdir)
        log.debug('Current path %s: %s', ident, self.workdir)

        if resource is None:
            resource = {}

        # init the output to a simple file
        token = ProcessToken()

        if ident is not None:
            # pre-compute final filename and check if it exists before starting any other processing
            if len(query)>0:
                token.setFile(self.initialWorkPath(ident, user_name=kw.get('user_name', None)))
                token.dims = self.getImageInfo(filename=token.data, series=token.series, infofile='%s.info'%token.data, meta=kw.get('imagemeta', None) )
                token.init(resource_id=ident, ifnm=token.data, imagemeta=kw.get('imagemeta', None), timeout=kw.get('timeout', None), resource_name=resource.get('name'))
                for action, args in query:
                    try:
                        service = self.operations[action]
                        # if the service has a dryrun function, some actions are same as dryrun
                        if callable( getattr(service, "dryrun", None) ):
                            token = service.dryrun(token, args)
                        else:
                            token = service.action(token, args)
                        log.debug ('DRY run: %s producing: %s', action, token.data)
                    except Exception:
                        pass
                    if token.isHttpError():
                        break
                localpath = os.path.join(os.path.realpath(self.workdir), token.data)
                log.debug('Dryrun test %s: [%s] [%s]', ident, localpath, str(token))
                if token.isFile() and os.path.exists(localpath):
                    log.debug('FINISHED %s: returning pre-cached result %s', ident, token.data)
                    with Locks(token.data):
                        pass
                    return token

            log.debug('STARTING full processing %s: with %s', ident, token)

            # ----------------------------------------------
            # start the processing
            b = self.ensureOriginalFile(ident, resource=resource)
            #log.debug('Original %s, %s, %s', b.path, b.sub, b.files)
            workpath = self.ensureWorkPath(b.path, ident, user_name=kw.get('user_name', None))
            token.setFile(workpath, series=(b.sub or 0))
            token.init(resource_id=ident, ifnm=b.path, imagemeta=kw.get('imagemeta', None), files=b.files, timeout=kw.get('timeout', None), resource_name=resource.get('name'), initial_workpath=workpath)

            if not os.path.exists(b.path):
                abort(404, 'File not found...')

            if len(query)>0:
                token.dims = self.getImageInfo(filename=token.first_input_file(), series=token.series, infofile='%s.info'%token.data, meta=token.meta)
                if token.dims is None or 'image_num_x' not in token.dims:
                    abort(415, 'File format is not supported...')
                # overwrite fields from resource image meta
                if token.meta is not None:
                    token.dims.update(token.meta)

        #process all the requested operations
        for action,args in query:
            log.debug ('ACTION %s: %s', ident, action)
            token = self.request(action, token, args)
            if token.isHttpError():
                break
        token = self.process_queue(token)

        # test output, if it is a file but it does not exist, set 404 error
        token.testFile()

        # if the output is a file but not an image or no processing was done to it
        # set to the original file name
        if token.isFile() and not token.isImage() and not token.isText() and not token.hasFileName():
            token.contentType = 'application/octet-stream'
            token.outFileName = token.resource_name

        # if supplied file name overrides filename
        for action,args in query:
            if (action.lower() == 'filename'):
                token.outFileName = args
                break

        log.debug ('FINISHED %s: %s', ident, query)
        return token


try:
    ImageServer.init_converters()
except Exception:
    log.warn("ImageServer is not available")
