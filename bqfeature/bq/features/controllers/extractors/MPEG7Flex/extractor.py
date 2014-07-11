#features included
# SCD,HTD2,EHD2,DCD,CSD,CLD,RSD
import numpy as np
from pyMPEG7FlexLib import extractCSD,extractSCD,extractCLD,extractDCD,extractHTD,extractEHD,extractRSD
from pylons.controllers.util import abort
import logging
import tables
from bq.features.controllers.Feature import calc_wrapper, ImageImport, rgb2gray #import base class
from bq.image_service.controllers.locks import Locks
from bq.features.controllers import Feature
from PIL import Image

log = logging.getLogger("bq.features")

#getting a double pointer error when run with multible threads
#class SCD(Feature.BaseFeature):
#    """
#        Initalizes table and calculates the SURF descriptor to be
#        placed into the HDF5 table.
#    """
#    
#    #parameters
#    name = 'SCD'
#    description = """Scalable Color Descriptor"""
#    length = 256 
#    type = ['color']
#    confidence = 'good'
#            
#    @calc_wrapper
#    def calculate(self, **resource):
#        """ Append descriptors to h5 table """
#        image_uri = resource['image']
#        log.debug('calculating scd')
#        with ImageImport(image_uri) as imgimp: #looking for the file internally and externally
#            #im=cv2.imread(str(imgimp), cv2.CV_LOAD_IMAGE_COLOR)
#            im = imgimp.from_tiff2D_to_numpy()
#            
#            im = np.asarray(im)
#            descriptors = extractSCD(im, descSize=256) #calculating descriptor
#            log.debug('descriptors: %s'%descriptors)
#        return [descriptors]

#FFTW is not thread-safe
#class HTD2(Feature.BaseFeature):
#    """
#    """
#    #initalize parameters
#    name = 'HTD2'
#    description = """Homogenious Texture Descritpor (Image\'s width and height must be greater than 128)"""
#    length = 62
#    type = ['texture']
#    confidence = 'good'
#            
#    @calc_wrapper
#    def calculate(self, **resource):
#        #initalizing
#        
#        image_uri = resource['image']
#        
#        with ImageImport(image_uri) as imgimp: #looking for the file internally and externally
#            im = imgimp.from_tiff2D_to_numpy()
#            if len(im.shape)==3:
#                im = rgb2gray(im)
#            im = np.asarray(im)
#            width, height = im.shape
#            if width<128 and height<128:
#                raise TypeError('Image\'s width and height must be greater than 128')
#            descriptors = extractHTD(im) #calculating descriptor
#        
#        return [descriptors]


class EHD2(Feature.BaseFeature):
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
    type = ['texture']
    confidence = 'good'    
        
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing
        
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im=np.asarray(im)
            
            descriptors = extractEHD(im) #calculating descriptor
        
        return [descriptors]
 
    
class DCD(Feature.BaseFeature):
    """
    
    """
    #parameters
    name = 'DCD'
    description = """Dominant Color Descriptor can be of any length. The arbitrary length decided to be stored in the
    tables is 100"""
    length = 100 
    type = ['color']
    confidence = 'good' 
            
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im=np.asarray(im)
            
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

class mDCD(DCD):
    """
    """
    
    #parameters
    name = 'mDCD'
    parent_feature = 'DCD'
    description = """Dominant Color Descriptor can be of any length. The arbitrary length decided to be stored in the
    tables is 100"""
    length = 100 
    parameter = ['label']
    resource = ['image','mask']
    type = ['color']
    confidence = 'good'  
 
    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            label     = tables.Int32Col(pos=3) 

        return Columns
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            feature       = tables.Col.from_atom(featureAtom, pos=4)
            label         = tables.Int32Col(pos=5)
            
        return Columns

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            error_code    = tables.Int32Col(pos=4)
            error_message = tables.StringCol(200,pos=5)
            
        return Columns
        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        
        image_uri = resource['image']
        mask_uri = resource['mask']
        
        with ImageImport(image_uri) as imgimp:
            with Feature.ImageImport(mask_uri) as maskimp:
            
                im = imgimp.from_tiff2D_to_numpy()

                mask = maskimp.from_tiff2D_to_numpy()

                #must atleast be grayscale
                if len(mask.shape)==3:
                    mask = rgb2gray(mask)    
                
                im=np.asarray(im)
                mask = np.asarray(mask)
                
                descritptor_list = []
                label_list = []
                #calculating descriptor
                for label in np.unique(mask):
                    lmask = np.array((mask==label)*255,dtype='uint8')
                    DCD = extractDCD(im, mask = lmask)
                    
                    label_list.append(label)
                    #log.debug('descriptors: %s'%descriptors)
                    #log.debug('length of descriptors: %s'%len(descriptors[0]))
                    
                    #DCD has a potentional to be any length
                    #the arbitrary decided length to store in the tables is 100
                    if len(DCD)>self.length:
                        log.debug('Warning: greater than 100 dimensions')
                        DCD=DCD[:self.length]
            
                    descriptors = np.zeros((self.length))
                    
                    descriptors[:len(DCD)]=DCD
                    descritptor_list.append(descriptors)
                
        #initalizing rows for the table
        return descritptor_list, label_list
  

class CSD(Feature.BaseFeature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'CSD'
    description = """Color Structure Descriptor"""
    length = 64 
    type = ['color']
    child_feature = ['mCSD']
    confidence = 'good' 
        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        #initalizing
        
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im=np.asarray(im)
            descriptors = extractCSD(im, descSize=64) #calculating descriptor
        
        return [descriptors]
        
class mCSD(CSD):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'mCSD'
    parent_feature = 'CSD'
    description = """Color Structure Descriptor"""
    length = 64 
    parameter = ['label']
    resource = ['image','mask']
    type = ['color']
    confidence = 'good' 
     
    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            label     = tables.Int32Col(pos=3) 

        return Columns
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            feature       = tables.Col.from_atom(featureAtom, pos=4)
            label         = tables.Int32Col(pos=5)
            
        return Columns

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            error_code    = tables.Int32Col(pos=4)
            error_message = tables.StringCol(200,pos=5)
            
        return Columns
        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        
        image_uri = resource['image']
        mask_uri = resource['mask']
        
        with ImageImport(image_uri) as imgimp:
            with ImageImport(mask_uri) as maskimp:

                im = imgimp.from_tiff2D_to_numpy()
                im=np.asarray(im)

                mask = maskimp.from_tiff2D_to_numpy()

                #must atleast be grayscale
                if len(mask.shape)==3:
                    mask = rgb2gray(mask)    
                
                
                im=np.asarray(im)
                mask = np.asarray(mask)
                
                descritptor_list = []
                label_list = []
                
                #calculating descriptor
                for label in np.unique(mask):
                    lmask = np.array((mask==label)*255,dtype='uint8')
                    descriptors = extractCSD(im, mask=lmask, descSize=64)
                    descritptor_list.append(descriptors)
                    label_list.append(label)
        
        return descritptor_list, label_list
 

class CLD(Feature.BaseFeature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'CLD'
    description = """Color Layout Descriptor"""
    length = 120
    child_feature = ['mCLD']
    confidence = 'good' 
        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to h5 table """
        
        image_uri = resource['image']
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            im = np.asarray(im)
            
            descriptors = extractCLD(im, numYCoef=64, numCCoef = 28)
            
        return [descriptors]

class mCLD(CLD):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'mCLD'
    parent_feature = 'CLD'
    description = """masked Color Layout Descriptor"""
    length = 120
    parameter = ['label']
    resource = ['image','mask']
    type = ['color']
    confidence = 'good' 

    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            label     = tables.Int32Col(pos=3) 

        return Columns
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            feature       = tables.Col.from_atom(featureAtom, pos=4)
            label         = tables.Int32Col(pos=5)
            
        return Columns

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            error_code    = tables.Int32Col(pos=4)
            error_message = tables.StringCol(200,pos=5)
            
        return Columns

        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        
        image_uri = resource['image']
        mask_uri = resource['mask']
        
        with ImageImport(image_uri) as imgimp:
            with ImageImport(mask_uri) as maskimp:
                
                im = imgimp.from_tiff2D_to_numpy()
                im=np.asarray(im)
                
                mask = maskimp.from_tiff2D_to_numpy()
                
                #must atleast be grayscale
                if len(mask.shape)==3:
                    mask = rgb2gray(mask)    
                
                im=np.asarray(im)
                mask = np.asarray(mask)
                
                descritptor_list = []
                label_list = []
                #calculating descriptor
                for label in np.unique(mask):
                    lmask = np.array((mask==label)*255,dtype='uint8')
                    descriptors = extractCLD(im,mask=lmask,numYCoef=64, numCCoef = 28)
                    descritptor_list.append(descriptors)
                    label_list.append(label)

        
        return descritptor_list, label_list



class RSD(Feature.BaseFeature):
    """
    """
    name = 'RSD'
    description = """Region Shape Descritpor"""
    length = 35
    type = ['shape','texture']
    #child_feature = ['RSD']
    confidence = 'good' 
 
    @calc_wrapper    
    def calculate(self, **resource):
        image_uri = resource['image']
        
        with ImageImport(image_uri) as imgimp:

            im = imgimp.from_tiff2D_to_numpy()
            
            im=np.asarray(im)
                
            descriptors = extractRSD(im)
            
        
        return [descriptors]
    
    
        
class pRSD(Feature.BaseFeature):
    """
        Initalizes table and calculates the pRSD descriptor to be
        placed into the HDF5 table.
    """
    
    name = 'pRSD'
    description = """Region Shape Descritpor"""
    length = 35
    resource = ['image','polygon']
    type = ['shape','texture']
    child_feature = ['mRSD']
    confidence = 'good'


        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image  = tables.StringCol(2000,pos=1)
            polygon = tables.StringCol(2000,pos=2)
            feature   = tables.Col.from_atom(featureAtom, pos=3)
            
        return Columns

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            polygon       = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            error_code    = tables.Int32Col(pos=4)
            error_message = tables.StringCol(200,pos=5)
            
        return Columns

            
    @calc_wrapper
    def calculate(self, **resource):
        #initalizing
        
        polygon_uri = resource['polygon']
        xml = Feature.xml_import(polygon_uri+'?view=deep')
        tree = xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append((int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))))
        else:
            raise ValueError(404, 'polygon not found: must be a polygon gobject')
        
        
        self.image_uri = resource['image']
        with ImageImport(image_uri) as imgimp:
            im = imgimp.from_tiff2D_to_numpy()
            
            col,row,channel = im.shape
            #creating mask
            import Image #requires pil
            import ImageDraw
            #parameters
            log.debug('contour: %s'%contour)
            img = Image.new('L', (row, col), 0)
            ImageDraw.Draw(img).polygon(contour, outline=1, fill=1)
            mask = np.array(img)*255
    
            
            #initalizing rows for the table
            descriptors = extractRSD(im, mask)
        
        return [descriptors]
    
    
class mRSD(RSD):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    name = 'mRSD'
    parent_feature = 'RSD'
    description = """Region Shape Descritpor"""
    length = 35
    parameter = ['label']
    resource = ['image','mask']
    type = ['shape','texture']
    confidence = 'good' 


    def cached_columns(self):
        """
            Columns for the cached tables
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            label     = tables.Int32Col(pos=3) 

        return Columns
        
    def output_feature_columns(self):
        """
            Columns for the output table for the feature column
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))

        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            feature       = tables.Col.from_atom(featureAtom, pos=4)
            label         = tables.Int32Col(pos=5)
            
        return Columns

    def output_error_columns(self):
        """
            Columns for the output table for the error columns
        """
        class Columns(tables.IsDescription):
            image         = tables.StringCol(2000,pos=1)
            mask          = tables.StringCol(2000,pos=2)
            feature_type  = tables.StringCol(20, pos=3)
            error_code    = tables.Int32Col(pos=4)
            error_message = tables.StringCol(200,pos=5)
            
        return Columns

        
    @calc_wrapper
    def calculate(self, **resource):
        """ Append descriptors to SURF h5 table """
        #initalizing
        
        image_uri = resource['image']
        mask_uri = resource['mask']
                
        with ImageImport(image_uri) as imgimp:
            with ImageImport(mask_uri) as maskimp:
                
                
                #im=cv2.imread(str(imgimp), cv2.CV_LOAD_IMAGE_COLOR)
                im = imgimp.from_tiff2D_to_numpy()

                im=np.asarray(im)
                
                mask = maskimp.from_tiff2D_to_numpy()
                
                #must atleast be grayscale
                if len(mask.shape)==3:
                    mask = rgb2gray(mask)                
                
                im = np.asarray(im)
                mask = np.asarray(mask)
                
                descritptor_list = []
                label_list = []
                
                #calculating descriptor
                for label in np.unique(mask):
                    lmask = np.array((mask==label)*255,dtype='uint8')
                    descriptors = extractRSD(im,mask=lmask)
                    descritptor_list.append(descriptors)
                    label_list.append(label)
                #initalizing rows for the table
        
        return descritptor_list, label_list
    