
# +
# future compatability code
# -
from __future__ import print_function


# +
# import(s)
# -
import numpy as np
import maxflow
import cv2
import os
import tifffile as tiff
import matplotlib.pyplot as plt

from skimage import measure


# +
# constant(s)
# -
MODULE_NAME = 'PlanteomeDeepSegmentDGC'
MODULE_VERSION = 'v0.3.0'
MODULE_DATE = '06 June, 2018'
MODULE_AUTHORS = 'Dimitrios Trigkakis, Justin Preece, Blake Joyce, Phil Daly'
MODULE_DESCRIPTION = '{} Module for BisQue {}'.format(MODULE_NAME, MODULE_VERSION)
MODULE_SOURCE = '{}.py'.format(MODULE_NAME)

GRAPH_POLYLINES = {}

GRAPH_PARAMETERS = {
    'bins': 8,
    'sigma': 7.0,
    'interaction_cost': 50,
    'stroke_dt': True,
    'stroke_var': 50,
    'hard_seeds': True
}

GRAPH_OPTIONS = {
    'file': None,
    'image_rgb': None,
    'resize': False,
    'w': 0,
    'h': 0,
    'blur': True,
    'show_figures': True,
    'log': False,
    'debug': False
}

WEIGHT_PARAMETERS = {
    'edges': None,
    'image': None,
    'lattice_size': (0, 0, 0),
    'nlink_sigma': 0
}


# +
# class: polyline()
# -
class DGCPolyLine(object):

    # +
    # __init__()
    # vertices is a list of point dictionaries
    # -
    def __init__(self, vertices=None):

        if vertices is not None and isinstance(vertices, list):
            self.vertices = vertices
        else:
            self.vertices = []

        self.points = []

    # +
    # method: transform()
    # -
    def transform(self, scaling=None):
        if scaling and scaling.get('w', -1.0) >= 0.0 and scaling.get('h', -1.0) >= 0.0:
            for vertex in self.vertices:
                if vertex.get('x', None) is not None:
                    vertex['x'] *= scaling['w']
                if vertex.get('y', None) is not None:
                    vertex['y'] *= scaling['h']

    # +
    # method: bresenham_point()
    # -
    @staticmethod
    def bresenham_point(v_prev=None, v_curr=None, mask=None):

        if v_prev is not None and v_curr is not None and mask is not None:

            x1, x2 = int(round(v_prev['x'])), int(round(v_curr['x']))
            y1, y2 = int(round(v_prev['y'])), int(round(v_curr['y']))
            dx, dy = x2 - x1, y2 - y1
            steep = abs(dy) > abs(dx)

            if steep:
                x1, y1 = y1, x1
                x2, y2 = y2, x2

            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1

            dx, dy = x2 - x1, y2 - y1

            error = int(dx / 2.0)
            y_add = 1 if y1 < y2 else -1

            # iterate over bounding box generating points between start and end
            y = y1
            for x in range(x1, x2 + 1):
                point = (y, x) if steep else (x, y)
                mask[point[1], point[0]] = 255
                error -= abs(dy)
                if error < 0:
                    y += y_add
                    error += dx

    # +
    # method: bresenham()
    # -
    def bresenham(self, mask=None):

        self.points = []

        if mask is not None and len(self.vertices)>0:
            vertex_prev = self.vertices[0]
            for i, vertex_curr in enumerate(self.vertices, start=1):
                self.bresenham_point(vertex_prev, vertex_curr, mask)
                vertex_prev = vertex_curr

        return

    # +
    # method: add_vertex()
    # -
    def add_vertex(self, vertex=None):
        if vertex is not None:
            self.vertices.append(vertex)

    # +
    # method: del_vertex()
    # -
    def del_vertex(self):
        self.vertices.pop()


# +
# class: GraphCutter()
# -
class GraphCutter(object):

    # +
    # __init__()
    # -
    def __init__(self, show_figures=True, logger=None):

        self.show_figures = show_figures
        self.logger = logger

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.__init__()> message on entry, show_figures={}, logger={}'.format(
                MODULE_NAME, str(self.show_figures), str(self.logger)))

        self.options = None
        self.polylines = None
        self.options = None
        self.parameters = None
        self.scaling = None
        self._i = None

        # exit message
        if self.logger is not None:
            self.logger.debug('{}.__init__()> message on exit, show_figures={}, logger={}'.format(
                MODULE_NAME, str(show_figures), str(logger)))

    # +
    # method: show()
    # -
    def show(self, image_data=None, name=''):

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.show()> message on entry, image_data={}, name={}, options={}'.format(
                MODULE_NAME, str(image_data), name, self.options))

        # check input(s)
        if image_data is None:
            return
        if not isinstance(name, str) or name == '':
            return
        if not self.options['show_figures']:
            return

        if isinstance(image_data, np.ndarray):
            if len(image_data.shape) == 2:
                image_data = image_data[:, ::-1]
        else:
            if len(image_data.shape) == 3:
                image_data = image_data.permute(2, 0, 1).numpy()

        # noinspection PyBroadException
        try:
            plt.imsave(name, image_data[..., ::-1])
        except:
            if self.logger is not None:
                self.logger.debug('{}.show()> failed to plot data {}'.format(MODULE_NAME, name))

        # exit message
        if self.logger is not None:
            self.logger.debug('{}.show()> message on exit, image_data={}, name={}, options={}'.format(
                MODULE_NAME, str(image_data), name, self.options))

        return

    # +
    # method: lattice_constructor()
    # -
    def lattice_constructor(self, connectivity=8, lattice_size=(0, 0)):

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.lattice_constructor()> message on entry, connectivity={}, lattice_size={}'.format(
                MODULE_NAME, connectivity, str(lattice_size)))

        r = lattice_size[0]
        c = lattice_size[1]

        if connectivity == 8 and r != 0 and c != 0:
            _n = r * c
            _m = r * (c - 1) + (r - 1) * c + 2 * (r - 1) * (c - 1)
            edges = np.zeros((_m, 2), dtype=np.int32)
            edge_nodes = np.arange(_n)
            edge_nodes = edge_nodes.reshape((r, c))

            _m_temp = r * (c - 1)
            edges[0:_m_temp, :] = np.concatenate((edge_nodes[:, 0:c - 1].reshape(
                (r * (c - 1), 1)), edge_nodes[:, 1:c].reshape((r * (c - 1), 1))), axis=1)

            edges[_m_temp:_m_temp + (r - 1) * c, :] = np.concatenate((edge_nodes[0:r - 1, :].reshape(
                ((r - 1) * c, 1)), edge_nodes[1:r, :].reshape(((r - 1) * c, 1))), axis=1)

            _m_temp = _m_temp + (r - 1) * c

            edges[_m_temp:_m_temp + (r - 1) * (c - 1), :] = np.concatenate((edge_nodes[0:r - 1, 0:c - 1].reshape(
                (r - 1) * (c - 1), 1), edge_nodes[1:r, 1:c].reshape(((r - 1) * (c - 1), 1))), axis=1)

            _m_temp = _m_temp + (r - 1) * (c - 1)

            edges[_m_temp:_m_temp + (r - 1) * (c - 1), :] = np.concatenate((edge_nodes[0:r - 1, 1:c].reshape(
                (r - 1) * (c - 1), 1), edge_nodes[1:r, 0:c - 1].reshape(((r - 1) * (c - 1), 1))), axis=1)

            # exit message
            if self.logger is not None:
                self.logger.debug('{}.lattice_constructor()> message on exit, connectivity={}, lattice_size={}'.format(
                    MODULE_NAME, connectivity, str(lattice_size)))

            return edges

    # +
    # method: edge_weights()
    # -
    def edge_weights(self, parameters=WEIGHT_PARAMETERS):

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.edge_weights()> message on entry, parameters={}'.format(MODULE_NAME, str(parameters)))

        r, c = parameters['lattice_size']
        _x, _y = np.meshgrid(np.arange(0, c), np.arange(0, r))
        edges = parameters['edges']
        _i = parameters['image']

        self.show(_i, 'I.jpg')
        self.show(_x, 'X.jpg')
        self.show(_y, 'Y.jpg')

        _x0 = _x[np.remainder(edges[:, 0], r).astype(np.int32), np.multiply(edges[:, 0], 1.0 / r).astype(np.int32)]
        _x1 = _x[np.remainder(edges[:, 1], r).astype(np.int32), np.multiply(edges[:, 1], 1.0 / r).astype(np.int32)]
        _xs = np.power(np.subtract(_x0, _x1), 2)

        _y0 = _y[np.remainder(edges[:, 0], r).astype(np.int32), np.multiply(edges[:, 0], 1.0 / r).astype(np.int32)]
        _y1 = _y[np.remainder(edges[:, 1], r).astype(np.int32), np.multiply(edges[:, 1], 1.0 / r).astype(np.int32)]
        _ys = np.power(np.subtract(_y0, _y1), 2)

        euclidean_distance = np.sqrt(np.add(_xs, _ys))

        # noinspection PyTypeChecker
        _i0 = _i[np.remainder(edges[:, 0], r).astype(np.int32),
                 np.multiply(edges[:, 0], 1.0 / r).astype(np.int32)].astype(np.float32)
        # noinspection PyTypeChecker
        _i1 = _i[np.remainder(edges[:, 1], r).astype(np.int32),
                 np.multiply(edges[:, 1], 1.0 / r).astype(np.int32)].astype(np.float32)

        k = 2
        w_feat = np.power(np.abs(np.subtract(_i0, _i1)), k)
        # self.show(w_feat.reshape(-1, 1), 'wfeat.jpg')

        sigma = parameters['nlink_sigma']
        if parameters['nlink_sigma'] <= 0:
            sigma = np.sqrt(np.mean(w_feat))

        weights = np.multiply(np.exp(np.multiply(-1.0 / (2 * sigma ** 2), w_feat)), np.divide(1, euclidean_distance))

        # exit message
        if self.logger is not None:
            self.logger.debug('{}.edge_weights()> message on exit, parameters={}'.format(MODULE_NAME, str(parameters)))

        return weights, euclidean_distance

    # +
    # method: vrl_gc()
    # -
    def vrl_gc(self, sizes, fg, bg, edges, weights):

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.vrl_gc()> message on entry, sizes={}, fg={}, bg={}, edges={}, weights={}'.format(
                MODULE_NAME, str(sizes), str(fg), str(bg), str(edges), str(weights)))

        grid_size = sizes[1] * sizes[2]
        g = maxflow.Graph[float](grid_size, (2 * grid_size) + (2 * sizes[3]))

        nodeids = g.add_nodes(grid_size)

        for i in range(grid_size):
            g.add_tedge(i, fg[int(i % sizes[1]), int(i / sizes[1])], bg[int(i % sizes[1]), int(i / sizes[1])])

        for i in range(sizes[3]):
            g.add_edge(edges[i, 0], edges[i, 1], weights[i], weights[i])

        g.maxflow()
        output = np.zeros((sizes[1], sizes[2]))
        for i in range(len(nodeids)):
            output[int(i % sizes[1]), int(i / sizes[1])] = g.get_segment(nodeids[i])

        # exit message
        if self.logger is not None:
            self.logger.debug('{}.vrl_gc()> message on exit, sizes={}, fg={}, bg={}, edges={}, weights={}'.format(
                MODULE_NAME, str(sizes), str(fg), str(bg), str(edges), str(weights)))

        return output

    # +
    # method: graph()
    # -
    def graph(self, polylines=GRAPH_POLYLINES, parameters=GRAPH_PARAMETERS, options=GRAPH_OPTIONS):

        # entry message
        if self.logger is not None:
            self.logger.debug('{}.graph()> message on entry, polylines={}, parameters={}, options={}'.format(
                MODULE_NAME, str(polylines), str(parameters), str(options)))

        # get input(s)
        self.polylines = polylines
        self.options = options
        self.parameters = parameters

        if self.logger:
            self.logger.debug('polylines = {}'.format(str(self.polylines)))
            self.logger.debug('options = {}'.format(str(self.options)))
            self.logger.debug('parameters = {}'.format(str(self.parameters)))

        if self.options.get('file', '') != '' and \
                os.path.exists(os.path.abspath(os.path.expanduser(self.options['file']))):
            self._i = cv2.imread(self.options['file'], 1)
            if self._i is None:
                self.logger.debug('failed to read {}, trying tifffile()'.format(self.options['file']))
                self._i = tiff.imread(self.options['file'])
        else:
            self.logger.debug('options[image_rgb] = {}'.format(self.options['image_rgb']))
            self._i = self.options['image_rgb']  # Debug-Fix : is it normalized to 0-1 and w-h-c?

        self.logger.debug('self._i = {}'.format(str(self._i)))

        o_h, o_w, o_c = self._i.shape
        assert o_c == 3
        self.scaling = {'w': 1.0, 'h': 1.0}

        self.show(self._i, 'OriginalImage.jpg')

        if self.options['resize']:
            resized_image = cv2.resize(self._i, (self.options['w'], self.options['h']))
            self.scaling = {'w': float(self.options['w']) / o_w, 'h': float(self.options['h']) / o_h}
            self.show(resized_image, 'ResizedImage.jpg')
        else:
            resized_image = self._i
            self.options['w'] = self._i.shape[1]
            self.options['h'] = self._i.shape[0]

        self.logger.debug('h x w x c --- input image {} transformed to {} with scaling {:0.2f}, {:0.2f}'.format(
            self._i.shape, (self.options['h'], self.options['w'], 3), *self.scaling.values()))

        blur = resized_image[:, :, 2]
        self.show(blur, 'BlurredImage_beforeGauss.jpg')
        blur = cv2.GaussianBlur(blur, (5, 5), 1.4)

        # polyline transformation to produce numpy pixel masks
        np_bg_mask = np.zeros((self.options['h'], self.options['w']), np.uint8)
        np_fg_mask = np.zeros((self.options['h'], self.options['w']), np.uint8)

        for loc in self.polylines:
            mask = np_bg_mask if loc == 'bg' else np_fg_mask
            for polyline in self.polylines[loc]:
                polyline.transform(self.scaling)
                polyline.bresenham(mask)

        self.show(np_fg_mask, 'FGmask.jpg')
        self.show(np_bg_mask, 'BGmask.jpg')
        self.show(blur, 'BlurredImage.jpg')

        histograms = {}
        dst = {}

        for loc in self.polylines:
            mask = np_bg_mask if loc == 'bg' else np_fg_mask
            channels = [0, 1, 2]
            ranges = [0, 256, 0, 256, 0, 256]
            # noinspection PyUnusedLocal
            histograms[loc] = cv2.calcHist([resized_image], channels, mask,
                                           [self.parameters['bins'] for i in channels], ranges)
            histograms[loc] = histograms[loc] / np.sum(histograms[loc])
            b, g, r = cv2.split(resized_image / (256.0 / self.parameters['bins']))
            dst[loc] = np.float32(histograms[loc][b.astype(np.uint64).ravel(), g.astype(np.uint64).ravel(),
                                                  r.astype(np.uint64).ravel()])
            dst[loc] = dst[loc].reshape(resized_image.shape[:2])
            self.show(dst[loc], 'back-projection{}.jpg'.format(str(loc)))

        if self.parameters['stroke_dt']:
            dist_transform = None
            if hasattr(cv2, 'DIST_L2'):
                dist_transform = cv2.distanceTransform(np_bg_mask, cv2.DIST_L2, maskSize=3)
            elif hasattr(cv2, 'cv') and hasattr(cv2.cv, 'CV_DIST_L2'):
                dist_transform = cv2.distanceTransform(255-np_fg_mask, cv2.cv.CV_DIST_L2, maskSize=3)
            if dist_transform is not None:
                stroke_d_t = np.exp(-dist_transform / (self.parameters['stroke_var']*1.0))
                dst['fg'] = dst['fg'] * stroke_d_t
                dst['bg'] = dst['bg'] * (1-stroke_d_t)
                self.show(dst['fg'], 'back-projection{}.jpg'.format(str('fg_DT_')))
                self.show(dst['bg'], 'back-projection{}.jpg'.format(str('bg_DT_')))

        for loc in self.polylines:
            dst[loc] = -np.log(dst[loc]+0.01)

        if self.parameters['hard_seeds']:
            for loc in self.polylines:
                mask = np_bg_mask if loc == 'fg' else np_fg_mask  # masks are inverted here
                dst[loc] = np.where(mask > 0, 10 ** 6, dst[loc])

        # edges is a numpy array of all node pairs in edges of a lattice of size w x h

        lattice_size = (options['w'], options['h'])
        edges = self.lattice_constructor(lattice_size=lattice_size)

        edge_parameters = {
            'edges': edges,
            'image': blur,
            'lattice_size': lattice_size[::-1],
            'nlink_sigma': self.parameters['sigma']
        }

        # image should be inverted to previous state, DT transform, hard seeds
        weights, w_dist = self.edge_weights(edge_parameters)
        weights = np.expand_dims(weights, axis=1)

        # set up all parameters to create the graph algorithm
        sizes = [2, self.options['h'], self.options['w'], edges.shape[0]]
        seg_fg = self.vrl_gc(sizes, dst['fg'], dst['bg'], np.subtract(edges, 1),
                             np.multiply(weights, self.parameters['interaction_cost']))

        zero_padding = 1
        seg_fg[:zero_padding, :] = 0
        seg_fg[:, :zero_padding] = 0
        seg_fg[-zero_padding:, :] = 0
        seg_fg[:, -zero_padding:] = 0

        self.show(seg_fg, 'segmentation.jpg')
        seg = measure.find_contours(seg_fg, 0.8)
        self.show(seg_fg, 'segmentation_f.jpg')

        max_points = 0
        m = None

        # noinspection PyBroadException
        try:
            for i in range(len(seg)):
                if len(seg[i]) > max_points:
                    max_points = len(seg[i])
                    m = seg[i]
        except:
            m = seg

        seg = m
        seg = seg[::, ::]

        retval = {
            'segmentation': seg_fg,
            'contours': seg,
            'polylines': self.polylines,
            'options': self.options,
            'parameters': self.parameters
        }

        # exit message
        if self.logger is not None:
            self.logger.debug('{}.graph()> message on exit, retval={}'.format(
                MODULE_NAME, str(retval)))

        return retval
