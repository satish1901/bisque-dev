# -*- coding: utf-8 -*-

"""WebHelpers used in bqcore."""

from webhelpers import date, feedgenerator, html, number, misc, text
from paste.deploy.converters import asbool

import bq
def add_global_tmpl_vars ():
    #log.debug ("add_global_tmpl_vars")
    #return dict (widgets = widgets)
    return dict(
        bq = bq,
        asbool = asbool
#         c = dict (
#         commandbar_enabled = True,
#         datasets_enabled =False,
#         organizer_enabled = False,
#         search_enabled = False,
#         analysis_enabled = False,
#         visualization_enabled = False,
#         upload_enabled = False    ,
#             )
        )
