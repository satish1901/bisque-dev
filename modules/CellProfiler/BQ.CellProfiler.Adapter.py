import os
import logging
import csv
import time
import sys
import math

from lxml import etree
from subprocess import call
from shutil import copy2
from glob import glob
from optparse import OptionParser
from bq.api import BQSession, BQTag, BQGObject, BQEllipse, BQVertex
from bq.api.util import fetchImage, fetchDataset, save_image_pixels


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('bq.modules')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

class CPShape(BQGObject):

    def __init__(self, name=None, value=None,  **params):
        BQGObject.__init__(self)

        self.name = name
        self.values = value and [value] or []
        self.tags =  []
        self.type='CPShape'
        self.gobjects = []

    def addEllipse(self, **params):

        header = params.get('header')
        record = params.get('record')
        getValue = lambda x: float(record[header.index(x)])
        
        ellipse = BQEllipse()
        self.addGObject(gob=ellipse)
        
        # centroid
        x = getValue('AreaShape_Center_X')
        y = getValue('AreaShape_Center_Y')
        theta = math.radians(-1*getValue('AreaShape_Orientation'))

        vCentroid = BQVertex(x=x, y=y)
        ellipse.addGObject(gob=vCentroid)

        # major axis/minor axis endpoint coordinates
        a = 0.5 * getValue('AreaShape_MajorAxisLength')
        b = 0.5 * getValue('AreaShape_MinorAxisLength')
        
        bX = round(x - b*math.sin(theta))
        bY = round(y + b*math.cos(theta))
        vMinor = BQVertex(x=bX, y=bY)
        ellipse.addGObject(gob=vMinor)

        aX = round(x + a*math.cos(theta))
        aY = round(y + a*math.sin(theta))
        vMajor = BQVertex(x=aX, y=aY)
        ellipse.addGObject(gob=vMajor)
        
        
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


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
        parentTag = BQTag(name='Summary: '+self.pipeline)

        # Read summary from csv and write to tags
        (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Summary.csv'))

        if header is not None:
            for i in range(len(records)):
                for j in range(len(header)):
                    parentTag.addTag(name=header[j], value=records[i][j])
        
        print 'Reading GObjects'

        # Read object measurements from csv and write to gobjects
        (header, records) = self.readCSV(os.path.join(self.outputDir, 'DefaultOUT_Objects.csv'))

        if header is not None:
            # create a new parent tag 'CellProfiler' to be placed on the mex
            parentGObject = BQGObject(name='CellProfiler: '+self.pipeline)
            
            for i in range(len(records)):
                shape = CPShape()
                shape.addEllipse(header=header, record=records[i])
                shape.addTag(name="Area", value=records[i][header.index('AreaShape_Area')])

                parentGObject.addGObject(gob=shape)

        # Read any image files that the pipeline generated and post them to mex
        imageTag = BQTag(name='Images')
        parentTag.addTag(tag=imageTag)
        
        imgFormats  = ['*.tif*', '*.jpg']
        fileList=[]
        for fmt in imgFormats:
            fileList.extend(glob(os.path.join(self.outputDir, fmt)))
        for file in fileList:
            content = save_image_pixels(self.bqSession, file)
            
            print '\n\n\nCONTENT BEGINS HERE'
            print content
            print '\n\n\n'
            
            if content is not None:
                uri = etree.XML(content).xpath('//image[@uri]/@uri')[0] or "BQ.CellProfiler.Adapter: Upload Error!"
                fileName = os.path.split(file)[1]
                tempTag = BQTag(name=fileName, value=uri, type='resource')
                imageTag.addTag(tag=tempTag)

        self.bqSession.finish_mex(tags = [parentTag], gobjects = [parentGObject])
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
