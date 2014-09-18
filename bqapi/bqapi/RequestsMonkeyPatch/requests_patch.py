import numpy
import requests
import requests.packages.urllib3 as urllib3
import email.utils
import mimetypes
from requests.packages.urllib3.packages import six
import warnings
from monkeypatch import *



requests_v = [int(s) for s in requests.__version__.split('.')]

if requests_v < [2, 4, 0] or requests_v > [2, 4, 1]:
    warnings.warn("""\
We need to patch requests 2.4.0 up to 2.4.2, make sure your version of requests
needs patching, greater than 2.4.1 we do know if this patch applys"""
                  )
#elif requests_v > [3, 0, 0]:
#    #does not require this patch
#    pass
else:
    @monkeypatch_method(urllib3.fields)
    def format_header_param(name, value):
        """
        Helper function to format and quote a single header parameter.
    
        Particularly useful for header parameters which might contain
        non-ASCII values, like file names. This follows RFC 2231, as
        suggested by RFC 2388 Section 4.4.
    
        :param name:
            The name of the parameter, a string expected to be ASCII only.
        :param value:
            The value of the parameter, provided as a unicode string.
        """
        if not any(ch in value for ch in '"\\\r\n'):
            result = '%s="%s"' % (name, value)
            try:
                result.encode('ascii')
            except UnicodeEncodeError:
                pass
            else:
                return result
        if not six.PY3:  # Python 2:
            value = value.encode('utf-8')
            
        value = '%s="%s"; %s*=%s' % (
            name, value.decode('utf-8'),
            name, email.utils.encode_rfc2231(value, 'utf-8'),
        )
        return value

