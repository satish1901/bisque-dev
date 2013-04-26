# -*- mode: python -*-
""" ShCoD library
"""
import cv2
import cv
import Feature #import base class
import scipy.io
import subprocess
import logging

class ShCoD(Feature.Feature):
    
    #parameters
    file = 'features_shcod.h5'
    name = 'ShCoD'
    description = """Shape Context Descritpor: num_theta = 12, num_r = 5"""
    length = 60
    parameter_info = ['feature_number']#,'x position', 'y position']
        
    def appendTable(self, uri, idnumber):

        """ Append descriptors to SURF h5 table """
        #initalizing
        self.uri=uri
        xml=Feature.XMLImport(self.uri+'?view=deep')
        tree=xml.returnxml()
        if tree.tag=='polygon':
            vertices = tree.xpath('vertex')
            contour = []
            for vertex in vertices:
                contour.append([int(float(vertex.attrib['x'])),int(float(vertex.attrib['y']))])
        else:
            abort(404, 'polygon not found: must be a polygon gobject')
        
        
        #creating an input file and output file
        fin = Feature.TempImport('mat')
        file_in_path = fin.returnpath()
        
        fout = Feature.TempImport('mat') #designating a file for temp
        file_out_path = fout.returnpath()
        
        #creating input file
        scipy.io.savemat(file_in_path, mdict={'contour':contour})

        log = logging.getLogger("bq.features")
        log.debug('fin_path: %s'%file_in_path)
        log.debug('fout_path: %s'%file_out_path)
        
        #creating output file
        fout.open()
        fout.close()
        
        #running matlab
        subprocess.call([r'c:\bisque\bqserver\bq\features\controllers\extraction_library\include\SCD\My_Calculate_SCD.exe', str(file_in_path), str(file_out_path), str(120)])

        #parse output file
        mat = scipy.io.loadmat(file_out_path)
        descriptors = mat['BH']
        del fin
        del fout
        
        #initalizing rows for the table
        for i in range(0,len(descriptors)):
            parameter= [i]#,x,y]
            self.setRow(uri, idnumber, descriptors[i], parameter)

    
            

