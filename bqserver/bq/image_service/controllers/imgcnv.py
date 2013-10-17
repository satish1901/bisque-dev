# imgcnv.py
# Author: Dmitry Fedorov and Kris Kvilekval
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" Functions to call BioImageConvert command line tools.
"""

__module__    = "imgcnv"
__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "1.2"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


#import os
from lxml import etree
from subprocess import Popen, call, PIPE
from locks import Locks

import logging
log = logging.getLogger('bq.image_service.imgcnv')

IMGCNV = 'imgcnv'

# runtime defined variables
format_list = [] # this is updated later

        
################################################################################
# imgcnv interface
################################################################################

def installed ():
    imgcnvfmt = Popen ([IMGCNV, '-fmt'],stdout=PIPE).communicate()[0]
    for line in imgcnvfmt.splitlines():
        if not line: continue
        return line.startswith( 'Format 0:' )

def version ():
    imgcnvver = Popen ([IMGCNV, '-v'],stdout=PIPE).communicate()[0]
    for line in imgcnvver.splitlines():
        if not line or line.startswith('Input'): return False
        return line.replace('\n', '')
        
def check_version ( needed ):
    # check the version
    inst = version()
    if not inst:            
        raise Exception('imgcnv is too old, cannot proceed')
    inst_ver = inst.split('.')
    need_ver = needed.split('.')
    if int(inst_ver[0])<int(need_ver[0]) or int(inst_ver[1])<int(need_ver[1]): 
        log.error('Imgcnv needs update! Has: %s Needs: %s'%(inst, needed))                  
        raise Exception('Imgcnv needs update! Has: %s Needs: %s'%(inst, needed))            

def installed_formats():
    return Popen ([IMGCNV,'-fmtxml'], stdout=PIPE).communicate()[0]

def supported(ifnm):
    log.debug('Supported for: %s'%ifnm )
    # dima: there will be an error here if the file name is in unicode, mitigate until teh real fix
    try:
        ifnm.encode('ascii')
    except UnicodeEncodeError:
        ifnm = ifnm.encode('utf8')
    with Locks (ifnm):
        supported = Popen ([IMGCNV, '-supported', '-i', ifnm],stdout=PIPE).communicate()[0]

    return supported.startswith('yes')


def convert(ifnm, ofnm, fmt=None, extra=[]):
    '''return list of output filenames'''
    with Locks(ifnm, ofnm) as l:
        if not l.locked:
            return 
        command = [IMGCNV, '-i', ifnm]
        if ofnm is not None:
            command.extend (['-o', ofnm])
        if fmt is not None:
            command.extend (['-t', fmt])
        command.extend (extra)
        cmds = " ".join(command)
        log.debug('Convert command: [%s]'% cmds) 
        retcode = call (command)
        if retcode != 0:
            log.error ('Error: [%s] returned [%s]'%(cmds, retcode))

def convert_list(ifnl, ofnm, fmt, extra=''):
    '''return list of output filenames'''
    log.debug('Convertlist for: %s'%(ifnl))
    command = [ IMGCNV ] 
    for fn in ifnl:
        command.extend(['-i', fn])

    with Locks(ifnl[0], ofnm) as l:
        if not l.locked:
            return
        command.extend ( [ '-o', ofnm, '-t', fmt] )
        command.extend (extra.split())
        cmds = ' '.join(command)
        log.debug('Convertlist command: %s'%cmds)
        retcode = call (command)
        if retcode != 0:
            log.error ('Error: [%s] returned [%s]'%(cmds, retcode))

info_map = { 
    'width'      : 'image_num_x', 
    'height'     : 'image_num_y', 
    'zsize'      : 'image_num_z', 
    'tsize'      : 'image_num_t',
    'channels'   : 'image_num_c',
    'pages'      : 'image_num_p',
    'format'     : 'format',
    'pixelType'  : 'image_pixel_format',
    'depth'      : 'image_pixel_depth',
    'endian'     : 'endian',
    'dimensions' : 'dimensions' }

def info(ifnm):
    log.debug('Info for: %s'%ifnm )
    with Locks(ifnm):
        info = Popen ([IMGCNV, '-info', '-i', ifnm], stdout=PIPE).communicate()[0]

    rd = {} 
    for line in info.splitlines():
        if not line: continue
        try:        
            tag, val = [ l.lstrip() for l in line.split(':',1) ]
        except:
            return rd
        if tag not in info_map: 
            continue
        else:
            tag = info_map[tag]
        val = val.replace('\n', '')
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
        rd[tag] = val        

    if len(rd)<1: return rd
    if not 'image_num_z' in rd: rd['image_num_z'] = 1
    if not 'image_num_t' in rd: rd['image_num_t'] = 1    
    if not 'image_num_p' in rd: rd['image_num_p'] = 1        
    if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
        rd['image_num_t'] = rd['image_num_p']
    return rd
    
def isTiff(ifnm):
    log.debug('isTiff for: %s'%(ifnm) )
    rd = info(ifnm)
    return 'tiff' in rd.get('format','').lower()

def formats():
    return format_list

def formatListRead():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for frmt in root:
        for codec in frmt:
            for tag in codec:
                if tag.attrib["name"]=='support' and tag.attrib["value"]=='reading': 
                    fmts.append( codec.attrib["name"].lower() )  
    return fmts    

def formatList():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for frmt in root:
        for codec in frmt:
            fmts.append( codec.attrib["name"].lower() )  
    return fmts   

if len(format_list)<1:
    format_list = formatList()

def formatListWrite():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for frmt in root:
        for codec in frmt:
            for tag in codec:
                if tag.attrib["name"]=='support' and tag.attrib["value"]=='writing': 
                    fmts.append( codec.attrib["name"].lower() )  
    return fmts    
 

def formatListWriteMultiPage():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for frmt in root:
        for codec in frmt:
            for tag in codec:
                if tag.attrib["name"]=='support' and tag.attrib["value"]=='writing multiple pages': 
                    fmts.append( codec.attrib["name"].lower() )  
    return fmts    
    
def defaultExtension(formatName):
    formatName = formatName.lower()  
    ext = ''
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring(xml)
    for frmt in root:
        for codec in frmt:
            if codec.attrib["name"].lower()==formatName:
                for tag in codec:
                    if tag.attrib["name"]=='extensions': 
                        ext = tag.attrib["value"]
                        exts = ext.split('|')
                        ext = exts[0]
    return ext    

def canWriteMultipage(formatName):
    fmts = formatListWriteMultiPage()
    formatName = formatName.lower()
    if (formatName in fmts): return True
    return False

def meta(ifnm):
    log.debug('Meta file: ' + ifnm )
    rd = {} 

    with Locks (ifnm):
        meta = Popen ([IMGCNV, '-meta', '-i', ifnm], stdout=PIPE).communicate()[0]
        rmeta= Popen ([IMGCNV, '-rawmeta', '-i', ifnm], stdout=PIPE).communicate()[0]

    for line in meta.splitlines():
        if not line: continue
        try:
            tag, val = [ l.lstrip() for l in line.split(':', 1) ]
        except:
            continue
        val = val.replace('\n', '')
        try:
            val = float(val)
        except ValueError:
            pass
        rd[tag] = val        
    
    metatxt = ''
    for line in rmeta.splitlines():
        if not line: continue
        if line == '\n': continue
        metatxt += line
    rd['raw_metadata'] = metatxt  
     
    if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
        rd['image_num_t'] = rd['image_num_p']
        
    return rd    


