# -*- mode: python -*-
"""Main server for graph}
"""
import os
import logging
import pkg_resources
from lxml import etree

from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates
from bq.core.service import ServiceController

from bq import data_service
from bq.util.hash import is_uniq_code


log = logging.getLogger("bq.graph")
class graphController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "graph"

    def __init__(self, server_url):
        super(graphController, self).__init__(server_url)

    @expose(content_type="text/xml")
    def index(self, **kw):
        """Add your first page here.. """

        query=kw.pop('query', None)
        if not query:
            return "No query"

        nodes = set()
        edges = set()
        checked = set()
        unchecked = []
        unchecked.append (query)
        response = etree.Element('graph', value=query)
        while unchecked:
            node = unchecked.pop(0)
            # Find everybody this node points to:
            xnode = data_service.resource_load (uniq=node,view='deep')
            node_type = xnode.tag
            if node_type == 'resource':
                node_type = xnode.get ('resource_type') or xnode.tag
            nodes.add( (node, node_type) )
            checked.add (node)
            points_to_list = [ x.rsplit('/',1)[1] for x in xnode.xpath('//@value') if x.startswith("http") ]
            log.debug ("points_to_list %s", points_to_list)
            for xlink in points_to_list:
                if is_uniq_code (xlink):
                    log.debug ("ADDING OUT EDGE : %s" % str( (node, xlink) ))
                    edges.add( (node, xlink) )


            # Find nodes that point to me
            siblings = data_service.query (None,tag_query='"*/%s"' % node)
            for snode in siblings:
                log.debug ("sibling %s", etree.tostring (snode))
                sibling_uniq = snode.get ('resource_uniq')
                log.debug ("ADDING IN EDGE : %s" % str ((sibling_uniq, node)))
                edges.add ( (sibling_uniq, node) )
                if sibling_uniq not in checked:
                    unchecked.append(sibling_uniq)
            log.debug ( "Nodes : %s, Edges : %s" % (nodes, edges) )

        for node in nodes:
            etree.SubElement (response, 'node', value = node[0], type=node[1])
        for edge in edges:
            etree.SubElement (response, 'edge', value = "%s:%s" % edge)
        return etree.tostring (response)


def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  graphController(uri)
    #directory.register_service ('graph', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("graph")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'graph', 'public'))]

def get_model():
    from bq.graph import model
    return model

__controller__ =  graphController
