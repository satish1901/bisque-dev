
# +
# future compatability code
# -
from __future__ import print_function


# +
# import(s)
# -
import numpy as np
import torchvision.transforms as transforms
import torch.nn as nn
import matplotlib.pyplot as plt
import os
import pickle
import torch
import logging
import sys

# noinspection PyPep8Naming
import PlanteomeDeepSegmentModels as models
import PlanteomeDeepSegmentDGC as DGC

from torch.autograd import Variable
from scipy.misc import imread, imresize


# +
# constant(s)
# -
MODULE_NAME = 'PlanteomeDeepSegmentLearning'
MODULE_VERSION = 'v0.3.0'
MODULE_DATE = '06 June, 2018'
MODULE_AUTHORS = 'Dimitrios Trigkakis, Justin Preece, Blake Joyce, Phil Daly'
MODULE_DESCRIPTION = '{} Module for BisQue {}'.format(MODULE_NAME, MODULE_VERSION)
MODULE_SOURCE = '{}.py'.format(MODULE_NAME)


# +
# logging
# -
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('bq.modules')
log.debug('{}> message on entry, args={}'.format(MODULE_NAME, sys.argv))


# +
# class: PlanteomeDeepSegmentLearningError()
# -
class PlanteomeDeepSegmentLearningError(Exception):

    def __init__(self, errstr=''):
        self.errstr = errstr


# +
# class: PlanteomeDeepSegmentLearning()
# -
class PlanteomeDeepSegmentLearning(object):

    # +
    # __init__()
    # -
    def __init__(self, contour_file='', data_file='', tiff_file='', results_file=''):

        self.contour_file = contour_file
        self.data_file = data_file
        self.tiff_file = tiff_file
        self.results_file = results_file

        # declare some variables and initialize them
        self.segmentation_file = os.path.abspath(os.path.expanduser('segmentation_result.png'))
        self.segmentation_result_masked = os.path.abspath(os.path.expanduser('segmentation_result_masked.png'))

        self.rois = None
        self.img_0 = None
        self.img_1 = None
        self.img_2 = None
        self.img_raw = None
        self.image = None
        self.oshape = None
        self.rois = None
        self.segment = None
        self.network = None
        self.quality = None
        self.deepsegment = None
        self.mex = None
        self.token = None
        self.gc = None
        self.width = None
        self.height = None
        self.t_scale = None
        self.polylines = {
            'fg': [], 'bg': []
        }
        self.gc_opts = {
            'file': self.tiff_file, 'image': None, 'resize': True, 'w': 0, 'h': 0, 'blur': True,
            'show_figures': True, 'debug': True, 'log': True
        }
        self.gc_pars = {
            'bins': 8, 'sigma': 7.0, 'interaction_cost': 50, 'stroke_dt': True, 'hard_seeds': True, 'stroke_var': 50
        }

    # +
    # hidden method: _show()
    # -
    @staticmethod
    def _show(image_data=None, name=''):

        # entry message
        log.debug('{}._show()> message on entry,image_data={}, name={}'.format(MODULE_NAME, str(image_data), name))

        if image_data is not None:
            if type(image_data) is np.ndarray:
                if len(image_data.shape) == 2:
                    image_data = image_data[:, ::-1]
            else:
                if len(image_data.shape) == 3:
                    image_data = image_data.permute(2, 0, 1).numpy()

            # plot it
            plt.imsave(name, image_data[..., ::-1])

        else:
            log.error('{}._show> no image data supplied'.format(MODULE_NAME))

        # exit message
        log.debug('{}._show()> message on exit'.format(MODULE_NAME))

    # +
    # method: process()
    # -
    def process(self, inrois=None, name=''):

        # entry message
        log.debug('{}.process()> message on entry, inrois={}, polylines[{}]={}'.format(
            MODULE_NAME, str(inrois), name, str(self.polylines[name])))

        # add entry if it doesn't exist
        if self.polylines.get(name, None) is None:
            self.polylines[name] = []

        # populate it
        if inrois:
            for _roi in inrois:
                self.polylines[name].append(DGC.DGCPolyLine(_roi))

        # exit message
        log.debug('{}.process()> message on exit, polylines[{}]={}'.format(
            MODULE_NAME, name, str(self.polylines[name])))

    # +
    # method: segmentation_processing()
    # -
    def segmentation_processing(self):

        # entry message
        log.debug('{}.segmentation_processing()> message on entry'.format(MODULE_NAME))

        # get graph cutter
        self.gc = DGC.GraphCutter(show_figures=True, logger=log)
        self.gc_opts['w'] = self.width
        self.gc_opts['h'] = self.height
        out = self.gc.graph(polylines=self.polylines, options=self.gc_opts, parameters=self.gc_pars)
        _seg_image, _contours_proper = out['segmentation'], out['contours']
        self._show(_seg_image, self.segmentation_file)

        self.img_0 = (((_seg_image - _seg_image.min()) / (_seg_image.max() - _seg_image.min())) * 1.0).astype(np.uint8)
        self.img_0 = np.expand_dims(self.img_0, axis=2)

        self.img_1 = np.array(self.image)
        self.img_1 = np.multiply(self.img_0, self.img_1)
        black = self.img_0[:, :, 0] == 0

        if self.network.split()[0].lower() == 'leaf':
            self.img_1[black] = [0.549 * 255, 0.570 * 255, 0.469 * 255]
        else:
            self.img_1[black] = [0.7446 * 255, 0.7655 * 255, 0.7067 * 255]

        self.img_2 = self.img_1.astype(np.uint8)
        self._show(self.img_2, self.segmentation_result_masked)

        # the sizes are inverted
        _t_scale_inverse = (self.oshape[0] / float(self.height), self.oshape[1] / float(self.width))
        pickle.dump([_contours_proper, _t_scale_inverse], open(self.contour_file, 'wb'))

        # exit message
        log.debug('{}.segmentation_processing()> message on exit'.format(MODULE_NAME))

    # +
    # method: main()
    # -
    def main(self):

        # entry message
        log.debug('{}.main()> message on entry'.format(MODULE_NAME))

        # unpickle the data
        [self.rois, self.segment, self.network, self.quality, self.deepsegment, self.mex, self.token] = pickle.load(
            open(self.data_file, 'rb'))

        # process ROIs
        for _e in self.rois:
            self.process(self.rois[_e], _e)

        # read image
        self.img_raw = imread(self.tiff_file)

        # resize width and height
        self.oshape = self.img_raw.shape
        self.width = max(int(self.oshape[1]), (2048 * int(self.quality))/20)
        self.height = max(int(self.oshape[0]), (2048 * int(self.quality))/20)
        self.image = imresize(self.img_raw, (self.height, self.width))

        self.t_scale = (float(self.width)/self.oshape[1], float(self.height)/self.oshape[0])

        if self.segment.lower() == 'true':
            self.segmentation_processing()

        _network = self.network.split()
        if _network[0].lower() == 'simple':

            dualnet = models.resnet50(pretrained=False)
            dualnet.fc = nn.Linear(2048, 5)

            nn.NLLLoss()
            nn.LogSoftmax()

            # cpu model for inference. The model itself is a gpu model, so we need to have the map_location arguments
            dualnet.load_state_dict(torch.load('DeepModels/resnet_model.pth',
                                               map_location=lambda storage, loc: storage))
            dualnet.eval()

            transform = transforms.Compose([transforms.ToTensor(),
                                            transforms.Normalize((0.549, 0.570, 0.469), (0.008, 0.0085, 0.0135))])

            if self.deepsegment.lower() == 'true':
                self.img_raw = self.img_2

            self.image = imresize(self.img_raw, (int(224), int(224)))
            img_tensor = transform(self.image)
            img_tensor = img_tensor.expand(1, 3, 224, 224)
            data = Variable(img_tensor, volatile=True)

            _output_class = dualnet(data)
            softmax = nn.Softmax()
            _output_class_s = softmax(_output_class)
            pred = _output_class_s.data.max(1)[1]
            conf = _output_class_s.data.max(1)[0]
            log.debug('{}.main()> prediction={}'.format(MODULE_NAME, pred))
            log.debug('{}.main()> confidence={}'.format(MODULE_NAME, conf))
            log.debug('{}.main()> prediction_c={:d}'.format(MODULE_NAME, int(pred.numpy()[0])))
            log.debug('{}.main()> confidence_c={:.2f}'.format(MODULE_NAME, float(conf.numpy()[0])))

            # is this captured somewhere? I think it must be
            with open(self.results_file, 'w+') as f:
                f.write('{}\n'.format(str(pred)))
                f.write('{}\n'.format(str(conf)))
                f.write('PREDICTION_C: {:d}\n'.format(int(pred.numpy()[0])))
                f.write('CONFIDENCE_C: {:f}\n'.format(float(conf.numpy()[0])))

        elif _network[0].lower() == 'leaf':

            dualnet = models.resnet18leaf(pretrained=False)
            dualnet.reform()

            nn.NLLLoss()
            nn.LogSoftmax()

            # cpu model for inference. The model itself is a gpu model, so we need to have the map_location arguments
            dualnet.load_state_dict(torch.load('DeepModels/leaf_model.pth', map_location=lambda storage, loc: storage))
            dualnet.eval()

            transform = transforms.Compose([transforms.ToTensor(),
                                            transforms.Normalize((0.7446, 0.7655, 0.7067), (0.277, 0.24386, 0.33867))])

            if self.deepsegment.lower() == 'true':
                self.img_raw = self.img_2

            self.image = imresize(self.img_raw, (int(224), int(224)))
            img_tensor = transform(self.image)
            img_tensor = img_tensor.expand(1, 3, 224, 224)
            data = Variable(img_tensor, volatile=True)

            output_class = dualnet(data)
            softmax = nn.Softmax()

            with open(self.results_file, 'w+') as f:
                for i in range(6):
                    f.write(softmax(output_class[i]).data.max(1)[1].numpy()[0])

        # exit message
        log.debug('{}.main()> message on exit'.format(MODULE_NAME))


# +
# main()
# -
if __name__ == '__main__':
    try:
        log.debug('{}.__main__()> starting ...'.format(MODULE_NAME))
        P = PlanteomeDeepSegmentLearning()
        P.main()
        log.debug('{}.__main__()> done'.format(MODULE_NAME))
    except PlanteomeDeepSegmentLearningError as err:
        print('{}.__main__()> failed, error={}'.format(MODULE_NAME, err.errstr))
