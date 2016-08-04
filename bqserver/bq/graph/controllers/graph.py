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


def _add_mex_inputs_outputs(xnode, edges, checked, unchecked):
    """
    Inputs: any ref in top "inputs" section without self-references
    Outputs: any ref in top "outputs" section without self-references or input references
    """
    node = xnode.get ('resource_uniq')
    points_to_list = [ x.rsplit('/',1)[1] for x in xnode.xpath('./tag[@name="outputs"]/tag/@value') if x.startswith("http") ]
    points_from_list = [ x.rsplit('/',1)[1] for x in xnode.xpath('./tag[@name="inputs"]/tag/@value') if x.startswith("http") ]
    log.debug ("points_to_list %s", points_to_list)
    log.debug ("points_from_list %s", points_from_list)
    for xlink in points_from_list:
        if is_uniq_code (xlink):
            # add edge unless it points to mex recursively
            if (xlink, node) not in edges and xlink != node:
                log.debug ("ADDING IN EDGE : %s" % str( (xlink, node) ))
                edges.add( (xlink, node) )
            if xlink not in checked:
                unchecked.add (xlink)
    for xlink in points_to_list:
        if is_uniq_code (xlink):
            # add edge unless it points to mex recursively or back to an input 
            if (node, xlink) not in edges and xlink != node and xlink not in points_from_list:
                log.debug ("ADDING OUT EDGE : %s" % str( (node, xlink) ))
                edges.add( (node, xlink) )
            if xlink not in checked:
                unchecked.add (xlink)

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
        resources = set()
        datasets = {}   # dataset uniq -> [ member id, member id, ... ]
        checked = set()
        unchecked = set()
        unchecked.add (query)
        response = etree.Element('graph', value=query)
        while unchecked:
            log.debug ( "graph unchecked %s", unchecked)
            node = unchecked.pop()
            
            # Find everybody this node references:
            xnode = data_service.resource_load (uniq=node,view='deep')
            if xnode is None:
                log.error ('could not load %s', node)
                continue
            node_type = xnode.tag
            if node_type == 'resource':
                node_type = xnode.get ('resource_type') or xnode.tag
            nodes.add( (node, node_type) )
            checked.add (node)
            if node_type == 'mex':
                # Mex => find inputs/outputs
                _add_mex_inputs_outputs(xnode, edges, checked, unchecked)
                # treat Mex's submex outputs as a dataset
                datasets[node] = [ x.rsplit('/',1)[1] for x in xnode.xpath('./mex/tag[@name="outputs"]/tag/@value') if x.startswith('http') ]
            else:
                # Non-mex => Find mexes that reference me (directly or indirectly via a dataset)
                if node_type == 'dataset':
                    datasets[node] = [ x.rsplit('/',1)[1] for x in xnode.xpath("./value/text()") ]
                else:
                    resources.add(node)
                siblings = data_service.query ('mex',tag_query='"*/%s"' % node)   #TODO: this will be very slow on large DBs                
                for snode in siblings:
                    unchecked.add(snode.get('resource_uniq'))
            log.debug ( "Nodes : %s, Edges : %s" % (nodes, edges) )

        # check if any resource is member of a dataset => add membership link
        members = set()
        for node in resources:
            for dataset in datasets:
                if node in datasets[dataset]:
                    members.add( (node, dataset) )

        for node in nodes:
            etree.SubElement (response, 'node', value = node[0], type=node[1])
        node_uniqs = [ n[0] for n in nodes ]
        for edge in edges:
            if edge[0] in node_uniqs  and edge[1] in node_uniqs:
                etree.SubElement (response, 'edge', value = "%s:%s" % edge)
            else:
                log.error ("Skipping edge %s due to missing nodes", edge)
        for edge in members:
            if edge[0] in node_uniqs  and edge[1] in node_uniqs:
                etree.SubElement (response, 'member', value = "%s:%s" % edge)
            else:
                log.error ("Skipping edge %s due to missing nodes", edge)
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
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'graph', 'public'))]

def get_model():
    from bq.graph import model
    return model

__controller__ =  graphController
