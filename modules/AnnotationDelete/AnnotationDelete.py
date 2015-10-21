import sys
import csv
from operator import itemgetter
import itertools
from datetime import datetime

try:
    from lxml import etree as etree
except ImportError:
    import xml.etree.ElementTree as etree

from bqapi import BQSession, BQTag, BQCommError

import logging
logging.basicConfig(filename='AnnotationDelete.log', level=logging.DEBUG)
log = logging.getLogger('AnnotationDelete')

def delete(image, text_old, ann_type='gobject', ann_attr='type'):
    modified = []
    gobs = image.xpath('//%s[@%s="%s"]'%(ann_type, ann_attr, text_old))
    for g in gobs:
        if g.get(ann_attr) == text_old:
            image.remove(g)
            modified.append({'g': g})
    return modified

class AnnotationDelete(object):
    """Example Python module
    Read tags from image server and store tags on image directly
    """
    def main(self, mex_url=None, bisque_token=None, image_url=None, bq=None):
        #  Allow for testing by passing an alreay initialized session
        if bq is None:
            bq = BQSession().init_mex(mex_url, bisque_token)
        pars = bq.parameters()
        image_url            = pars['dataset_url']
        annotation_type      = pars['annotation_type']
        annotation_attribute = pars['annotation_attribute']
        value_old            = pars['value_old']

        bq.update_mex('Starting')
        mex_id = mex_url.split('/')[-1]
        if image_url is None or len(image_url)<2:
            datasets = bq.fetchxml ('/data_service/dataset')
            datasets = [d.get('uri') for d in datasets.xpath('dataset')]
        else:
            datasets = [image_url]
        total = 0
        changes = []

        # delete annotations for each element in the dataset
        for ds_url in datasets:
            dataset = bq.fetchxml (ds_url, view='deep')
            dataset_name = dataset.get('name')
            bq.update_mex('processing "%s"'%dataset_name)

            refs = dataset.xpath('value[@type="object"]')
            for r in refs:
                url = r.text
                image = bq.fetchxml (url, view='deep')
                uuid = image.get('resource_uniq')
                modified = delete(image, value_old, ann_type=annotation_type, ann_attr=annotation_attribute)
                if len(modified)>0:
                    bq.postxml(url, image, method='PUT')
                    total = total + len(modified)
                    changes.append({
                        'name': '%s (%s)'%(image.get('name'), image.get('resource_uniq')),
                        'value': '%s'%len(modified)
                    })

        changes.insert(0, {
            'name': 'Total',
            'value': '%s'%total
        })
        bq.finish_mex(tags = [{
            'name': 'outputs',
            'tag' : [{
                'name': 'deleted',
                'tag' : changes,
            }]
        }])
        sys.exit(0)
        #bq.close()


if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-c", "--credentials", dest="credentials",
                      help="credentials are in the form user:password")
    #parser.add_option('--image_url')
    #parser.add_option('--mex_url')
    #parser.add_option('--auth_token')

    (options, args) = parser.parse_args()

    M = AnnotationDelete()
    if options.credentials is None:
        mex_url, auth_token, image_url = args[:3]
        M.main(mex_url, auth_token, image_url)
    else:
        image_url = args.pop(0)

        if not options.credentials:
            parser.error('need credentials')
        user,pwd = options.credentials.split(':')

        bq = BQSession().init_local(user, pwd)
        M.main(image_url, bq=bq)


