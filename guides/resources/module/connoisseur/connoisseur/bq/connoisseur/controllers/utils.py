###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
## Copyright (c) 2017-2018 by the Regents of the University of California    ##
## Copyright (c) 2017-2018 (C) ViQi Inc                                      ##
## All rights reserved                                                       ##
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
##        software must display the following acknowledgment: This product   ##
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
Utility constants and functions for classification service
"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara, ViQi Inc"

import os
import logging
import math
import struct
import re
import shutil
import collections
from lxml import etree

import numpy as np
from PIL import Image
import skimage.io

log = logging.getLogger("bq.connoisseur.utils")

##################################################################
# constants
##################################################################

colors = [
    "#012C58", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
    "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
    "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
    "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
    "#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
    "#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
    "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
    "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",

    "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
    "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
    "#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
    "#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
    "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
    "#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
    "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
    "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58"
]


##################################################################
# classification goodness
##################################################################

# L1 distance between two numpy arrays of equal length
def dist_L1(a, b):
    return sum(abs(a-b))

# goodness estimate for a sample probability distribution
def distr_goodness (Psample, Pgood, Xbest, Xworst, dist):
    d = dist(Psample, Pgood)
    return 1.0 - ((d-Xbest)/(Xworst-Xbest))

def compute_measures (r):
    m_g = r.get('goodness', 0)
    m_a = r.get('accuracy', 0)
    m_c = r.get('confidence') or (m_a/100.0) * m_g * 100.0
    return m_g, m_a, m_c

##################################################################
# datums and image vectors
##################################################################

def datum_to_vect(datum, mu):
    x = np.fromstring(datum.data, dtype=np.uint8)
    x = x.reshape(1, datum.channels, datum.height, datum.width).squeeze().transpose((1,2,0))
    x = x.astype(np.float32) - mu # mean substraction
    #print 'Shape: %s'%str(x.shape)
    #im = Image.fromarray(x)
    #im.save( '%s_lmdb_%s_%s.png'%(key, datum.label, datetime.now().strftime('%Y%m%dT%H%M%S')) )
    return x

def datum_to_image(datum, filename):
    x = np.fromstring(datum.data, dtype=np.uint8)
    x = x.reshape(1, datum.channels, datum.height, datum.width).squeeze().transpose((1,2,0))
    #im = Image.fromarray(x)
    #im.save( filename )
    skimage.io.imsave(filename, x)

def image_to_vect(im, x, y, tw, th):
    x1 = x - tw/2
    y1 = y - th/2
    pic = im.crop((x1,y1,x1+tw,y1+th))
    pix = np.array(pic, dtype=np.float32)
    return pix

def image_patch(im, x, y, tw, th, inside=True):
    '''
    use "inside" to ensure the patch is fully contained within the image
    '''
    if inside is False:
        x1 = x - tw/2
        y1 = y - th/2
    else:
        W,H = im.shape[0:2]
        x1 = int(round(x - tw/2))
        y1 = int(round(y - th/2))
        x1 = max(0, x1)
        y1 = max(0, y1)
        x1 = min(x1, W-tw)
        y1 = min(y1, H-th)

    p = None
    if len(im.shape) == 2:
        p = im[x1:x1+tw,y1:y1+th] #.astype(np.float32)
    if len(im.shape) == 3:
        p = im[x1:x1+tw,y1:y1+th,:] #.astype(np.float32)
    return p


##################################################################
# colors
##################################################################

def get_color_html(n):
    sz = len(colors)
    if n<= sz:
        return colors[n]
    nn = sz*int(math.floor(n / float(sz)))
    return colors[n - nn]

def get_color_tuple(n):
    c = get_color_html(n)
    return struct.unpack('BBB', c.replace('#', '').decode('hex'))

def get_color_tuple_by_label(l):
    hash = 0
    for i in l:
        hash = ord(i) + ((hash << 5) - hash)
    color = [(hash >> (i*8)) & 0xFF for i in range(3)]
    if color == [0,0,0]:
        return (255,255,255)
    return color

##################################################################
# http
##################################################################

def http_parse_accept(h):
    '''
    Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8

    <MIME_type>/<MIME_subtype>
    A single, precise MIME type, like text/html.
    <MIME_type>/*
    A MIME type, but without any subtype. image/* will match image/png, image/svg, image/gif and any other image types.
    */*
    Any MIME type
    ;q= (q-factor weighting)
    Any value used is placed in an order of preference expressed using relative quality value called the weight.
    '''
    if h is None: return None
    h = re.split('[\;\,]', h.replace(' ', ''))
    h = [m for m in h if not m.startswith('q=')]
    return h if len(h)>0 else None


def http_parse_content_type(h):
    '''
    Content-Type: text/html; charset=utf-8
    Content-Type: multipart/form-data; boundary=something

    charset=
    boundary=
    '''
    if h is None: return None
    h = re.split('[\;\,]', h.replace(' ', ''))
    h = [m for m in h if not (m.startswith('charset=') or m.startswith('boundary=')) ]
    return h if len(h)>0 else None

##################################################################
# urls
##################################################################

def ensure_url(url_or_uuid):
    url = url_or_uuid
    if url.startswith('/') is not True and url.startswith('http') is not True:
        url = '/data_service/%s'%url
    return url

##################################################################
# bqapi tags
##################################################################

def safe_div(numerator, denominator, default):
    try:
        return numerator / float(denominator)
    except ZeroDivisionError:
        return default

def safe_number(v):
    try:
        v = int(v)
    except ValueError:
        try:
            v = float(v)
        except ValueError:
            pass
    except TypeError: #in case of Nonetype
        pass
    return v

def safe_boolean(v):
    try:
        v = (str(v).lower() == 'true')
    except Exception:
        v = False
    return v

def get_tag_value(tag, default=None):
    v = tag.get('value', default)
    t = tag.get('type')
    if t == 'number':
        v = safe_number(v)
    elif t == 'boolean':
        v = safe_boolean(v)
    elif t is not None and 'number' in t and 'list' in t:
        v = [ safe_number(i) for i in v.split(',')]
    elif t is not None and 'boolean' in t and 'list' in t:
        v = [ safe_boolean(i) for i in v.split(',')]
    elif t is not None and 'list' in t:
        v = v.split(',')
    return v

def set_tag_value(tag, v):
    if isinstance(v, basestring): # string
        tag.set('value', v)
    elif isinstance(v, bool): # boolean
        tag.set('value', str(v).lower())
        tag.set('type', 'boolean')
    elif isinstance(v, int) or isinstance(v, float): # number
        tag.set('value', str(v))
        tag.set('type', 'number')
    elif isinstance(v, collections.Iterable) and isinstance(v[0], bool): #boolean,list
        tag.set('value', ','.join([str(i).lower() for i in v]))
        tag.set('type', 'boolean,list')
    elif isinstance(v, collections.Iterable) and isinstance(v[0], basestring): #string,list
        tag.set('value', ','.join(v))
        tag.set('type', 'string,list')
    elif isinstance(v, collections.Iterable) and (isinstance(v[0], int) or isinstance(v[0], float)): #number,list
        tag.set('value', ','.join([str(i) for i in v]))
        tag.set('type', 'number,list')

def set_tag(resource, name, value):
    tag = resource.find('./tag[@name="%s"]'%name)
    if tag is None:
        tag = etree.SubElement(resource, 'tag', name=name)
    set_tag_value(tag, value)

##################################################################
# files and dirs
##################################################################

def safe_remove_dir_file (path):
    try:
        os.remove(path)
    except OSError:
        shutil.rmtree(path, ignore_errors=True)


