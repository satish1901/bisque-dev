# converter_base.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" Base class defining command line converter API
"""

__module__    = "converter_base"
__author__    = "Dmitry Fedorov"
__version__   = "0.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os.path
from subprocess import call
from locks import Locks
from collections import OrderedDict

import logging
log = logging.getLogger('bq.image_service.converter')


################################################################################
# Format - the definition of a format
################################################################################

class Format:
    def __init__(self, name='', fullname='', ext=[], reading=False, writing=False, multipage=False, metadata=False, samples=(0,0), bits=(0,0)):
        self.name      = name
        self.fullname  = fullname
        self.ext       = ext
        self.reading   = reading
        self.writing   = writing        
        self.multipage = multipage
        self.metadata  = metadata
        self.samples_per_pixel_min_max = samples
        self.bits_per_sample_min_max   = bits

    def supportToString(self):
        s = []
        if self.reading   is True: s.append('reading')
        if self.writing   is True: s.append('writing')
        if self.multipage is True: s.append('multipage')
        if self.metadata  is True: s.append('metadata')
        return ','.join(s)

################################################################################
# ConverterBase
################################################################################

class ConverterBase:
    installed = False
    version = None
    installed_formats = None # OrderedDict containing Format and keyed by format name 
    CONVERTERCOMMAND = 'convert' if os.name != 'nt' else 'convert.exe'

    #######################################
    # Init
    #######################################

    #@staticmethod 
    @classmethod
    def init(cls):
        cls.version = cls.get_version()
        cls.installed = cls.get_installed()
        cls.get_formats()    

    #######################################
    # Version and Installed
    #######################################

    # overwrite with appropriate implementation    
    @classmethod    
    def get_version (cls):
        '''returns the version of command line utility'''
        return {
            'full': '0.0.0',
            'numeric': [0,0,0],
            'major': 0,
            'minor': 0,
            'build': 0,            
        }

    @classmethod
    def get_installed (cls):
        '''Returns true if converter is installed'''
        if cls.version is not None and 'full' in cls.version: 
            return True
        return False    
    
    @classmethod
    def check_version ( cls, needed ):
        '''checks if converter is of proper version'''
        if cls.version is None or not 'numeric' in cls.version: 
            return False
        if isinstance(needed, str): 
            needed = [int(s) for s in needed.split('.')]
        has = cls.version['numeric']
        return needed <= has

    @classmethod    
    def ensure_version ( cls, needed ):
        '''checks if converter is of proper version and sets installed to false if its older'''
        cls.installed = cls.check_version ( needed )
        return cls.installed

    #######################################
    # Formats
    #######################################

    # overwrite with appropriate implementation    
    @classmethod 
    def get_formats(cls):
        '''inits supported file formats'''
        if cls.installed_formats is None:
            cls.installed_formats = OrderedDict() # OrderedDict containing Format and keyed by format name 
    
    def formats(self):
        '''return the XML with supported file formats'''
        return self.installed_formats

    #######################################
    # Supported
    #######################################
    
    # overwrite with appropriate implementation
    def supported(self, ifnm):
        '''return True if the input file format is supported'''
        return False


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################
      
    # overwrite with appropriate implementation  
    def meta(self, ifnm, series=0):
        '''returns a dict with file metadata'''        
        return {}
    
    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    
    # overwrite with appropriate implementation    
    def info(self, ifnm, series=0):
        '''returns a dict with file info'''
        if not self.installed:
            return {}
        if not os.path.exists(ifnm):
            return {}
    
        rd = self.meta(ifnm, series)
        core = [ 'image_num_series', 'image_num_x', 'image_num_y', 'image_num_z', 'image_num_c', 'image_num_t', 
                 'image_pixel_format', 'image_pixel_depth',
                 'pixel_resolution_x', 'pixel_resolution_y', 'pixel_resolution_z',
                 'pixel_resolution_unit_x', 'pixel_resolution_unit_y', 'pixel_resolution_unit_z' ]
        
        return {k:v for k,v in rd.iteritems() if k in core}

    #######################################
    # Conversion
    #######################################

    def run(self, ifnm, ofnm, args ):
        '''converts input filename into output using exact arguments as provided in args'''
        if not self.installed: 
            return None
        with Locks(ifnm, ofnm) as l:
            if not l.locked:
                return None
            command = [self.CONVERTERCOMMAND]
            command.extend(args)   
            log.debug('Convert command: [%s]', ' '.join(command))
            if os.path.exists(ofnm):
                log.warning ('Run: [%s] exists before command', ofnm)            
            retcode = call (command)
            if retcode != 0:
                log.error ('Run: [%s] returned [%s]', ' '.join(command), retcode)
                return None
            # tile command does not produce a file with this filename
#             if not os.path.exists(ofnm):
#                 log.error ('Run: [%s] does not exist after command', ofnm)
#                 return None
            # safeguard for incorrectly converted files, sometimes only the tiff header can be written
            if os.path.exists(ofnm) and os.path.getsize(ofnm) < 16:
                log.error ('Run: [%s] file is smaller than 16 bytes, probably an error, removing', ofnm)                
                os.remove(ofnm)
                return None
            return ofnm
    
    def convert(self, ifnm, ofnm, fmt=None, series=0, extra=[]):
        '''converts a file and returns output filename'''
        command = ['-input', ifnm]
        if ofnm is not None:
            command.extend (['-output', ofnm])
        if fmt is not None:
            command.extend (['-format', fmt])
        if series is not None:
            command.extend (['-series', str(series)])               
        #command.extend (extra)
        return self.run(ifnm, ofnm, command )
    
    # overwrite with appropriate implementation 
    def convertToOmeTiff(self, ifnm, ofnm, series=0, extra=[]):
        '''converts input filename into output in OME-TIFF format'''
        return self.run(ifnm, ofnm, ['-input', ifnm, '-output', ofnm, '-format', 'OmeTiff', '-series', '%s'%series] )

    # overwrite with appropriate implementation
    def thumbnail(self, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        return self.run(ifnm, ofnm, ['-input', ifnm, '-output', ofnm, '-format', 'jpeg', '-series', '%s'%series, '-thumbnail'] )

    # overwrite with appropriate implementation
    def slice(self, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi
        info = kw['info']
                
        return self.run(ifnm, ofnm, ['-input', ifnm, '-output', ofnm, '-format', 'OmeTiff', '-series', '%s'%series, 'z', '%s'%z, 't', '%s'%t] )
    

#ConverterBase.init()
