# imgcnv.py
# Author: Dmitry Fedorov and Kris Kvilekval
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" Functions to call BioImageConvert command line tools.
"""

__module__    = "imgcnv"
__author__    = "Dmitry Fedorov and Kris Kvilekval"
__version__   = "1.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


import os
from lxml import etree
from subprocess import Popen, call, PIPE
from locks import Locks

import logging
log = logging.getLogger('bq.image_service.imgcnv')

IMGCNV='imgcnv'
        
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
        raise Exception('imgcnv is too old, cannot procede')
    inst_ver = inst.split('.')
    need_ver = needed.split('.')
    if int(inst_ver[0])<int(need_ver[0]) or int(inst_ver[1])<int(need_ver[1]): 
        log.error('Imgcnv needs update! Has: '+inst+' Needs: '+needed)                  
        raise Exception('Imgcnv needs update! Has: '+inst+' Needs: '+needed)            

def installed_formats():
    return Popen ([IMGCNV,'-fmtxml'], stdout=PIPE).communicate()[0]

def supported(ifnm):
    log.debug('IMGCNV: supported for: %s'%ifnm )
    # dima: there will be an error here if the file name is in unicode, mitigate until teh real fix
    try:
        ifnm.encode('ascii')
    except UnicodeEncodeError:
        ifnm = ifnm.encode('utf8')
    with Locks (ifnm):
        supported = Popen ([IMGCNV, '-supported', '-i', ifnm],stdout=PIPE).communicate()[0]

    return supported.startswith('yes')


def convert(ifnm, ofnm, fmt, extra=''):
    '''return list of output filenames'''
    with Locks(ifnm, ofnm) as l:
        if not l.locked:
            return 

        command = [IMGCNV, '-i', ifnm, '-o', ofnm, '-t', fmt]
        command.extend (extra.split())

        command_line = " ".join(command) 
        log.debug('IMGCNV: %s ' % command_line)
        retcode = call (command)
        if retcode != 0:
            log.debug ("IMGCNV:  returned %s" % retcode)
        #raise RuntimeError ("IMGCNV failed: %s" % command_line)

    return

def convert_list(ifnl, ofnm, fmt, extra=''):
    '''return list of output filenames'''
    log.debug('IMGCNV: convertlist for: '+str(ifnl) )
    command = [ IMGCNV ] 
    #ifnm = ''
    for fn in ifnl:
    #    ifnm = ifnm + ' -i ' + fn
        command.extend ( [ '-i', fn] )

    with Locks(ifnl[0], ofnm) as l:
        if not l.locked:
            return
        command.extend ( [ '-o', ofnm, '-t', fmt] )
        command.extend (extra.split())
        log.debug('IMGCNV: %s ' % " ".join(command) )
        retcode = call (command)
    return

def info(ifnm):
    log.debug('IMGCNV: info for: '+str(ifnm) )
    with Locks(ifnm):
        info = Popen ([IMGCNV, '-info', '-i', ifnm], stdout=PIPE).communicate()[0]

    rd = {} 
    for line in info.splitlines():
        if not line: continue
        #log.debug('line: '+unicode(line) )
        try:        
            tag, val = [ l.lstrip() for l in line.split(':',1) ]
        except:
            return rd
        val = val.replace('\n', '')
        rd[tag] = val
        try:
            rd[tag] = float(val)
        except ValueError:
            pass
        try:
            rd[tag] = int(val)
        except ValueError:
            pass
            
    if len(rd) < 1: return rd
    if not 'zsize' in rd: rd['zsize'] = 1
    if not 'tsize' in rd: rd['tsize'] = 1    
    if not 'pages' in rd: rd['pages'] = 1        
    if rd['zsize']==1 and rd['tsize']==1 and rd['pages']>1:
    	  rd['tsize'] = rd['pages']
        
    return rd
    
def isTiff(ifnm):
    log.debug('IMGCNV: isTiff for: '+str(ifnm) )
    with Locks (ifnm):
        info = Popen ([IMGCNV, '-info','-i',ifnm], stdout=PIPE).communicate()[0]

    rd = {} 
    for line in info.splitlines():
        if not line: continue
        if line == 'Input format is not supported': break          
        try:
            tag, val = [ l.lstrip() for l in line.split(':', 1) ]
            rd[tag] = val
        finally:
            pass
    
    if 'format' not in rd:
        return False
    return 'tiff' in rd['format'].lower()

def formats():
    return formatList()

def formatListRead():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for format in root:
      for codec in format:
        for tag in codec:
          if tag.attrib["name"]=='support' and tag.attrib["value"]=='reading': 
            fmts.append( codec.attrib["name"].lower() )  
    return fmts    

def formatList():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for format in root:
      for codec in format:
        fmts.append( codec.attrib["name"].lower() )  
    return fmts   

def formatListWrite():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for format in root:
      for codec in format:
        for tag in codec:
          if tag.attrib["name"]=='support' and tag.attrib["value"]=='writing': 
            fmts.append( codec.attrib["name"].lower() )  
    return fmts    
 

def formatListWriteMultiPage():
    fmts = []
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for format in root:
      for codec in format:
        for tag in codec:
          if tag.attrib["name"]=='support' and tag.attrib["value"]=='writing multiple pages': 
            fmts.append( codec.attrib["name"].lower() )  
    return fmts    
    
def defaultExtension(formatName):
    formatName = formatName.lower()  
    ext = ''
    xml = Popen ([IMGCNV, '-fmtxml'], stdout=PIPE).communicate()[0]
    xml = "<formats>\n" + xml + "\n</formats>\n"
    root = etree.fromstring( xml )
    for format in root:
      for codec in format:
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
        rd[tag] = val
        
        try:
            rd[tag] = float(val)
        except ValueError:
            pass
        try:
            rd[tag] = int(val)
        except ValueError:
            pass
    
    metatxt = ''
    for line in rmeta.splitlines():
        if not line: continue
        if line == '\n': continue
        metatxt += line
    rd['raw_metadata'] = metatxt  
     
    if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
    	  rd['image_num_t'] = rd['image_num_p']
        
    return rd    


