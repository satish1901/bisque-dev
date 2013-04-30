#features included
# SCD,HTD2,EHD2,DCD,CSD,CLD,RSD
import cv2
import cv
import numpy as np
from MPEG7FexLib import extractCSD,extractSCD,extractCLD,extractDCD,extractHTD,extractEHD,extractRSD
import bq.features.controllers.Feature as Feature #import base class


class SCD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_scd.h5'
    name = 'SCD'
    description = """Scalable Color Descriptor"""
    length = 256 
    temptable = []
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        
        descriptors = extractSCD(im, descSize=256) #calculating descriptor
        
        self.setRow(uri, idnumber, descriptors)



class HTD2(Feature.Feature):
    """
    """
    #initalize parameters
    file = 'features_htd2.h5'
    name = 'HTD2'
    description = """Homogenious Texture Descritpor"""
    length = 62 
    temptable = []
        
    def appendTable(self, uri, idnumber):
        #initalizing
        

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        
        descriptors = extractHTD(im) #calculating descriptor
        
        
        self.setRow(uri, idnumber, descriptors)


class EHD2(Feature.Feature):
    """
        Initalizes table and calculates the Edge Histogram descriptor to be
        placed into the HDF5 table

        scale = 6
        rotation = 4
    """
    #initalize parameters
    file = 'features_ehd2.h5'
    name = 'EHD2'
    description = """Edge histogram descriptor also known as EHD"""
    length = 80 
    temptable = []
        
    def appendTable(self, uri, idnumber):
        #initalizing
        

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        
        descriptors = extractEHD(im) #calculating descriptor
        
        self.setRow(uri, idnumber, descriptors)


class DCD(Feature.Feature):
    """

    """
    
    #parameters
    file = 'features_dcd.h5'
    name = 'DCD'
    description = """Dominant Color Descriptor"""
    length = 64 
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        
        
        
         #calculating descriptor
        DCD = extractDCD(im)
        #log.debug('descriptors: %s'%descriptors)
        #log.debug('length of descriptors: %s'%len(descriptors[0]))
        if len(DCD[0])>self.length:
            log.debug('Warning: greater than 64 dimensions')
            desc_len = self.length
        else:
            desc_len = len(DCD[0])
        descriptors = np.zeros((1,self.length))
        descriptors[:,0:desc_len]=DCD
        
        #initalizing rows for the table
        self.setRow(uri, idnumber, descriptors)
        
        
class CSD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_csd.h5'
    name = 'CSD'
    description = """Color Structure Descriptor"""
    length = 64 
    temptable = []
        
    def appendTable(self, uri, idnumber):
        
        """ Append descriptors to h5 table """
        #initalizing
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        
        descriptors = extractCSD(im, descSize=64) #calculating descriptor
        
        
        self.setRow(uri, idnumber, descriptors)


class CLD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_cld.h5'
    name = 'CLD'
    description = """Color Layout Descriptor"""
    length = 120
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to h5 table """
        
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        del Im
        
        descriptors = extractCLD(im, numYCoef=64, numCCoef = 28)
        self.setRow(uri, idnumber, descriptors)


class RSD(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    file = 'features_rsd.h5'
    name = 'RSD'
    description = """Region Shape Descritpor"""
    length = 35 
        
    def appendTable(self, uri, idnumber):
        """ Append descriptors to SURF h5 table """
        #initalizing

        self.uri = uri
        xml=Feature.XMLImport(self.uri+'?view=deep')
        tree=xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append((int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))))
        else:
            abort(404, 'polygon not found: must be a polygon gobject')
        
        
        gobject = self.uri.replace('/',' ').replace('?',' ').split()
        image_id=[]
        for i,split in enumerate(gobject):
            if split == 'image':
                image_id.append(gobject[i+1])
        
        if len(image_id)>1:
            abort(500,'too many ids')
        elif len(image_id)<1:
            about(500,'no ids')
        else:
            self.image_uri = 'http://bisque.ece.ucsb.edu/data_service/image/'+image_id[0]
        
        Im = Feature.ImageImport(self.image_uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
        
        col,row,channel = im.shape
        #creating mask
        img = Image.new('L', (row, col), 0)
        ImageDraw.Draw(img).polygon(contour, outline=1, fill=1)
        mask = np.array(img)
        
        del Im
        
        #initalizing rows for the table
        
        descriptors = extractRSD(im, mask)
        self.setRow(uri, idnumber, descriptors)