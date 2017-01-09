import sys
import traceback
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
logging.basicConfig(filename='AnnotationHistograms.log', level=logging.DEBUG)
log = logging.getLogger('AnnotationHistograms')


ignore_tags = set(['filename', 'upload_datetime'])


def make_directory(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def compute_unique_names(image, unique_tags):
    # get unique tag names
    tags = image.xpath('tag')
    for t in tags:
        unique_tags.add(t.get('name'))

def compute_unique_gob_types(image, unique_gobs):
    # get unique gob names
    gobs = image.xpath('gobject')
    for g in gobs:
        unique_gobs.add(g.get('type'))

def fetch_unique_tag_names(session):
    unique_gobs = set()
    url = '/data_service/image/?tag_names=true&wpublic=false'
    q = session.fetchxml (url)

    # get unique gob types
    gobs = q.xpath('tag')
    for g in gobs:
        unique_gobs.add(g.get('name'))
    return unique_gobs

def fetch_unique_gob_types(session):
    unique_gobs = set()
    url = '/data_service/image/?gob_types=true&wpublic=false'
    q = session.fetchxml (url)

    # get unique gob types
    gobs = q.xpath('gobject')
    for g in gobs:
        c = g.get('type', '').replace('Primary - ', '').replace('Secondary - ', '')
        unique_gobs.add(c)
    return unique_gobs

def find_matches(image, preferred='secondary'):
    gobs = image.xpath('//gobject')
    if len(gobs)<1:
        return []

    uuid = image.get('resource_uniq')
    filename = image.get('name')
    uri = image.get('uri')

    points = []
    for g in gobs:
        try:
            t = g.get('type')
            v = g.xpath('point/vertex')[0]
            x = float(v.get('x'))
            y = float(v.get('y'))
            points.append({'g': g, 'coord': (x,y), 'type': t})
        except IndexError:
            print 'IndexError in %s'%g
            pass
    points = sorted(points, key=itemgetter('coord'))

    delta = 150
    filtered = []
    surveyed = []
    i = 0
    for p in reversed(points):
        i=i+1
        matched = [p]
        points.remove(p)
        if p in surveyed:
            continue

        x1,y1 = p['coord']
        points2 = points
        for pp in reversed(points2):
            x2,y2 = pp['coord']
            if abs(x1-x2)<delta and abs(y1-y2)<delta:
                matched.append(pp)
                surveyed.append(pp)

        selected = None
        if len(matched) == 1:
            selected = p
        else:
            for pp in matched:
                if pp['type'].lower().startswith(preferred):
                    selected = pp
                    break

        if selected is None:
            selected = matched[0]
            print 'In %s (%s) could not select from matched points'%(filename, uri)
            for m in matched:
                print 'matched: %s, %s'%(m['type'], m['coord'])
            print 'Selected: %s, %s'%(selected['type'], selected['coord'])

        filtered.append(selected)


    filtered = list(reversed(filtered))

    if len(filtered)!=100 and len(filtered) != len(gobs):
        print '%s (%s) found %s preferred of %s'%(filename, uri, len(filtered), len(gobs))
    elif len(gobs)<100:
        print '%s (%s) has only %s annotations'%(filename, uri, len(gobs))
    return filtered

def compute_histogram(dataset, image, matches, unique_tags, unique_gobs):
    row = [dataset.get('name'), image.get('name')]

    # get unique tag names
    for t in unique_tags:
        tags = image.xpath('tag[@name="%s"]'%t)
        if len(tags)>0:
            row.append(tags[0].get('value', ''))
        else:
            row.append('')

    # get gob histogram
    h = {}
    for m in matches:
        c = m['type'].replace('Primary - ', '').replace('Secondary - ', '')
        try:
            h[c] = h[c] + 1
        except KeyError:
            h[c] = 1

    for t in unique_gobs:
        try:
            row.append('%s'%h[t])
        except KeyError:
            row.append('0')

    return row



class AnnotationHistograms(object):
    """Example Python module
    Read tags from image server and store tags on image directly
    """
    def main(self, mex_url=None, bisque_token=None, bq=None):
        #  Allow for testing by passing an alreay initialized session
        if bq is None:
            bq = BQSession().init_mex(mex_url, bisque_token)
        bq.update_mex('Starting')
        image_url = bq.parameter_value(name='dataset_url')

        use_full_path = bq.parameter_value(name='use_full_path')

        mex_id = mex_url.split('/')[-1]
        dt = datetime.now().strftime('%Y%m%dT%H%M%S')
        if image_url is None or len(image_url)<2:
            datasets = bq.fetchxml ('/data_service/dataset')
            datasets = [d.get('uri') for d in datasets.xpath('dataset')]
        else:
            datasets = [image_url]

        # compute tag and gobject types
        unique_tags = fetch_unique_tag_names(bq)
        unique_gobs = fetch_unique_gob_types(bq)

        unique_tags = unique_tags - ignore_tags
        unique_tags = sorted(unique_tags)
        unique_gobs = sorted(unique_gobs)

        header = ['dataset', 'filename']
        header.extend(unique_tags)
        header.extend(unique_gobs)

        csv_filename = 'histograms_one_layer_%s_%s.csv'%(dt, mex_id)
        with open(csv_filename, 'wb') as csvfile:
            w = csv.writer(csvfile, delimiter=',')
            w.writerow(header)

            # compute histograms per dataset
            for ds_url in datasets:
                dataset = bq.fetchxml (ds_url, view='deep')
                dataset_name = dataset.get('name')
                bq.update_mex('processing "%s"'%dataset_name)

                refs = dataset.xpath('value[@type="object"]')
                for r in refs:
                    image = bq.fetchxml (r.text, view='deep')
                    matches = find_matches(image, preferred='secondary')
                    if len(matches)<1:
                        continue
                    row = compute_histogram(dataset, image, matches, unique_tags, unique_gobs)
                    w.writerow(row)

        # need to save the CSV file and write its reference
        resource = etree.Element('resource', type='table', name='ModuleExecutions/AnnotationHistograms/%s'%(csv_filename) )
        blob = etree.XML(bq.postblob(csv_filename, xml=resource))
        print etree.tostring(blob)
        blob = blob.find('./')
        print blob
        if blob is None or blob.get('uri') is None:
            bq.fail_mex('Could not insert the Histogram file into the system')
        else:
            bq.finish_mex(tags = [{ 'name': 'outputs',
                                    'tag' : [{ 'name': 'histogram',
                                               'value': blob.get('uri'),
                                               'type' : 'table' }]}])

if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-c", "--credentials", dest="credentials",
                      help="credentials are in the form user:password")
    #parser.add_option('--mex_url')
    #parser.add_option('--auth_token')

    (options, args) = parser.parse_args()

    M = AnnotationHistograms()
    if options.credentials is None:
        mex_url, auth_token = args[:2]
        bq = BQSession().init_mex(mex_url, auth_token)
    else:
        mex_url = ''
        if not options.credentials:
            parser.error('need credentials')
        user,pwd = options.credentials.split(':')
        bq = BQSession().init_local(user, pwd)

    try:
        M.main(mex_url=mex_url, bq=bq )
    except Exception, e:
        bq.fail_mex(traceback.format_exc())
    sys.exit(0)
