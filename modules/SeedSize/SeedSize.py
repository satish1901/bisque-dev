#!/usr/bin/env python
import os
import sys
import optparse 
import subprocess
import glob
import csv
import pickle
import logging
import itertools

from bq.api import BQSession
from bq.api.util import fetch_dataset, fetch_image_pixels, d2xml



EXEC = "./seedSize"
IMAGE_MAP = "image_map.txt"

def gettag (el, tagname):
    for kid in el:
        if kid.get ('name') == tagname:
            return kid, kid.get('value')
    return None,None
            
class SeedSize(object):

    def setup(self):
        if not os.path.exists(self.images):
            os.makedirs(self.images)

        self.bq.update_mex('initializing')
        if self.is_dataset:
            results = fetch_dataset(self.bq, self.resource_url, self.images, True)
        else:
            results = fetch_image_pixels(self.bq, self.resource_url, self.images, True) 

        with open(self.image_map_name, 'wb') as f:
            pickle.dump(results, f)
        return 0
        

    def start(self):
        self.bq.update_mex('executing')
        # Matlab requires trailing slash
        r = subprocess.call([EXEC, 'images/'])
        return r

    def teardown(self):
        with  open(self.image_map_name, 'rb') as f:
            self.url2file = pickle.load(f) # 
            self.file2url =  dict((v,k) for k,v in self.url2file.iteritems())

        summary    = os.path.join(self.images, 'summary.csv')

        summary_tags = self._read_summary(summary)

        # Post all submex for files and return xml list of results
        tags = []
        gobjects = []
        if not self.is_dataset:
            localfiles = glob.glob(os.path.join(self.images, '*C.csv'))
            gobs = self._read_results(localfiles[0])
            gobjects = [ { 'name': 'SeedSize', 'gobject':gobs } ]
            #tags = [{ 'name':'image_url', 'value' : self.resource_url}]
            tags = summary_tags
        else:
            mexlist = self._post_submex()
            tags.extend(summary_tags)
            for i, submex in enumerate(mexlist):
                tag, image_url = gettag(submex, 'image_url')
                gob, gob_url = gettag(submex, 'SeedSize')

                mexlink = { 'name' : 'submex', 
                            'tag'  : [{ 'name':'mex_url', 'value':submex.get('uri')},
                                      { 'name':'image_url', 'value' : image_url},
                                      { 'name':'gobject_url', 'value' : gob.get('uri') } ]
                            }
                tags.append(mexlink)

        self.bq.finish_mex(tags = tags, gobjects = gobjects)
        return 0


    def _post_submex(self):
        submex = []

        localfiles = glob.glob(os.path.join(self.images, '*C.csv'))
        result2url = dict( (os.path.splitext(f)[0] + 'C.csv', u) for f, u in self.file2url.items())
        

        for result in localfiles:
            gobs = self._read_results(result)
            if result not in result2url:
                log.error ("Can't find url for %s given files %s and map %s" % 
                           result, localfile, result2url)
            mex = { 'type' : self.bq.mex.type,
                    'name' : self.bq.mex.name,
                    'value': 'FINISHED', 
                    'tag': [ {'name': 'image_url', 'value':  result2url [result]},
                             {'name': 'resource_url', 'value': self.config.resource_url }],
                    'gobject' : { 'name' : 'SeedSize', 'gobject' : gobs },
                    
                    }
            submex.append (mex)
        
        url = self.bq.service_url('data_service', 'mex', query={ 'view' : 'deep' })
        response = self.bq.postxml(url, d2xml({'request' : {'mex': submex}} ))

        return response
        

    def _read_summary(self, csvfile):
        #%mean(area), mean(minoraxislen), mean(majoraxislen), standarddev(area),
        #standarddev(minoraxislen), standarddev(majoraxislen), total seedcount,
        #mean thresholdused, weighted mean of percentclusters1, weighted mean of percentclusters2
        f= open(csvfile,'rb')
        rows = csv.reader (f)
        tag_names = [ 'mean_area', 'mean_minoraxis', 'mean_majoraxis',
                      'std_area', 'std_minoraxis', 'std_majoraxis',
                      'seedcount',
                      'mean_threshhold', 
                      'weighted_mean_cluster_1','weighted_mean_cluster_2',
                      ]

        # Read one row(rows.next()) and zip ( name, col) unpacking in d2xml format
        summary_tags = [ { 'name': n[0], 'value' : n[1] } 
                         for n in itertools.izip(tag_names, rows.next()) ] 
        f.close()
        
        return  [ {'name':'summary', 'tag':summary_tags } ]

    def _read_results(self, csvfile):
        results  = []
        f= open(csvfile,'rb')
        rows = csv.reader (f)
        for col in rows:
            results.append( {
                    'type' : 'seed',
                    'tag' : [ { 'name': 'area', 'value': col[0]},
                              { 'name': 'major', 'value': col[2]},
                              { 'name': 'minor', 'value': col[1]} ],
                    'ellipse' : { 
                        'vertex' : [ { 'x': col[3], 'y':col[4], 'index':0 },
                                     { 'x': col[8], 'y':col[9], 'index':1 },
                                     { 'x': col[6], 'y':col[7], 'index':2 }]
                        }
                    })
        f.close()
        return results



    def run(self):
        parser  = optparse.OptionParser()
        parser.add_option('-d','--debug', action="store_true")
        parser.add_option('-n','--dryrun', action="store_true")
        parser.add_option('--resource_url')
        parser.add_option('--mex_url')
        parser.add_option('--staging_path')
        parser.add_option('--auth_token')
        parser.add_option('--credentials')

        (options, args) = parser.parse_args()


        if options.auth_token:
            self.bq = BQSession().init_mex(options.mex_url, options.auth_token)
        else:
            user,pwd = options.credentials.split(':')
            self.bq = BQSession().init_local(user,pwd)

        if len(args) != 1 or options.resource_url is None:
            parser.error('Need a command and resource_url')

        command = args.pop(0)

        if command not in ('setup','teardown', 'start'):
            parser.error('Command must be start, setup or teardown')

        logging.basicConfig(level=logging.DEBUG)

        # maltab code requires trailing slash..
        self.images = os.path.join(options.staging_path, 'images') + os.sep
        self.image_map_name = os.path.join(options.staging_path, IMAGE_MAP)
        self.resource_url = options.resource_url
        self.config = options
        self.is_dataset = 'dataset' in self.resource_url



            
        command = getattr(self, command)
        try:
            r = command()
        except:
            logging.exception ("problem during %s" % command)
            sys.exit(1)
        
        sys.exit(r)



if __name__ == "__main__":
    SeedSize().run()
    
