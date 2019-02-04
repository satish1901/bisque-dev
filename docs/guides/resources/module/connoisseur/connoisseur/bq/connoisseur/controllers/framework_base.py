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
Connoisseur: base for frameworks

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

# default imports
import os
import logging
import pkg_resources

import bq.connoisseur.controllers.responses as responses

log = logging.getLogger("bq.connoisseur.framework_base")

#---------------------------------------------------------------------------------------
# FrameworkBase
#---------------------------------------------------------------------------------------

class FrameworkBase(object):
    '''Base for DL frameworks for classification and training'''

    name = ''
    version = '1.0'

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        pass

    def __str__(self):
        return 'Framework(name: %s)'%(self.name)

    def __init__(self, model=None):
        self.model = model
        if model is not None:
            self.load(model=model)
            try:
                self.activate (training=False)
            except RuntimeError:
                log.debug('Could not activate the framework')
            except Exception:
                log.exception('Error while trying to activate the framework')

    def load (self, model):
        ''' load all the pertinent data in CPU memory '''
        self.model = model

    def activate (self, training=False):
        ''' activates the network, e.g. loads it in the GPU '''
        pass

    def deactivate (self):
        ''' deactivates the network, e.g. un-loads it in the GPU '''
        pass

    def is_activate (self):
        ''' returns if network is active '''
        return False

    def get_device_info (self):
        ''' returns a list of deice info dictionaries '''
        return []

    def classify(self, x):
        ''' returns class_id and its goodness for the sample x '''
        out_class = None
        goodness = 0
        return (out_class, goodness)

    def cache_sample_preview(self, class_id, sample_id, filename):
        ''' saves sample into a file '''
        pass

    def reset_sample_db(self):
        '''
        clear model sample database and init a brand new one
        '''
        pass

    def update_model_from_template(self):
        '''
        parse all template files and create all required files with proper variables set
        '''
        pass

    def update_sample_db(self, image):
        '''
        add samples from a given image into db, this can be run in parallel in threads, processes and machines
        make sure that parallel use will not create problems and collisions
        '''
        pass

    def split_samples_training_testing(self, sample_preview_paths=None):
        '''
        this should filter and split samples into sets that can be used directly for training and validation
        '''
        pass

    def train(self, method='finetune'):
        '''
        train the model on the existing training set
        accepted methods now are: None, 'full', 'finetune', 'snapshot'
        '''
        pass

    def validate(self, classes, my_goodness):
        '''
        classes is a dictionary keyed by class number and added variables:
            v['true_positive'] = 0
            v['false_negative'] = 0
            v['false_positive'] = 0
            v['false_positive_classes'] = [] # we need to compute weighted false positive later based on number of tested samples in each set
            v['n'] = 0
            v['discarded'] = 0
        my_goodness is the goodness level at which to validate the classification
        '''
        pass
