import sys
import collections
try:
    from lxml import etree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from bqapi import BQSession, BQTag
import logging



logging.basicConfig(filename='MetaData.log',level=logging.DEBUG)

wanted_tags = [
    'data_time',
    'pixel_resolution_x',
    'pixel_resolution_unit_x',
    'pixel_resolution_y',
    'pixel_resolution_unit_y',
    'pixel_resolution_z',
    'pixel_resolution_unit_z',
    'pixel_resolution_t',
    'pixel_resolution_unit_t',
    'image_num_x',
    'image_num_y',
    'image_num_z',
    'image_num_t',
    'image_num_c',
    'image_num_p',
    'image_pixel_depth',
    ]

class MetaData(object):
    """Example Python module
    Read tags from image server and store tags on image directly
    """
    def main(self, image_url,  mex_url = None, bisque_token=None, bq = None):
        #  Allow for testing by passing an alreay initialized session
        if bq is None:
            bq = BQSession().init_mex(mex_url, bisque_token)
        
        # ---------- EXAMPLE OF HOW TO CHECK FOR LIST PARAMETERS ----------
        params = bq.get_mex_inputs()
        image_iter = params.get('image_url', [])
        if isinstance(image_iter, collections.Iterable) and not isinstance(image_iter, dict):
            image_iter = list(image_iter)
        else:
            image_iter = [image_iter]
        # ------------------------------------------------------------------

        for image_url in image_iter:
            metadata_tag = self._process_single_img(bq, image_url.get('value'))        
            if metadata_tag is None:
                bq.fail_mex ("could not write tag: no write access")
                return

        bq.finish_mex(tags = [{ 'name': 'outputs',
                                'tag' : [{ 'name': 'metadata',
                                           'value': metadata_tag.uri,
                                           'type' : 'tag' }]}])
        sys.exit(0)
        #bq.close()
        
    def _process_single_img(self, bq, image_url):
        # Fetch the image metadata
        image = bq.load(image_url)

        # Fetch embedded tags from image service
        meta = image.pixels().meta().fetch()
        meta = ET.XML(meta)
        tags = []
        # Create a new tag 'MetaData' to be placed on the image
        md = BQTag(name='MetaData')
        # Filter the embedded metadata and place subtags in MetaData
        for t in meta.getiterator('tag'):
            if t.get('name') in wanted_tags:
                md.addTag (name=t.get('name'),
                           value=t.get('value'))
        # Add the new tag to the image
        image.addTag(tag = md)
        metadata_tag = bq.save(md, image.uri + "/tag")
        return metadata_tag



if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-c", "--credentials", dest="credentials",
                      help="credentials are in the form user:password")
    #parser.add_option('--image_url')
    #parser.add_option('--mex_url')
    #parser.add_option('--auth_token')

    (options, args) = parser.parse_args()

    M = MetaData()
    if options.credentials is None:
        image_url, mex_url,  auth_token  = args[:3]
        M.main(image_url, mex_url, auth_token)
    else:
        image_url = args.pop(0)

        if not options.credentials:
            parser.error('need credentials')
        user,pwd = options.credentials.split(':')

        bq = BQSession().init_local(user, pwd)
        M.main(image_url, bq=bq)



