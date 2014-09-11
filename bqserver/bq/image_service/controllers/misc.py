# misc.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" miscellaneous functions for Image Service and COmmand Line Converters
"""

__module__    = "misc"
__author__    = "Dmitry Fedorov"
__version__   = "0.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

from subprocess import Popen, PIPE
import os
import ctypes
import tempfile
import hashlib
import datetime
from itertools import groupby

from bq.util.mkdir import _mkdir

import logging
log = logging.getLogger('bq.image_service.misc')


################################################################################
# Misc
################################################################################

def blocked_alpha_num_sort(s):
    return [int(u''.join(g)) if k else u''.join(g) for k, g in groupby(unicode(s), unicode.isdigit)]

def between(left,right,s):
    _,_,a = s.partition(left)
    a,_,_ = a.partition(right)
    return a

def xpathtextnode(doc, path, default='', namespaces=None):
    r = doc.xpath(path, namespaces=namespaces)
    if len(r)<1:
        return default
    else:
        return r[0].text

def safeint(s, default=0):
    try:
        v = int(s)
    except ValueError:
        v = default
    return v

def safefloat(s, default=0.0):
    try:
        v = float(s)
    except ValueError:
        v = default
    return v

def safetypeparse(v):
    try:
        v = int(v)
    except ValueError:
        try:
            v = float(v)
        except ValueError:
            pass
    return v

def safeencode(s):
    if isinstance(s, unicode) is not True:
        return str(s)
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        s = s.encode('utf8')
    return s

def toascii(s):
    if isinstance(s, unicode) is not True:
        return s
    return s.encode('ascii', 'replace')

def run_command(command):
    '''returns a string of a successfully executed command, otherwise None'''
    try:
        p = Popen (command, stdout=PIPE, stderr=PIPE)
        o,e = p.communicate()
        if p.returncode!=0:
            log.info ("BAD non-0 return code for %s", command)
            return None
        # Qt reports an error: 'Qt: Untested Windows version 6.2 detected!\r\n'
        #if e is not None and len(e)>0:
        #    return None
        return o
    except OSError:
        log.warning ('Command not found [%s]', command[0])
    except:
        log.exception ('Exception during execution [%s]', command )
    return None

def isascii(s):
    if isinstance(s, str) is True:
        return True
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        return False
    return True

# dima: We have to do some ugly stuff to get all unicode filenames to work correctly 
# under windows, although imgcnv and ImarisConvert support unicode filenames
# bioformats and openslide do not, moreover in python <3 subprocess package 
# does not support unicode either, thus we decided to link unicode filenames
# prior to operations and unlink them right after, this is a windows only problem!
if os.name != 'nt':
    def dolink(source, link_name):
        log.debug('Hard link %s -> %s', source, link_name)
        #return os.symlink(source, link_name)
        return os.link(source, link_name)
    
    def start_nounicode_win(ifnm, command):
        return command, None
    
    def end_nounicode_win(tmp):
        pass
    
else:
    def hardlink(source, link_name):
        source = unicode(os.path.normpath(source))
        link_name = unicode(os.path.normpath(link_name))
        csl = ctypes.windll.kernel32.CreateHardLinkW
        if csl(link_name, source, 0) == 0:
            raise ctypes.WinError()
    
    def dolink(source, link_name):
        log.debug('Hard link %s -> %s', source, link_name)        
        return hardlink(source, link_name)
    
    def start_nounicode_win(ifnm, command):
        if isascii(ifnm):
            return command, None
        ext = os.path.splitext(ifnm)[1]
        uniq = hashlib.md5('%s%s'%(ifnm.encode('ascii', 'xmlcharrefreplace'),datetime.datetime.now())).hexdigest()
        tmp_path = '%s\\temp'%os.path.splitdrive(ifnm)[0] 
        
        # preserve drive letter to create hard link on the same drive
        # dima: os.path.join does not join drive letters correctly
        tmp_path = os.path.splitdrive(ifnm)[0]
        if tmp_path != '':
            tmp_path = '%s\\temp'%tmp_path
        _mkdir(tmp_path)
        tmp = os.path.join(tmp_path, '%s%s'%(uniq, ext))
        
        #tmp = '%s%s'%(uniq, ext) # dima: same drive as running system - may not work
        log.debug('start_nounicode_win hardlink: [%s] -> [%s]', ifnm, tmp)
        try:
            hardlink(ifnm, tmp)
        except OSError:
            return command, None
        command = [tmp if x==ifnm else x for x in command]
        return command, tmp
    
    def end_nounicode_win(tmp):
        if tmp is None:
            return
        log.debug('end_nounicode_win unlink: [%s]', tmp)
        try:
            os.remove(tmp) # gets the system into a dark state of recursion?
        except OSError:
            log.warning('Could not remove temp link: %s', tmp)
            pass

