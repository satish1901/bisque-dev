import sys
from operator import itemgetter
import itertools
from datetime import datetime
import traceback
try:
    from lxml import etree as etree
except ImportError:
    import xml.etree.ElementTree as etree

from bqapi import BQSession, BQTag, BQCommError

import logging
logging.basicConfig(filename='Connoisseur.log',level=logging.DEBUG)

import os
import posixpath
from datetime import datetime
BQ_SERVER_PATH = 'ModuleExecutions/Connoisseur/%s'%(datetime.now().strftime('%Y%m%dT%H%M%S'))

def upload_file(bq, path, _type='image', _server_path=None, hidden=True):
    server_path = posixpath.join(_server_path or BQ_SERVER_PATH, os.path.basename(path))
    resource = etree.Element(_type, name=server_path, type=_type )
    if hidden is True:
        resource.set('hidden', 'true')
    blob = etree.XML(bq.postblob(path, xml=resource))
    blob = blob.find('./')
    if blob is not None:
        return blob.get('uri')


class Connoisseur(object):
    """Example Python module
    Read tags from image server and store tags on image directly
    """
    def main(self, mex_url=None, bisque_token=None, image_url=None, bq=None):
        #  Allow for testing by passing an alreay initialized session
        if bq is None:
            bq = BQSession().init_mex(mex_url, bisque_token)

        bq.update_mex('Classifying...')
        pars = bq.parameters()
        image_url = pars.get('data_url', None)
        model_url = pars.get('model_url', None)
        store_on_image = pars.get('store_on_image', False)
        method = pars.get('method', 'points')

        points = int(pars.get('number_of_points', 10))
        confidence = int(pars.get('confidence', 95))
        border = int(pars.get('border', 0))

        _,image_uniq = image_url.rsplit('/', 1)
        _,model_uniq = model_url.rsplit('/', 1)
        url = '%s/connoisseur/%s/classify:%s/method:%s/points:%s/confidence:%s/border:%s'%(bq.bisque_root, model_uniq, image_uniq, method, points, confidence, border)

        # dima: the moving of the image is not of the best taste, this should be changed later
        if method != 'segmentation':
            url += '/format:xml'
            txt = bq.c.fetch(url, headers = {'Content-Type':'text/xml', 'Accept':'text/xml'})
            gobs = etree.fromstring(txt)
        else:
            color_mode = 'colors'
            url += '/colors:colors'
            filename = '%s_%s_conf%.2f_n%s_b%s.png'%(image_uniq, color_mode, confidence, points, border)
            filename = bq.c.fetch(url, path=filename)
            image_url = upload_file(bq, filename) or ''
            gobs = None

        bq.update_mex('Storing results...')
        outputs = etree.Element('tag', name="outputs")
        img = etree.SubElement(outputs, 'tag', name="MyImage", type="image", value=image_url)
        if gobs is not None:
            img.append(gobs)
        if store_on_image is True:
            r = bq.postxml(image_url, xml=txt)

        bq.finish_mex(tags=[outputs])

if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-c", "--credentials", dest="credentials",
                      help="credentials are in the form user:password")
    #parser.add_option('--image_url')
    #parser.add_option('--mex_url')
    #parser.add_option('--auth_token')

    (options, args) = parser.parse_args()

    M = Connoisseur()
    if options.credentials is None:
        mex_url, auth_token, image_url = args[:3]
        bq = BQSession().init_mex(mex_url, auth_token)
    else:
        mex_url = ''
        image_url = args.pop(0)
        if not options.credentials:
            parser.error('need credentials')
        user,pwd = options.credentials.split(':')
        bq = BQSession().init_local(user, pwd)

    try:
        M.main(mex_url=mex_url, image_url=image_url, bq=bq )
    except Exception, e:
        bq.fail_mex(traceback.format_exc())
    sys.exit(0)

