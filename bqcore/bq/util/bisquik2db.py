###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

"""
import logging
import itertools
import urlparse
import time
import copy
import io
import posixpath

from lxml import etree
from datetime import datetime
import sqlalchemy
from sqlalchemy.orm import object_mapper
from sqlalchemy.sql import and_, or_

from tg import config

from bq.core.model import DBSession
from bq.data_service.model import Taggable, Value, Vertex, dbtype_from_tag
from bq.exceptions import BQException
from bq.util.compat import OrderedDict
from bq.util.hash import is_uniq_code

log = logging.getLogger('bq.db')

# Determine whether limited responses are generated
# Limited-response allows smaller document to be generated
# forcing the client to refetch more data if needed .
max_response_time = float(config.get ('bisque.data_service.max_response_time', 0))


class BQParseException(BQException):
    pass

def unicode_safe(u):
    try:
        return unicode(u, "utf-8")
    except TypeError:
        return unicode(u)



#: Gobject type that may be used as top level tags
known_gobjects = [
    'gobject',
    'point',
    'line' ,
    'polygon',
    'polyline',
    'rectangle',
    'circle',
    'ellipse' ,
    'label',
    ]



system_types = [
    'value',
    'vertex',
    'gobject',
    'tag',
    'file',
    'image',
    'dataset',
    'system',
    'service',
    'module',
    'user',
    'template',
    'mex',
    'auth',
    'store',
    'dir',
    'link',
    'preference',
    'annotation',
    ]


def valid_element(tag):
    """Determine whether the tag is a valid XML Element

    XML elements must follow these naming rules:

    Names can contain letters, numbers, and other characters
    Names cannot start with a number or punctuation character
    Names cannot start with the letters xml (or XML, or Xml, etc)
    Names cannot contain spaces
    Any name can be used, no words are reserved.
    """
    try:
        tag = etree.Element(tag).tag
        return tag
    except ValueError:
        return None



class XMLNode(list):
    '''Surrogate XML node for non-database items'''
    def __init__(self, tag):
        self.xmltag = tag
        self.tags = []
        self.gobjects = []
        self.children = []
        self.document = None
    def __iter__(self):
        return itertools.chain(self.tags, self.gobjects, self.children)
    def __len__(self):
        return len(self.tags)+ len(self.gobjects)+len(self.children)
    def __getitem__(self, key):
        return (self.tags + self.gobjects + self.children)[key]

    def __str__(self):
        return "%s tag:%s gobject:%s kids %s" % (self.xmltag,
                                                 self.tags,
                                                 self.gobjects,
                                                 self.kids)


##################################################
# Resource
class ResourceFactory(object):
    '''Create db class based on XML tags and place in proper
    hierarchy
    '''
    @classmethod
    def load_uri(cls, uri, parent):
        #log.debug('factory.load_uri %s' % uri)
        node =   load_uri(uri)
        if node is not None and parent is not None:
            if node.id != parent.id:  # POST /ds/image/1/ <image uri="/ds/image/1" ..>
                cls.set_parent (node, parent)
        return node

    @classmethod
    def new(cls, xmlnode, parent, **kw):
        xmlname = xmlnode.tag
        if xmlname in known_gobjects:
            node = Taggable('gobject', parent = parent)
            if xmlname != 'gobject':
                node.resource_user_type = xmlname
        elif xmlname == "vertex":
            node = Vertex()
            parent.vertices.append (node)
            node.indx = len(parent.vertices)-1 # Default value (maybe overridden)
            node.document = parent.document
        elif xmlname == "value":
            node = Value()
            parent.resource_value = None
            parent.values.append(node)
            parent.resource_value = None
            node.indx = len(parent.values)-1   # Default value (maybe overridden)
            node.document = parent.document
        elif xmlname== "request" or xmlname=="response":
            if parent:
                node = parent
            else:
                node = XMLNode(xmlname)
        else:
            if xmlname=="resource":
                xmlname = xmlnode.get ('resource_type')

            tag, type_ = dbtype_from_tag(xmlname)
            node = type_(xmlname, parent=parent)
            if tag == 'mex':
                node.mex = node
            if tag == 'user':
                node.user = node

        log.debug  ('factory.new %s -> %s document(%s)' % (xmlname, node, node.document))
        return node

    @classmethod
    def set_parent(cls, node, parent):
        xmlname = node.xmltag
        if xmlname == "vertex":
            if parent and node not in parent.vertices:
                parent.vertices.append (node)
                node.indx = len(parent.vertices)-1 # Default value (maybe overridden)
        elif xmlname == "value":
            if node not in parent.values:
                parent.resource_value = None
                parent.values.append(node)
                parent.resource_value = None
                node.indx = len(parent.values)-1   # Default value (maybe overridden)
        elif xmlname== "request" or xmlname=="response":
            pass
        else:
            if parent and node not in parent.children:
                node.document = parent.document
                parent.children.append(node)


    index_map = dict(vertex=('vertices',Vertex), value=('values', Value))
    @classmethod
    def index(cls, node, parent, indx, cleared):
        xmlname = node.tag
        if xmlname in known_gobjects:
            xmlname = 'gobject'
        #return cls.new(xmlname, parent)
        array, klass = cls.index_map.get (xmlname, (None,None))
        if array:
            objarr =  getattr(parent, array)
            # If values have been 'cleared', then arrary will be empty
            # this will get the
            log.debug ("CURRENTLEN = %s " % (len(objarr)))
            objarr.extend ([ klass() for x in range(((indx+1)-len(objarr)))])
            for x in range(len(objarr), indx+1):
                objarr[indx].indx = x
                objarr[indx].document = parent.document


            v = DBSession.query(klass).get( (parent.id, indx) )
            log.debug('indx %s fetched %s ' % (indx, v))
            #objarr.extend ([ klass() for x in range(((indx+1)-len(objarr)))])
            if v is not None:
                objarr[indx] = v
            objarr[indx].document = parent.document
            #log.debug('ARRAY = %s' % [ str(x) for x in objarr ])
            return objarr[indx]



#####################################
#

#: Fields that are not included when rendering DB objects
#  Map of fields to:
#      None :  Don't render field
#      'str'  :  Replace the name of field with equivalent field 'str'
#      callable : Replace the value of the
#      (name, value) : A tuple for renaming and revalueing the


def make_owner (dbo, fn, baseuri):
    return ('owner', baseuri + str(dbo.owner))
def make_uri(dbo, fn, baseuri):
    return ('uri', "%s%s" % (baseuri , str (dbo.uri)))
    #return ('uri', "%s" % (dbo.uri))
def get_email (dbo, fn, baseuri):
    return ('email', dbo.user.resource_value)
def make_user (dbo, fn, baseuri):
    return ('user', baseuri + str(dbo.user))
def make_time(dbo, fn, baseuri):
    ts = getattr(dbo, fn, None)
    return (fn, ts and ts.isoformat())

clean_fields = [ 'name', 'value', 'type', 'x', 'y', 'index', 'z', 't', 'ch', 'resource_uniq', 'resource_type' ]

child_fields = [ 'name', 'value', 'type', 'index' ]

mapping_fields = {
#    'table_name':'type',
    'engine_id' : 'engine',
    'gobjects':None,
    'id': make_uri,
    'indx': 'index',
#    'name_id':None,
    # Taggable
    'owner_id':None,
    'owner' : make_owner,
    'perm'  : 'permission',
    'parent_id':None,
    'children': None,
    'childrenq': None,
    'docnodes': None,
    'docvalues':None,
    'docvertices': None,
#    'type' : 'resource_user_type',
#    'name' : 'resource_name',
#    'value': 'resoruce_value',
    'document_id': None,
    'document' : None,
    'created' : make_time,
    'ts'      : make_time,
    'resource_parent_id': None,
    'resource_name' : 'name',
    'resource_value': 'value',
    'resource_type' : None,
    'resource_user_type' : 'type',
    'resource_hidden' : 'hidden',
    'resource_index' : 'index',
    'module_type_id':None,
    'mex' : None,
    'mex_id' : None,
    'parent':None,
    'tagname':'name',
    'tags':None,
    'tagq':None,
    'tb_id':None,
#    'type':None,
    'type_id':None,
    'type_name': 'type',
    'values':None,
    'valstr':None,
    'valnum':None,
    'valobj':None,
    'objref':None,
    'vertices':None,
    'tguser':None,
    'password': None,
    'acl' : None,
    'user_acls': None,
    'owns' : None,
    # Auth
    'user_id' : get_email,
    'user'    : make_user,
    'taggable_id': None,
    'action_code': 'action',
    'resource': None,
    'xmltag': None,
    'primary': 'id',
    }



def model_fields(dbo, baseuri=None):
    '''Extract known fields from  a DB object, while removing
    any known from C{excluded_fields}

    @rtype: dict
    @return fields to rendered in XML
    '''
    attrs = {}
    try:
        dbo_fields = object_mapper (dbo)._props.keys()
    except sqlalchemy.orm.exc.UnmappedInstanceError:
        # This occurs when the object is a fake DB objects
        # The dictionary is sufficient
        dbo_fields= dbo.__dict__
    #log.debug ('dbo_fields %s' % dbo_fields)
    for fname in dbo_fields:
        fn = mapping_fields.get(fname, fname)
        if fn is None:
            continue                    # Skip when map is None
        if callable(fn):
            fn, attr_val = fn(dbo, fname, baseuri)
        else:
            attr_val = getattr(dbo, fn, None)
        if attr_val is not None: # and attr_val!='':
            if isinstance(attr_val, basestring):
                attrs[fn] = attr_val
            else:
                attrs[fn] = unicode(attr_val) #unicode(attr_val,'utf-8')
    return attrs



def xmlelement(dbo, parent, baseuri, view, **kw):
    'Produce a single XML element based on the DB object and the view'
    xtag = kw.pop('xtag', getattr(dbo, 'resource_type', dbo.xmltag))
    if not kw:
        kw = model_fields (dbo, baseuri)
        if 'clean' in view:
            kw = dict([ (k,v) for k,v in kw.items() if k in clean_fields])

    if 'primary' in view:
        kw['primary'] = str(dbo.id) if hasattr(dbo,'id') else ''

    if 'canonical' in view or xtag not in system_types:
        kw['resource_type'] = xtag
        xtag = 'resource'
    elif xtag == 'gobject' and dbo.type in known_gobjects:
        xtag  = dbo.type
        kw.pop('type')
    text = kw.pop ('text',None)
    if parent is not None:
        #log.debug ("etree: " + str(xtag)+ str(kw))
        elem =  etree.SubElement (parent, xtag, **kw)
    else:
        elem =  etree.Element (xtag,  **kw)
    elem.text = text and str(text)
    return elem


def xmlnode(dbo, parent, baseuri, view, **kw):
    'Produce a XML element and children '
    rtype = getattr(dbo, 'resource_type', dbo.xmltag)
    #log.debug ('xmlnode %s %s ' % (rtype, view))
    #rtype = dbo.xmltag
    if rtype not in ('value', 'vertex'):
        elem = xmlelement (dbo, parent, baseuri, view=view)
        if 'deep' not in view and hasattr(dbo,'resource_value') and dbo.resource_value == None:
            if 'short' not in view:
                junk = [ xmlnode(x, elem, baseuri, view) for x in dbo.values ]
        if 'deep' not in view and 'short' not in view and hasattr(dbo, 'vertices'):
            junk = [ xmlnode(x, elem, baseuri, view) for x in dbo.vertices ]
        return elem

    #if rtype == 'tag':
    #    elem = xmlelement (dbo, parent, baseuri, view=view)
    #    if 'deep' not in view and dbo.resource_value == None:
    #        junk = [ xmlnode(x, elem, baseuri, view) for x in dbo.values ]
    #    return elem
    #if  rtype == 'gobject':
    #    if 'canonical' not in view and dbo.type in known_gobjects:
    #        elem = xmlelement (dbo, parent, baseuri, xtag=dbo.type, view=view)
    #    else:
    #        elem = xmlelement (dbo, parent, baseuri, view=view)
    #    if 'deep' not in view:
    #        junk = [ xmlnode(x, elem, baseuri, view) for x in dbo.vertices ]
    #    return elem
    if rtype=='value':
        elem = xmlelement (dbo, parent, baseuri, view=view)
        elem.set('type', dbo.type)
        if dbo.type == 'object':
            elem.text = baseuri + unicode_safe(dbo.value)
        else:
            elem.text = unicode_safe(dbo.value)
        return elem

    elem = xmlelement (dbo, parent, baseuri, view=view)
    return elem


def resource2nodes(dbo, parent=None, view=[], baseuri=None,  qfilter=None, **kw):
    'load every element associated with dbo i.e load the document'
    from bq.data_service.controllers.resource_query import resource_permission
    doc_id = dbo.document_id
    if qfilter is None:
        qfilter =  (Taggable.document_id == doc_id)


    docnodes = DBSession.query(Taggable).filter(qfilter)
    docnodes = resource_permission(docnodes)
    #docnodes = docnodes.order_by(Taggable.id)
    #log.debug("reosurce2nodes: %s",  str(docnodes))
    #log.debug('resource2nodes: %s %s doc %s' , str(docnodes), dbo.id , doc_id)
    nodes = {}
    parents = {}

    for node in docnodes:
        nodes[node.id]   = xmlnode(node, None, baseuri, view)
        parents[node.id] = node.resource_parent_id
    for node_id, parent_id in parents.items():
        try:
            # attached xml nodes in position
            if parent_id is not None:
                nodes[parent_id].append(nodes[node_id])
        except KeyError:
            log.error("Missing parent node %s (permission error?) in document %s" , parent_id, doc_id)
            continue
    # for node in docnodes:
    #     if node.resource_parent_id is not None:
    #         try:
    #             node_parent = nodes[node.resource_parent_id]
    #         except KeyError:
    #             log.error("Missing parent node %s (permission error?) in document %s" % (node.resource_parent_id, doc_id))
    #             continue
    #         #elem = etree.SubElement(parent, node.resource_type)
    #         elem = xmlnode (node, node_parent, baseuri, view)
    #         nodes[node.id] = elem
    #     else:
    #         #elem = root = etree.Element(node.resource_type)
    #         elem = root = xmlnode(node, None, baseuri, view)
    #         nodes[node.id] = elem

    vnodes = DBSession.query(Value).filter(Value.document_id == doc_id).order_by(
        Value.resource_parent_id, Value.indx)
    for v in vnodes:
        if v.resource_parent_id in nodes and nodes[v.resource_parent_id].get('value') is None:
            xmlnode (v, parent = nodes[v.resource_parent_id], baseuri=baseuri, view=view)
    vnodes = DBSession.query(Vertex).filter(Vertex.document_id == doc_id).order_by(
        Vertex.resource_parent_id, Vertex.indx)
    for v in vnodes:
        if v.resource_parent_id in nodes:
            xmlnode (v, parent = nodes[v.resource_parent_id], baseuri=baseuri, view=view)

    log.debug('resource2nodes: doc %s read %d nodes ', doc_id,  (len(nodes.keys())))
    return nodes, doc_id


def resource2tree(dbo, parent=None, view=[], baseuri=None, nodes= {}, doc_id = None, qfilter=None, **kw):
    'load an entire document tree for a particular node'

    try:
        if doc_id != dbo.document_id:
            nodes, doc_id = resource2nodes(dbo, parent, view, baseuri, qfilter, **kw)
        if parent is not None:
            log.debug ("parent %s + %s" % (parent, nodes[dbo.id]))
            parent.append ( nodes[dbo.id])
        # Make a copy of the document from the request position to e
        if dbo.document_id != dbo.id:
            return copy.deepcopy(nodes[dbo.id]), nodes, doc_id
        else:
            return nodes[dbo.id], nodes, doc_id
    except KeyError:
        log.exception ("Problem loading tree for document %s: nodes %s" % (doc_id, nodes))

    return xmlnode(dbo, parent=parent, baseuri=baseuri, view=view), nodes, doc_id


def db2tree(dbo, parent=None, view=[], baseuri=None, progressive=False, **kw):
    "Convert a Database Object into ElementTree representation"
    if isinstance(view, basestring):
        # pylint:disable=E1103
        view = [ x.strip() for x in view.split(',') ]
    view = view or []

    #if 'fulluri' in view:
    #    view = [ x for x in view if x != 'fulluri' ]
    #else:
    #    baseuri = urlparse.urlparse(baseuri).path

    endtime = 0
    if progressive and max_response_time>0:
        log.debug ("progressive response: max %f", max_response_time)
        starttime = time.clock()
        endtime   = starttime + max_response_time;
    log.debug ("db2tree: %s", str(dbo))

    complete,r = db2tree_int(dbo, parent, view, baseuri, endtime, **kw)


    if not complete:
        offset = len(r) + kw.get('offset', 0)
        etree.SubElement(parent, 'resource',
                         type="bisque+extension",
                         uri = "%s/%s?offset=%d"%(baseuri, dbo.xml_tag,offset))
    log.debug ("converted %d" % len (r))
    return r


def db2tree_int(dbo, parent = None, view=None, baseuri=None, endtime=None, **kw):
    '''Convert a database object to a tree/doc'''
    nodes =  {}
    doc_id = None
    if hasattr(dbo, '__iter__'):
        r = []
        for x in dbo:
            #log.debug ("proxing %s "% x)
            if endtime and  time.clock() >= endtime:
                fetched = len (r)
                return False, r
            n, nodes, doc_id = db2node(x, parent, view, baseuri, nodes, doc_id, **kw)
            r.append(n)
        #log.debug ("returning array %s" % r)
        return True, r
        #return [ db2tree_int(x, parent, view, baseuri) for x in dbo ]
    n, nodes, doc_id = db2node(dbo, parent, view, baseuri, nodes, doc_id, **kw)
    return True, n



def db2node(dbo, parent, view, baseuri, nodes, doc_id, **kw):
    from bq.data_service.controllers.resource_query import resource_permission
    log.debug ("db2node dbo=%s view=%s" % ( dbo, view))
    if dbo is None:
        log.error ("None pass to as DB object parent = %s", parent)
        return None, nodes, doc_id
    if 'deep' in view:
        n, nodes, doc_id = resource2tree(dbo, parent, view, baseuri, nodes, doc_id)
        return n, nodes, doc_id

    # newview = filter (lambda x: x not in ('full','deep','short', 'canonical'), view)
    # if newview:
    #     qfilter = (Taggable.resource_parent_id == None)
    #     for tag_name in newview:
    #         qfilter = or_(qfilter, and_(Taggable.resource_type == 'tag',
    #                                     Taggable.resource_name == tag_name))
    #     qfilter = and_(Taggable.document_id == dbo.document_id, qfilter)

    #     n, nodes, doc_id = resource2tree(dbo, parent, ['deep'], baseuri, nodes, doc_id, qfilter)
    #     return n, nodes, doc_id


    node = xmlnode(dbo, parent, baseuri, view)
    if "full" in view :
        #v = filter (lambda x: x != 'full', view)
        log.debug ('FULL %s', kw)
        q = dbo.childrenq
        if kw.has_key('offset'):
            q = q.offset (int(kw.pop('offset')))
        if kw.has_key('limit'):
            q = q.limit (int(kw.pop('limit')))
        tl = [ xmlnode(x, node, view=view, baseuri=baseuri) for x in resource_permission(q) ]
        #gl = [ db2tree_int(x, node, view=v, baseuri=baseuri) for x in dbo.gobjects ]
#    elif "deep" in view:
#         tl = [ db2tree_int(x, node, view, baseuri) for x in dbo.children ]
#         #gl = [ db2tree_int(x, node, view, baseuri) for x in dbo.gobjects ]
    elif view is None or len(view)==0 or 'short' in view:
    #elif not view or 'short' in view:
        pass
    else:
        # Allow a list of tags to be specified in the view parameter which
        # will be included the object
        v = filter (lambda x: x not in ('full','deep','short', 'canonical'), view)
        #log.debug ("TAG VIEW=%s", v)
        #tl = [ db2tree_int(x, node, v, baseuri) for x in dbo.tags if x.resource_name in v ]
        for tag_name in v:
            tags = DBSession.query(Taggable).filter(Taggable.document_id == dbo.document_id,
                                                    Taggable.resource_type == 'tag',
                                                    Taggable.resource_name == tag_name)
            for tag in tags:
                kid = xmlnode(tag, node, view=view, baseuri=baseuri)
                tl = [ xmlnode(x, kid, view=view, baseuri=baseuri) for x in tag.childrenq ]
             #tag = dbo.tagq.filter_by(resource_name = tag_name).first()
             #if tag:
             #    xmlnode(tag, node, view=v, baseuri=baseuri)

    return node, nodes, doc_id



# def db2tree_iter(dbo, parent = None, view=None ,  baseuri=None, endtime=None):
#     '''Convert a database object to a tree/doc'''
#     if hasattr(dbo, '__iter__'):
#         for x in dbo:
#             yield   db2tree_iter(x, parent, view, baseuri)
#     #print "dbo=", dbo
#     node = toxmlnode(dbo.next(), parent, baseuri, view)
#     yield node
#     #log.debug ('node = '+ etree.tostring(node))
#     if "full" in view :
#         v = itertools.ifilter (lambda x: x != 'full', view)
#         for x in dbo.tags:
#             yield db2tree_iter(x, node, view=v, baseuri=baseuri)
#         for x in dbo.gobjects:
#             yield db2tree_iter(x, node, view=v, baseuri=baseuri)

#         #[ etree.SubElement (node, 'tag', **model_fields(x)) for x in dbo.tags ]
#         #[ etree.SubElement (node, 'gobject', **model_fields(x)) for x in dbo.gobjects ]
#     elif "deep" in view:
#         for x in dbo.tags:
#             yield db2tree_iter(x, node, view, baseuri)
#         for x in dbo.gobjects:
#             yield db2tree_iter(x, node, view, baseuri)
#     elif  'short' in view:
#         return
#     elif  True: #'normal' in view:
#         #if len(dbo.tags):
#         # Hack to keep from loading tags when checking for existance
#         if DBSession.query(Tag).filter (dbo.id == tags.c.parent_id).count()!=0:
#             etree.SubElement(node, 'resource', uri=baseuri+dbo.uri+'/tags')
#             yield node
#         #if len(dbo.gobjects):
#         # Hack to keep from loading gobjects when checking for existance
#         if DBSession.query(GObject).filter (dbo.id == gobjects.c.parent_id).count()!=0:
#             etree.SubElement(node, 'resource', uri=baseuri+dbo.uri+'/gobjects')
#             yield node
#     return




######################################################################
#
def parse_bisque_uri(uri):
    ''' Parse a bisquie uri into  service, and optional dbclass , and ID
    @type  uri: string
    @param uri: a bisquik uri representation of a resourc
    @rtype:  A quad-tuple (service, dbclass, id, rest )
    @return: The parse resource
    '''
    # (scheme, host, path, ...)
    url = urlparse.urlsplit(uri)
    if url.scheme not in ('http', 'https', ''):
        return None, None, None, None
    # /service_name/ [ id or or class ]*
    parts = posixpath.normpath(url[2]).strip('/').split('/')
    # paths are /class/id or /resource_uniq
    if not parts :
        return url[1], 'data_service', None, None

    # should have a service name or a uniq code
    if is_uniq_code (parts[0]):
        service = 'data_service'
        # class  follows or nothing
    else:
        service = parts.pop(0)
    # first element may be a docid
    ida = None
    if is_uniq_code (parts[0]):
        ida = parts.pop(0)
    clname = None
    rest   = []
    while parts:
        sym = parts.pop()
        if not sym[0].isdigit():
            rest.append(sym)
            continue
        ida = sym
        if parts:
            clname = parts.pop()
        break
    return service, clname, ida, rest



def load_uri (uri, query=False):
    '''Load the object specified by the root tree and return a rsource
    @type   root: Element
    @param  root: The db object root with a uri attribute
    @rtype:  tag_model.Taggable
    @return: The resource loaded from the database
    '''
    # Check that we are looking at the right resource.

    try:
        resource = None
        service, clname, ida, rest = parse_bisque_uri(uri)
        if service  not in  ('data_service', 'module_service'):
            return None
        if ida and is_uniq_code (ida):
            log.debug("loading resource_uniq %s" % ida)
            resource = DBSession.query(Taggable).filter_by(resource_uniq = ida)
        elif clname:
            name, dbcls = dbtype_from_tag(clname)
            log.debug("loading %s -> name/type (%s/%s)(%s) " %(uri, name,  str(dbcls), ida))
            #resource = DBSession.query(dbcls).get (int (ida))
            resource = DBSession.query(dbcls).filter (dbcls.id == int(ida))
        if not query:
            resource = resource.first()
        log.debug ("loaded %s", str(resource))
        return resource
    except Exception:
        log.exception("Failed to load uri %s", uri)
        return None

converters = OrderedDict( (
    ('object' , load_uri),
    ('integer',  int),
    ('float'  ,  float),
    ('number'  , float),
    ('string'  , unicode_safe),
    ) )

def try_converters (value):
    for ty_, converter in converters.items():
        try:
            v = converter(value)
            if v is not None:
                return v
        except ValueError:
            pass
    # we should never get here
    raise ValueError

def updateDB(root=None, parent=None, resource = None, factory = ResourceFactory, replace=False):
    '''Update the database type resource with doc or tree'''
    try:
        evnodes = etree.iterwalk(root, events=('start','end'))
        log.debug ("updateDB: walking " + str(root))
    except TypeError, e:
        log.exception ("bad parse of tree: %s" % [ root, resource ] )
        raise e

    last_resource = None
    stack = [  ]
    if parent:
        stack.append (parent)
    try:
        ts = datetime.now()
        for ev, obj in evnodes:
            if isinstance(obj, etree._Comment) or isinstance(obj, etree._ProcessingInstruction):
                continue
            # Completely skip over these in the tree
            if obj.tag == 'response' or obj.tag == 'request':
                continue
            #Begin a descent into the tree
            #log.debug ("ev %s obj %s" % (ev, obj.tag))
            if ev == 'start':
                if len(stack) == 0:
                    parent = None
                else:
                    parent = stack[-1]

                attrib = dict (obj.attrib)

                uri   = attrib.pop ('uri', None)
                type_ = attrib.get ('type', None)
                indx  = attrib.get ('index', None)
                ts_   = attrib.pop ('ts', None)
                created_ = attrib.pop ('created', None)
                owner = attrib.pop ('owner', None)
                #uniq  = attrib.pop ('resource_uniq', None)

                cleared = []
                if resource is not None:
                    factory.set_parent (resource, parent)
                elif uri:
                    resource = factory.load_uri (uri, parent)
                    if resource is None:
                        log.debug ("load failed %s: creating" % uri)
                        resource = factory.new (obj, parent, uri=uri)
                        resource.created = ts
                    elif replace:
                        cleared = resource.clear()
                elif indx is not None:
                    log.debug('index of %s[%s] on parent %s'%(obj.tag, indx, parent))
                    resource = factory.index (obj, parent, int(indx), cleared)
                else:
                    # TODO if tag == resource, then type should be used
                    resource = factory.new (obj, parent)
                    resource.created = ts

                    #log.debug("update: created %s:%s of %s" % (obj.tag, resource, resource.document))
                    log.debug("update: created %s:%s" % (obj.tag, resource))
                # Assign attributes
                resource.ts = ts
                for k,v in attrib.items():
                    #log.debug ("%s attr %s:%s" % (resource, k, v))
                    if getattr(resource, k, v) != v:
                        setattr(resource, k, unicode_safe(v))

                # Check for text
                value = attrib.pop ('value', None)
                if value is None and obj.tag == 'value':
                    value = obj.text
                if value is not None and value != resource.value:
                    convert = converters.get(type_, try_converters)
                    resource.value = convert (value.strip())
                    #log.debug (u"assigned %s = %s" % (obj.tag , unicode(value,"utf-8")))
                stack.append (resource)
                last_resource = resource
                resource = None

            elif ev == 'end':
                last_resource = stack.pop()
                #log.debug ("last_resource, resource %s, %s "  %(last_resource, resource))
            else:
                log.debug ("other node %s" % obj.tag)

    except Exception, e:
        log.exception("during parse of %s " % (etree.tostring(root, pretty_print=True)))
        raise e
    return  last_resource

def bisquik2db_internal(inputs, parent, resource,  replace):
    '''Parse a document (either as a doc, or an etree.
    Verify against xmlschema if present
    '''
    results=[]
    if parent is not None:
        parent = DBSession.merge(parent)
    if resource is not None:
        resource = DBSession.merge(resource)
    for el in inputs:
        node = updateDB(root=el, parent = parent, resource=resource, replace=replace)
        log.debug ("returned %s " % str(node))
        log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
                   (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
        if node not in DBSession:
            DBSession.add(node)
        results.append(node)

    DBSession.flush()
    for node in results:
        DBSession.refresh(node)
    log.debug ('modifyed : new (%d), dirty (%d), deleted(%d)' %
               (len(DBSession.new), len(DBSession.dirty), len(DBSession.deleted)))
    log.debug("Bisquik2db last_node %s of document %s " % ( node, node.document ))
    if len(results) == 1:
        return node
    return results


def bisquik2db(doc= None, parent=None, resource = None, xmlschema=None, replace=False):
    '''Parse a document (either as a doc, or an etree.
    Verify against xmlschema if present
    '''
    if hasattr(doc,'read'):
        doc = etree.parse(doc)
    if isinstance(doc, basestring):
        doc = etree.parse(io.BytesIO(doc))

    log.debug ("Bisquik2db parent:" + str (parent))
    if isinstance(doc , etree._ElementTree):
        inputs = [ doc.getroot() ]
        if doc.getroot().tag in ( 'request', 'response' ):
            inputs = list (doc.getroot())
    else:
        inputs = [ doc ]

    DBSession.autoflush = False
    if replace and resource:
        resource.clear()
    return bisquik2db_internal(inputs, parent, resource, replace)




#def itertest():
#    r = etree.Element ('resource')
#    q = DBSession.query(Image)[0:10]
#    return db2tree_iter (iter(q), r, view=[], baseuri = 'http://host' )


