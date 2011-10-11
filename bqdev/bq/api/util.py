import os
import shutil
import urllib
import poster
import time

from lxml import etree as ET
from xmldict import xml2d, d2xml
from bqclass import fromXml, toXml, BQMex


def safecopy (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            print ("linking %s to %s"%(f,dest))
            if os.path.exists(dest):
                print ("Found existing file %s: removing .." % dest)
                os.unlink (dest)
            os.link(f, dest)
        except (OSError, AttributeError), e:
            print ("Problem in link %s .. trying copy" % e)
            shutil.copy2(f, dest)

def parse_qs(query):
    'parse a uri query string into a dict'
    pd = {}
    for el in query.split('&'):
        nm, junk, vl = el.partition('=')
        pd.setdefault(nm, []).append(vl)
    return pd

def make_qs(pd):
    'convert back from dict to qs'
    query = []
    for k,vl in pd.items():
        for v in vl:
            pair = v and "%s=%s" % (k,v) or k
            query.append(pair)
    return "&".join(query)




def fetch_image_planes(session, uri, dest, uselocalpath=False):
    'fetch all the image planes of an image locally'
    image = session.load (uri)
    tplanes = int(image.t)
    zplanes = int(image.z)

    planes=[]
    for t in range(tplanes):
        for z in range(zplanes):
            ip = image.pixels().slice(z=z+1,t=t+1).format('tiff')
            if uselocalpath:
                ip = ip.localpath()
            planes.append (ip)

    files = []
    for i, p in enumerate(planes):
        slize = p.fetch()
        fname = os.path.join (dest, "%.5d.tif" % i)
        if uselocalpath:
            path = ET.XML(slize).xpath('/resource/@src')[0]
            safecopy (path, fname)
        else:
            f = open(fname, 'wb')
            f.write(slize)
            f.close()
        files.append(fname)

    return files

def fetch_image_pixels(session, uri, dest, uselocalpath=False):
    image = session.load (uri)
    ip = image.pixels().format('tiff')
    if uselocalpath:
        ip = ip.localpath()
    pixels = ip.fetch()
    if os.path.isdir(dest):
        dest = os.path.join (dest, "0.tif")

    if uselocalpath:
        path = ET.XML(pixels).xpath('/resource/@src')[0]
        path = urllib.url2pathname(path[5:])
        # Skip 'file:'
        safecopy (path, dest)
        return { uri : dest }
    f = open(dest, 'wb')
    f.write(pixels)
    f.close()
    return { uri : dest }
            

def fetch_dataset(session, uri, dest, uselocalpath=False):
    dataset = session.fetchxml (uri, view='deep')
    members = dataset.xpath('//value[@type="object"]')

    results = { }
    for i, imgxml in enumerate(members):
        uri =  imgxml.text   #imgxml.get('uri')
        print "FETCHING", uri
        fname = os.path.join (dest, "%.5d.tif" % i)
        fetch_image_pixels (session, uri,
                            fname, uselocalpath=uselocalpath)
        results[uri] = fname
    return results
        
        
def fetchImage(session, uri, dest, uselocalpath=False):
    
    image = session.load(uri).pixels().getInfo()
    fileName = ET.XML(image.fetch()).xpath('//tag[@name="filename"]/@value')[0]
    
    ip = session.load(uri).pixels().format('tiff')

    if uselocalpath:
        ip = ip.localpath()
    
    pixels = ip.fetch()
    
    if os.path.isdir(dest):
        dest = os.path.join (dest, fileName)

    if uselocalpath:
        path = ET.XML(pixels).xpath('/resource/@src')[0]
        path = urllib.url2pathname(path[5:])

        # Skip 'file:'
        safecopy (path, dest)
        return { uri : dest }
    f = open(dest, 'wb')
    f.write(pixels)
    f.close()
    return { uri : dest }

            
def fetchDataset(session, uri, dest, uselocalpath=False):
    dataset = session.fetchxml(uri, view='deep')
    members = dataset.xpath('//value[@type="object"]')
    results = {}
    
    for i, imgxml in enumerate(members):
        uri = imgxml.text
        print "FETCHING: ", uri
        #fname = os.path.join (dest, "%.5d.tif" % i)
        result = fetchImage(session, uri, dest, uselocalpath=uselocalpath)
        results[uri] = result[uri]
    return results

            
# Post fields and files to an http host as multipart/form-data.
# fields is a sequence of (name, value) elements for regular form
# fields.  files is a sequence of (name, filename, value) elements
# for data to be uploaded as files
# Return the tuple (rsponse headers, server's response page)

# example:
#   post_files ('http://..',
#   fields = {'file1': open('file.jpg','rb'), 'name':'file' })
#   post_files ('http://..', fields = [('file1', 'file.jpg', buffer), ('f1', 'v1' )] )  

def save_image_pixels(session,  localfile, image_tags=None):
    """put a local image on the server and return the URL
    to the METADATA XML record

    @param session: the local session
    @param image: an BQImage object
    @param localfile:  a file-like object or name of a localfile
    @return XML content  when upload ok
    """
    url = session.service_url('client_service', 'upload_images')
    
    if isinstance(localfile, basestring):
        localfile = open(localfile,'rb')
    with localfile:
        fields = { 'file' : localfile}
        if image_tags:
            fields['file_tags'] = etree.tostring(toXml(image_tags))
        body, headers = poster.encode.multipart_encode(fields)
        content = session.c.post(url, headers=headers, content=body)
    return content


    
