# -*- coding: utf-8 -*-

"""The application's Globals object"""

__all__ = ['Globals']

try:
    from turbomail.adapters import tm_pylons
    has_turbomail = True
except ImportError:
    has_turbomail = False

class Globals(object):
    """Container for objects available throughout the life of the application.

    One instance of Globals is created during application initialization and
    is available during requests via the 'app_globals' variable.

    """

    def __init__(self):
        """Do nothing, by default."""
        self.services = '';
        if has_turbomail:
            tm_pylons.start_extension()
