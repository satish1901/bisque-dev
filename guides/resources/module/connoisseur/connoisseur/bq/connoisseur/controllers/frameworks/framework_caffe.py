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

""" Caffe model implementation
"""

__author__    = "Dmitry Fedorov"
__version__   = "0.1"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara, ViQi Inc"

import os
import sys
import logging
#import math
#import struct
import copy
import random
import hashlib
#import cPickle as pickle

from lxml import etree
import numpy as np
#from scipy import ndimage
import scipy
#from PIL import Image
import lmdb
import caffe
import skimage.io

from subprocess import Popen, PIPE

from bq import data_service
import bq.util.io_misc as misc

from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses
from bq.connoisseur.controllers.utils import dist_L1, distr_goodness, safe_remove_dir_file, set_tag_value
from bq.connoisseur.controllers.classifier_model import ClassifierModel
from bq.connoisseur.controllers.framework_base import FrameworkBase
from bq.connoisseur.controllers.ximage import XImage

import logging
log = logging.getLogger('bq.connoisseur.frameworks.caffe')

################################################################################
# CaffeModel - interface to everything needed to train and use Caffe models
# including sample I/O using LMDB
################################################################################

class FrameworkCaffe(FrameworkBase):
    'Caffe framework implementation'

    name = 'caffe'
    version = '1.0'

    COMMAND_CAFFE = 'caffe' if os.name != 'nt' else 'caffe.exe'
    COMMAND_MEAN  = 'caffe_compute_image_mean' if os.name != 'nt' else 'compute_image_mean.exe'

    default_parameters = {
        'max_iter': 100000,
        'stepsize': 20000,
        'snapshot': 10000,
        'base_lr': 0.001,
        'gamma': 0.1,
        'momentum': 0.9,
        'weight_decay': 0.0005,
        'test_interval': 1000,
        'test_iter': 100,
    }

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        for n,v in cls.default_parameters.iteritems():
            tag = etree.SubElement (node, 'tag', name=n)
            set_tag_value(tag, v)

    def __str__(self):
        return 'Caffe DL framework'

    def __init__(self, model=None):
        self.file_def = None
        self.file_def_train = None
        self.file_solver = None
        self.file_weights = None
        self.file_mean = None

        self.net = None
        self.mu = None

        # paths to dbs with training in validation patches
        self.db_images = None
        self.db_train  = None
        self.db_val    = None
        self.db_test   = None
        self.db_keys   = None

        self.sz_key    = 256 # gob idx is resource_uuid + sub_id + augmented_id, something like: 00-79Hfk6V5wPQZwuWMDcQxH5-650-9 with 32 chars
        self.sz_keyenc = 128 # 64 # sha256 hashed key

        self.goodness_function = None

        devices = self.get_device_info()
        if len(devices)<1:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'No Caffe available devices were detected...')

        super(self.__class__, self).__init__(model)

    def load (self, model):
        super(self.__class__, self).load(model)

        self.path = self.model.path

        #----------------------------------------------------------
        # paths to required files
        #----------------------------------------------------------
        self.file_def = os.path.join(self.path, 'deploy.prototxt')
        self.file_def_train = os.path.join(self.path, 'train_val.prototxt')
        self.file_solver = os.path.join(self.path, 'solver.prototxt')
        self.file_weights = os.path.join(self.path, 'weights.caffemodel')
        self.file_mean = os.path.join(self.path, 'mean.binaryproto')
        self.files = [self.file_def, self.file_def_train, self.file_solver, self.file_weights, self.file_mean]

        self.db_images = os.path.join(self.path, 'image_lmdb')
        self.db_train  = os.path.join(self.path, 'image_train_lmdb')
        self.db_val    = os.path.join(self.path, 'image_val_lmdb')
        self.db_test   = os.path.join(self.path, 'image_test_lmdb')
        self.db_keys   = os.path.join(self.path, 'keys_lmdb')

        self.files_samples = [self.db_images, self.db_train, self.db_val, self.db_test, self.db_keys]

        if self.model.number_classes_in_model<1:
            log.debug('Model has less than 1 class, skipping further loading...')
            return

        #----------------------------------------------------------
        # create best and worst probability distributions
        #----------------------------------------------------------
        my_dist = dist_L1

        NC = self.model.number_classes_in_model
        Pb = np.zeros(NC); Pb[0] = 1.0
        Pw = np.ones(NC) / NC

        L1b = my_dist(Pb, Pb)
        L1w = my_dist(Pb, Pw)

        def compute_goodness (probs):
            return distr_goodness (probs, Pb, L1b, L1w, my_dist)
        self.goodness_function = compute_goodness

        #----------------------------------------------------------
        # load mean image
        #----------------------------------------------------------
        try:
            blob = caffe.proto.caffe_pb2.BlobProto()
            with open( self.file_mean, 'rb' ) as f:
                blob.ParseFromString(f.read())
            mu = np.array( caffe.io.blobproto_to_array(blob) )
            self.mu = mu.squeeze().transpose((1,2,0))
        except Exception:
            log.debug('Could not load the mean image')

        # try:
        #     self.activate (training=False)
        # except RuntimeError:
        #     log.debug('Could not activate the framework')
        # except Exception:
        #     log.exception('Error while trying to activate the framework')

    def activate (self, training=False):
        mode = caffe.TEST if training is False else caffe.TEST

        #caffe.set_mode_cpu()
        caffe.set_mode_gpu()
        self.net = caffe.Net(self.file_def,      # defines the structure of the model
                             self.file_weights,  # contains the trained weights
                             mode)               # use test mode (e.g., don't perform dropout)

        # set the size of the input (we can skip this if we're happy
        #  with the default; we can also change it later, e.g., for different batch sizes)
        self.net.blobs['data'].reshape(self.model.batch_size,                                           # batch size of 10
                                       self.model.model_patch_size[4],                                  # 3-channel (BGR) images
                                       self.model.model_patch_size[0], self.model.model_patch_size[1])  # image size is 227x227

    def deactivate (self):
        del self.net

    def is_activate (self):
        return self.net is not None

    def get_device_info (self):
        ''' returns a list of deice info dictionaries

        I0615 11:40:41.533318 40528 caffe.cpp:138] Querying GPUs all
        I0615 11:40:41.964962 40528 common.cpp:186] Device id:                     0
        I0615 11:40:41.964962 40528 common.cpp:187] Major revision number:         6
        I0615 11:40:41.964962 40528 common.cpp:188] Minor revision number:         1
        I0615 11:40:41.964962 40528 common.cpp:189] Name:                          GeForce GTX 1070
        I0615 11:40:41.964962 40528 common.cpp:190] Total global memory:           8589934592
        I0615 11:40:41.964962 40528 common.cpp:191] Total shared memory per block: 49152
        I0615 11:40:41.964962 40528 common.cpp:192] Total registers per block:     65536
        I0615 11:40:41.964962 40528 common.cpp:193] Warp size:                     32
        I0615 11:40:41.964962 40528 common.cpp:194] Maximum memory pitch:          2147483647
        I0615 11:40:41.964962 40528 common.cpp:195] Maximum threads per block:     1024
        I0615 11:40:41.964962 40528 common.cpp:196] Maximum dimension of block:    1024, 1024, 64
        I0615 11:40:41.964962 40528 common.cpp:199] Maximum dimension of grid:     2147483647, 65535, 65535
        I0615 11:40:41.964962 40528 common.cpp:202] Clock rate:                    1771500
        I0615 11:40:41.964962 40528 common.cpp:203] Total constant memory:         65536
        I0615 11:40:41.964962 40528 common.cpp:204] Texture alignment:             512
        I0615 11:40:41.964962 40528 common.cpp:205] Concurrent copy and execution: Yes
        I0615 11:40:41.964962 40528 common.cpp:207] Number of multiprocessors:     15
        I0615 11:40:41.964962 40528 common.cpp:208] Kernel execution timeout:      Yes
        I0615 01:10:55.654201  1904 common.cpp:193] Device id:                     1
        I0615 01:10:55.654223  1904 common.cpp:194] Major revision number:         5
        I0615 01:10:55.654238  1904 common.cpp:195] Minor revision number:         2
        I0615 01:10:55.654240  1904 common.cpp:196] Name:                          GeForce GTX TITAN X
        I0615 01:10:55.654243  1904 common.cpp:197] Total global memory:           12800163840
        I0615 01:10:55.654247  1904 common.cpp:198] Total shared memory per block: 49152
        I0615 01:10:55.654249  1904 common.cpp:199] Total registers per block:     65536
        I0615 01:10:55.654254  1904 common.cpp:200] Warp size:                     32
        I0615 01:10:55.654258  1904 common.cpp:201] Maximum memory pitch:          2147483647
        I0615 01:10:55.654273  1904 common.cpp:202] Maximum threads per block:     1024
        I0615 01:10:55.654278  1904 common.cpp:203] Maximum dimension of block:    1024, 1024, 64
        I0615 01:10:55.654294  1904 common.cpp:206] Maximum dimension of grid:     2147483647, 65535, 65535
        I0615 01:10:55.654299  1904 common.cpp:209] Clock rate:                    1215500
        I0615 01:10:55.654302  1904 common.cpp:210] Total constant memory:         65536
        I0615 01:10:55.654306  1904 common.cpp:211] Texture alignment:             512
        I0615 01:10:55.654310  1904 common.cpp:212] Concurrent copy and execution: Yes
        I0615 01:10:55.654315  1904 common.cpp:214] Number of multiprocessors:     24
        I0615 01:10:55.654319  1904 common.cpp:215] Kernel execution timeout:      No
        ...
        '''

        command = [self.COMMAND_CAFFE, 'device_query', '-gpu', 'all']
        log.debug('Running binary: %s', command)
        o = misc.run_command(command) #, shell=True )
        if o is None:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Error while running Caffe...')

        # parse the output
        devices = []
        d = None
        for l in o.splitlines():
            try:
                _,l = l.split('] ', 1)
                k,v = [s.strip() for s in l.split(':', 1)]
                if k == 'Device id':
                    if d is not None:
                        devices.append(d)
                    d = {}
                d[k] = v
            except Exception:
                pass
        if d is not None:
            devices.append(d)

        return devices

    def classify(self, x):
        ''' x - 3D numpy array representing RGB image in np.float32
        '''

        if self.goodness_function is None:
            self.load(self.model)
            if self.goodness_function is None:
                raise ConnoisseurException(responses.BAD_REQUEST, 'Caffe classify: model is not loaded properly')

        if self.net is None:
            self.activate (training=False)
            if self.net is None:
                raise ConnoisseurException(responses.BAD_REQUEST, 'Caffe classify: network is not activated')

        # mean subtraction
        if self.mu is not None:
            try:
                x = x - self.mu
            except ValueError:
                log.debug('Classify: failed to subtract mean, adjusting the size of the patch %s to %s', str(x.shape), str(self.mu.shape) )
                x = scipy.misc.imresize(x, self.mu.shape)
                log.debug('Classify: attempting mean subtraction with shape %s', str(x.shape) )
                x = x - self.mu
                log.debug('Classify: final subtracted patch with shape %s', str(x.shape) )

        #caffe.set_mode_cpu()
        #caffe.set_mode_gpu()
        samples = caffe.io.oversample([x], (self.model.model_patch_size[0], self.model.model_patch_size[1]))
        for i in range(samples.shape[0]):
            self.net.blobs['data'].data[i] = samples[i,:,:,:].transpose(2,0,1)

        # copy the image data into the memory allocated for the net
        #self.net.blobs['data'].data[...] = samples[0,:,:,:].transpose(2,0,1)
        #self.net.blobs['data'].data[...] = x
        #self.net.blobs['data'].data[...] = transformer.preprocess('data', image)

        ### perform classification
        output = self.net.forward()
        #log.debug('Net output: %s', output)

        classes = []
        for output_prob in output['prob']:
            out_class = output_prob.argmax()
            #print 'for label %s predicted class is: %s with probability %s'%(datum.label, out_class, output_prob[out_class])
            classes.append(out_class)
        #log.debug('Net output classes: %s', classes)
        # majority vote for class output
        out_class = np.bincount(classes).argmax()
        #log.debug('out class: %s', out_class)
        #log.debug('len of classes: %s', len(classes))
        #log.debug('number_classes: %s', self.number_classes_in_model)

        probs = np.zeros(self.model.number_classes_in_model)
        C = 0
        for output_prob in output['prob']:
            predicted_class = output_prob.argmax()
            #log.debug('probs: %s', probs)
            #log.debug('output_prob: %s', output_prob)

            if predicted_class == out_class:
                probs = probs + np.sort(output_prob)[::-1]
                C += 1
        probs = probs / C
        #log.debug('probabilities: %s', probs)

        p = probs[0]
        g = self.goodness_function (probs)
        agreement = float(C) / float(self.model.batch_size)
        goodness = p * g * agreement
        #log.debug('goodness: %s', goodness)

        return (out_class, goodness)

    def cache_sample_preview(self, class_id, sample_id, filename):
        x = None
        cur_sample = -1
        rdb  = lmdb.open(self.db_images, readonly=True)
        with rdb.begin() as rtxn:
            cursor = rtxn.cursor()
            for key, value in cursor:
                #pylint: disable=no-member
                datum = caffe.proto.caffe_pb2.Datum()
                datum.ParseFromString(value)
                if datum.label != class_id:
                    continue
                cur_sample += 1
                if cur_sample < sample_id:
                    continue
                x = np.fromstring(datum.data, dtype=np.uint8)
                x = x.reshape(1, datum.channels, datum.height, datum.width).squeeze().transpose((1,2,0))
                break
        rdb.close()
        if x is None:
            raise ConnoisseurException(responses.NOT_FOUND, 'Requested sample was not found')
        skimage.io.imsave(filename, x)

    def run_caffe_bin(self, bin_name, args):
        command = [bin_name]
        command.extend(args)
        log.debug('Running binary: %s', command)
        return misc.run_command(command, cwd=self.path) #, shell=True )

    def fix_path(self, path):
        if os.name != 'nt':
            path = path.replace('\\', '/')
        else:
            path = path.replace('/', '\\')
        path = os.path.abspath(path)
        return path

    def reset_sample_db(self):
        safe_remove_dir_file(self.db_images)
        safe_remove_dir_file(self.db_train)
        safe_remove_dir_file(self.db_val)
        safe_remove_dir_file(self.db_test)
        safe_remove_dir_file(self.db_keys)

    def update_model_from_template(self):
        variables = {
            '$NUM_OUTPUT$': str(self.model.number_classes_in_model),
        }
        for n,v in self.default_parameters.iteritems():
            variables['$%s$'%n] = v
        for n,v in self.model.framework_parameters.iteritems():
            variables['$%s$'%n] = v

        files = [os.path.join(self.path, f) for f in os.listdir(self.path) if f.endswith('.template')]
        for fn in files:
            with open(fn, 'rb') as f:
                text = f.read()
            for n,v in variables.iteritems():
                text = text.replace(n, str(v))
            with open(fn.replace('.template', ''), 'wb') as f:
                f.write(text)

    def get_db_element_size(self):
        '''
        should only be needed for win and macos where file size is in fact allocated a priory
        '''
        msz = self.model.db_patch_size
        #print 'get_db_element_size for model patch size %s'%(str(msz))
        # create array with CHW order
        pix = np.ndarray(shape=(msz[4], msz[1], msz[0]), dtype=np.uint8)
        #pylint: disable=no-member
        datum = caffe.io.array_to_datum(pix)
        datum.label = 0
        s = bytes(datum.SerializeToString())
        return len(s)*2

    def get_lmdb_size(self, num_records, key_sz, val_sz):
        '''
        should only be needed for win and macos where file size is in fact allocated a priory
        '''
        return 16 + num_records * (8+key_sz+val_sz)

    def patch_shape_matches_db(self, pix):
        psz = pix.shape
        msz = self.model.db_patch_size
        #print 'Pix shape: %s, dtype: %s'%(pix.shape, pix.dtype)

        if len(psz) == 2: #HW
            return psz==(msz[1], msz[0])
        elif len(psz) == 3: #HWC
            return psz==(msz[1], msz[0], msz[4])
        elif len(psz) == 4: #HWZC - this is ambiguous with T but not used for now
            return psz==(msz[1], msz[0], msz[2], msz[4])
        elif len(psz) == 5: #HWZTC
            return psz==(msz[1], msz[0], msz[2], msz[3], msz[4])

        return False

    def update_sample_db(self, image):
        if isinstance(image, (str, unicode)) is True:
            image = XImage(base_url=image)

        adapter_pixels = self.model.create_adapter_pixels(model=self.model, image=image)
        adapter_gobs = self.model.create_adapter_gobs(model=self.model, image=image)

        # get gobjects
        gobs = adapter_gobs.get_gobjects()
        if len(gobs)<1:
            return
        log.debug('number gobs: %s', len(gobs))
        log.debug('total_samples: %s', self.model.total_samples)

        # estimate db sizes
        if os.name == 'nt' or sys.platform == 'darwin':
            db_img_sz = self.get_lmdb_size(self.model.total_samples, self.sz_keyenc, self.get_db_element_size())
            db_key_sz = self.get_lmdb_size(self.model.total_samples, self.sz_keyenc*2, self.sz_key)
        else:
            db_img_sz=int(1e12)
            db_key_sz=int(1e12)

        log.debug('db_img_sz %s', db_img_sz)
        log.debug('db_key_sz %s', db_key_sz)

        # write samples with randomized keys
        keys = {}
        error = None
        ldb = lmdb.open(self.db_images, map_size=db_img_sz, lock=True)
        try:
            with ldb.begin(write=True) as txn:
                for g in gobs:
                    c = g.type
                    if c not in self.model.classes_model and not self.model.use_background_class:
                        continue
                    elif c not in self.model.classes_model and self.model.use_background_class is True:
                        c = self.model.background_class_name

                    #log.debug('Processing sample from class %s', c)
                    cid = self.model.classes_model[c]['id'] # get numerical value for class name

                    #pix = adapter_pixels.get_adapted_image_patch(gob=g)
                    # test if augmentation is used
                    if 'samples_actual' in self.model.classes_model[c]:
                        #log.debug('Using augmentation')
                        pixs = adapter_pixels.get_augmented_image_patches(gob=g)
                    else:
                        #log.debug('Using single patch')
                        pixs = [adapter_pixels.get_adapted_image_patch(gob=g)]

                    for i,pix in enumerate(pixs):
                        #log.debug('Pix shape: %s', pix.shape)
                        if self.patch_shape_matches_db(pix) is not True:
                            log.warning('Patch size does not match, requires %s but has %s, skipping...'%(str(self.model.db_patch_size), str(pix.shape)))
                            # dima: we could reshape the patch to match here
                            continue

                        #pix = pix[:,:,::-1] # RGB -> BGR
                        pix = pix.transpose((2,0,1)) # HWC -> CHW

                        #pylint: disable=no-member
                        datum = caffe.io.array_to_datum(pix)
                        datum.label = cid
                        #print 'datum: %sx%sx%s, len: %s, label: %s'%(datum.width, datum.height, datum.channels, len(datum.data), datum.label)

                        # key is composed of resource uniq + object id + augmentation id
                        key = ('%s-%s'%(g.idx,i)).encode('ascii')

                        # use hashed key to randomize sample order
                        enc_key = hashlib.sha256(key).hexdigest()

                        txn.put(enc_key, datum.SerializeToString())

                        # store the mapping from encoded key to key
                        # using the same hashing algorithm we can quickly test presence of real key in the db
                        # likewise it's quick to find the real key for the encoded one if needed
                        keys[enc_key] = key

                        # update number of samples
                        self.model.classes_model[c]['samples'] += 1

        except (lmdb.MapFullError, lmdb.DbsFullError, lmdb.BadTxnError):
            log.exception('LMDB image file size exhausted')
            error = responses.INSUFFICIENT_STORAGE
        except Exception:
            log.exception('Problem writing data to LMDB file')
            error = responses.INTERNAL_SERVER_ERROR
        finally:
            ldb.close()

        # if error is not None:
        #     safe_remove_dir_file(self.db_images)
        #     raise ConnoisseurException(error, 'Problem creating sample database')

        # store the mapping from encoded key to key
        # using the same hashing algorithm we can quickly test presence of real key in the db
        # likewise it's quick to find the real key for the encoded one if needed
        kdb = lmdb.open(self.db_keys, map_size=db_key_sz, lock=True)
        try:
            with kdb.begin(write=True) as kxn:
                for enc_key,key in keys.iteritems():
                    kxn.put(enc_key, key)
        except (lmdb.MapFullError, lmdb.DbsFullError, lmdb.BadTxnError):
            log.exception('LMDB key file size exhausted')
            error = responses.INSUFFICIENT_STORAGE
        except Exception:
            log.exception('Problem writing keys to LMDB file')
            error = responses.INTERNAL_SERVER_ERROR
        finally:
            kdb.close()

        if error is not None:
            raise ConnoisseurException(error, 'Problem creating sample database')


    def split_samples_training_testing(self, sample_preview_paths=None):

        # testing_percent indicates the size of the testing set in percent
        # the validation set will be the same size as the testing set
        # the training set will include everything else
        # by default we'll use the 60%/20%/20% split for Training/Validation/Test
        total_samples_test = 0
        total_samples_val = 0
        total_samples_train = 0
        for k,c in self.model.classes_model.iteritems():
            v = c['samples']
            n_val = (v*self.model.testing_percent)/100
            n_test = n_val
            n_train = v - n_val - n_test
            c['samples_training']   = n_train
            c['samples_validation'] = n_val
            c['samples_testing']    = n_test
            total_samples_test += n_test
            total_samples_val += n_val
            total_samples_train += n_train

        classes = copy.deepcopy(self.model.classes_model)
        classes_by_id = dict((v['id'],v) for k,v in classes.iteritems())

        for k,c in classes.iteritems():
            c['preview'] = 0

        random.seed()

        # clear dbs
        safe_remove_dir_file(self.db_train)
        safe_remove_dir_file(self.db_val)
        safe_remove_dir_file(self.db_test)

        # estimate db sizes
        if os.name == 'nt' or sys.platform == 'darwin':
            el_sz = self.get_db_element_size()
            db_train_sz = self.get_lmdb_size(total_samples_train, self.sz_keyenc, el_sz)
            db_val_sz = self.get_lmdb_size(total_samples_val, self.sz_keyenc, el_sz)
            db_test_sz = self.get_lmdb_size(total_samples_test, self.sz_keyenc, el_sz)
        else:
            db_train_sz = int(1e12)
            db_val_sz = int(1e12)
            db_test_sz = int(1e12)

        # create split dbs
        error = None
        dbs = ['samples_training', 'samples_validation', 'samples_testing' ]
        rdb  = lmdb.open(self.db_images, readonly=True)
        tdb  = lmdb.open(self.db_train, map_size=db_train_sz, lock=True)
        vdb  = lmdb.open(self.db_val, map_size=db_val_sz, lock=True)
        tedb = lmdb.open(self.db_test, map_size=db_test_sz, lock=True)
        try: # protect the writing process
            with rdb.begin(buffers=True) as rtxn:
                cursor = rtxn.cursor()
                with vdb.begin(write=True) as vtxn:
                    with tdb.begin(write=True) as ttxn:
                        with tedb.begin(write=True) as tetxn:
                            for key, value in cursor:
                                    #pylint: disable=no-member
                                    datum = caffe.proto.caffe_pb2.Datum()
                                    datum.ParseFromString(value)
                                    c = classes_by_id[datum.label]

                                    # randomly decide which set to write the sample into
                                    out_set = random.randint(0, 2)
                                    c[dbs[out_set]] -= 1

                                    if out_set == 2 and c[dbs[out_set]]>=0:
                                        tetxn.put(key, datum.SerializeToString())
                                    elif out_set == 1 and c[dbs[out_set]]>=0:
                                        vtxn.put(key, datum.SerializeToString())
                                    else:
                                        ttxn.put(key, datum.SerializeToString())

                                    precache_key = '{0}.{1}'.format(c['id'], c['preview'])
                                    if sample_preview_paths and precache_key in sample_preview_paths:
                                        filename = sample_preview_paths.get(precache_key)
                                        x = np.fromstring(datum.data, dtype=np.uint8)
                                        x = x.reshape(1, datum.channels, datum.height, datum.width).squeeze().transpose((1,2,0))
                                        skimage.io.imsave(filename, x)
                                        c['preview'] = c['preview'] + 1

        except (lmdb.MapFullError, lmdb.DbsFullError, lmdb.BadTxnError):
            log.exception('LMDB split file size exhausted')
            error = responses.INSUFFICIENT_STORAGE
        except Exception:
            log.exception('Problem splitting LMDB files')
            error = responses.INTERNAL_SERVER_ERROR
        finally:
            rdb.close()
            tdb.close()
            vdb.close()
            tedb.close()

        if error is not None:
            safe_remove_dir_file(self.db_train)
            safe_remove_dir_file(self.db_val)
            safe_remove_dir_file(self.db_test)
            raise ConnoisseurException(error, 'Problem splitting sample database')

        # compute mean of the dataset
        safe_remove_dir_file(self.file_mean)
        args = [self.fix_path(self.db_images), self.fix_path(self.file_mean)]
        o = self.run_caffe_bin(self.COMMAND_MEAN, args)
        if o is None:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Error while running Caffe')

    def train(self, method='finetune'):
        args = ['train', '-gpu', 'all', '-solver', self.fix_path(self.file_solver)]

        # fine-tuning
        if method=='finetune':
            args.extend(['-weights', self.fix_path(self.file_weights)])

        # recovery from snapshot
        if method=='snapshot':
            # find the latest snapshot
            files = [f for f in os.listdir(self.path) if f.endswith('.solverstate') and f.startswith('weights_iter_')]
            files.sort(key=lambda x: int(x.replace('weights_iter_', '').replace('.solverstate', '')))
            latest_snapshot = os.path.join(self.path, files[-1])
            args.extend(['--snapshot=%s'%self.fix_path(latest_snapshot)])

        # capture output to update the loss/accuracy plot,
        # we need to parse: training loss, testing loss and testing accuracy for n iterations
        # right now we capture after run finished
        #args.extend(['>', 'out.log'])
        o = self.run_caffe_bin(self.COMMAND_CAFFE, args)
        if o is None:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Error while running Caffe, intermediate states were preserved...')

        # parse output
        # o

        # rename final snapshot to weights file
        try:
            files = [f for f in os.listdir(self.path) if f.endswith('.caffemodel') and f.startswith('weights_iter_')]
            files.sort(key=lambda x: int(x.replace('weights_iter_', '').replace('.caffemodel', '')))
            latest = os.path.join(self.path, files[-1])
            safe_remove_dir_file(self.file_weights)
            log.debug('Moving %s to %s', latest, self.file_weights)
            os.rename(latest, self.file_weights)
        except Exception:
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Error while updating weights, intermediate states were preserved...')

        # remove temporary snapshots
        files = [f for f in os.listdir(self.path) if f.startswith('weights_iter_')]
        for f in files:
            log.debug('Removing %s', f)
            safe_remove_dir_file(os.path.join(self.path, f))

    def validate(self, classes, my_goodness):
        ''' classes is a dictionary similar to model classes dict with inited and added variables:
                v['true_positive'] = 0
                v['false_negative'] = 0
                v['false_positive'] = 0
                v['false_positive_classes'] = [] # we need to compute weighted false positive later based on number of tested samples in each set
                v['n'] = 0
                v['discarded'] = 0
        '''

        # classify samples from the test set
        ldb = lmdb.open(self.db_test, readonly=True)
        try: # protect the writing process
            with ldb.begin(buffers=True) as txn:
                cursor = txn.cursor()
                for key, value in cursor:
                    #pylint: disable=no-member
                    datum = caffe.proto.caffe_pb2.Datum()
                    datum.ParseFromString(value)

                    # convert datum data into a 2D image like array WxHxC
                    x = np.fromstring(datum.data, dtype=np.uint8)
                    x = x.reshape(1, datum.channels, datum.height, datum.width).squeeze().transpose((1,2,0))
                    # mean subtraction
                    if self.mu is not None:
                        x = x - self.mu
                    out_class,goodness = self.classify(x)

                    classes[datum.label]['n'] += 1
                    if classes[out_class].get('ignored', False) is True:
                        classes[datum.label]['discarded'] += 1
                        continue
                    if goodness < my_goodness:
                        classes[datum.label]['discarded'] += 1
                        continue

                    # update class list
                    if datum.label == out_class:
                        classes[datum.label]['true_positive'] += 1
                    else:
                        classes[datum.label]['false_negative'] += 1
                        classes[out_class]['false_positive'] += 1
                        classes[out_class]['false_positive_classes'].append(datum.label)

        except Exception:
            log.exception('Problem validating the model')
            raise ConnoisseurException(responses.INTERNAL_SERVER_ERROR, 'Problem validating the model')
        finally:
            ldb.close()

        return classes
