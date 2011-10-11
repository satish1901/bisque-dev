# -*- coding: utf-8 -*-

"""The application's Globals object"""

__all__ = ['Globals']

import tgscheduler
from turbomail.adapters import tm_pylons

class Globals(object):
    """Container for objects available throughout the life of the application.

    One instance of Globals is created during application initialization and
    is available during requests via the 'app_globals' variable.

    """

    def __init__(self):
        """Do nothing, by default."""
        self.services = '';
        tgscheduler.start_scheduler()
        tm_pylons.start_extension()
