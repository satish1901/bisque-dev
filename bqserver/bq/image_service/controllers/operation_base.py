""" 
Base class for all image service operations
"""

__author__    = "Dmitry Fedorov"
__version__   = "1.0"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

################################################################################
# Operations baseclass
################################################################################

class BaseOperation(object):
    '''Provide operations base'''
    name = 'base'

    def __init__(self, server):
        self.server = server

    def __str__(self):
        return 'base: describe your service and its arguments'

    # optional method, used to generate the final file quickly
    # defined if action does convertions and not only enques its arguments
    #def dryrun(self, token, arg):
    #    return token

    # required method
    def action(self, token, arg):
        return token

