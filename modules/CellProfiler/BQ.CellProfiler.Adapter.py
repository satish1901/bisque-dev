import os
import logging
import csv
import time
import sys

from lxml import etree
from subprocess import call
from shutil import copy2
from glob import glob
from optparse import OptionParser
from bq.api import BQSession, BQTag, BQGObject, BQShape
from bq.api.util import fetchImage, fetchDataset, save_image_pixels


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('bq.modules')

class CellProfiler():

    def validateInput(self, parser, args):
        
        logger.debug('\nCellProfiler - resourceURL: %s, mexURL: %s, stagingPath: %s, token: %s' % (self.options.resourceURL, self.options.mexURL, self.options.stagingPath, self.options.token))
        
        if len(args) != 1 or self.options.resourceURL is None or self.options.mexURL is None or self.options.stagingPath is None:
            parser.error('\nBQ.CellProfiler.Adapter: Insufficient options or arguments!')
            return False

        command = args.pop(0)
        
        if command not in ('setup','teardown', 'start'):
            parser.error('\nBQ.CellProfiler.Adapter: Invalid Command! Must be setup, start or teardown.')
            return False
        
        return getattr(self, command)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def setup(self):
        
        self.bqSession.update_mex('Initializing...')
        
        pipelinePath = os.path.join(self.options.modulePath, os.path.join("pipelines", self.pipeline))
        commandPath = os.path.join(self.options.modulePath, os.path.join("commands", self.pipelineCmd))

        # copy the requested pipeline file into the staging directory
        copy2(pipelinePath, self.pipeline)
        
        # create input/output folders
        os.mkdir(self.inputDir)
        os.mkdir(self.outputDir)
        
        # fetch the input image
        if self.options.isDataset:
            results = fetchDataset(self.bqSession, self.options.resourceURL, self.inputDir, True)
        else:
            results = fetchImage(self.bqSession, self.options.resourceURL, self.inputDir, True) 
        
        
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def start(self):
        
        self.bqSession.update_mex('Working...')

        # need to know the path to CellProfiler executable in Win or Linux
        if os.name=='nt':
            executable = "C:\Program Files\CellProfiler\CellProfiler.exe"
        else:
            executable = "CellProfiler"

        call([executable, "-c", "-r", "-i", self.inputDir, "-o", self.outputDir, "-p", self.pipeline])

        
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def teardown(self):

        self.bqSession.update_mex('Collecting results...')
        print 'Collecting Results'
        
        # create a new parent tag 'CellProfiler' to be placed on the mex
        parentTag = BQTag(name='CellProfiler Summary')
        self.bqSession.mex.addTag(tag = parentTag)

        # Read summary from csv and write to tags
        (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Summary.csv'))

        if header is not None:
            for i in range(len(records)):
                for j in range(len(header)):
                    parentTag.addTag(name=header[j], value=records[i][j])
        
        print 'Read GObjects'

        # Read object measurements from csv and write to gobjects
        (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Objects.csv'))

        if header is not None:
            # create a new parent tag 'CellProfiler' to be placed on the mex
            parentGObject = BQGObject(name='CellProfiler: '+self.pipeline)
            
            for i in range(len(records)):
                shape = BQShape(header=header, record=records[i])
                shape.addTag(name="Area", value=records[i][header.index('AreaShape_Area')])
                shape.set_parent(parentGObject)
            
            self.bqSession.mex.addGObject(gob = parentGObject)


        # Read any image files that the pipeline generated and post them to mex
        imageTag = BQTag(name='Images')
        imageTag.set_parent(parentTag)
        
        imgFormats  = ['*.tif*', '*.jpg']
        fileList=[]
        for fmt in imgFormats:
            fileList.extend(glob(os.path.join(self.outputDir, fmt)))
        for file in fileList:
            content = save_image_pixels(self.bqSession, file)
            if content is not None:
                uri = etree.XML(content).xpath('//image[@uri]/@uri')[0] or "BQ.CellProfiler.Adapter: Upload Error!"
                fileName = os.path.split(file)[1]
                tempTag = BQTag(name=fileName, value=uri, type='resource')
                tempTag.set_parent(imageTag)

        self.bqSession.finish_mex()
        self.bqSession.close()


    def readCSV(self, fileName):
        
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


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def run(self):
        
        parser = OptionParser()
        
        parser.add_option('--resource_url', dest="resourceURL")
        parser.add_option('--mex_url', dest="mexURL")
        parser.add_option('--module_dir', dest="modulePath")
        parser.add_option('--staging_path', dest="stagingPath")
        parser.add_option('--auth_token', dest="token")
        parser.add_option('--pipeline', dest="pipeline")
        
        (options, args) = parser.parse_args()
        self.options = options
        
        self.options.isDataset = 'dataset' in self.options.resourceURL
        self.inputDir = os.path.join(self.options.stagingPath, 'input') + os.sep
        self.outputDir = os.path.join(self.options.stagingPath, 'output') + os.sep
        self.pipeline = self.options.pipeline + ".cp"
        self.pipelineCmd = self.options.pipeline + ".py"

        command = self.validateInput(parser, args)
        
        if (command):
            self.bqSession = BQSession().init_mex(self.options.mexURL, self.options.token)
            command()
            
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

if __name__ == "__main__":
    CellProfiler().run()
    sys.exit(0)
