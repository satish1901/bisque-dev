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

import logging
log = logging.getLogger('bq.image_service.misc')


################################################################################
# Misc
################################################################################

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

def run_command(command):
    '''returns a string of a successfully executed command, otherwise None'''
    try:
        p = Popen (command, stdout=PIPE, stderr=PIPE)
        o,e = p.communicate()
        if p.returncode!=0:
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
