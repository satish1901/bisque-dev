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
Connoisseur base for adapters: adapt BisQue resources into model elements

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

import os
import re
import logging
import pkg_resources

import skimage.io
import numpy as np
from scipy import ndimage #pylint: disable=import-error

from .gobjects import factory
from bq.connoisseur.controllers.exceptions import ConnoisseurException
import bq.connoisseur.controllers.responses as responses

log = logging.getLogger("bq.connoisseur.adapter_base")

AUGMENTATION_SCALE = 10

#---------------------------------------------------------------------------------------
# utils
#---------------------------------------------------------------------------------------

def do_rotate(pix, ang):
    if ang == 180:
        img = np.flipud(pix)
    else:
        img = ndimage.rotate(pix, ang, reshape=False, mode='reflect')
    #print img.shape, img.dtype
    #skimage.io.imsave('tile_r%s.png'%ang, img)
    return img

def do_scale(pix, sc):
    img = ndimage.interpolation.zoom(pix, (sc,sc,1))
    D = (np.array(img.shape) - np.array(pix.shape)) / 2
    X,Y,C = img.shape
    img = img[D[0]:-D[0], D[1]:-D[1], :]
    #print img.shape, img.dtype
    #skimage.io.imsave('tile_s%s.png'%sc, img)
    return img

#---------------------------------------------------------------------------------------
# AdapterPixelsBase
#---------------------------------------------------------------------------------------

class AdapterPixelsBase(object):
    '''
    Connoisseur base for pixel adapters: Convert annotation into pixels

    These adapters are supposed to return pixel data in exact format needed by the model,
    they might download and modify a whole image or request necessary transformations
    on the image service, they might have to keep track of image resolution and radiometric
    parameters using image meta-data.

    The location and definition of the pixel data comes from gobjects delineating the image
    region. Each adapter might use them differently but they should support transformations
    of all gobject types recognized by the system.

    Pixel data coming out of the adapter must be a patch in exact format defined by the model.
    '''

    name = '' # ex: 'rgb_2d_roi'
    version = '1.0'

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        pass

    def __init__(self, model=None, args=None, image=None, **kw):
        self.pars = {}
        self.model = None
        self.args = None
        self.image = None
        if image and not None and model is not None:
            self.init(model, args, image, **kw)

    def __str__(self):
        return 'Adapts image resource data to model patch'

    def init(self, model, args, image, **kw):
        """ init adapter data if needed, for example, load an image in memory """
        self.model = model
        self.args = args
        self.image = image
        self.pars = self.model.adapter_descr_pixels.parameters
        #log.debug('Pars: %s', self.pars)

    def get_adapted_image_scale(self):
        """ returns scale for (y,x,z,t) of the whole as seen by this adapter """
        return (1.0, 1.0, 1.0, 1.0)

    def get_adapted_image_size(self):
        """ returns (H,W) of the whole as seen by this adapter """
        raise ConnoisseurException(responses.NOT_IMPLEMENTED, 'Class adapter must implement "get_adapted_image_size" method')

    def get_adapted_image_patch(self, gob, **kw):
        """ return image pixels for a given gobject as a numpy array """
        raise ConnoisseurException(responses.NOT_IMPLEMENTED, 'Class adapter must implement "get_adapted_image_patch" method')

    def get_augmented_image_patches(self, gob, **kw):
        """ return a list of image pixels with several perturbations for a given gobject as a numpy array """
        pix = self.get_adapted_image_patch(gob, **kw)

        # various 90 deg rotations
        pix_r90 = do_rotate(pix, 90)
        pix_r180 = do_rotate(pix, 180)
        pix_r270 = do_rotate(pix, 270)

        # 45 deg rotation and scale
        pix_r45 = do_rotate(pix, 45)
        pix_r135 = do_rotate(pix, 135)
        pix_r225 = do_rotate(pix, 225)
        pix_r315 = do_rotate(pix, 315)

        # scale changes
        pix_s15 = do_scale(pix, 1.5)
        pix_s25 = do_scale(pix, 2.5)

        return [pix, pix_r90, pix_r180, pix_r270, pix_r45, pix_r135, pix_r225, pix_r315, pix_s15, pix_s25]


#---------------------------------------------------------------------------------------
# AdapterGobjectsBase
#---------------------------------------------------------------------------------------

class AdapterGobjectsBase(object):
    '''
    Connoisseur base for gobjects extractors: Convert annotations into a list of gobjects

    These adapters are supposed to extract graphical annotations from resources
    perform transformations of the gob list first (possibly reducing the number of gobs)
    then transform all gob types using class name adapter and finally return the
    complete list of gobjects as lightweight python objects.

    get_class_name - performs class name transformation by constructing a string from
    xml node and later modifying it according to parameters

    get_gobjects - creates a list of gobs, transforms it, uses get_class_name on all types
    and returns final list
    '''

    name = '' # value_text
    version = '1.0'

    @classmethod
    def get_parameters (cls, node):
        ''' add sub-nodes with parameter definitions '''
        pass

    def __init__(self, model=None, args=None, image=None, **kw):
        self.pars = {}
        self.model = None
        self.args = None
        self.image = None
        if model is not None:
            self.init(model, args, image, **kw)

    def __str__(self):
        return 'Adapts image annotations into list of gobjects'

    def init(self, model, args, image, **kw):
        """ init adapter data if needed, for example, load an image resource in memory """
        self.model = model
        self.args = args
        self.image = image
        self.pars = self.model.adapter_descr_gobs.parameters
        #log.debug('Pars: %s', self.pars)

    def get_class_name(self, node, **kw):
        """ must implement: return a class name for a given node """
        raise ConnoisseurException(responses.NOT_IMPLEMENTED, 'Class adapter must implement "get_class_name" method')

    def get_gobjects(self, **kw):
        """ return a list of gobjects for a given image, the default implementation returns a full list of
            gobjects as they appear in the resource with adapted class names. One may re-implement this
            function in order to modify the gobjects list, e.g. obtain aggregation behavior, etc...
        """
        resource = self.image.get_resource()

        # find all gobject nodes that have an inner object containing vertices
        nodes = resource.xpath('//gobject/*/vertex/../..')
        gobs = [factory.make(n) for n in nodes]
        for i,n in enumerate(nodes):
            try:
                gobs[i].type = self.get_class_name(n)
            except Exception:
                pass
        gobs = [g for g in gobs if g is not None and g.type is not None]
        return gobs


