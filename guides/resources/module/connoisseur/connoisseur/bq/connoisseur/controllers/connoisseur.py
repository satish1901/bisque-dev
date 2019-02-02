###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
## Copyright (c) 2017-2018 by the Regents of the University of California    ##
## Copyright (c) 2017-2018 (C) ViQi Inc                                      ##
## All rights reserved                                                       ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgment: This product   ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################

"""
Connoisseur : classification service

INFO API
==============

GET /connoisseur
or
GET /connoisseur/info

CLASSIFICATION API
====================

GET /connoisseur/MODEL_ID/classify:IMAGE_ID
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:points] # default, classify uniformly distributed points
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:points_random] # classify randomly distributed points
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:segmentation] # segment image pixels producing image mask with class labels
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:regions] # partition image into regions producing low-res polygons

GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:salient] #
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:salient_uniform] #
GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:image] #

Parameters for all methods:

points: number of output points, approximate for some methods
goodness: % (0-100), minimum sample goodness for an output point
border: % (0-100) of the image size, border in pixels will be estimated from image's dimensions
accuracy: % (0-100), minimum class accuracy for an output point
confidence: % (0-100), minimum confidence (combination of goodness and accuracy) for an output point

# parameters for point classification random and uniform
GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points[/points:10][/goodness:95][/border:5][/format:csv]

format: xml, json, csv, hdf

# parameters for region partitioning
GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:regions[/points:10][/goodness:95][/border:5][/format:csv]

format: xml, json, csv, hdf

# parameters for segmentation
GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:segmentation[/points:10][/goodness:95][/border:5][/colors:ids]
GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:segmentation[/points:10][/goodness:95][/border:5][/colors:colors]

formats: png


MODEL INFO API
================

GET /connoisseur/MODEL_ID/class:3/sample:1


RESTful API
=============

    GET - request classification, preview or training

Responses:
    204 Empty results
    400 Bad Request
    401 Unauthorized
    500 Internal Server Error
    501 Not Implemented

MODEL DEFINITION
==================

See classifier_model.py

CLASSIFIER OUTPUTS
==================

[table/gobs]
gob type: str | gob label: str | gob vertices: [(x,y,z,...)] | goodness: float | accuracy: float | color: str

[image/png]
bytes...


STATUS WORKFLOW
==================

1. new
2. classes loaded    <-----   # needs to re-load all files from template and repeat all steps: 3-8
3. classes filtered       |
4. samples loaded    <-----   # needs to re-split the samples and other steps: 5-8
5. samples split          |
6. trained                |
7. validated              |
8. finished          ------

TRAINING WORKFLOW
===================

The model resource is created by the JS UI and initially may only contain a user-given name and a dataset to train on.
After the model resource is created in the system several operations may be requested following a typical training sequence.

1. Define required model parameters
    a. Pick a model template to fine-tune or train from scratch
    b. This should define a "mode", currently point classification but later also fully convolutional

2. Find classes for the model, this will lock the model for current classes and will not allow further changes

3. Create training samples, using parameters defined in the model. This can be repeated to augment the sample list
    a. Absolute minimum number of samples per class
    b. Minimum number of samples to activate sample augmentation

4. Train on available samples
    a. train the model
    b. validate the model and update classes performance

5. Set classes that will be used for classification based on observed performance in the training step

6. Model is ready for recognition

6. Repeat step 3 and further to improve the model


MODEL MODIFICATION API
========================

GET /connoisseur/create/template:CaffeNet[/dataset:UUID]
GET /connoisseur/MODEL_ID/update[/classes:init][/classes:filter][/samples:init][/samples:update][/samples:split]
GET /connoisseur/MODEL_ID/train[/method:finetune][/method:snapshot]
GET /connoisseur/MODEL_ID/validate

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

# default imports
import os
import logging
#import cPickle as pickle

#import sys
import inspect
#from datetime import datetime
from six.moves import urllib
#import cStringIO as StringIO
#from urllib import quote
#from urllib import unquote
#import inspect
#from itertools import *
#import random
#import math
import shutil

import pkg_resources
from lxml import etree
import numpy as np
from PIL import Image
import skimage.io

from tg import expose, request, response, require, config
from repoze.what import predicates
#from pylons.i18n import ugettext as _, lazy_ugettext as l_
from pylons.controllers.util import abort, forward
from repoze.what.predicates import Any, in_group
from paste.fileapp import FileApp


from bqapi import *
from bq.core.service import ServiceController
from bq.core import identity
from bq import data_service
#from bq import blob_service
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir

from .exceptions import ConnoisseurException
from .plugin_manager import PluginManager
from .framework_base import FrameworkBase
from .classifier_base import ClassifierBase
from .adapter_base import AdapterGobjectsBase, AdapterPixelsBase
from .importer_base import ImporterBase
from .exporter_base import ExporterBase
from .ximage import XImage
from .utils import http_parse_accept, http_parse_content_type
from .classifier_model import ClassifierModel
from . import  responses

log = logging.getLogger("bq.connoisseur")

format_as_mime_type = {
    'xml':  'text/xml',
    'json': 'application/json',
    'csv':  'text/csv',
    'hdf':  'application/x-hdf',
}

################################################################################
# ConnoisseurController
################################################################################

class ConnoisseurController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()

    service_type = "connoisseur"

    allow_only = Any(in_group("admin"), in_group('admins'), in_group (service_type))

    def __init__(self, server_url):
        super(ConnoisseurController, self).__init__(server_url)
        self.basepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        self.workdir = config.get('bisque.connoisseur.models', data_path('connoisseur'))
        #_mkdir (self.workdir)

        self.path_models = os.path.join(self.workdir, 'models')
        self.path_templates = os.path.join(self.workdir, 'templates')
        self.path_images = os.path.join(self.workdir, 'images')
        _mkdir (self.path_models)
        _mkdir (self.path_templates)
        _mkdir (self.path_images)


        self.adapters_gobs = PluginManager('adapters_gobs', os.path.join(self.basepath, 'adapters_gobs'), AdapterGobjectsBase)
        self.adapters_pixels = PluginManager('adapters_pixels', os.path.join(self.basepath, 'adapters_pixels'), AdapterPixelsBase)

        # frameworks available in the system
        self.frameworks = PluginManager('frameworks', os.path.join(self.basepath, 'frameworks'), FrameworkBase)

        # classifiers available to the system, requested with method argument
        self.classifiers = PluginManager('classifiers', os.path.join(self.basepath, 'classifiers'), ClassifierBase)

        # importers are matched by their input mime and output mime
        self.importers = PluginManager('importers', os.path.join(self.basepath, 'importers'), ImporterBase)
        self.importers_by_mime = {'%s;%s'%(e.mime_input, e.mime_type): e for k,e in self.importers.plugins.iteritems()}
        #log.debug('Importers: %s', self.importers_by_mime)

        # exporters are matched by their input mime and output mime
        self.exporters = PluginManager('exporters', os.path.join(self.basepath, 'exporters'), ExporterBase)
        self.exporters_by_mime = {'%s;%s'%(e.mime_input, e.mime_type): e for k,e in self.exporters.plugins.iteritems()}
        #log.debug('Exporters: %s', self.exporters_by_mime)

        # loaded models hashed by their ID
        self.models_loaded_max = 10
        self.models = {}

        log.info('Connoisseur service started, using temp space at: %s'%self.workdir)

    #----------------------------------------------------------------------------------------------
    # RESTful API
    #----------------------------------------------------------------------------------------------

    #@expose('bq.connoisseur.templates.index')
    @expose(content_type='text/xml')
    def index(self, **kw):
        """Add your service description here """
        self.log_start()
        try:
            return self.info()
        finally:
            self.log_finish()

    @expose()
    @require(predicates.not_anonymous(msg='Requires authenticated users'))
    def _default(self, *args, **kw):
        """find export plugin and run export"""
        self.log_start()
        path = request.path_qs.replace(self.baseuri, '', 1).split('/')
        path = [urllib.parse.unquote(p) for p in path if len(p)>0]
        log.debug("Path: %s", path)

        #GET /connoisseur/MODEL_ID/classify:IMAGE_ID
        #GET /connoisseur/MODEL_ID/classify:IMAGE_ID/points:100

        #GET /connoisseur/MODEL_ID/train
        #GET /connoisseur/MODEL_ID/class:3/sample:1

        if len(path)<1:
            #abort(responses.BAD_REQUEST, 'resource ID is required as a first parameter, ex: /connoisseur/MODEL_ID/classify:IMAGE_ID' )
            return self.info()
        model_uniq = path.pop(0)

        # parse URL: read all operations and arguments
        args = {}
        while len(path)>0:
            o = path.pop(0)
            try:
                n,v = o.split(':', 1)
                args[n.lower()] = v
            except ValueError:
                args[o.lower()] = None

        # operations not requiring model uniq id
        op = model_uniq.lower()
        if op in ['info', 'api', 'devices', 'templates', 'template', 'create']:
            try:
                if op in ['info', 'api']:
                    return self.info()
                elif op in ['devices']:
                    return self.devices()
                elif op in ['templates']:
                    return self.templates(args)
                elif op in ['template']:
                    return self.template(args)
                elif op in ['create']:
                    return self.create(args)
            except ConnoisseurException, e:
                abort(e.code, e.message)
            except Exception:
                log.exception('Error processing %s', op)
                abort(responses.INTERNAL_SERVER_ERROR, 'Server error')
            finally:
                self.log_finish()
            return

        # run operations
        try:
            # check permissions
            resource_model = self.check_access(model_uniq)
            log.debug('Model: %s', etree.tostring(resource_model))

            # parse some important headers
            accept = http_parse_accept(request.headers['Accept'])
            if accept is not None: args['_http_accept'] = accept
            content_type = http_parse_content_type(request.headers['Content-Type'])
            if content_type is not None: args['_http_content_type'] = content_type

            # process body if needed and augment args
            if request.method == 'POST' and request.body is not None:
                args['_http_body'] = request.body

            if 'info' in args:
                return self.info()
            elif 'class' in args:
                return self.preview(model_uniq, args)
            elif 'classify' in args:
                return self.classify(model_uniq, args)
            elif 'update' in args:
                return self.update(model_uniq, args)
            elif 'train' in args:
                return self.train(model_uniq, args)
            elif 'validate' in args:
                return self.validate(model_uniq, args)
            #elif 'complete' in args:
            #    return self.complete(model_uniq, args)
        except ConnoisseurException, e:
            abort(e.code, e.message)
        except Exception:
            log.exception('Error processing %s', str(args))
            abort(responses.INTERNAL_SERVER_ERROR, 'Server error')
        finally:
            self.log_finish()

    #----------------------------------------------------------------------------------------------
    # Internal API
    #----------------------------------------------------------------------------------------------

    def run_classify(self, model_uniq, args):
        self.log_start()
        try:
            # check permissions
            resource_model = self.check_access(model_uniq)
            log.debug('Model: %s', etree.tostring(resource_model))

            return self.classify(model_uniq, args)
        finally:
            self.log_finish()

    #----------------------------------------------------------------------------------------------
    # info for API
    #----------------------------------------------------------------------------------------------

    def info(self):
        response.headers['Content-Type'] = 'text/xml'

        xml = etree.Element ('resource', type='API', uri=self.baseuri)
        etree.SubElement(xml, 'api', name='url', value='%sMODEL_ID/OPERATION/[ARGUMENT:VALUE]/[ARGUMENT:VALUE]'%self.baseuri)

        g = etree.SubElement (xml, 'tag', name='operations')
        etree.SubElement (g, 'operation', name='api', value='Returns API description XML, ex: GET /connoisseur/api')
        etree.SubElement (g, 'operation', name='info', value='Returns API description XML, same as API, ex: GET /connoisseur/info')
        etree.SubElement (g, 'operation', name='devices', value='Returns devices available per framework, ex: GET /connoisseur/devices')
        etree.SubElement (g, 'operation', name='templates', value='Lists available templates, ex: GET /connoisseur/templates')


        etree.SubElement (g, 'operation', name='classify', value='Classifies a resource, ex: GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points[/points:10][/goodness:95][/border:300][/format:csv]')
        etree.SubElement (g, 'operation', name='class', value='Returns training samples for class X, ex: GET /connoisseur/MODEL_ID/class:3/sample:1')
        #etree.SubElement (g, 'operation', name='thumbnail', value='Returns model thumbnail, ex: GET /connoisseur/MODEL_ID/thumbnail')

        # model modification
        etree.SubElement (g, 'operation', name='create', value='Creates a model from template, ex: GET /connoisseur/create/template:CaffeNet[/name:SeaCreatures][/dataset:UUID]')
        etree.SubElement (g, 'operation', name='update', value='Updates the model, ex: GET /connoisseur/MODEL_ID/update[/classes:init][/classes:filter][/samples:init][/samples:update][/samples:split]')
        etree.SubElement (g, 'operation', name='train', value='Trains the model, ex: GET /connoisseur/MODEL_ID/train[/method:finetune][/method:snapshot]')
        etree.SubElement (g, 'operation', name='validate', value='Validates the model, ex: GET /connoisseur/MODEL_ID/validate')
        #etree.SubElement (g, 'operation', name='complete', value='Complete the model with training, testing, etc..., ex: GET /connoisseur/MODEL_ID/complete')

        g = etree.SubElement (xml, 'tag', name='frameworks', value='Available Deep Learning frameworks')
        for p in self.frameworks.plugins.itervalues():
            t = etree.SubElement (g, 'plugin', name=p.name, value=str(p))
            p.get_parameters(t)

        g = etree.SubElement (xml, 'tag', name='classifiers', value='Available classification methods')
        for p in self.classifiers.plugins.itervalues():
            etree.SubElement (g, 'plugin', name=p.name, value=str(p))

        g = etree.SubElement (xml, 'tag', name='formats', value='Mapping between formats and mime types')
        for k,v in format_as_mime_type.iteritems():
            etree.SubElement (g, 'format', name=k, value=v)

        g = etree.SubElement (xml, 'tag', name='importers', value='Available formatters for POSTed body documents')
        for p in self.importers.plugins.itervalues():
            etree.SubElement (g, 'plugin', name=p.name, value=str(p))

        g = etree.SubElement (xml, 'tag', name='exporters', value='Available formatters for output documents')
        for p in self.exporters.plugins.itervalues():
            etree.SubElement (g, 'plugin', name=p.name, value=str(p))

        g = etree.SubElement (xml, 'tag', name='adapters_gobjects', value='Available formatters for graphical annotations')
        for p in self.adapters_gobs.plugins.itervalues():
            t = etree.SubElement (g, 'plugin', name=p.name, value=str(p))
            p.get_parameters(t)

        g = etree.SubElement (xml, 'tag', name='adapters_pixels', value='Available formatters for input pixel data')
        for p in self.adapters_pixels.plugins.itervalues():
            t = etree.SubElement (g, 'plugin', name=p.name, value=str(p))
            p.get_parameters(t)

        g = etree.SubElement (xml, 'tag', name='templates', value='Available templates for model creation')
        for name in self.get_templates():
            etree.SubElement (g, 'plugin', name=name)

        return etree.tostring(xml)

    def devices(self):
        response.headers['Content-Type'] = 'text/xml'
        xml = etree.Element ('resource', type='devices', uri=self.baseuri)
        g = etree.SubElement (xml, 'tag', name='frameworks', value='Available devices per framework')
        for p in self.frameworks.plugins.itervalues():
            t = etree.SubElement (g, 'plugin', name=p.name, value=str(p))
            devices = p.get_device_info()
            for i,d in enumerate(devices):
                tt = etree.SubElement (t, 'device', name=str(i))
                for k,v in d.iteritems():
                    etree.SubElement (tt, 'tag', name=str(k), value=str(v))

        return etree.tostring(xml)

    #----------------------------------------------------------------------------------------------
    # info for samples, templates
    #----------------------------------------------------------------------------------------------

    def templates(self, args):
        tmpls = self.get_templates()
        s = []
        for t,p in tmpls.iteritems():
            s.append(self.get_template(t))
        response.headers['Content-Type'] = 'text/xml'
        return '<templates>%s</templates>'%''.join(s)

    def template(self, args):
        name = ''
        #tmpls = self.get_templates()
        s = self.get_template(name)
        response.headers['Content-Type'] = 'text/xml'
        return s

    def preview(self, model_uniq, args):
        class_id = int(args.get('class', -1))
        sample_id = int(args.get('sample', -1))
        log.debug('Preview model %s, class_id %s, sample_id %s', model_uniq, class_id, sample_id)

        # if class_id < 0:
        #     response.headers['Content-Type'] = 'text/xml'
        #     return '<model />'

        # if sample_id < 0:
        #     response.headers['Content-Type'] = 'text/xml'
        #     return '<class />'

        # if asking for a sample from a specific class
        if class_id >= 0 and sample_id >= 0:
            # load thumbnail for requested class and sample_id
            model = self.get_model(model_uniq)
            path = os.path.join(model.path, 'class_{0:05d}'.format(class_id))
            thumbnail = os.path.join(path, 'sample_{0:05d}.png'.format(sample_id))
            if not os.path.exists(thumbnail):
                _mkdir (path)
                model.cache_sample_preview(class_id, sample_id, thumbnail)
                # if asking for a model's thumbnail
        elif class_id < 0 or sample_id < 0:
            model = self.get_model(model_uniq)
            thumbnail = '%s/thumbnail.svg'%model.path

        return forward(FileApp(thumbnail,
                               content_type='image/png',
                               #content_disposition=disposition,
                               ).cache_control (max_age=60*60*24*7*6)) # 6 weeks

    #----------------------------------------------------------------------------------------------
    # classification
    #----------------------------------------------------------------------------------------------

    def classify(self, model_uniq, args):
        image_uniq = args.get('classify')
        log.debug('Classify: %s on model %s', image_uniq, model_uniq)

        # ensure model is loaded
        model = self.get_model(model_uniq)
        #log.debug('Model: %s', str(model))

        args['_workdir'] = self.path_images
        args['_filename'] = '.'.join([ '%s_%s'%(k,v) for k,v in args.iteritems() if not k.startswith('_') ])

        # get image
        image = XImage(image_uniq)
        log.debug('Image info: %s', image.info())

        # classify
        method = args.get('method', 'points').lower()
        if method not in self.classifiers.plugins:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Requested method "%s" not supported'%method)
        log.debug('Classifying using: %s', method)

        # format body if needed and augment args
        if '_http_body' in args:
            fmt_mime = args.get('_http_content_type', [None])[0] or format_as_mime_type.get('xml')
            import_mime = '%s;%s'%(fmt_mime, method)
            if import_mime in self.importers_by_mime:
                token = self.importers_by_mime[import_mime].format(data=args['_http_body'], args=args)

        # run classifier
        c = self.classifiers.plugins[method]
        token = c.classify(image, model, args)

        # format output
        fmt_mime = format_as_mime_type.get(args.get('format')) or args.get('_http_accept', [None])[0] or format_as_mime_type.get('xml')
        export_mime = '%s;%s'%(token.mime, fmt_mime)
        log.debug('Export mime: %s', export_mime)
        if export_mime in self.exporters_by_mime:
            token = self.exporters_by_mime[export_mime].format(token, args=args)

        # return output
        disposition = None
        if token.filename is not None:
            try:
                disposition = 'filename="%s"'%(token.filename.encode('ascii'))
            except UnicodeEncodeError:
                disposition = 'filename="%s"; filename*="%s"'%(token.filename.encode('utf8'), token.filename.encode('utf8'))

        if token.isFile() is True:
            return forward(FileApp(token.data,
                                   content_type=token.mime,
                                   content_disposition=disposition,
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks
        else:
            response.headers['Content-Type'] = token.mime
            response.headers['Content-Disposition'] = disposition
            return token.data

    #----------------------------------------------------------------------------------------------
    # modifying the model
    #----------------------------------------------------------------------------------------------

    def create(self, args):
        ''' GET /connoisseur/create/template:CaffeNet[/name:SeaCreatures][/dataset:UUID]
        '''
        template = args.get('template')
        dataset = args.get('dataset')
        name = args.get('name')
        log.debug('Create model from: %s', template)

        tmpls = self.get_templates()
        if template not in tmpls:
            raise ConnoisseurException(responses.NOT_FOUND, 'Requested template "%s" not found'%template)
        path_template = tmpls[template]
        model = etree.fromstring(self.get_template(template))

        if name is not None:
            model.set('name', name)

        if dataset is not None:
            t = model.find('tag[@name="training_set"]')
            if t is not None:
                t.set('value', '%s'%dataset)

        # next post the model document and get its UUID
        model = data_service.new_resource(resource=model)

        # finally copy all of the template files over to model storage
        uniq = model.get('resource_uniq')
        path_model = os.path.join(self.path_models, uniq)
        _mkdir (path_model)
        log.debug('Creating model in: %s', path_model)
        self.copy_dir(path_template, path_model)

        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(model)

    def update(self, model_uniq, args):
        ''' GET /connoisseur/MODEL_ID/update[/classes:init][/classes:filter][/samples:init][/samples:update][/samples:split]
        '''
        model = self.get_model(model_uniq)

        classes = args.get('classes', '').lower()
        samples = args.get('samples', '').lower()
        log.debug('Update model %s with classes: %s, samples: %s', model_uniq, classes, samples)

        if classes == 'init':
            model.init_classes_dataset()
        elif classes == 'filter':
            model.init_classes_model()
        elif samples == 'init':
            # dispatch this as a celery task
            model.create_sample_db()
        elif samples == 'update':
            # dispatch this as a celery task
            #model.update_sample_db()
            pass
        elif samples == 'split':
            args = {
                'template_path': os.path.join(model.path, 'class_{0:05d}'),
                'template_filename': 'sample_{0:05d}.png',
                'num_per_class': 10,
            }

            # dispatch this as a celery task
            model.split_samples_training_testing(args=args)
        else:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Requested operation is not supported')

        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(model.resource)

    def train(self, model_uniq, args):
        '''
        GET /connoisseur/MODEL_ID/train[/method:finetune]
        accepted methods now are: 'full', 'finetune', 'snapshot'
        '''
        method = args.get('method', 'finetune').lower()
        log.debug('Train model %s with method: %s', model_uniq, method)

        model = self.get_model(model_uniq)

        # dispatch this as a celery task
        model.train(method=method)

        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(model.resource)

    def validate(self, model_uniq, args):
        ''' GET /connoisseur/MODEL_ID/validate
        '''
        log.debug('Validate model %s', model_uniq)

        model = self.get_model(model_uniq)

        # dispatch this as a celery task
        model.validate()

        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(model.resource)

    # def complete(self, model_uniq, args):
    #     ''' GET /connoisseur/MODEL_ID/validate
    #     '''
    #     log.debug('Complete model %s', model_uniq)

    #     model = self.get_model(model_uniq)

    #     # dima: need to identify which steps are still needed to be run

    #     # dispatch this as a celery task
    #     model.init_classes_model()
    #     model.create_sample_db()
    #     model.split_samples_training_testing()
    #     model.train()
    #     model.validate()

    #     response.headers['Content-Type'] = 'text/xml'
    #     return etree.tostring(model.resource)

    #----------------------------------------------------------------------------------------------
    # internal
    #----------------------------------------------------------------------------------------------

    def log_start(self):
        log.info ("STARTING: %s", request.url)

    def log_finish(self):
        log.info ("FINISHED: %s", request.url)

    def check_access(self, uniq):
        resource = data_service.resource_load (uniq = uniq)
        if resource is None:
            if identity.not_anonymous():
                abort(responses.FORBIDDEN)
            else:
                abort(responses.UNAUTHORIZED)
        return resource

    def load_model(self, uniq):
        path_model = os.path.join(self.path_models, uniq)
        log.debug('Loading model from: %s', path_model)

        resource = data_service.resource_load (uniq=uniq, view='deep')
        if (resource.get('type') or resource.get('resource_type') or resource.tag) != 'connoisseur':
            raise ConnoisseurException(responses.BAD_REQUEST, 'Resource %s is not a Connoisseur model'%uniq)

        adapters = {
            'pixels': self.adapters_pixels.plugins,
            'gobs': self.adapters_gobs.plugins,
            'frameworks': self.frameworks.plugins,
        }
        model = ClassifierModel(resource=resource, path=path_model, adapters=adapters)

        return model

    def is_model_updated(self, uniq):
        model = self.models[uniq]
        resource = data_service.resource_load (uniq=uniq, view='short')
        return model.timestamp == resource.get('ts')

    def get_model(self, uniq):
        # dima: this probably needs some sharing techniques between threads/processes?
        if uniq not in self.models:
            self.models[uniq] = self.load_model(uniq)
        if self.is_model_updated(uniq) is not True:
            self.models[uniq] = self.load_model(uniq)
        return self.models[uniq]

    def get_template(self, uniq):
        tmpls = self.get_templates()
        if uniq not in tmpls:
            return None
        s = ''
        p = tmpls.get(uniq)
        path = '%s/template.xml'%p
        with open(path, 'rb') as f:
            s = f.read()
        return s

    def get_templates(self):
        path = self.path_templates
        try:
            tmpls = dict((p, os.path.join(path,p)) for p in os.listdir(path) if os.path.isdir(os.path.join(path,p)))
        except Exception:
            log.error('Problem accessing/creating template directories, model creation will be disabled...')
            tmpls = {}
        return tmpls

    def copy_dir(self, fro, to):
        for fn in os.listdir(fro):
            shutil.copy(os.path.join(fro, fn), to)

#---------------------------------------------------------------------------------------
# bisque init stuff
#---------------------------------------------------------------------------------------

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  ConnoisseurController(uri)
    #directory.register_service ('connoisseur', service)
    return service

# def get_static_dirs():
#     """Return the static directories for this server"""
#     package = pkg_resources.Requirement.parse ("connoisseur")
#     package_path = pkg_resources.resource_filename(package,'bq')
#     return [(package_path, os.path.join(package_path, 'connoisseur', 'public'))]

# def get_model():
#     from bq.connoisseur import model
#     return model

__controller__ =  ConnoisseurController
