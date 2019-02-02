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

Model class is a connection between the model resource stored in the system and functionality
provided by the framework driver.

MODEL DEFINITION
==================

<connoisseur name="Watersipora: aiBrandon" ts="2016-04-25T02:28:00" resource_uniq="00-XYZ">
    <!-- model files -->
    <value index="0" type="string">file:///XYZ/network_weights.caffemodel</value>
    <value index="0" type="string">file:///XYZ/mean.binaryproto</value>
    <value index="0" type="string">file:///XYZ/deploy.prototxt</value>
    <value index="0" type="string">file:///XYZ/solver.prototxt</value>

    <!-- description, used in template document -->
    <tag name="author" value="" />
    <tag name="license" type="license" value="" />
    <tag name="copyright" type="copyright" value="" />
    <tag name="description" value="" />
    <tag name="thumbnail" value="" />

    <!-- model attributes -->
    <tag name="status" value="finished" />

    <!-- status per stage, if present contains finished or an error, if not present then the stage never ran -->
    <tag name="status.classes.init" value="finished" />
    <tag name="status.classes.filter" value="finished" />
    <tag name="status.samples.init" value="finished" />
    <tag name="status.samples.update" value="" />
    <tag name="status.samples.split" value="Error: problem running caffe..." />
    <tag name="status.train" value="" />
    <tag name="status.validate" value="" />


    <tag name="framework" value="caffe">
    </tag>

    <!-- output produced by the network: classes, image -->
    <tag name="model_output" value="classes" />

    <tag name="training_set" type="dataset" value="http://XXXXX" />
    <tag name="training_set_timestamp" type="datetime" value="YYYY-MM-DDTHH..." />
    <tag name="total_images" type="number" value="4567" />
    <tag name="total_samples" type="number" value="678904" />

    <tag name="minimum_samples" type="number" value="500" />
    <tag name="minimum_samples_augmentation" type="number" value="2000" />
    <tag name="minimum_accuracy" type="number" value="0.70" />
    <tag name="minimum_goodness" type="number" value="0.95" />
    <tag name="use_background_class" type="boolean" value="false" />

    <!-- all sizes are in 5D -->
    <tag name="model_patch_size" type="number,list" value="227,227,1,1,3" />
    <tag name="db_patch_size" type="number,list" value="256,256,1,1,3" />
    <tag name="batch_size" type="number" value="10"/>

    <!-- adapters -->
    <tag name="adapter_pixels" value="rgb_2d_resized">
        <tag name="accept_gobjects" value="point,polygon" type="string,list" />
        <tag name="width" value="6000" type="number" />
        <tag name="height" value="6000" type="number" />
    </tag>

    <tag name="adapter_gobjects" value="gob_type_replace">
        <tag name="accept_gobjects" value="point,polygon" type="string,list" />
        <tag name="replace_text" value="Primary - " />
        <tag name="replace_with" value="" />
    </tag>

    <!-- classes in the data -->
    <tag name="classes_data">
        <tag name="class" value="Barnacle (Megabalanus californicus, Balanus sp.)">
            <tag name="id" type="number" value="XXX" />
            <tag name="ignored" type="boolean" value="true" /> <!-- user input if the class should be ignored -->
            <tag name="samples" type="number" value="1234" />
        </tag>
        ...
    </tag>

    <!-- classes selected for the model -->
    <tag name="classes_model">
        <tag name="class" value="Barnacle (Megabalanus californicus, Balanus sp.)">
            <tag name="id" type="number" value="YYY" />
            <tag name="id_original" type="number" value="XXX" />
            <tag name="ignored" type="boolean" value="true" /> <!-- user input if the class should be ignored -->
            <tag name="samples" type="number" value="1234" />
            <tag name="samples_actual" type="number" value="1234" /> <!-- stored when augmentation is used -->
            <tag name="samples_training" type="number" value="1384" />
            <tag name="samples_validation" type="number" value="460" />
            <tag name="samples_testing" type="number" value="460" />

            <!-- validation results -->
            <tag name="goodness" type="number,list" value="0.0,0.5,0.99" />
            <tag name="accuracy" type="number,list" value="61.3043478261,75.67,89.34" />
            <tag name="error" type="number,list" value="12.1643130221,5.3,3.45" />
            <tag name="F1" type="number,list" value="0.538470950604,0.75,0.93" />
            <tag name="MCC" type="number,list" value="0.538470950604,0.75,0.93" />
            <tag name="false_positive" type="number,list" value="143,102,84" />
            <tag name="false_negative" type="number,list" value="178,146,111" />
            <tag name="true_positive" type="number,list" value="282,298,319" />
        </tag>
        ...
    </tag>
</connoisseur>


STATUS WORKFLOW
==================

1. new                        # resource and files copied from the template and some variables updated
2. classes loaded    <-----   # on re-run needs to re-load all files from template and repeat all steps: 3-8
3. classes filtered       |
4. samples loaded    <-----   # on re-run needs to re-split the samples and other steps: 5-8
5. samples split          |
6. trained                |
7. validated              |
8. finished          ------

"""

__author__    = "Dmitry Fedorov"
__version__   = "0.1"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara, ViQi Inc"

import os
from lxml import etree
from collections import Counter

from bq import data_service
import bq.util.io_misc as misc
from bq.util.locks import Locks
from bq.util.mkdir import _mkdir

from .exceptions import ConnoisseurException
from .ximage import XImage
from .utils import ensure_url, set_tag, set_tag_value, get_tag_value, safe_div
import bq.connoisseur.controllers.responses as responses
from .adapter_base import AUGMENTATION_SCALE

import transaction #dima: temporary hack to commit data to the model resource

import logging
log = logging.getLogger('bq.connoisseur.classifier_model')

################################################################################
# utils
################################################################################

def get_classes(resource, name):
    classes = {}
    nodes = resource.xpath('tag[@name="%s"]/tag[@name="class"]'%name)
    #log.debug('Num nodes: %s', len(nodes))
    for n in nodes:
        k = n.get('value')
        c = {'label': k}
        tags = n.xpath('tag')
        for tag in tags:
            name = tag.get('name')
            c[name] = get_tag_value(tag)
        classes[k] = c
    #log.debug('Num classes: %s', len(classes))
    return classes

def set_classes(resource, name, classes):
    #log.debug('Resource initial: %s', etree.tostring(resource))
    node = resource.find('./tag[@name="%s"]'%name)
    if node is not None:
        # remove old classes
        node.clear()
        node.set('name', name)
    else:
        node = etree.SubElement(resource, 'tag', name=name)

    # encode all classes
    for k,c in classes.iteritems():
        t = etree.SubElement(node, 'tag', name='class', value=k)
        for n,v in c.iteritems():
            tag = etree.SubElement(t, 'tag', name=n)
            set_tag_value(tag, v)

    #log.debug('Resource updated: %s', etree.tostring(resource))

def get_framework_parameters(resource):
    parameters = {}
    tags = resource.xpath('tag[@name="framework"]/tag')
    for tag in tags:
        name = tag.get('name')
        parameters[name] = get_tag_value(tag)
    return parameters

def get_error_contribution_string(v, fp, classes_model_by_id):
    if len(v)<1: return ''
    ERC = Counter(v).most_common() # [(5, 8), (11, 6), (6, 5)]
    #log.debug('false_positive_classes: %s', ERC)

    ERC = [(i[0], i[1]/float(fp)) for i in ERC]
    #log.debug('false_positive_classes percent: %s', ERC)

    ERC = [(classes_model_by_id[i[0]]['label'], int(i[1]*100)) for i in ERC if i[1]*100>=1]
    #log.debug('false_positive_classes labels: %s', ERC)

    ERC = ';'.join(["'%s': %s%%"%i for i in ERC])
    #log.debug('ERC string: %s', ERC)
    return ERC

################################################################################
# python representation of model structures
################################################################################

################################################################################
# AdapterDescriptor
# <tag name="adapter_data" value="rgb_2d_resized">
#     <tag name="accept_gobjects" value="point,polygon" type="string,list" />
#     <tag name="width" value="6000" type="number" />
#     <tag name="height" value="6000" type="number" />
# </tag>
################################################################################

class AdapterDescriptor(object):

    def __init__(self, node=None):
        self.name = None
        self.cls = None
        self.parameters = {}
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.get('value')
        # parse parameters as internal tags
        tags = node.xpath('tag')
        for tag in tags:
            n = tag.get('name')
            self.parameters[n] = get_tag_value(tag)

################################################################################
# ClassifierModel
################################################################################

class ClassifierModel(object):
    'Base descriptor for classifier models'

    name = ''
    version = '1.0'

    def __str__(self):
        return 'ClassifierModel(name: %s,  N classes: %s)'%(self.name, self.number_classes_in_model)

    def __init__(self, resource=None, path=None, adapters=dict()):
        self.resource = None
        self.name = None
        self.timestamp = None
        self.uniq = None

        self.template = 'caffenet'
        self.framework_name = 'caffe'
        self.framework_parameters = {}
        self.model_output = 'classes'
        self.status = 'new'

        self.training_set = ''
        self.training_set_timestamp = None

        self.total_images = 0
        self.total_samples = 0

        self.minimum_samples = 500
        self.minimum_samples_augmentation = 1000
        self.minimum_accuracy = 0.3
        self.minimum_goodness = 0.5

        self.classes_data = {}
        self.classes_data_by_original_id = {}
        self.classes_model = {}
        self.classes_model_by_id = {}
        self.classes_model_by_original_id = {}
        self.number_classes_in_model = 0

        # testing_percent indicates the size of the testing set in percent
        # the validation set will be the same size as the testing set
        # the training set will include everything else
        # by default we'll use the 60%/20%/20% split for Training/Validation/Test
        self.testing_percent = 20

        self.use_background_class = False # use discarded samples in the additional sink class
        self.background_class_name = 'The equals'

        self.model_patch_size = [0,0,0,0,0]
        self.db_patch_size = [0,0,0,0,0]
        self.batch_size = 10
        self.path = path
        self.lockable = os.path.join(self.path, 'lock')

        # paths to all files needed for the model
        self.files = []
        self.files_samples = []

        # adapter descriptors
        self.adapter_descr_pixels = AdapterDescriptor()
        self.adapter_descr_gobs = AdapterDescriptor()

        # functional adapters
        self.framework = None
        self.adapters = adapters

        if resource is not None:
            self.load(resource=resource, path=path, adapters=adapters)

    def is_loaded(self):
        return self.number_classes_in_model>0 and self.framework is not None

    def safe_value(self, xpath, default=None):
        try:
            tag = self.resource.xpath(xpath)[0]
            return get_tag_value(tag, default)
        except Exception:
            pass
        return default

    def load (self, resource, path=None, adapters=dict()):
        self.path = path

        #----------------------------------------------------------
        # load classes
        #----------------------------------------------------------
        self.resource = resource
        self.name = self.resource.get('name')
        self.timestamp = self.resource.get('ts')
        self.uniq  = self.resource.get('resource_uniq')

        self.framework_name = self.safe_value('tag[@name="framework"]', default=self.framework_name)
        self.framework_parameters = get_framework_parameters(self.resource)
        self.model_output = self.safe_value('tag[@name="model_output"]', default=self.model_output)
        self.status = self.safe_value('tag[@name="status"]', default=self.status)

        self.training_set = self.safe_value('tag[@name="training_set"]', default=self.training_set)
        self.training_set_timestamp = self.safe_value('tag[@name="training_set_timestamp"]', default=self.training_set_timestamp)
        self.total_images = self.safe_value('tag[@name="total_images"]', default=self.total_images)
        self.total_samples = self.safe_value('tag[@name="total_samples"]', default=self.total_samples)

        self.minimum_samples = self.safe_value('tag[@name="minimum_samples"]', default=self.minimum_samples)
        self.minimum_samples_augmentation = self.safe_value('tag[@name="minimum_samples_augmentation"]', default=self.minimum_samples_augmentation)
        self.minimum_accuracy = self.safe_value('tag[@name="minimum_accuracy"]', default=self.minimum_accuracy)
        self.minimum_goodness = self.safe_value('tag[@name="minimum_goodness"]', default=self.minimum_goodness)
        self.use_background_class = self.safe_value('tag[@name="use_background_class"]', default=self.use_background_class)


        self.classes_data = get_classes(self.resource, 'classes_data')
        self.classes_data_by_original_id = dict((v['id'],v) for k,v in self.classes_data.iteritems())

        self.classes_model = get_classes(self.resource, 'classes_model')
        self.classes_model_by_id = dict((v['id'],v) for k,v in self.classes_model.iteritems())
        self.classes_model_by_original_id = dict((v['id_original'],v) for k,v in self.classes_model.iteritems())

        self.number_classes_in_model = len(self.classes_model)

        # model parameters
        self.batch_size = self.safe_value('tag[@name="batch_size"]', default=self.batch_size)
        self.model_patch_size = self.safe_value('tag[@name="model_patch_size"]', default=self.model_patch_size)
        self.db_patch_size = self.safe_value('tag[@name="db_patch_size"]', default=self.db_patch_size)

        # set adapters
        self.adapters = adapters
        self.adapters_pixels = self.adapters.get('pixels')
        self.adapters_gobs = self.adapters.get('gobs')
        self.adapters_frameworks = self.adapters.get('frameworks')

        # pixel adapters
        try:
            self.adapter_descr_pixels.parse(self.resource.xpath('tag[@name="adapter_pixels"]')[0])
            self.adapter_descr_pixels.cls = self.adapters_pixels[self.adapter_descr_pixels.name].__class__
        except Exception:
            self.adapter_descr_pixels = None
            log.exception('Could not load pixel adapter for model: %s'%self.resource.get('resource_uniq'))

        # class name adapters
        try:
            self.adapter_descr_gobs.parse(self.resource.xpath('tag[@name="adapter_gobjects"]')[0])
            self.adapter_descr_gobs.cls = self.adapters_gobs[self.adapter_descr_gobs.name].__class__
        except Exception:
            self.adapter_descr_gobs = None
            log.exception('Could not load gobjects adapter for model: %s'%self.resource.get('resource_uniq'))

        # framework adapter
        try:
            self.framework = self.adapters_frameworks[self.framework_name].__class__(model=self)
        except Exception:
            self.framework = None
            log.exception('Could not load framework for model: %s'%self.resource.get('resource_uniq'))

    def create_adapter_pixels (self, model=None, args=None, image=None, **kw):
        return self.adapter_descr_pixels.cls(model=model, args=args, image=image, **kw)

    def create_adapter_gobs (self, model=None, args=None, image=None, **kw):
        return self.adapter_descr_gobs.cls(model=model, args=args, image=image, **kw)

    def activate (self, training=False):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot activate model without initialized framework')
        self.framework.activate(training=training)

    def classify(self, x):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot use model without initialized framework')

        return self.framework.classify(x)
        # with Locks(None, self.lockable, failonexist=True) as l:
        #     if l.locked: # the file is not being currently written by another process
        #         return self.framework.classify(x)
        # raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing')

    #----------------------------------------------------------------------------------------------
    # reading data
    #----------------------------------------------------------------------------------------------

    def cache_sample_preview(self, class_id, sample_id, filename):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot use model without initialized framework')

        # find the db_class_id from original class_id
        if class_id not in self.classes_model_by_original_id:
            raise ConnoisseurException(responses.NOT_FOUND, 'Class not found')
        class_id = self.classes_model_by_original_id[class_id]['id']

        self.framework.cache_sample_preview(class_id, sample_id, filename)

    def get_sample_preview_paths(self, template_path, template_filename, num_per_class=10):
        paths = {}
        for orig_id,c in self.classes_model_by_original_id.iteritems():
            path = template_path.format(orig_id)
            _mkdir (path)
            class_id = c['id']
            for i in range(num_per_class):
                filename = template_filename.format(i)
                paths['{0}.{1}'.format(class_id,i)] = os.path.join(path, filename)
        return paths

    #----------------------------------------------------------------------------------------------
    # syncing with resource
    #----------------------------------------------------------------------------------------------

    def lock(self, edit=False):
        pass

    def unlock(self):
        pass

    def sync_resource(self, status=None, view='deep'):
        if status is not None:
            self.status = status
            set_tag(self.resource, 'status', self.status)
        #log.debug('Writing resource to DB:\n%s', etree.tostring(self.resource))
        r = data_service.update_resource(resource=self.resource, new_resource=self.resource, view=view)
        if view == 'deep':
            #log.debug('Setting resource from DB:\n%s', etree.tostring(r))
            # dima: for some reason this returns document without values???
            # dima: bug fix, for now move values into r
            # for v in self.resource.xpath('value'):
            #     vv = etree.SubElement(r, 'value')
            #     vv.text = v.text
            #     log.debug('Re-Setting value:\n%s', etree.tostring(v))
            # # dima: bug fix
            self.resource = r

        # dima: temporary hack to make sure resource update is committed immediately
        transaction.commit()
        transaction.begin()
        # dima: temporary hack to make sure resource update is committed immediately

    def update_status(self, status=None):
        if status is None:
            status = 'finished'
        self.sync_resource(status=status, view='short')

    def update_with_error(self, name, value):
        set_tag(self.resource, name, value)
        self.sync_resource(status='finished', view='short')

    #----------------------------------------------------------------------------------------------
    # editing the model
    #----------------------------------------------------------------------------------------------

    def init_classes_dataset(self):
        if self.training_set is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot initialize classes due to missing training dataset')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')
            try:
                dataset_url = ensure_url(self.training_set)
                adapter_gobs = self.create_adapter_gobs(model=self, image=None)

                classes = {}
                gobs = data_service.query(resource_type='value', parent=dataset_url, extract='gobject[type]')
                idx = 0
                self.total_samples = 0
                for g in gobs:
                    k = g.get('type')
                    n = misc.safeint(g.text, 0)
                    if k is None: continue
                    k = adapter_gobs.get_class_name(g) # adapt the class name, might need some change since the node is not a true gobject
                    if k is None: continue
                    if k not in classes:
                        classes[k] = {
                            'label': k,
                            'id': idx,
                            'samples': n,
                        }
                        idx += 1
                    else:
                        classes[k]['samples'] += n
                    self.total_samples += n
                self.classes_data = classes
                self.classes_data_by_original_id = dict((v['id'],v) for k,v in self.classes_data.iteritems())
                #log.debug('Classes data: %s', str(self.classes_data))

                self.classes_model = {}
                self.classes_model_by_id = {}
                self.classes_model_by_original_id = {}
                self.number_classes_in_model = 0
            except:
                self.update_with_error('status.classes.init', 'Exception during init_classes_dataset')
                raise

            # update model resource
            set_tag(self.resource, 'total_samples', self.total_samples)
            set_classes(self.resource, 'classes_data', self.classes_data)
            set_classes(self.resource, 'classes_model', self.classes_model)
            set_tag(self.resource, 'status.classes.init', 'finished')
            self.sync_resource()

    def init_classes_model(self):
        if self.classes_data is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot initialize model classes due to missing data classes')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')
            try:
                classes = {}
                idx = 0

                # append background class if requested
                if self.use_background_class is True:
                    classes[self.background_class_name] = {
                        'label': self.background_class_name,
                        'id': idx,
                        'id_original': -1,
                        'samples': 0,
                        'samples_training': 0,
                        'samples_validation': 0,
                        'samples_testing': 0,
                        'ignored': True,
                    }
                    idx += 1

                # add all the classes found in the dataset
                self.total_samples = 0
                for k,c in self.classes_data.iteritems():
                    if c['samples'] >= self.minimum_samples and c.get('ignored', False) is not True:
                        classes[k] = {
                            'label': k,
                            'id': idx,
                            'id_original': c['id'],
                            #'samples': c['samples'],
                            'samples': 0,
                            'samples_training': 0,
                            'samples_validation': 0,
                            'samples_testing': 0,
                        }

                        if c['samples'] < self.minimum_samples_augmentation:
                            classes[k]['samples_actual'] = c['samples']
                            self.total_samples += c['samples'] * AUGMENTATION_SCALE
                        else:
                            self.total_samples += c['samples']

                        idx += 1
                    elif self.use_background_class is True:
                        #classes[self.background_class_name]['samples'] += c['samples']
                        self.total_samples += c['samples']
            except:
                self.update_with_error('status.classes.filter', 'Exception during init_classes_model')
                raise

            if self.total_samples < 10:
                self.update_with_error('status.classes.filter', 'Too few samples were found, model cannot be trained')
                raise ConnoisseurException(responses.NO_CONTENT, 'Too few samples were found, model cannot be trained')

            self.classes_model = classes
            self.classes_model_by_id = dict((v['id'],v) for k,v in self.classes_model.iteritems())
            self.classes_model_by_original_id = dict((v['id_original'],v) for k,v in self.classes_model.iteritems())
            self.number_classes_in_model = len(self.classes_model)

            # update model resource
            set_tag(self.resource, 'total_samples', self.total_samples)
            set_classes(self.resource, 'classes_model', self.classes_model)
            set_tag(self.resource, 'status.classes.filter', 'finished')
            self.sync_resource()

    def create_sample_db(self):
        if self.training_set is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Cannot create sample DB due to missing training dataset')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')

            dataset_url = ensure_url(self.training_set)
            dataset = data_service.get_resource(dataset_url, view='full')
            if (dataset is None or dataset.tag) != 'dataset':
                raise ConnoisseurException(responses.BAD_REQUEST, 'Provided resource is not a dataset')

            self.training_set_timestamp = dataset.get('ts')
            set_tag(self.resource, 'training_set_timestamp', self.training_set_timestamp)

            images = []
            refs = dataset.xpath('value[@type="object"]')
            for r in refs:
                images.append(XImage(base_url=r.text))

            self.total_images = len(images)
            set_tag(self.resource, 'total_images', self.total_images)

            self.update_status(status='Creating sample db')

            # dima: this should be parallelized
            #r = self.framework.create_sample_db(images)
            log.info('STARTING samples:init for %s images', self.total_images)
            try:
                for i,image in enumerate(images):
                    log.info('PROCESSING samples:init %s/%s for %s', i, self.total_images, image)
                    self.framework.update_sample_db(image)
            except:
                self.update_with_error('status.samples.init', 'Exception during create_sample_db')
                raise
            log.info('FINSHED samples:init for %s images', self.total_images)

            set_classes(self.resource, 'classes_model', self.classes_model)
            set_tag(self.resource, 'status.samples.init', 'finished')
            self.sync_resource(status='finished')
            return r

    def split_samples_training_testing(self, args=None):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Model is incomplete for split operation')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')

            # dispatch this as a celery task
            self.update_status(status='Splitting data for training and testing')

            paths = None
            if args is not None and 'template_path' in args:
                paths = self.get_sample_preview_paths(args.get('template_path'), args.get('template_filename'), args.get('num_per_class'))

            try:
                r = self.framework.split_samples_training_testing(sample_preview_paths=paths)
            except:
                self.update_with_error('status.samples.split', 'Exception during split_samples_training_testing')
                raise

            set_classes(self.resource, 'classes_model', self.classes_model)
            set_tag(self.resource, 'status.samples.split', 'finished')
            self.sync_resource(status='finished')
            return r

    def train(self, method='finetune'):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Model is incomplete for train operation')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')

            # dispatch this as a celery task
            self.update_status(status='Training')

            try:
                self.framework.deactivate()
                r = self.framework.update_model_from_template()
                r = self.framework.train(method=method)
            except:
                self.update_with_error('status.train', 'Exception during train')
                raise

            set_tag(self.resource, 'status.train', 'finished')
            self.sync_resource(status='finished')
            self.framework.activate (training=False)
            if self.framework.is_activate() is False:
                raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Could not activate network after training, something is wrong...')
            return r

    def validate_by_goodness(self, my_goodness):

        # Init all required variables in test classes

        keys = range(len(self.classes_model))
        classes = dict(zip(keys, [dict() for i in [None]*len(keys)]))
        for k,v in classes.iteritems():
            v['true_positive'] = 0
            v['false_negative'] = 0
            v['false_positive'] = 0
            v['false_positive_classes'] = [] # we need to compute weighted false positive later based on number of tested samples in each set
            v['n'] = 0
            v['discarded'] = 0
            v['weight'] = 1.0
            v['ignored'] = self.classes_model_by_id[k].get('ignored', False)

        # classify samples from the test set
        classes = self.framework.validate(classes, my_goodness)

        #########################
        # Create per class weights based on number of samples tested in each

        # compute smallest class size
        min_sz = float('inf')
        for k,v in classes.iteritems():
            vv = v['n'] - v['discarded']
            if vv>0 and v['n']>0:
                min_sz = min(min_sz, vv)

        # compute per class weights
        for k,v in classes.iteritems():
            vv = v['n'] - v['discarded']
            if vv>0 and v['n']>0:
                v['weight'] = safe_div(min_sz, vv, 1.0)

        # compute weighted false positives, others will be weighted on the fly
        for k,v in classes.iteritems():
            fpw = 0
            for fpc in v['false_positive_classes']:
                fpw += classes[fpc]['weight']
            v['false_positive_w'] = fpw


        # compute testing results
        #print '\n\nTested model "%s"\nwith goodness at %.0f%% on the image db "%s"\n'%(model_weights, my_goodness*100.0, db_name)

        #print 'id\tsamples\tgood\ttrash\tfp\tfn\tAccu\tError\tF1\tMCC\tclass\n'
        N=0; NW=0; TP=0; FP=0; NN=0; NNW=0; TPP=0; FPP=0; D=0; DW=0; DD=0; DDW=0
        #for k,v in sorted(classes_final.items(), key=lambda x: x[1]['class_label']):
        for k,v in classes.iteritems():
            n  = float(v['n'])
            tp = float(v['true_positive'])
            fp = float(v['false_positive'])
            fn = float(v['false_negative'])
            d  = float(v['discarded'])
            w  = float(v['weight'])

            nw  = n*w
            dw  = d*w
            tpw = tp*w
            fnw = fn*w
            fpw = float(v['false_positive_w'])

            A = safe_div(100.0*tp, n-d, 0)
            E = safe_div(100.0*fpw, nw+fpw, 100)
            F = safe_div(tpw, tpw + fnw + fpw, 0)
            MCC = safe_div(tpw*1 - fpw*fnw, tpw + fnw + fpw, 0)
            ERC = get_error_contribution_string(v['false_positive_classes'], fp, self.classes_model_by_id)

            v['error'] = E
            v['F1'] = F
            v['accuracy'] = A
            v['MCC'] = MCC
            v['error_contributions'] = ERC

        return classes

    def validate(self):
        if self.framework is None:
            raise ConnoisseurException(responses.BAD_REQUEST, 'Model is incomplete for validation operation')

        with Locks(None, self.lockable, failonexist=True) as l:
            if l.locked is False: # the file is being written by another process
                raise ConnoisseurException(responses.LOCKED, 'The model is locked for processing by another process')

            #log.debug('Initial model:\n\n %s\n\n\n', self.classes_model)

            # dispatch this as a celery task
            self.update_status(status='Validating')

            try:
                goodnesses = [0.0, 0.5, 0.9]
                results = []

                for my_goodness in goodnesses:
                    v = self.validate_by_goodness(my_goodness)
                    results.append(v)

                # initialize classes with resulting vectors
                attr = ['true_positive', 'false_negative', 'false_positive', 'discarded', 'weight', 'accuracy', 'error', 'F1', 'MCC', 'error_contributions']
                keys = range(len(self.classes_model))
                classes = dict(zip(keys, [dict() for i in [None]*len(keys)]))
                for i,v in classes.iteritems():
                    for a in attr:
                        v[a] = []
                    v['goodness'] = goodnesses
                    for r in results:
                        for a in attr:
                            v[a].append(r[i][a])

                # update classes and resource
                attr.append('goodness')
                for k,v in classes.iteritems():
                    class_name = self.classes_model_by_id[k]['label']
                    for a in attr:
                        self.classes_model[class_name][a] = v[a]
                    #print 'Class %s\n%s\n'%(class_name, self.classes_model[class_name])

            except:
                self.update_with_error('status.validate', 'Exception during validate')
                raise

            #log.debug('Final model:\n\n %s\n\n\n', self.classes_model)

            #     #print 'id samples good trash fp fn Accu Error F1 MCC class'
            #     print "%s\t%s\t%s\t%s\t%s\t%s\t%.0f%%\t%.1f%%\t%.2f\t%.2f\t%s"%(k, n, tp, d, fp, fn, A, E, F, MCC, cls)
            #     N += n; NW += nw; TP += tpw; FP += fpw; D += d; DW += dw
            #     if has_background_class is True and cls != background_class_name:
            #         NN += n; NNW += nw; TPP += tpw; FPP += fpw; DD += d; DDW += dw

            # print("\nClassified %sx%s samples in %.2fs, %.0fsamples/s"%( total, batch_sz, runtime, float(total*batch_sz)/runtime ))
            # print 'Final accuracy: %.2f%% and error %.2f%% on %s samples with %s discarded (%.1f%%)\n'%( (100.0*TP)/(NW-DW), (100.0*FP)/(NW+FP), N-D, D, (100.0*D)/total )
            # if has_background_class is True:
            #     print 'Accuracy excluding +1: %.2f%% error %.2f%% on %s samples (%.1f%%)\n'%( (100.0*TPP)/(NNW-DDW), (100.0*FPP)/(NNW+FPP), NN-DD, (100.0*DD)/(total-(N-NN)) )

            set_classes(self.resource, 'classes_model', self.classes_model)
            set_tag(self.resource, 'status.validate', 'finished')
            self.sync_resource(status='finished')
