

from http import *

from lxml import etree


url = 'http://hammer.ece.ucsb.edu:8080/ome/images?limit=3'
# view=[count, full, deep, normal] normal
# limit 
# offset
# 

head, content = request (url, userpass=('admin','admin'))

if head['status'] == '200':
    print content
    xml = etree.XML (content)
    for node in xml:
        print node.tag, str (dict (node.attrib))




