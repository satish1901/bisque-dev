###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################

"""
Statistics operatiors : map a vector of object into a vector of strings or numbers

DESCRIPTION
===========

 2) MAP: [vector of objects -> uniform vector of numbers or strings]
    An operator is applied onto the vector of objects to produce a vector of numbers or strings
    The operator is specified by the user and can take specific elements and produces specific result
    for example: operator "area" could take polygon or rect and produce a number
                 operator "numeric-value" can take a "tag" and return tag's value as a number
                 possible operator functions should be extensible and maintained by the stat service

EXTENSIONS
===========

Operations are added by simply deriving from StatOperator and adding your code here

"""

__module__    = "statistics_service.py"
__author__    = "Dmitry Fedorov"
__version__   = "1.0"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

from lxml import etree
import sys
import math
import logging

from bqapi import *

log = logging.getLogger('bisquik.SS.operators')

__all__ = [ 'StatOperator' ] 

################################################################################
# Base class for operators
################################################################################

class StatOperator (object):
    '''Maps vector of objects into a vector of numbers or strings''' 
    name = "StatOperator"  
    version = '1.0'
    def __init__(self):
        #self.server = server
        pass

    def __call__(self, v_in, **kw):
        return self.do_map(v_in, **kw) 
        
    def do_map(self, v_in, **kw):
        # this one does nothing really                 
        return v_in

################################################################################
# Tag Operator implementations
################################################################################       

class StatOperatorTagName (StatOperator):
    '''maps tags into a vector of their names as strings''' 
    name = 'tag-name-string'
    version = '1.1'        
    def do_map(self, v_in, **kw):
        def nameSafe(t): return t.get('name', '')
        return map(nameSafe, v_in)

class StatOperatorTagValue (StatOperator):
    '''maps tags into a vector of their values as strings''' 
    name = 'tag-value-string'
    version = '1.1'        
    def do_map(self, v_in, **kw):
        def valueSafe(t): 
            v = BQValue(element=t)
            return v.toString()
        return map(valueSafe, v_in)
        
class StatOperatorTagNameNumeric (StatOperator):
    '''maps tags into a vector of their names as numbers''' 
    name = 'tag-name-number'
    version = '1.0'        
    def do_map(self, v_in, **kw):
        def intValueSafe(t):
            try:
                return float(t.attrib['name'])
            except:
                return None
        return map(intValueSafe, v_in)
        
class StatOperatorTagValueNumeric (StatOperator):
    '''maps tags into a vector of their values as numbers''' 
    name = 'tag-value-number'
    version = '1.1'        
    def do_map(self, v_in, **kw):
        def intValueSafe(t):
            v = BQValue(element=t)
            try:
                return float(v.toString())
            except:
                return None
        return map(intValueSafe, v_in)
        

################################################################################
# Gob Operator primitives
################################################################################       

# TODO:
# GObjects:
# point polyline polygon circle ellipse square rectangle 
#
# Features:
# length, perimeter, area, major axis, minor axis

def gobNumber(gob):
    # return just the object itself right now
    return 1

def gobType(gob):
    return str(BQFactory.make(gob).getAttr('type'))
    
def gobName(gob):
    return str(BQFactory.make(gob).getAttr('name'))

def gobPerimeter(gob):
    return BQFactory.make(gob).perimeter()

def gobArea(gob):
    return BQFactory.make(gob).area()
    
#-------------------------------------------------------------------------------
# Gob Operator implementations
#-------------------------------------------------------------------------------       

class StatOperatorGobName (StatOperator):
    '''maps GObjects into a vector of their names''' 
    name = 'gobject-name'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobName, v_in)
        
class StatOperatorGobType (StatOperator):
    '''maps GObjects into a vector of their types''' 
    name = 'gobject-type'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobType, v_in)

class StatOperatorGobTypePrimitive (StatOperator):
    '''returns only present primitive types''' 
    name = 'gobject-type-primitive'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        t = map(gobType, v_in)
        return [i for i in t if i in gobject_primitives]

class StatOperatorGobTypeComposed (StatOperator):
    '''maps GObjects into a vector of their types''' 
    name = 'gobject-type-composed'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        t = set( map(gobType, v_in) )      
        return [i for i in t if not i in gobject_primitives]


class StatOperatorGobLength (StatOperator):
    '''maps GObjects into a vector of their perimeters or lengths''' 
    name = 'gobject-length'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobPerimeter, v_in)

class StatOperatorGobPerimeter (StatOperator):
    '''maps GObjects into a vector of their perimeters or lengths''' 
    name = 'gobject-perimeter'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobPerimeter, v_in)

class StatOperatorGobArea (StatOperator):
    '''maps GObjects into a vector of their areas''' 
    name = 'gobject-area'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobArea, v_in)

class StatOperatorGobNumber (StatOperator):
    '''maps GObjects into a vector of their number, each number is object + children''' 
    name = 'gobject-number'
    version = '1.0'    
    def do_map(self, v_in, **kw):
        return map(gobNumber, v_in)





