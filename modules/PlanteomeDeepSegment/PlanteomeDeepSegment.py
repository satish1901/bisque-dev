
# +
# future compatability code
# -
from __future__ import print_function


# +
# import(s)
# -
import csv

try:
    # noinspection PyPep8Naming
    from lxml import etree as eTree
except ImportError:
    import xml.etree.ElementTree as eTree

from bqapi.comm import BQSession
from optparse import OptionParser

from PlanteomeDeepSegmentLeaf import *
from PlanteomeDeepSegmentLearning import *


# +
# constant(s)
# -
MODULE_NAME = 'PlanteomeDeepSegment'
MODULE_VERSION = 'v0.3.0'
MODULE_DATE = '06 June, 2018'
MODULE_AUTHORS = 'Dimitrios Trigkakis, Justin Preece, Blake Joyce, Phil Daly'
MODULE_DESCRIPTION = '{} Module for BisQue {}'.format(MODULE_NAME, MODULE_VERSION)
MODULE_SOURCE = '{}.py'.format(MODULE_NAME)

PICKLE_CONTOURS_FILE = 'contours.pkl'
PICKLE_DATA_FILE = 'data.pkl'
TEXT_RESULTS_FILE = 'results.txt'
TIFF_IMAGE_FILE = 'temp.tif'
CSV_LEAF_FILE = '{}LeafMappings.csv'.format(MODULE_NAME)


# +
# logging
# -
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('bq.modules')
log.debug('{}> message on entry, args={}'.format(MODULE_NAME, sys.argv))


# +
# class: PlanteomeDeepSegmentError()
# -
class PlanteomeDeepSegmentError(Exception):

    def __init__(self, errstr=''):
        self.errstr = errstr


# +
# class: PlanteomeDeepSegment()
# -
class PlanteomeDeepSegment(object):

    # +
    # __init__()
    # -
    def __init__(self):

        # entry message
        log.debug('{}.__init__()> message on entry'.format(MODULE_NAME))

        # declare some variables and initialize them
        self.options = None
        self.bqSession = None
        self.rois = None
        self.message = None

        # get full path(s) to file(s)
        self.contours_file = os.path.abspath(os.path.expanduser(PICKLE_CONTOURS_FILE))
        self.data_file = os.path.abspath(os.path.expanduser(PICKLE_DATA_FILE))
        self.results_file = os.path.abspath(os.path.expanduser(TEXT_RESULTS_FILE))
        self.tiff_file = os.path.abspath(os.path.expanduser(TIFF_IMAGE_FILE))
        self.csv_leaf_file = os.path.abspath(os.path.expanduser(CSV_LEAF_FILE))

        log.debug('{}.__init()> self.contours_file={}'.format(MODULE_NAME, self.contours_file))
        log.debug('{}.__init()> self.data_file={}'.format(MODULE_NAME, self.data_file))
        log.debug('{}.__init()> self.results_file={}'.format(MODULE_NAME, self.results_file))
        log.debug('{}.__init()> self.tiff_file={}'.format(MODULE_NAME, self.tiff_file))
        log.debug('{}.__init()> self.csv_leaf_file={}'.format(MODULE_NAME, self.csv_leaf_file))

        # exit message
        log.debug('{}.__init__()> message on exit'.format(MODULE_NAME))

    # +
    # hidden method: _mex_parameter_parser()
    # -
    def _mex_parameter_parser(self, mex_xml=None):

        # entry message
        log.debug('{}._mex_parameter_parser()> message on entry, mex_xml={}'.format(MODULE_NAME, str(mex_xml)))

        if mex_xml is not None:
            mex_inputs = mex_xml.xpath('tag[@name="inputs"]')
            if mex_inputs:
                for tag in mex_inputs[0]:
                    if tag.tag == 'tag' and tag.attrib['type'] != 'system-input':
                        _name = tag.attrib['name'].strip()
                        _value = tag.attrib['value'].strip()
                        log.debug('{}._mex_parameter_parser()> setting self.options.{}={}'.format(
                            MODULE_NAME, _name, _value))
                        setattr(self.options, _name, _value)
                        log.debug("{}._mex_parameter_parser()> set self.options.{}={}".format(
                            MODULE_NAME, _name, getattr(self.options, _name)))
            else:
                log.error('{}.mex_parameter_parser()> no inputs found on mex!'.format(MODULE_NAME))
        else:
            self.message = '{}.mex_parameter_parser()> mex_xml is None'.format(MODULE_NAME)
            log.error(self.message)

        # exit message
        log.debug('{}.main()> message on exit, options={}'.format(MODULE_NAME, self.options))

    # +
    # hidden method: _validate_input()
    # -
    def _validate_input(self):

        # entry message
        retval = False
        log.debug('{}._validate_input()> message on entry, retval={}'.format(MODULE_NAME, retval))

        # run module through engine_service (default)
        if self.options.mexURL and self.options.token:
            retval = True

        # run module locally
        elif self.options.user and self.options.pwd and self.options.root:
            retval = True

        else:
            retval = False
            log.error('{}.validate_input()> insufficient options or arguments to start this module'.format(MODULE_NAME))

        # exit message
        log.debug('{}._validate_input()> message on exit, retval={}'.format(MODULE_NAME, retval))
        return retval

    # +
    # hidden method: _construct_vertices()
    # -
    def _construct_vertices(self, child=None):

        # entry message
        vertices = None
        roi = []
        log.debug('{}._construct_vertices()> message on entry, child={}'.format(MODULE_NAME, str(child)))

        # get annotation type
        if child is not None:
            annotation_type = 'fg' if 'foreground' in child.values() else 'bg'

            # get vertices
            vertices = child.getchildren()[0].getchildren()
            for _vertex in vertices:
                _values = _vertex.values()
                roi.append({'x': int(float(_values[2])), 'y': int(float(_values[3]))})

            log.debug('{}._construct_vertices()> ROI: appending {} value with {}'.format(
                MODULE_NAME, annotation_type, str(roi)))
            self.rois[annotation_type].append(roi)

        # exit message
        log.debug('{}._construct_vertices()> message on exit, vertices={}, length={}, rois={}'.format(
            MODULE_NAME, str(vertices), len(vertices), str(self.rois)))

    # +
    # hidden method: _show_structure()
    # -
    def _show_structure(self, r_xml=None):

        # entry message
        log.debug('{}._show_structure()> message on entry, r_xml={}'.format(MODULE_NAME, str(r_xml)))

        if r_xml is not None:
            for _i, _child in enumerate(r_xml.getchildren()):
                log.debug('{}._show_structure()> index={}, child={}'.format(MODULE_NAME, _i, str(_child)))
                log.debug('{}._show_structure()> index={}, values={}'.format(MODULE_NAME, _i, str(_child.values())))
                if 'background' in _child.values() or 'foreground' in _child.values():
                    self._construct_vertices(_child)
                else:
                    self._show_structure(_child)

        # exit message
        log.debug('{}._show_structure()> message on exit'.format(MODULE_NAME))

    # +
    # method: setup()
    # -
    def setup(self):

        # entry message
        log.debug('{}.setup()> message on entry, options={}'.format(MODULE_NAME, self.options))

        # run locally
        if self.options.user and self.options.pwd and self.options.root:
            log.debug('{}.setup()> running locally with user={}, pwd={}, root={}'.format(
                MODULE_NAME, self.options.user, self.options.pwd, self.options.root))
            self.bqSession = BQSession().init_local(self.options.user, self.options.pwd, bisque_root=self.options.root)
            self.options.mexURL = self.bqSession.mex.uri

        # run on the server with a mexURL and an access token
        elif self.options.mexURL and self.options.token:
            log.debug('{}.setup()> running on server with mexURL={}, token={}'.format(
                MODULE_NAME, self.options.mexURL, self.options.token))
            self.bqSession = BQSession().init_mex(self.options.mexURL, self.options.token)

        # failed to connect to bisque
        else:
            self.bqSession = None
            self.message('{}.setup()> failed to connect to bisque'.format(MODULE_NAME))
            log.error(self.message)
            raise PlanteomeDeepSegmentError(self.message)

        # parse the xml and construct the tree, also set options to proper values after parsing it
        if self.bqSession is not None:
            self._mex_parameter_parser(self.bqSession.mex.xmltree)
            log.debug('{}.setup()> image URL={}, mexURL={}, stagingPath={}, token={}'.format(
                MODULE_NAME, self.options.image_url, self.options.mexURL, self.options.stagingPath, self.options.token))

        # exit message
        log.debug('{}.setup()> message on exit, options={}'.format(MODULE_NAME, self.options))

    # +
    # method: run()
    # The core of the PlanteomeDeepSegment module. It requests features on the provided image, classifies each tile
    # and selects a majority amongst the tiles.
    # -
    def run(self):

        # entry message
        log.debug('{}.run()> message on entry, options={}'.format(MODULE_NAME, self.options))

        self.rois = {'fg': [], 'bg': []}
        r_xml = self.bqSession.fetchxml(self.options.mexURL, view='deep')
        log.debug('{}.run()> Shols structura'.format(MODULE_NAME))
        self._show_structure(r_xml)
        log.debug(self.rois)

        # dump image as .tiff
        image = self.bqSession.load(self.options.image_url)
        ip = image.pixels().format('tiff')
        with open(self.tiff_file, 'wb') as f:
            f.write(ip.fetch())

        # pickle the data
        try:
            if self.rois and getattr(self.options, 'segmentImage') != '' and \
                    getattr(self.options, 'deepNetworkChoice') != '' and getattr(self.options, 'qualitySeg') != '' and \
                    getattr(self.options, 'deepSeg') != '' and getattr(self.options, 'mexURL') != '' and \
                    getattr(self.options, 'token') != '':
                log.debug('{}.run()> pickling data to {}'.format(MODULE_NAME, self.data_file))
                pickle.dump([self.rois, self.options.segmentImage, self.options.deepNetworkChoice,
                             self.options.qualitySeg, self.options.deepSeg, self.options.mexURL, self.options.token],
                            open(self.data_file, 'wb'))
        except AttributeError as e:
            self.message('{}.run()> failed to pickle data, e={}'.format(MODULE_NAME, str(e)))
            log.error(self.message)

        # do something
        x = PlanteomeDeepSegmentLearning(self.contours_file, self.data_file, self.tiff_file, self.results_file)
        x.main()

        # exit message
        log.debug('{}.run()> message on exit, options={}'.format(MODULE_NAME, self.options))

    # +
    # method: teardown()
    # -
    def teardown(self):

        # entry message
        log.debug('{}.teardown()> message on entry, options={}'.format(MODULE_NAME, self.options))

        # set up tag(s)
        self.bqSession.update_mex('Returning results...')
        output_tag = eTree.Element('tag', name='outputs')
        output_sub_tag_image = eTree.SubElement(output_tag, 'tag', name='Final Image', value=self.options.image_url)
        output_sub_tag_summary = eTree.SubElement(output_tag, 'tag', name='summary')

        log.info('Module will output image {}'.format(self.options.image_url))

        # segment the image (if required)
        if getattr(self.options, 'segmentImage', '') != '' and self.options.segmentImage.lower() == 'true' and \
                os.path.isfile(self.contours_file):
            log.debug('{}.teardown()> module will segment image from file {}'.format(MODULE_NAME, self.contours_file))

            eTree.SubElement(output_sub_tag_summary, 'tag', name='Segment Image', value=self.options.segmentImage)

            [_contours, _t_scale] = pickle.load(open(self.contours_file, 'rb'))
            _gob = eTree.SubElement(output_sub_tag_image, 'gobject', name='Annotations', type='Annotations')
            _polyseg = eTree.SubElement(_gob, 'polygon', name='SEG')
            eTree.SubElement(_polyseg, 'tag', name='color', value="#0000FF")
            _opd = 0
            _output_sampling = 1 + int(len(_contours)/100)
            for _j in range(len(_contours)):
                if _j % _output_sampling == 0:
                    _opd += 1
                    _x = str(1 + int(_t_scale[1]*_contours[_j][1]))
                    _y = str(1 + int(_t_scale[0]*_contours[_j][0]))
                    eTree.SubElement(_polyseg, 'vertex', x=_x, y=_y)
            log.debug('{}.teardown()> _opd={}'.format(MODULE_NAME, _opd))
        else:
            log.info('Module will not segment image, (were foreground and background polyline annotations provided?)')

        # select deepNetworkChoice
        opts = getattr(self.options, 'deepNetworkChoice', '')
        eTree.SubElement(output_sub_tag_summary, 'tag', name='Model File', value=opts)
        if opts == '':
            log.error('{}.teardown()> deepNetworkChoice={}'.format(MODULE_NAME, self.options.deepNetworkChoice))

        else:

            # simple classification
            if opts.split()[0].lower() == 'simple':

                # get prediction
                prediction_c = -1
                confidence_c = 0.0
                prediction_t = -1
                confidence_t = 0.0
                try:
                    with open(self.results_file, 'r') as f:
                        for _line in f:
                            if _line.strip() != '':
                                log.debug('{}.teardown()> _line={}'.format(MODULE_NAME, _line))
                                if 'PREDICTION_C:' in _line:
                                    prediction_c = int(_line.split(':')[1].strip())
                                if 'CONFIDENCE_C:' in _line:
                                    confidence_c = float(_line.split(':')[1].strip())
                                if 'PREDICTION_T:' in _line:
                                    prediction_t = int(_line.split(':')[1].strip())
                                if 'CONFIDENCE_T:' in _line:
                                    confidence_t = float(_line.split(':')[1].strip())
                except IOError as e:
                    self.message = '{}.teardown()> io error reading results, e={}'.format(MODULE_NAME, str(e))
                    log.error(self.message)
                finally:
                    log.debug('{}.teardown()> prediction_c={}'.format(MODULE_NAME, prediction_c))
                    log.debug('{}.teardown()> confidence_c={}'.format(MODULE_NAME, confidence_c))
                    log.debug('{}.teardown()> prediction_t={}'.format(MODULE_NAME, prediction_t))
                    log.debug('{}.teardown()> confidence_t={}'.format(MODULE_NAME, confidence_t))

                # annotate with prediction
                classes = [
                    'Leaf (PO:0025034): http://browser.planteome.org/amigo/term/PO:0025034',
                    'Fruit (PO:0009001): http://browser.planteome.org/amigo/term/PO:0009001',
                    'Flower (PO:0009046): http://browser.planteome.org/amigo/term/PO:0009046',
                    'Stem (PO:0009047): http://browser.planteome.org/amigo/term/PO:0009047',
                    'Whole plant (PO:0000003): http://browser.planteome.org/amigo/term/PO:0000003 '
                ]
                prediction_c = classes[prediction_c] if (0 <= prediction_c <= len(classes)) else 'unknown'

                eTree.SubElement(output_sub_tag_summary, 'tag', name='Class', value=prediction_c)
                if prediction_c.lower() != 'unknown':
                    eTree.SubElement(output_sub_tag_summary, 'tag', type='link', name='Class link',
                                     value=prediction_c.split('):')[-1].strip())
                eTree.SubElement(output_sub_tag_summary, 'tag', name='Class Confidence', value=str(confidence_c))

            # leaf classification
            elif opts.split()[0].lower() == 'leaf':

                log.debug('{}.teardown()> leaf_targets{}'.format(MODULE_NAME, leaf_targets))
                log.debug('{}.teardown()> leaf_targets_links{}'.format(MODULE_NAME, leaf_targets_links))

                # map each leaf target to the corresponding PO term
                with open(self.csv_leaf_file) as cf:
                    reader = csv.reader(cf, delimiter=',', quotechar='|')

                    _cn = ''
                    for _row in reader:
                        _n = _row[0] if _row[0] != '' else 'undefined'
                        _m = _row[1] if _row[1] != '' else 'undefined'
                        # _c = _row[2] if _row[2] != '' else 'undefined'
                        _t = _n.replace(' ', '').lower()

                        # get the current name
                        for _lc in leaf_keys_nospaces:
                            if _t == _lc:
                                _cn = leaf_keys_spaces[leaf_keys_nospaces.index(_lc)]
                                break

                        # replace dictionary entry is mapping exists
                        if _cn in leaf_targets:
                            for _l in leaf_targets[_cn]:
                                if _n == _l.replace(' ', ''):
                                    _i = leaf_targets[_cn].index(_l)
                                    leaf_targets_links[_cn][_i] = _m
                                    break

                # read result(s)
                with open(self.results_file, 'r') as f:
                    class_list = []
                    for _i, _line in enumerate(f):

                        # remove after introduction of the leaf classifier (below start with appends)
                        if int(_line) == len(leaf_targets[leaf_keys[_i]]) - 1:
                            _line = '0'
                        class_list.append(_line)

                        eTree.SubElement(output_sub_tag_summary, 'tag',
                                         name='{}-Name'.format(leaf_keys_proper_names[_i]),
                                         value=leaf_targets[leaf_keys[_i]][int(class_list[_i])])

                        if leaf_targets_links[leaf_keys[_i]][int(class_list[_i])] != 'undefined':
                            eTree.SubElement(
                                output_sub_tag_summary, 'tag', type='link',
                                name='{}-Accession'.format(leaf_keys_proper_names[_i]),
                                value='http://browser.planteome.org/amigo/term/{}'.format(
                                    leaf_targets_links[leaf_keys[_i]][int(class_list[_i])]))
                        else:
                            eTree.SubElement(
                                output_sub_tag_summary, 'tag',
                                name='{}-Accession'.format(leaf_keys_proper_names[_i]),
                                value=leaf_targets_links[leaf_keys[_i]][int(class_list[_i])])

        # update mex
        self.bqSession.finish_mex(tags=[output_tag])
        self.bqSession.close()

        # exit message
        log.debug('{}.teardown()> message on exit, options={}'.format(MODULE_NAME, self.options))

    # +
    # method: main()
    # -
    def main(self):

        # entry message
        log.debug('{}.main()> message on entry, args={}'.format(MODULE_NAME, sys.argv))

        parser = OptionParser()
        parser.add_option('--image_url', dest="image_url")
        parser.add_option('--mex_url', dest="mexURL")
        parser.add_option('--module_dir', dest="modulePath")
        parser.add_option('--staging_path', dest="stagingPath")
        parser.add_option('--bisque_token', dest="token")
        parser.add_option('--user', dest="user")
        parser.add_option('--pwd', dest="pwd")
        parser.add_option('--root', dest="root")
        (options, args) = parser.parse_args()

        log.debug('{}.main()> options={}'.format(MODULE_NAME, options))
        log.debug('{}.main()> args={}'.format(MODULE_NAME, args))

        # set up the mexURL and token based on the arguments passed to the script
        try:
            if not options.mexURL:
                options.mexURL = sys.argv[1]
            if not options.token:
                options.token = sys.argv[2]
            if not options.stagingPath:
                options.stagingPath = ''
        except IndexError:
            pass
        finally:
            self.options = options
            log.debug('{}.main()> self.options={}'.format(MODULE_NAME, self.options))

        # check input(s)
        if self._validate_input():

            # noinspection PyBroadException
            try:
                # set up the module
                self.setup()
            except PlanteomeDeepSegmentError as e:
                self.message = '{}.main()> specific exception after setup(), e={}'.format(MODULE_NAME, str(e.errstr))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except Exception as e:
                self.message = '{}.main()> exception after setup(), e={}'.format(MODULE_NAME, str(e))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except:
                self.message = '{}.main()> error after setup()'.format(MODULE_NAME)
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)

            # noinspection PyBroadException
            try:
                # run the module
                self.run()
            except PlanteomeDeepSegmentError as e:
                self.message = '{}.main()> specific exception after run(), e={}'.format(MODULE_NAME, str(e.errstr))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except Exception as e:
                self.message = '{}.main()> exception after run(), e={}'.format(MODULE_NAME, str(e))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except:
                self.message = '{}.main()> error after run()'.format(MODULE_NAME)
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)

            # noinspection PyBroadException
            try:
                # tear down the module
                self.teardown()
            except PlanteomeDeepSegmentError as e:
                self.message = '{}.main()> specific exception after teardown(), e={}'.format(MODULE_NAME, str(e.errstr))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except Exception as e:
                self.message = '{}.main()> exception after teardown(), e={}'.format(MODULE_NAME, str(e))
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)
            except:
                self.message = '{}.main()> error after teardown()'.format(MODULE_NAME)
                log.exception(self.message)
                self.bqSession.fail_mex(msg=self.message)
                raise PlanteomeDeepSegmentError(self.message)

        else:
            self.message = '{}.main()> failed to validate instance'.format(MODULE_NAME)
            log.error(self.message)
            self.bqSession.fail_mex(msg=self.message)
            raise PlanteomeDeepSegmentError(self.message)

        # exit message
        log.debug('{}.main()> message on exit, args={}'.format(MODULE_NAME, sys.argv))


# +
# main()
# -
if __name__ == "__main__":
    try:
        log.debug('{}.__main__()> starting ...'.format(MODULE_NAME))
        P = PlanteomeDeepSegment()
        P.main()
        log.debug('{}.__main__()> done'.format(MODULE_NAME))
    except PlanteomeDeepSegmentError as err:
        print('{}.__main__()> failed, error={}'.format(MODULE_NAME, err.errstr))
