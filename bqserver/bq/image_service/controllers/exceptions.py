"""
Provides typical exceptions thrown by the image service
"""

__author__    = "Dmitry Fedorov"
__version__   = "1.0"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import sys
import logging


################################################################################
# Exceptions
################################################################################

class ImageServiceException(Exception):
    """Raised when any operation or decoder fails

    Attributes:
        code: Response error code, same as HTTP response code
        message: String explaining the exact reason for the failure
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message