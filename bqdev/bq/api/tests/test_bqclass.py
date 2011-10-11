from lxml import etree
from bqapi.bqclass import fromXml, toXml


X="""
<resource >
<image uri="/is/1" x="100" y="100">
<tag name="filename" value="boo"/>
<tag name="xxx" value = "yyy"/>
</image>
</resource>
"""


def test_conversion():
    'test simple xml conversions'
    print "ORIGINAL"
    print X

    r = etree.XML(X)
    x = fromXml(r)
    
    print "PARSED"
    print x
    
    r = toXml(x)
    
    print "XML"
    print etree.tostring (r)
