
from lxml import etree
import http
import httplib

def new_image (url, tags):
    image = etree.Element('image')
    image.attrib['url'] = url
    for k,v in tags.items():
        etree.SubElement(image, 'tag', name=k, value=v)

    http.xmlrequest ('flour.ece.ucsb.edu:8080/bisquik/upload_file',
                     'POST',
                     etree.tostring(image))
    



new_image('http://aaa', { 'filename': 'aaa' })


    
