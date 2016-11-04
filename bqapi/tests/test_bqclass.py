from lxml import etree
from bqapi.bqclass import BQFactory


X="""
<resource>
<image uri="/is/1">
<tag name="filename" value="boo"/>
<tag name="xxx" value="yyy"/>
</image>
</resource>
"""




def test_conversion(session):
    'test simple xml conversions'
    print "ORIGINAL"
    print X

    factory = BQFactory(session)

    r = factory.from_string(X)
    print "PARSED"

    x = factory.to_string (r)

    print "XML"
    print r
    assert x == X.translate(None, '\r\n')
