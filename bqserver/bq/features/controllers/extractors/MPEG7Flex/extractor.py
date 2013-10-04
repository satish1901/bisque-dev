#features included
# SCD,HTD2,EHD2,DCD,CSD,CLD,RSD
import cv2
import cv
import numpy as np
from pyMPEG7FlexLib import extractCSD,extractSCD,extractCLD,extractDCD,extractHTD,extractEHD,extractRSD
import bq.features.controllers.Feature as Feature #import base class
from pylons.controllers.util import abort
import logging
log = logging.getLogger("bq.features")

class SCD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'SCD'
    description = """Scalable Color Descriptor"""
    length = 256 
        
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        descriptors = extractSCD(im, descSize=256) #calculating descriptor
        
        return [descriptors]



class HTD2(Feature.Feature):
    """
    """
    #initalize parameters
    name = 'HTD2'
    description = """Homogenious Texture Descritpor"""
    length = 62 
        
    @Feature.wrapper
    def calculate(self, **resource):
        #initalizing
        
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        descriptors = extractHTD(im) #calculating descriptor
        
        return [descriptors]


class EHD2(Feature.Feature):
    """
        Initalizes table and calculates the Edge Histogram descriptor to be
        placed into the HDF5 table

        scale = 6
        rotation = 4
    """
    #initalize parameters
    name = 'EHD2'
    description = """Edge histogram descriptor also known as EHD"""
    length = 80 
        
    @Feature.wrapper
    def calculate(self, **resource):
        #initalizing
        
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        descriptors = extractEHD(im) #calculating descriptor
        
        return [descriptors]


class DCD(Feature.Feature):
    """

    """
    
    #parameters
    name = 'DCD'
    description = """Dominant Color Descriptor can be of any length. The arbitrary length decided to be stored in the
    tables is 100"""
    length = 100 
        
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        #calculating descriptor
        DCD = extractDCD(im)
        #log.debug('descriptors: %s'%descriptors)
        #log.debug('length of descriptors: %s'%len(descriptors[0]))
        
        #DCD has a potentional to be any length
        #the arbitrary decided length to store in the tables is 100
        if len(DCD)>self.length:
            log.debug('Warning: greater than 100 dimensions')
            DCD=DCD[:self.length]

        descriptors = np.zeros((self.length))
        descriptors[:len(DCD)]=DCD
        
        #initalizing rows for the table
        return [descriptors]
        
        
class CSD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'CSD'
    description = """Color Structure Descriptor"""
    length = 64 
        
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        #initalizing
        
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        descriptors = extractCSD(im, descSize=64) #calculating descriptor
        
        return [descriptors]


class CLD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'CLD'
    description = """Color Layout Descriptor"""
    length = 120
        
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        
        image_uri = resource['image']
        Im = Feature.ImageImport(image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        im=np.asarray(im)
        if im==None:
            abort(415, 'Format was not supported')
        
        descriptors = extractCLD(im, numYCoef=64, numCCoef = 28)
        return [descriptors]

class RSD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    name = 'RSD'
    description = """Region Shape Descritpor"""
    length = 35
    resource = ['image','polygon']
        
    @Feature.wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        
        polygon_uri = resource['polygon']
        xml = Feature.XMLImport(polygon_uri+'?view=deep')
        tree = xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append((int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))))
        else:
            abort(404, 'polygon not found: must be a polygon gobject')
        
        
#        gobject = self.uri.replace('/',' ').replace('?',' ').split()
#        image_id=[]
#        for i,split in enumerate(gobject):
#            if split == 'image':
#                image_id.append(gobject[i+1])
#        
#        if len(image_id)>1:
#            abort(500,'too many ids')
#        elif len(image_id)<1:
#            about(500,'no ids')
#        else:
#            root = 'http://128.111.185.26:8080'
#            xml = Feature.XMLImport(root+'/data_service/image/'+image_id[0])
#            tree = xml.returnxml()
#            self.image_uri = root+'/image_service/image/'+tree.attrib['resource_uniq']
        
        
        image_uri = resource['image']
        Im = Feature.ImageImport(self.image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        
        col,row,channel = im.shape
        #creating mask
        import Image
        import ImageDraw
        #parameters
        log.debug('contour: %s'%contour)
        img = Image.new('L', (row, col), 0)
        ImageDraw.Draw(img).polygon(contour, outline=1, fill=1)
        mask = np.array(img)*255

        
        #initalizing rows for the table
        descriptors = extractRSD(im, mask)
        del Im
        
        return [descriptors]
    
    def outputTable(self,filename):
        """
        Output table for hdf output requests and uncached features
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            image  = tables.StringCol(2000,pos=1)
            polygon = tables.StringCol(2000,pos=2)
            feature   = tables.Col.from_atom(featureAtom, pos=3)
            
        with Locks(None, filename), tables.openFile(filename,'a', title=self.name) as h5file: 
            outtable = h5file.createTable('/', 'values', Columns, expectedrows=1000000000)
            outtable.flush()
            
        return