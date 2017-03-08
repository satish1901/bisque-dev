#################################################
###     CellProfiler Module for Bisque        ###
#################################################
import os
import re
import sys
import math
import csv
import time
import urllib
import logging
import itertools
import subprocess
import json
from datetime import datetime

from lxml import etree
from optparse import OptionParser
#from bqapi import BQGObject, BQEllipse, BQVertex
from bqapi.util import fetch_image_pixels, save_image_pixels


#constants
DATA_SERVICE                    = 'data_service'


#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='CPfile.log',filemode='a',level=logging.DEBUG)
log = logging.getLogger('bq.modules')


from bqapi.comm import BQSession
#from bq.util.mkdir import _mkdir


# replace "@..." placeholders in pipeline based on provided params dict
def _replace_placeholders(pipeline, params):
    # TODO: improve this by adding transformation step from universal pipeline representation -> CellProfiler pipeline
    pipeline_res = ''
    for line in pipeline.splitlines():
        indent = len(line) - len(line.lstrip())
        toks = line.strip().split(':')
        if len(toks) > 1:
            tag = toks[0]
            val = ':'.join(toks[1:])
            try:
                if val.startswith('@NUMPARAM'):
                    val = float(params[tag])
                elif val.startswith('@STRPARAM'):
                    val = str(params[tag])                
            except KeyError:
                raise CPError("pipeline parameter '%s' not provided" % tag)
            pipeline_res += "%s%s:%s\n" % (' '*indent, tag, val)
        else:
            pipeline_res += line + '\n'
    return pipeline_res


class CPError(Exception):

    def __init__(self, message):
        self.message = "CellProfiler error: %s" % message
    def __str__(self):
        return self.message        
        
 
        

class CellProfiler(object):
    """
        CellProfiler Module
    """

    def mex_parameter_parser(self, mex_xml):
        """
            Parses input of the xml and add it to CellProfiler's options attribute (unless already set)

            @param: mex_xml
        """
        # inputs are all non-"pipeline params" under "inputs" and all params under "pipeline_params"
        mex_inputs = mex_xml.xpath('tag[@name="inputs"]/tag[@name!="pipeline_params"] | tag[@name="inputs"]/tag[@name="pipeline_params"]/tag')
        if mex_inputs:
            for tag in mex_inputs:
                if tag.tag == 'tag' and tag.get('type', '') != 'system-input': #skip system input values
                    if not getattr(self.options,tag.get('name', ''), None):
                        log.debug('Set options with %s as %s'%(tag.get('name',''),tag.get('value','')))
                        setattr(self.options,tag.get('name',''),tag.get('value',''))
        else:
            log.debug('CellProfiler: No Inputs Found on MEX!')


    def validate_input(self):
        """
            Check to see if a mex with token or user with password was provided.

            @return True is returned if validation credention was provided else
            False is returned
        """
        if (self.options.mexURL and self.options.token): #run module through engine service
            return True

        if (self.options.user and self.options.pwd and self.options.root): #run module locally (note: to test module)
            return True

        log.debug('CellProfiler: Insufficient options or arguments to start this module')
        return False


    def setup(self):
        """
            Fetches the mex and appends input_configurations to the option
            attribute of CellProfiler
        """
        self.bqSession.update_mex('Initializing...')
        self.mex_parameter_parser(self.bqSession.mex.xmltree)
        self.output_file = None


    def run(self):
        """
            The core of the CellProfiler runner
        """

        #retrieve tags
        self.bqSession.update_mex('Extracting properties')

        #type check
        image_resource = self.bqSession.fetchxml(self.options.InputFile)
        if image_resource.tag != 'image':
            raise CPError("trying to run CellProfiler on non-image resource")

        image_uri = image_resource.get('uri')
        image_file = fetch_image_pixels(self.bqSession, image_uri, self.options.stagingPath)[image_uri]
        filelist_file = os.path.join(self.options.stagingPath, 'filelist.txt')
        with open(filelist_file, 'w') as fo:
            fo.write(image_file+'\n')
        
        # create pipeline with correct parameters
        pipeline_params = self.bqSession.mex.xmltree.xpath('tag[@name="inputs"]/tag[@name="pipeline_params"]/tag')
        params = {}
        for tag in pipeline_params:
            params[tag.get('name','')] = getattr(self.options, tag.get('name',''))
        pipeline_file, err_file = self._instantiate_pipeline(pipeline_url=self.options.pipeline_url, params=params)

        # run CellProfiler on the pipeline
        self.bqSession.update_mex('Running CellProfiler')
        log.debug('run CellProfiler on %s', pipeline_file)
        res = 1
        with open(err_file, 'w') as fo:
            res = subprocess.call(['python',
                                   '/module/CellProfiler/CellProfiler.py',
                                   '-c',
                                   '-r',
                                   '-i', self.options.stagingPath,
                                   '-o', self.options.stagingPath,
                                   '-p', pipeline_file,
                                   '--file-list', filelist_file],
                                  stderr=fo, stdout=fo)
            log.debug("CellProfiler returned: %s", str(res))

        if res > 0:
            err_msg = 'pipeline execution failed\n'
            with open(err_file, 'r') as fo:
                err_msg += ''.join(fo.readlines())
            if len(err_msg) > 1024:
                err_msg = err_msg[:512] + '...' + err_msg[-512:]
            raise CPError(err_msg)
        
        self.output_file = os.path.join(self.options.stagingPath, 'Objects.csv')   #!!! TODO: extract from pipeline

    def _instantiate_pipeline(self, pipeline_url, params):
        """instantiate cellprofiler pipeline file with provided parameters"""
        pipeline_resource = self.bqSession.fetchxml(pipeline_url, view='short')
        out_pipeline_file = os.path.join(self.options.stagingPath, 'pipeline.cp')
        out_error_file = os.path.join(self.options.stagingPath, 'cp_error.txt')
        pipeline_url = self.bqSession.service_url('blob_service', path=pipeline_resource.get('resource_uniq'))
        self.bqSession.fetchblob(pipeline_url, path=os.path.join(self.options.stagingPath, 'pipeline_uninit.cp'))
        pipeline_file = os.path.join(self.options.stagingPath, 'pipeline_uninit.cp')
        with open(pipeline_file, 'r') as fi:
            pipeline = fi.read()
            # pipeline = json.load(fi)
            # replace all placeholders in pipeline template
            pipeline = _replace_placeholders(pipeline, params)
            # write out pipeline to provided file
            with open(out_pipeline_file, 'w') as fo:
                fo.write(pipeline)
                # json.dump(pipeline, fo)
        return out_pipeline_file, out_error_file


    def teardown(self):
        """
            Post the results to the mex xml.
        """
        #save the image output and upload it with all the meta data
        self.bqSession.update_mex( 'Returning results')
        log.debug('Storing image output')

        #constructing and storing image file
        mex_id = self.bqSession.mex.uri.split('/')[-1]
        dt = datetime.now().strftime('%Y%m%dT%H%M%S')
        final_output_file = "ModuleExecutions/CellProfiler/%s_%s_%s"%(self.options.OutputPrefix, dt, mex_id)

        #does not accept no name on the resource
        cl_model = etree.Element('resource', resource_type='table', name=final_output_file)

        #module identifier (a descriptor to be found by the CellProfiler model)
        etree.SubElement(cl_model, 'tag', name='module_identifier', value='CellProfiler')

        #hdf filename
        etree.SubElement(cl_model, 'tag', name='OutputFile', value=final_output_file)

        #pipeline param
        #etree.SubElement(cl_model, 'tag', name='RefFrameZDir', value=self.options.RefFrameZDir)

        #input hdf url
        #etree.SubElement(cl_model, 'tag', name='InputFile', type='link', value=self.options.InputFile)

        #input pipeline
        #etree.SubElement(cl_model, 'tag', name='pipeline_url', type='link', value=self.options.pipeline_url)

        #description
        etree.SubElement(cl_model, 'tag', name='description', value = 'output from CellProfiler Module')

        #storing the table in blobservice
        log.debug('before postblob')   #!!!
        r = self.bqSession.postblob(self.output_file, xml = cl_model)
        r_xml = etree.fromstring(r)

        outputTag = etree.Element('tag', name ='outputs')
        etree.SubElement(outputTag, 'tag', name='output_table', type='table', value=r_xml[0].get('uri',''))

        # Read object measurements from csv and write to gobjects
        (header, records) = self._readCSV(os.path.join(self.output_file))
 
        if header is not None:
            # create a new parent tag 'CellProfiler' to be placed on the mex
            image_resource = self.bqSession.fetchxml(self.options.InputFile)
            image_elem = etree.SubElement(outputTag, 'tag', type='image', name=image_resource.get('name'), value=image_resource.get('uri'))
            parentGObject = etree.SubElement(image_elem, 'gobject', type='detected shapes', name='detected shapes')
            for i in range(len(records)):
                shape = self._get_ellipse_elem(name=str(i), header=header, record=records[i])
                parentGObject.append(shape)

        self.bqSession.finish_mex(tags=[outputTag])

    def _get_ellipse_elem(self, name, **params): 
        header = params.get('header')
        record = params.get('record')
        getValue = lambda x: float(record[header.index(x)])

        shape = etree.Element('gobject', name=name, type='detected shape')
        res = etree.SubElement(shape, 'ellipse')

        # centroid
        x = getValue('AreaShape_Center_X')
        y = getValue('AreaShape_Center_Y')
        theta = math.radians(getValue('AreaShape_Orientation'))

        etree.SubElement(res, 'vertex', x=str(x), y=str(y))
 
        # major axis/minor axis endpoint coordinates
        a = 0.5 * getValue('AreaShape_MajorAxisLength')
        b = 0.5 * getValue('AreaShape_MinorAxisLength')
 
        bX = round(x - b*math.sin(theta))
        bY = round(y + b*math.cos(theta))
        etree.SubElement(res, 'vertex', x=str(bX), y=str(bY))
 
        aX = round(x + a*math.cos(theta))
        aY = round(y + a*math.sin(theta))        
        etree.SubElement(res, 'vertex', x=str(aX), y=str(aY))
        
        # area of ellipse as tag        
        etree.SubElement(res, 'tag', name="Compactness", value=str(getValue('AreaShape_Compactness')))
        etree.SubElement(res, 'tag', name="Eccentricity", value=str(getValue('AreaShape_Eccentricity')))
        etree.SubElement(res, 'tag', name="FormFactor", value=str(getValue('AreaShape_FormFactor')))
        etree.SubElement(res, 'tag', name="Solidity", value=str(getValue('AreaShape_Solidity')))
        return shape
        
    def _readCSV(self, fileName):
 
        if os.path.exists(fileName) == False:
            return (None, None)
 
        records = []
        handle = open(fileName, 'rb')
        csvHandle = csv.reader(handle)
        header = csvHandle.next()
 
        for row in csvHandle:
            records.append(row)
 
        handle.close()
        return (header, records)


    def main(self):
        """
            The main function that runs everything
        """
        log.info('sysargv : %s' % sys.argv )
        parser = OptionParser()

        parser.add_option('--mex_url'         , dest="mexURL")
        parser.add_option('--module_dir'      , dest="modulePath")
        parser.add_option('--staging_path'    , dest="stagingPath")
        parser.add_option('--bisque_token'    , dest="token")
        parser.add_option('--user'            , dest="user")
        parser.add_option('--pwd'             , dest="pwd")
        parser.add_option('--root'            , dest="root")
        parser.add_option('--entrypoint'      , dest="entrypoint")

        (options, args) = parser.parse_args()

        fh = logging.FileHandler('phase_%s.log' % (options.entrypoint or 'main'), mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)8s --- %(message)s ' +
                                  '(%(filename)s:%(lineno)s)',datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        log.addHandler(fh)

        try: #pull out the mex

            if not options.mexURL:
                options.mexURL = sys.argv[1]
            if not options.token:
                options.token = sys.argv[2]

        except IndexError: #no argv were set
            pass

        if not options.stagingPath:
            options.stagingPath = '/module/CellProfiler/workdir'

        log.info('\n\nPARAMS : %s \n\n Options: %s' % (args, options))
        self.options = options

        if self.validate_input():

            #initalizes if user and password are provided
            if (self.options.user and self.options.pwd and self.options.root):
                self.bqSession = BQSession().init_local( self.options.user, self.options.pwd, bisque_root=self.options.root)
                self.options.mexURL = self.bqSession.mex.uri

            #initalizes if mex and mex token is provided
            elif (self.options.mexURL and self.options.token):
                self.bqSession = BQSession().init_mex(self.options.mexURL, self.options.token)

            else:
                raise CPError('Insufficient options or arguments to start this module')

            if not self.options.entrypoint:
                # NOT a special phase => perform regular run processing
                try:
                    self.setup()
                except Exception as e:
                    log.exception("Exception during setup")
                    self.bqSession.fail_mex(msg = "Exception during setup: %s" %  str(e))
                    return

                try:
                    self.run()
                except (Exception, CPError) as e:
                    log.exception("Exception during run")
                    self.bqSession.fail_mex(msg = "Exception during run: %s" % str(e))
                    return

                try:
                    self.teardown()
                except (Exception, CPError) as e:
                    log.exception("Exception during teardown")
                    self.bqSession.fail_mex(msg = "Exception during teardown: %s" %  str(e))
                    return

            else:
                # in a special phase => run special code                
                self.bqSession.fail_mex(msg = "Unknown CellProfiler entrypoint: %s" %  self.options.entrypoint)
                return

            self.bqSession.close()

if __name__=="__main__":
    CellProfiler().main()




















# import os
# import logging
# import csv
# import time
# import sys
# import math
# import subprocess
# 
# from lxml import etree
# from shutil import copy2
# from glob import glob
# from optparse import OptionParser
# from bqapi import BQSession, BQTag, BQGObject, BQEllipse, BQVertex
# from bqapi.util import fetch_image_pixels, fetch_dataset, save_image_pixels
# 
# 
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('bq.modules')
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
# class CPShape(BQGObject):
# 
#     def __init__(self, name=None, value=None,  **params):
#         BQGObject.__init__(self)
# 
#         self.name = name
#         self.values = value and [value] or []
#         self.tags =  []
#         self.type='CPShape'
#         self.gobjects = []
# 
#     def addEllipse(self, **params):
# 
#         header = params.get('header')
#         record = params.get('record')
#         getValue = lambda x: float(record[header.index(x)])
# 
#         ellipse = BQEllipse()
#         self.addGObject(gob=ellipse)
# 
#         # centroid
#         x = getValue('AreaShape_Center_X')
#         y = getValue('AreaShape_Center_Y')
#         theta = math.radians(-1*getValue('AreaShape_Orientation'))
# 
#         vCentroid = BQVertex(x=x, y=y)
#         ellipse.addGObject(gob=vCentroid)
# 
#         # major axis/minor axis endpoint coordinates
#         a = 0.5 * getValue('AreaShape_MajorAxisLength')
#         b = 0.5 * getValue('AreaShape_MinorAxisLength')
# 
#         bX = round(x - b*math.sin(theta))
#         bY = round(y + b*math.cos(theta))
#         vMinor = BQVertex(x=bX, y=bY)
#         ellipse.addGObject(gob=vMinor)
# 
#         aX = round(x + a*math.cos(theta))
#         aY = round(y + a*math.sin(theta))
#         vMajor = BQVertex(x=aX, y=aY)
#         ellipse.addGObject(gob=vMajor)
# 
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
# 
# class CellProfiler(object):
# 
#     def validateInput(self, parser, args):
# 
#         logger.debug('\nCellProfiler - resourceURL: %s, mexURL: %s, stagingPath: %s, token: %s' % (self.options.resourceURL, self.options.mexURL, self.options.stagingPath, self.options.token))
# 
#         if len(args) != 1 or self.options.resourceURL is None or self.options.mexURL is None or self.options.stagingPath is None:
#             parser.error('\nBQ.CellProfiler.Adapter: Insufficient options or arguments!')
#             return False
# 
#         command = args.pop(0)
# 
#         if command not in ('setup','teardown', 'start'):
#             parser.error('\nBQ.CellProfiler.Adapter: Invalid Command! Must be setup, start or teardown.')
#             return False
# 
#         return getattr(self, command)
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
#     def setup(self):
# 
#         self.bqSession.update_mex('Initializing...')
# 
#         pipelinePath = os.path.join(self.options.modulePath, os.path.join("pipelines", self.pipeline))
# 
#         # copy the requested pipeline file into the staging directory
#         copy2(pipelinePath, self.pipeline)
# 
#         # create input/output folders
#         os.mkdir(self.inputDir)
#         os.mkdir(self.outputDir)
# 
#         # fetch the input image
#         if self.options.isDataset:
#             results = fetch_dataset(self.bqSession, self.options.resourceURL, self.inputDir, True)
#         else:
#             results = fetch_image_pixels(self.bqSession, self.options.resourceURL, self.inputDir, True)
# 
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
#     def start(self):
# 
#         self.bqSession.update_mex('Working...')
# 
#         # need to know the path to CellProfiler executable in Win or Linux
#         if os.name=='nt':
#             executable = "C:\Program Files\CellProfiler\CellProfiler.exe"
#         else:
#             executable = "CellProfiler"
# 
#         cp_cmd = [executable, "-c", "-r", "-i", self.inputDir, "-o", self.outputDir, "-p", self.pipeline]
#         logger.info ("calling: %s", " ".join(cp_cmd))
#         p = subprocess.Popen(cp_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#         (stout, sterr) = p.communicate()
# 
#         #if r != 0:   CP DOES NOT RETURN AN ERROR CODE ON FAILURE
#         if not os.path.exists (os.path.join(self.outputDir, "DefaultOUT_Summary.csv")):
#             self.bqSession.fail_mex ("cell profiler did not complete: %s" % stout)
# 
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
#     def teardown(self):
# 
#         self.bqSession.update_mex('Collecting results...')
#         print 'Collecting Results'
# 
#         # create a new parent tag 'CellProfiler' to be placed on the mex
#         outputsTag = BQTag(name='outputs')
#         parentTag = BQTag(name='Summary')
#         outputsTag.addTag(tag=parentTag)
# 
#         # Read summary from csv and write to tags
#         (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Summary.csv'))
# 
#         if header is not None:
#             for i in range(len(records)):
#                 for j in range(len(header)):
#                     parentTag.addTag(name=header[j], value=records[i][j])
# 
# 
#         # Add parent image tag
#         imageTag = BQTag(name='Output image', value=self.options.resourceURL, type='image')
#         outputsTag.addTag(tag=imageTag)
# 
#         print 'Reading GObjects'
# 
#         # Read object measurements from csv and write to gobjects
#         (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Objects.csv'))
# 
#         if header is not None:
#             # create a new parent tag 'CellProfiler' to be placed on the mex
#             parentGObject = BQGObject(name='CellProfiler Annotations')
# 
#             for i in range(len(records)):
#                 shape = CPShape()
#                 shape.addEllipse(header=header, record=records[i])
#                 shape.addTag(name="Area", value=records[i][header.index('AreaShape_Area')])
#                 parentGObject.addGObject(gob=shape)
#             imageTag.addGObject(gob=parentGObject)
# 
#         # Read any image files that the pipeline generated and post them to mex
#         imgFormats  = ['*.tif*', '*.jpg']
#         fileList=[]
#         for fmt in imgFormats:
#             fileList.extend(glob(os.path.join(self.outputDir, fmt)))
#         for file in fileList:
#             content = save_image_pixels(self.bqSession, file)
# 
#             if content is not None:
#                 print 'BQ.CellProfiler.Adapter: Upload Error!'
#                 uri = etree.XML(content).xpath('//image[@uri]/@uri')[0] or "BQ.CellProfiler.Adapter: Upload Error!"
#                 fileName = os.path.split(file)[1]
#                 tempTag = BQTag(name=fileName, value=uri, type='image')
#                 outputsTag.addTag(tag=tempTag)
# 
#         self.bqSession.finish_mex(tags = [outputsTag])
#         self.bqSession.close()
# 
# 
#     def readCSV(self, fileName):
# 
#         if os.path.exists(fileName) == False:
#             return (None, None)
# 
#         records = []
#         handle = open(fileName, 'rb')
#         csvHandle = csv.reader(handle)
#         header = csvHandle.next()
# 
#         for row in csvHandle:
#             records.append(row)
# 
#         handle.close()
#         return (header, records)
# 
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
#     def main(self):
#         """
#             The main function that runs everything
#         """
#         logger.debug('sysargv : %s' % sys.argv )
#         parser = OptionParser()
# 
#         parser.add_option('--resource_url', dest="resourceURL")
#         parser.add_option('--mex_url', dest="mexURL")
#         parser.add_option('--module_dir', dest="modulePath")
#         parser.add_option('--staging_path', dest="stagingPath")
#         parser.add_option('--auth_token', dest="token")
#         parser.add_option('--pipeline', dest="pipeline")
# 
#         (options, args) = parser.parse_args()
# 
#         logger.debug('\n\nPARAMS : %s \n\n Options: %s' % (args, options))
#         self.options = options
# 
#         self.options.isDataset = 'dataset' in self.options.resourceURL
#         self.inputDir = os.path.join(self.options.stagingPath, 'input') + os.sep
#         self.outputDir = os.path.join(self.options.stagingPath, 'output') + os.sep
#         self.pipeline = self.options.pipeline.lower() + ".cp"
# 
#         command = self.validateInput(parser, args)
# 
#         if (command):
#             self.bqSession = BQSession().init_mex(self.options.mexURL, self.options.token)
#             try:
#                 command()
#             except Exception, e:
#                 logger.exception("During Command %s" % command)
#                 self.bqSession.fail_mex(msg = "Exception during %s: %s" % (command,  str(e)))
#                 sys.exit(1)
# 
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# 
# if __name__ == "__main__":
#     CellProfiler().main()
#     sys.exit(0)
