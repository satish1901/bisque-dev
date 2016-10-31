from lxml import etree
from bqapi.bqclass import BQFactory


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

    r = BQFactory.from_string(X)

    print "PARSED"
    print x

    r = BQFactory.to_string (x)

    print "XML"
    print r
