# bioformats.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" Functions to call BioFormats command line tools.
    This module requires bioformats to be installed in path.
"""

__module__    = "bioformats"
__author__    = "Dmitry Fedorov"
__version__   = "0.5"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


import os.path
from subprocess import Popen, call, PIPE
from locks import Locks

import logging
log = logging.getLogger('bq.bioformats')

BFINFO    = 'showinf'
BFCONVERT = 'bfconvert'
BFORMATS  = 'formatlist'

if os.name == 'nt':
    BFINFO    = 'showinf.bat' 
    BFCONVERT = 'bfconvert.bat'
    BFORMATS  = 'formatlist.bat'

 
################################################################################
# bioformats interface
################################################################################

is_installed = True # this is updated later

def run_command(command):
    '''returns a string of a successfully executed command, otherwise None'''
    try:
        p = Popen (command, stdout=PIPE, stderr=PIPE)
        o,e = p.communicate()
        
        if p.returncode!=0: 
            return None
        if e is not None and len(e)>0: 
            return None
       
        return o
    except OSError, e:
        log.warn ('%s command not found' % command[0])
    except:
        log.exception ("during execution %s" % command )
    return None

################################################################################
# Version
################################################################################

#$ ./showinf -version
#Version: 4.2.0
#SVN revision: 6685
#Build date: 9 July 2010

#Version: 4.3.2
#VCS revision: bb54cc7
#Build date: 14 September 2011

def get_version ():
    '''returns the version of bioformats'''    
    o = run_command( [BFINFO, '-version'] )
    if o is None: return None

    v = {}    
    for line in o.splitlines():
        if not line: continue
        d = line.split(': ', 1)
        if len(d)<2: continue
        v[d[0]] = d[1]
    
    if 'Version' in v:
        v['full'] =  v['Version']

    if 'full' in v:
        d = [int(s) for s in v['full'].split('.', 2)]
        if len(d)>2:
            v['numeric']  = d
            v['major']    = d[0]
            v['minor']    = d[1]
            v['build']    = d[2]
            #v['revision'] = d[3]            

    return v

is_version = get_version()
def version ():
    '''returns the version of bioformats'''    
    return is_version
    
################################################################################
# Installed
################################################################################    

def check_installed ():
    '''Returns true if bioformats are installed'''
    if is_version is None: return False
    if 'full' in is_version: return True      
    return False

is_installed = check_installed()

def installed ():
    '''return true if bioformats are installed'''
    return is_installed
        
def check_version ( needed ):
    '''checks if bioformats are of proper version'''  
    if is_version is None or not 'numeric' in is_version: return False
    if isinstance(needed, str): needed = [int(s) for s in needed.split('.')]
    has = is_version['numeric']
    return needed < has

def ensure_version ( needed ):
    '''checks if bioformats are of proper version and sets installed to false if its older'''  
    is_installed = check_version ( needed )
    return is_installed    

################################################################################
# Formats
################################################################################

def installed_formats():
    '''return the XML with supported file formats'''
    fs = run_command( [BFORMATS, '-xml'] )
    if fs is None: 
        return ''    
    fs = fs.replace('format', 'codec')
    fs = fs.replace('<response>', "<format name='bioformats' version='%s'>"%is_version['full'])
    fs = fs.replace('</response>', '</format>') 
    return fs

#./showinf -nopix -nometa 13_1.lsm
def supported(ifnm, original=None):
    '''returnd True if the input file format is supported'''
    return len(info(ifnm, original))>0


################################################################################
# Conversion
################################################################################                            

# '.ome.tiff' or '.ome.tif'.
# 
#sh bfconvert -bigtiff -compression LZW  ../53676.svs ../output.ome.tiff

def convert(ifnm, ofnm, original=None, series=-1):
    '''returns output filename'''
    if not is_installed: return None
    with Locks(ifnm, ofnm) as l:
        if not l.locked:
            return       
        if original is None:
            command = [BFCONVERT, ifnm, ofnm]
        else:
            command = [BFCONVERT, '-map', ifnm, original, ofnm]
        command.extend(['-bigtiff', '-compression', 'LZW'])            
        if series>=0:
            command.append('-series')
            command.append('%s'%series)
        log.debug('Convert: %s' % ' '.join (command) )
            
        #retcode = call (command)
        if os.path.exists(ofnm):
            log.error ('Convert: %s exists before command' % ofnm)

        p = Popen (command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        o,e = p.communicate(input='y\n')
        if p.returncode != 0:
            log.error ('Convert: returned %s %s %s' % (p.returncode, o, e))
            #raise RuntimeError( "BioFormats failed: %s" % '.'.join(command) )      
    return ofnm 


################################################################################
# Info
################################################################################  

#This command will give you the "core" metadata (width, height, number of planes, etc.), 
#the original metadata as a list of key/value pairs, and the converted OME-XML:
#showinf -nopix -omexml
#If you don't want the original metadata to be displayed, add the '-nometa' option.

#$ ./showinf.bat -nopix -nometa "13_1.lsm"
#Checking file format [Zeiss Laser-Scanning Microscopy]
#Initializing reader
#        Removing thumbnails
#        Reading LSM metadata
#Initialization took 0.152s
#
#Reading core metadata
#Filename = 13_1.lsm
#Series count = 1
#Series #0 :
#        Image count = 61
#        RGB = true (2)
#        Interleaved = false
#        Indexed = false
#        Width = 512
#        Height = 512
#        SizeZ = 61
#        SizeT = 1
#        SizeC = 2 (effectively 1)
#        Thumbnail size = 128 x 128
#        Endianness = motorola (big)
#        Dimension order = XYCZT (uncertain)
#        Pixel type = uint16
#        Metadata complete = false
#        Thumbnail series = false

def info(ifnm, original=None):
    '''returns the dict with file info'''
    if not os.path.exists(ifnm): 
        return {}   
    if not is_installed: 
        return {}

    if original is None:
        command = [BFINFO, '-nopix', '-nometa', ifnm]
    else:
        command = [BFINFO, '-nopix', '-nometa', '-map', ifnm, original ]
        
    log.debug('Info for: %s'%(ifnm) )
    with Locks(ifnm):
        o = run_command( command )
    if o is None: return {}

    bfmap = { 'Image count': 'image_num_p', 
              'Width': 'image_num_x', 
              'Height': 'image_num_y', 
              'SizeZ': 'image_num_z', 
              'SizeT': 'image_num_t', 
              'SizeC': 'image_num_c', 
              'Dimension order': 'dimensions' }
    
    rd = { 'image_num_z': 1, 
           'image_num_t': 1, 
           'image_num_p': 1 }
    
    in_series = False
    for line in o.splitlines():
        if not line: continue
        line = line.strip()
        
        if line.startswith('Checking file format ['):
            rd['format'] = line.replace('Checking file format [', '').replace(']', '')
            continue

        if line.startswith('Series count = '):
            val = line.replace('Series count = ', '')
            try:
                rd['image_num_series'] = int(val)
            except ValueError:
                pass            
            continue

        if line.startswith('Series #0'):
            in_series = True
            continue

        if line.startswith('Series #1'):
            break
          
        if not in_series: continue
          
        try:        
            tag, val = [ l.strip(' \n') for l in line.split('=',1) ]
        except:
            break

        if not tag in bfmap: 
            continue
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
        rd[bfmap[tag]] = val

    if len(rd)<4: return {}
    if rd['image_num_p']>1 and rd['image_num_z']<=1 and rd['image_num_t']<=1:
        rd['image_num_t'] = rd['image_num_p']

    return rd

