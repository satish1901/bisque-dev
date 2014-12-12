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
   Parse and execute query expressions for DoughDB objects
"""
import re
import logging
import string
import textwrap

from tg import config, url, session
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Unicode, Float, Boolean
from sqlalchemy.sql import select, func, exists, and_, or_, not_, asc, desc, operators, cast
from sqlalchemy.orm import Query, aliased
from pylons.controllers.util import abort

#from datetime import strptime

from bq.core.model import DBSession

#from bq.data_service.model import UniqueName, names
from bq.data_service.model import Taggable, taggable, Image, LEGAL_ATTRIBUTES
from bq.data_service.model import TaggableAcl, BQUser
from bq.data_service.model import Tag, GObject
from bq.data_service.model import Value, values
from bq.data_service.model import dbtype_from_tag
from bq.client_service.controllers import notify_service

from bq.core.identity import get_user_id, is_admin, get_user
from bq.core.model import User
from bq.util.mkdir import _mkdir
from bq.util.paths import data_path
from bq.util.converters import asbool

from .resource import Resource
from .filter_parser import filter_parse

log = logging.getLogger('bq.data_service.query')

PUBLIC=0
PRIVATE=1
RESOURCE_READ=0
RESOURCE_EDIT=1
RESOURCE_SHARE=2


#####################################################
# tag_query parser
report_errors = True

try:
    import ply.yacc as yacc
    import ply.lex as lex
except Exception:
    import yacc as yacc
    import lex as lex



_OPERATIONS = {
        '==': operators.eq,
        '!=': operators.ne,
        '<': operators.lt,
        '<=': operators.le,
        '>': operators.gt,
        '>=': operators.ge,
#        'IN': operators.contains,
#        'NOT IN': lambda a, b: not operators.contains(b, a)
        }

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Lexer
tokens = ('TAGVAL',  'SEP', 'TYSEP', 'AND', 'OR', 'LP', 'RP', 'QUOTED', 'REL')
reserved = { 'and':'AND', 'AND':'AND', 'or':'OR', 'OR':'OR', }

#t_TAGVAL   = r'\w+\*?'
t_TYSEP = r'::'
t_SEP   = r':'
t_AND   = r'\&'
t_OR    = r'\|'
t_LP    = r'\('
t_RP    = r'\)'
t_REL   = r'<|>|<=|>=|==|!='
#t_VALEXP= r'\w+\*'

t_ignore = r' '

def t_QUOTED(t):
    r'(?s)(?P<quote>["\'])(?:\\?.)*?(?P=quote)'
    t.type = 'TAGVAL'
    t.value = t.value[1:-1]
    return t
def t_TAGVAL(t):
    r'[^:=<>\t\n\r\f\v()" ]+'
    t.type = reserved.get(t.value, 'TAGVAL')
    if t.type != 'TAGVAL':
        t.value = t.value.upper()
    return t


# def t_TAGVAL(t):
#     r'([^:"\'\t\n\t\f\v() ]+)|(?P<q>["\'])[^"\']*(?P=q)'
#     t.type = reserved.get(t.value, 'TAGVAL')
#     if t.type != 'TAGVAL':
#         t.value = t.value.upper()
#     t.value = t.value.strip('"\'')
#     return t

def t_error(t):
    global report_errors
    if (report_errors):
        print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

lex.lex()

# End Lexer
#############


def p_query_simple(p):
    '''query : expr'''
    p[0] = p[1]

def p_expr_binop(p):
    ''' expr : expr AND term
             | expr OR term
    '''
    op = { 'AND' : and_, 'OR' : or_ } [ p[2] ]
    p[0] = op (p[1], p[3])

def p_expr_default(p):
    ''' expr : expr term '''
    p[0] = and_(p[1], p[2])
#    p[0] = and_ (Taggable.id.in_ (select([Taggable.id], p[1]).correlate(None)),
#                 Taggable.id.in_ (select([Taggable.id], p[2]).correlate(None)))

def p_expr_paren(p):
    '''term : LP expr RP'''
    p[0] = p[2]

def p_expr_term(p):
    '''expr : term'''
    #p[0] = Taggable.id.in_ (select([Taggable.id], p[1]).correlate(None))
    p[0] = p[1]


def p_term_tagvaltype(p):
    '''term : tvexpr '''

    log.debug ('tagval %s' % list(p[1]))
    name, val, type_, rel = p[1]
    #vals= values.alias()
    tag = taggable.alias ()


    tagfilter =None
    if name:
        # attributes
        if name[0] == '@' and val:
            name = name[1:]
            if name in LEGAL_ATTRIBUTES:
                op = _OPERATIONS[rel]
                if val.count('*'):
                    val = val.replace('*', '%')
                p[0] = op(getattr(Taggable, LEGAL_ATTRIBUTES[name]), val)
            return

        # standard subtag
        if name.count('*'):
            namexpr = tag.c.resource_name.ilike (name.replace('*', '%'))
        else:
            namexpr = tag.c.resource_name == name
        tagfilter = namexpr

    if val:
        v = val.lower()
        valexpr = None
        if val.count('*'):
            v = v.replace('*', '%')
            valexpr = tag.c.resource_value.ilike(v)
        else:
            op = _OPERATIONS[rel]
            if is_number(val):
                # Cast does not work as column may contain non-float values
                #valexpr = cast (tag.c.resource_value, Float)
                #valexpr = op(valexpr ,  float(v))
                valexpr = op(tag.c.resource_value ,  v)
            else:
                valexpr = func.lower(tag.c.resource_value)
                valexpr = op(valexpr ,  v)

        if tagfilter is not None:
            tagfilter = and_(tagfilter, valexpr)
        else:
            tagfilter = valexpr

    if type_:
        ty = type_.lower()
        tyexpr = (func.lower(tag.c.resource_user_type) == ty)
        if tagfilter is not None:
            tagfilter = and_(tagfilter, tyexpr)
        else:
            tagfilter = tyexpr

    if tagfilter is not None:
        tagfilter = and_(tagfilter, tag.c.document_id == taggable.c.id)
    else:
        tagfilter = (tag.c.document_id == taggable.c.id)

    p[0] = exists([tag.c.id]).where(tagfilter)

    log.debug ("SQL %s" % p[0])



### Parsing
#   [[TYPE ::]NAME:][<><=>===][VALUE]
###
## tuple is (name,value,type_, rel)
def p_tvexpr_val(p):
    '''tvexpr : reltagval'''
    # return (name,value,type)
    p[0] = (None, p[1][0], None, p[1][1])
def p_tvexpr_nameval (p):
    '''tvexpr : tagval SEP reltagval'''
    # return (name,value,type)
    p[0] = (p[1], p[3][0], None, p[3][1])
def p_tvexpr_typenameval (p):
    '''tvexpr :  tagval TYSEP tagval SEP  reltagval'''
    # return (name,value,type)
    p[0] = (p[3], p[5][0], p[1], p[5][1])
def p_tvexpr_typeval (p):
    '''tvexpr :  tagval TYSEP SEP  reltagval'''
    # return (name,value,type)
    p[0] = (None, p[4][0], p[1], p[4][1])


def p_reltagval (p):
    ''' reltagval : tagval
                  | REL tagval'''
    if len(p) == 3:
        p[0] = (p[2], p[1])
    else:
        p[0] = (p[1], '==')

def p_tagval(p):
    '''tagval : TAGVAL
              | QUOTED
              | empty
    '''
    p[0] = p[1]

def p_empty(p):
    'empty :'
    p[0] = ''


def p_error(p):
    print "Syntax error at token", p
    #yacc.errok()

#  We generate the table once and leave it in generated.  This should be
#  move to some system directory like "/var/run/bisque"
# http://www.dabeaz.com/ply/ply.html#ply_nn18
#_mkdir("generated")
yacc.yacc(outputdir=data_path(), debug= 0)

# End Parser
#############################################################

def prepare_permissions (query, user_id, with_public, action = RESOURCE_READ):
    # get system supplied user ID
    public_vals = { 'false': False, '0': False, 'private':False, 0:False,
                    'true': True, '1': True, 'public': True, 1:True
                    }
    with_public = public_vals.get(with_public, False)
    user_id = user_id or get_user_id()

    if is_admin():
        if with_public:
            log.info('user (%s) is admin wpublic %s. Skipping protection filters' , user_id, with_public)
            return query

    # Check if logged in, else just check for public items.
    if user_id:
        visibility = ( Taggable.owner_id == user_id )
        if with_public and action == RESOURCE_READ:
            visibility = or_(visibility, Taggable.perm == PUBLIC)
        visibility = or_(visibility,
                         Taggable.acl.any(and_(TaggableAcl.user_id == user_id,
                                               TaggableAcl.action_code >= action)))
    else:
        visibility = (Taggable.perm == PUBLIC)

    return query.filter(visibility)
    #v = DBSession.query(Taggable).filter(visibility).subquery()
    #return query.filter(Taggable.document_id == v.c.id)


def prepare_tag_expr (query, tag_query=None):

    if tag_query:
        tag_query = tag_query.strip()
        if tag_query=='*':
            return query
        lexer = lex.lex()
        parser = yacc.yacc(outputdir = data_path(), debug = 0)
        log.debug ("parsing '%s'  " % (tag_query))
        #expr = parser.parse (tag_query, lexer=lexer, debug=log)
        expr = parser.parse (tag_query, lexer=lexer)
        log.debug ("parsed '%s' -> %s " % (tag_query, expr))
        query = query.filter(expr)
    return query





def prepare_type (resource_type):
    """Prepare a query based on the resource_type

    @param resource_type: A tuple or string of resource_type names (seperate by '|')
    @return: a name,dbtype, query tuple
    """
    if resource_type is None:
        resource_type = (None, Taggable)
    if isinstance (resource_type, tuple):
        types = [ resource_type ]
        name, dbtype = resource_type
    elif isinstance(resource_type, basestring):
        types = [ dbtype_from_tag(x.strip()) for x in resource_type.split('|') ]
        name, dbtype = (None, Taggable)

    query = DBSession.query(dbtype)
    query_expr = None
    for resource_type in types:
        ## Setup universal query type
        log.debug ("query type %s %s" % (name, dbtype))
        nm, dbty = resource_type
        query_type = None
        # Special clause for non-system resource and list of resources
        # the name 'nm' is the local type and we will filter those
        if dbtype == Taggable and nm is not None and nm != 'resource':
            log.debug ("query resource_type %s" % nm)
            #query_expr = (Taggable.tb_id == UniqueName(name).id)
            query_type =  (Taggable.resource_type == nm)
        # Check if value or vertix ?
        elif not issubclass(dbty, Taggable) and hasattr(dbtype, 'id'):
            query_type = (dbty.id == Taggable.id)
        if query_type is not None:
            if query_expr is None :
                query_expr = query_type
            else:
                query_expr = or_(query_expr, query_type)

    if query_expr is not None:
        log.debug ("adding filter %s " , str(query_expr))
        query = query.filter (query_expr)
    return (name, dbtype, query)





def prepare_parent(resource_type, query, parent_query=None):
    if isinstance(parent_query, Query):
        name, dbtype = resource_type
        subquery = parent_query.with_labels().subquery()
        #parent = parent_query.first()
        #log.debug ("subquery " + str(subquery))
        log.debug ( "adding parent of %s %s " % ( name , dbtype))
        #query = DBSession.query(dbtype).filter (dbtype.resource_parent_id == subquery.c.taggable_id)
        query  = query.filter(dbtype.resource_parent_id == subquery.c.taggable_id)
        #query  = query.filter(dbtype.resource_parent_id == parent.id)
    elif isinstance(parent_query, Taggable):
        query = query.filter_by(resource_parent_id = parent_query.id)
    elif parent_query is False:
        pass
    else:
        query = query.filter_by(resource_parent_id = None)
    return query


def prepare_order_expr (query, tag_order, **kw):
    if tag_order:
        ordering = lambda x:  x
        for order in tag_order.split(','):
            if order.endswith(':asc'):
                order = order[:-4]
                ordering = asc
            elif order.endswith(':desc'):
                order = order[:-5]
                ordering = desc
            order = order.strip('"\'')

            log.debug ("tag_order: %s" % (order))

            if order.startswith('@'):
                # skip illegal attributes
                attribute = LEGAL_ATTRIBUTES.get(order[1:])
                if attribute:
                    query = query.order_by(ordering(getattr(Taggable, attribute)))
                continue
            ordertags = taggable.alias()
            ordervals = values.alias()
            query_expr = and_ (#query_expr,
                               Taggable.id == ordertags.c.document_id,
                               ordertags.c.resource_type == 'tag',
                               ordertags.c.resource_name == order)
                               #ordertags.c.id == ordervals.c.resource_parent_id)

            query = query.filter(query_expr).order_by (ordering(ordertags.c.resource_value))
            #query = query.filter(query_expr).order_by (ordering(ordervals.c.valstr))
    else:
        query = query.order_by(Taggable.id)

    return query

def count_special(**kw):
    if kw.pop('images2d', None):
        #vs = DBSession.execute(select ([func.sum (Image.z * Image.t)])).fetchall()
        #count = vs[0][0]
        count = DBSession.query(Image).count()
        if count:
            return count
    return None

def resource_count (resource_type,  **kw):
    count =   count_special(**kw)
    if count is None:
        query  =  resource_query(resource_type=resource_type,
                                 **kw)
        #count = query.distinct().count()
        count = query.count()
        #log.debug ('counted ' + str(query) + '=' + str(count))
    return count

class fobject(object):
    ''' A fake database object'''
    def __init__(self, xmltag = None, **kw):
        self.xmltag = xmltag or kw.get('resource_type')
        self.tags = []
        self.gobjects = []
        self.children = []
        self.values = []
        self.vertices = []
        self.resource_name  = None
        self.resource_value = None
        self.__dict__.update(**kw)

    @classmethod
    def fromdict (cls, d):
        if isinstance(d, list):
            return [ cls.fromdict (x) for x in d ]
        if isinstance(d, dict):
            o = fobject(xmltag = d.pop('xmltag') )
            for k,v in d.items():
                o.__dict__[k] = cls.fromdict(v)
            return o
        return str(d)

    def __str__(self):
        return str(self.__dict__)



##   NOTE: Please examine for a better way of handling
##   specilized attribute queries esp.  'name' and 'value' queries
##

def unique(l, fn):
    current = l[0]
    yield current
    for x in l[1:]:
        if fn(x) != fn(current):
            current = x
            yield current



def tags_special(dbtype, query, params):
    '''Specialized query for tags to support tag based browsing
       tag_names=1 :  names of all tags that can be found on the
                  queried objects

       tag_values=tag_name : all possible values for a particular tag name
       name=tag_name   : all tags have a name="tag_name" as an attribute
       value=tag_val   : all tags having a value attribute of tag_val
    '''
    filter_map = {#param         DBType, Attribute, Filter
                  'tag_names' : (Tag,  ['resource_name'], None,),
                  'tag_values': (Tag, ['resource_name', 'resource_value'], 'resource_name'),
                  #'tag_types': (Tag, 'resource_user_type', None),
                  'gob_names' : (GObject, ['resource_name', 'resource_user_type'], 'resource_user_type'),
                  #'gob_values': (GObject, 'resource_value', 'resource_name'),
                  'gob_types' : (GObject, ['resource_user_type'], None),
                   }

    name_map = { 'resource_name' : 'name', 'resource_user_type' : 'type', 'resource_value': 'value', 'count':'text' }

    # extract=tag[name],tag[value, name="qqq"],gobject[type],gobject[name,type="Fish*",value, ts ]
    # /tag[name],tag[value,name=qqq]

    tn = params.pop ('extract',None)
    if tn:
        sq1 = query.with_labels().subquery()
        results = []
        for (dbclass, columns, filters) in filter_parse(tn):

            filters.append (dbclass.document_id == sq1.c.taggable_document_id)
            query = DBSession.query(func.count(columns[-1]).label('count'), *columns)
            query =query.filter (*filters)
            query =query.group_by(*columns).order_by(*columns)
            #log.debug ("FILTER %s" % query)
            q = [ fobject(resource_type=dbclass.xmltag, **(dict ((name_map[k], v) for k,v in attr._asdict().items()))) for  attr in query]
            #q = []
            results.extend (q)
        return results

    # OLD versions
    if any (filt in params for filt in filter_map.keys()):
        results = []
        sq1 = query.with_labels().subquery()
        for filt in filter_map.keys():
            if filt not in params:
                continue
            fv  = params.pop (filt, None)
            dbtyp, dbcols, sel = filter_map [filt]
            columns = [ getattr(dbtyp, dbcol) for dbcol in dbcols ]
            sq2 = DBSession.query (func.count (columns[-1]).label('count'), *columns).filter(Taggable.document_id == sq1.c.taggable_document_id)
            if fv and sel:
                sq2=sq2.filter(getattr(dbtyp, sel) == fv)
            sq3 = sq2.group_by(*columns).order_by(*columns)
            #log.debug ("NEWSPECIAL %s" % sq3)

            # tag_names : fobject (resource_type='tag' , name=tg.resource_name
            # tag_values: fobject (resource_type='tag', name = tv, value = v.resource_value, resource_value = v.resource_value)
            # gob_names:  fobject (resource_type='gobject', type = tv, name = v.resource_name)
            # gob_type :  fobject (resource_type='gobject' , type=tg.resource_user_type )
            q = [ fobject(resource_type=dbtyp.xmltag, **(dict ((name_map[k], v) for k,v in attr._asdict().items()))) for  attr in sq3]
            results.extend (q)
        return results
    return None





    tn = params.pop('gob_types', None)
    if tn:
        ### Return all tha available tag names for the given superquery
        sq1 = query.with_labels().subquery()
        # Fetch all name on all 'top' level tags from the query
        sq2 = DBSession.query(GObject.resource_user_type).filter(GObject.document_id == sq1.c.taggable_document_id)
        sq3 = sq2.distinct().order_by(Tag.resource_user_type)
        vsall = sq3.all()
        # for sqlite (no distinct on)
        try:
            vsall = unique(vsall, lambda x: x.resource_user_type)
            #log.debug ("tag_names query = %s" % sq1)
            q = [ fobject (resource_type='gobject' , type=tg.resource_user_type ) for tg in vsall]
        except (IndexError, StopIteration):
            return []
        return q

    tv = params.pop('gob_names', None)
    if tv:
        log.debug ("GOB %s" % tv)
        ### Given a query and a tag_name, return all the possible values for the tag
        #valtags = tags.alias()
        #tv = UniqueName(tv)
        sq1 = query.with_labels().subquery()
        #sq2 = DBSession.query(Tag).filter(and_(Tag.parent_id == sq1.c.taggable_id,
        #                                     Tag.name_id == tv.id)).with_labels().subquery()
        #sq2 = DBSession.query(GObject).filter(
        #    and_(GObject.resource_user_type == tv,
        #         GObject.document_id == sq1.c.taggable_document_id)).with_labels().subquery()
        sq2 = DBSession.query(GObject.resource_name).filter(
            and_(GObject.resource_user_type == tv,
                 GObject.document_id == sq1.c.taggable_document_id)).distinct().order_by(GObject.resource_name)
        # for sqllite (no distinct on)
        try:
            vsall = unique(sq2.all(), lambda x: x.resource_name)
            q = [ fobject (resource_type='gobject', type = tv, name = v.resource_name)
                 for v in vsall ]
        except (IndexError, StopIteration):
            return []
        return q



    tn = params.pop('tag_names', None)
    if tn:

        ### Return all tha available tag names for the given superquery
        sq1 = query.with_labels().subquery()
        # Fetch all name on all 'top' level tags from the query
        sq2 = DBSession.query(Tag.resource_name, func.count (Taggable.resource_name)).filter(Tag.document_id == sq1.c.taggable_document_id)
        #sq3 = sq2.distinct(Tag.resource_name).order_by(Tag.resource_name)
        sq3 = sq2.distinct().order_by(Tag.resource_name)
        vsall = sq3.all()
        # for sqlite (no distinct on)
        try:
            vsall = unique(vsall, lambda x: x.resource_name)
            #log.debug ("tag_names query = %s" % sq1)
            #q = [ fobject (resource_type='tag' , name=tg.resource_name, type=tg.resource_user_type ) for tg in vsall]
            q = [ fobject (resource_type='tag' , name=tg.resource_name  ) for tg in vsall]
        except (IndexError, StopIteration):
            return []
        return q

    tv = params.pop('tag_values', None)
    if tv:
        ### Given a query and a tag_name, return all the possible values for the tag
        #valtags = tags.alias()
        #tv = UniqueName(tv)
        sq1 = query.with_labels().subquery()
        #sq2 = DBSession.query(Tag).filter(and_(Tag.parent_id == sq1.c.taggable_id,
        #                                     Tag.name_id == tv.id)).with_labels().subquery()
        #sq2 = DBSession.query(Tag).filter(
        #    and_(Tag.resource_name == tv,
        #         Tag.document_id == sq1.c.taggable_document_id)).with_labels().subquery()
        sq2 = DBSession.query(Tag.resource_value).filter(
            and_(Tag.resource_name == tv,
                 Tag.document_id == sq1.c.taggable_document_id)).distinct().order_by(Tag.resource_value)
        # for sqllite (no distinct on)
        try:
            vsall = unique(sq2.all(), lambda x: x.resource_value)
            q = [ fobject (resource_type='tag', name = tv, value = v.resource_value, resource_value = v.resource_value)
                 for v in vsall ]
        except (IndexError, StopIteration):
            return []

        #vs=DBSession.query(Value.valstr).filter(Value.resource_parent_id == sq2.c.taggable_id).distinct()
        #vsall = vs.all()
        #log.debug ('tag_values = %s' % vsall)
        #q = [ fobject (resource_type='tag', name = tv, value = v[0], resource_value = v[0])
        #     for v in vsall ]
        return q

    # Return name of specified resource
    tn = params.pop('names', None)
    if tn:
        name, dbtype1 = dbtype_from_tag(tn)
        ### Return all tha available tag names for the given superquery
        sq1 = query.with_labels().subquery()
        # Fetch all name on all 'top' level tags from the query
        sq2 = DBSession.query(dbtype1).filter(dbtype1.document_id == sq1.c.taggable_document_id)
        sq3 = sq2.distinct(dbtype1.resource_name).order_by(dbtype1.resource_name)
        #log.debug ("tag_names query = %s" % sq1)
        q = [ fobject (resource_type=dbtype1.xmltag , name=tg.resource_name, type=tg.resource_user_type ) for tg in sq3]
        return q



    if params.has_key('name') and dbtype == Tag:
        ### Find tags with name
        ## Equiv .../tag[@name=param]
        sq1 = query.with_labels().subquery()
        return DBSession.query(Tag).filter(
            and_(Tag.document_id == sq1.c.taggable_document_id,
                 Tag.resource_name == params.pop('name')))
    if params.has_key('value') and dbtype == Tag:
        ### Find tags with name
        ## Equiv .../tag[@value=param]
        return DBSession.query(Tag).filter(
            and_(Tag.id == Value.resource_parent_id,
                 Value.valstr == params.pop('value')))



    #if params.has_key('name') and dbtype==Tag:
        ### Find tags with name
        ## Equiv .../tag[@name=param]
        #q  =  and_(Tag.name_id == names.c.id,
        #           names.c.name == params.pop('name'),
        #           Taggable.id == Tag.id)
        #return DBSession.query(Tag).filter(q)



    #if params.has_key('value') and dbtype==Tag:
    #    ### Find tags with name
    #    ## Equiv .../tag[@name=param]
    #    q  = and_(Tag.id == Value.parent_id,
    #              Value.valstr == params.pop('value'),
    #              Taggable.id == Tag.id)
    #
    #    return DBSession.query(Tag).filter(q)

    return None



ATTR_EXPR = re.compile('([><=]*)([^><=]+)')
def resource_query(resource_type,
                   tag_query=None,
                   tag_order=None,
                   parent=None,
                   permcheck = True,
                   user_id=None,
                   wpublic = False,
                   action = RESOURCE_READ,
                   **kw):
    '''Perform a query for the specified type, using the credentials user_id.
    tag_query will specify a set of tags that should be subordinate to the objects
    found.

    @type string:
    @param resource_type:  a database type
    @param tag_query: match the tag expression
    @param tag_order: order of the items to be returned
    @param parent:  The parent object (all results must be under this parent) (maybe a query, id, None (toplevel objects) or False (no parent clause)
    @param user_id:
    @param **kw: All other keyword args are used as attribute value to be matched
    '''
    name, dbtype, query = prepare_type(resource_type)
    log.debug ("type (%s,%s) query =  %s", name, dbtype, str(query))

    log.debug ("query %s: %s order %s parent %s attributes %s" % (name, tag_query, tag_order, parent, str(kw)))
    query = prepare_parent( (name, dbtype), query, parent)

    # This converts an request for values to the actual
    # objects represented by those values;  :o
    if dbtype == Value:
        log.debug ("VALUE QUERY %s" % query)
        sq1 = query.with_labels().subquery()
        query = DBSession.query (Taggable).filter (Taggable.id == sq1.c.values_valobj)
        wpublic = 1

    if  permcheck :
        query = prepare_permissions(query, user_id, with_public = wpublic, action=action)
    else:
        log.warn ("skipping permissions")

    ## Extra attributes
    if kw.has_key('hidden'):
        query = query.filter(Taggable.resource_hidden == asbool(kw.pop('hidden')))
    else:
        query = query.filter(Taggable.resource_hidden == None)

    query = prepare_tag_expr(query, tag_query)

    ## Special tag expressions
    r = tags_special(dbtype, query, kw)
    if r is not None:
        log.debug ('handled by tags special')
        return r

    # Order the query if there is a sort order
    query = prepare_order_expr(query, tag_order)

    # This maybe should be moved to special
    # Given  a tag query fetch only the tags specified by the names list
    # /ds/images/19292/tags?names=experimenter,date
    tv = kw.pop('names', None)
    if tv and dbtype==Tag:
#        query = query.filter (or_(*[ dbtype.name_id==UniqueName(k).id
        query = query.filter (or_(*[ taggable.c.resource_name == k
                                     for k in tv.split(',')]))



    for ky,v in kw.items():
        #log.debug ("extra " + str(k) +'=' + str(v))
        k = LEGAL_ATTRIBUTES.get(ky)
        if k and hasattr(dbtype, k):
            if not hasattr(v, '__iter__'):
                v = [v]
            for val  in v:
                val  = val.strip('"\'')
                op, val = ATTR_EXPR.match(val).groups()
                if k in ('ts', 'created'):
                    try:
                        if '.' not in val:
                            val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
                        else:
                            val, frag = val.split('.')
                            val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
                            val = val.replace(microsecond=int(frag))
                    except ValueError:
                        log.error('bad time: %s' %val)
                        continue
                log.debug ("adding attribute search %s %s op=%s %s" % (dbtype, k, op,  val))
                if op == '>=':
                    query =query.filter( getattr(dbtype, k) >= val)
                elif op == '>':
                    query =query.filter( getattr(dbtype, k) > val)
                elif op == '<=':
                    query =query.filter( getattr(dbtype, k) <= val)
                elif op == '<':
                    query =query.filter( getattr(dbtype, k) < val )
                else:
                    if '*' in val:
                        query =query.filter( getattr(dbtype, k).like (val.replace('*', '%')))
                    else:
                        query =query.filter( getattr(dbtype, k)==val)
            del kw[ky]

    # These must be last @ SQLAlchemy issues
    if kw.has_key('offset'):
        query = query.offset (int(kw.pop('offset')))
    if kw.has_key('limit'):
        query = query.limit (int(kw.pop('limit')))

    #log.debug ("query = %s" % query)
    #query =  query.distinct()

    return query



def resource_load(resource_type = (None, Taggable),
                  ident=None,
                  uniq = None,
#                  user_id=None,
#                  with_public=True,
#                  action=RESOURCE_READ,
                  **kw):
    name, dbtype, query = prepare_type (resource_type)
#    resource = prepare_permissions (resource, user_id, with_public = with_public, action=action)
    if uniq is not None:
        resource = query.filter_by (resource_uniq = uniq)
    else:
        resource = query.filter_by (id = ident)

    return resource


def resource_permission(resource, action = RESOURCE_READ, user_id=None, with_public = True):
    resource = prepare_permissions (resource, user_id, with_public = with_public, action=action)
    return resource


def send_mail(user_list, content):
    """send an email to the users list
       NOT IMPLEMENTED
    """
    pass


def match_user (user_url =None, email =None ):
    """Match a user by user url or email

    @return: tuple (new user, boolean created)
    """
    user = None
    if user_url is None and email is None:
        raise IllegalOperation()
    if user_url:
        user = DBSession.query(BQUser).get (int (user_url.rsplit('/', 1)[1]))
    if not user and email:
        user = DBSession.query(BQUser).filter_by(resource_value=unicode(email)).first()
    if  user is not None:
        #log.debug ('Found user %s', str(user.user_name)
        return (user, False)
    log.debug ('AUTH: no user %s sending invite %s', email)
    # Setup a temporary user so that we can add the ACL
    # Also setup the pre-registration info they can
    name = email.split('@',1)[0]
    count = 1
    check_name = name
    while True:
        user = DBSession.query(BQUser).filter_by(
            resource_name=check_name).first()
        if user is None:
            name = check_name
            break
        check_name = name + str(count)
        count += 1

    log.debug('AUTH: tg_user name=%s email=%s display=%s' ,  name, email, email)
    tg_user = User(user_name=name, password='bisque', email_address=email, display_name=email)
    DBSession.add(tg_user)
    DBSession.flush()
    log.debug ("AUTH: tg_user = %s" % tg_user)

    # we should have created the BQUser by now.
    user = DBSession.query(BQUser).filter_by(resource_name = name).first()
    return (user, True)


def resource_auth (resource, action=RESOURCE_READ, newauth=None, notify=True, invalidate=True):
    """View or edit authoization records associated the resource

    @param resource: a database taggable
    @param action : RESOURCE_READ or RESOURCE_EDIT
    @param newauth: list of (user_id, permissions) tuples

    when editing:
       determine list of user not authorized yet
       if notify:
          send email
       replace acl with authorized user list
       if invalidate:
          invalidate users
    """
    log.debug ("resource_auth %s %s", str(resource), str(newauth))
    DBSession.autoflush = False
    q = DBSession.query (TaggableAcl).filter_by (taggable_id = resource.id)
    current_user = get_user()
    # If simply trying to read permissions then, we can answer right away.
    if action==RESOURCE_READ:
        #if user_id == get_admin_id():

        if is_admin() and resource.owner_id != current_user.id:
            q = list (q.all())
            q.append(fobject('auth', current_user = "/data_service/%s" % current_user.uri, email= current_user.value, action = "edit", resource_value=''))
        return q

    # setup for an edit of auth records
    #
    if action==RESOURCE_EDIT:
        #owner  = DBSession.query(BQUser).get(resource.owner_id)
        owner = current_user
        owner_name = owner.name
        owner_email = owner.value

        # Remove the previous ACL elements and replace with the provided xml

        log.debug ("RESOURCE EDIT %d %s" % (resource.id, resource.acl))
        current_shares = []
        previous_shares = []
        shares = []
        for acl in resource.acl:
            previous_shares.append (acl.user)

        invite_msg = """
        You've been invited by $owner_name <$owner_email> to view an image at
        $image_url

         A login has been created for you at $root.  Please login
        using $name as login ID and bisque as your password.
        """

        share_msg = """
        You've been invited by $owner_name <$owner_email> to view an image at
        $image_url
        """
        bisque_root = config.get ('bisque.root')

        common_email = {
            'owner_name' : owner_name,
            'owner_email' : owner_email,
            'image_url'  : url ('%s/client_service/view?resource=%s' % (bisque_root, "/data_service/%s" % (resource.uri))),
            'root'       : bisque_root,
            }

        for auth in newauth:
            email  = auth.get ('email', None)
            action = auth.get ('action', RESOURCE_READ)
            user_url   = auth.get ('user', None)
            log.debug ("AUTH : %s %s %s" , user_url, email, action)

            # Get a user
            if (user_url or email)  and action is not None:
                invite = None

                user = None
                if user_url:
                    try:
                        user = DBSession.query(BQUser).get (int (user_url.rsplit('/', 1)[1]))
                    except ValueError:
                        user = DBSession.query(BQUser).filter_by (resource_uniq= (user_url.rsplit('/', 1)[1])).first()
                if not user and email:
                    user = DBSession.query(BQUser).filter_by(resource_value=unicode(email)).first()

                if user  and is_admin(user):
                    # admins should never be added to acl for now.. no reason.
                    continue

                if  user is None:
                    log.debug ('AUTH: no user %s sending invite' % email)

                    # Setup a temporary user so that we can add the ACL
                    # Also setup the pre-registration info they can
                    name = email.split('@',1)[0]
                    count = 1
                    check_name = name
                    while True:
                        user = DBSession.query(BQUser).filter_by(
                            resource_name=check_name).first()
                        if user is None:
                            name = check_name
                            break
                        check_name = name + str(count)
                        count += 1

                    log.debug('AUTH: tg_user name=%s email=%s display=%s' %
                              ( name, email, email))

                    tg_user = User(user_name=name, password='bisque', email_address=email, display_name=email)
                    DBSession.add(tg_user)
                    DBSession.flush()
                    log.debug ("AUTH: tg_user = %s" % tg_user)

                    #user = BQUser(create_tg=True,
                    #              user_name = name,
                    #              password  = 'bisque',
                    #              email_address = email,
                    #              display_name=name)

                    user = DBSession.query(BQUser).filter_by(resource_name = name).first()
                    invite = string.Template(textwrap.dedent(invite_msg)).substitute(
                        common_email,
                        name = name,
                        email = email)
                elif user not in previous_shares:
                    invite = string.Template(textwrap.dedent(share_msg)).substitute(
                        common_email,
                        email = email)
                else:
                    previous_shares.remove(user)

                user = DBSession.merge(user)
                ####################
                # User is now available modify ACL in DB
                log.debug ('AUTH: user  %s invalidate %s ',  user.id, invalidate)
                # Find acl or create
                try:
                    acl = (a for a in resource.acl if a.user == user).next()
                except StopIteration:
                    # Not found
                    acl = TaggableAcl()
                    log.info('new acl for user %s' % user.name)
                    acl.user = user
                    #resource.acl.append(acl)

                current_shares.append (user)
                shares.append(acl)
                acl.action = action
                if invalidate:
                    #Resource.hier_cache.invalidate ('/', user = user.id)
                    Resource.hier_cache.invalidate_resource (None, user = user.id)

                try:
                    if notify and invite is not None:
                        notify_service.send_mail (owner_email,
                                                  email,
                                                  "Invitation to view",
                                                  invite,
                                                  )
                except Exception:
                    log.exception("Mail not sent")

        resource.acl = shares
        if invalidate:
            for user in set(previous_shares) - set(current_shares):
                #Resource.hier_cache.invalidate ('/', user = user.id)
                Resource.hier_cache.invalidate_resource (None, user = user.id)
        DBSession.flush()

    return []


def resource_delete(resource, user_id=None):
    """Delete the given resource:
       1. if owner delete the resource
       2. else remove ACL permissions
       3. Ensure all references are deleted also.
       """
    log.info('resource_delete %s: start' % resource)
    if  user_id is None:
        user_id = get_user_id()
    if resource.owner_id != user_id and not is_admin(): # user_id != get_admin_id():
        # Remove the ACL only
        q = DBSession.query (TaggableAcl).filter_by (taggable_id = resource.id)
        q = q.filter (TaggableAcl.user_id == user_id)
        q.delete()
        log.debug('deleting acls reource_owner(%s) delete(%s) %s' % (resource.owner_id, user_id, q))
        Resource.hier_cache.invalidate_resource (q, user = user_id)
        #Resource.hier_cache.invalidate ('/', user = user_id)
        return
    # owner so first delete all referneces.
    # ACL, values etc..
    #
    DBSession.autoflush = False
    value_count = DBSession.query(Value).filter_by(valobj = resource.id).count()
    if value_count:
        resource.resource_hidden = True
        log.debug('hiding resource due to references')
        return
    q = DBSession.query (TaggableAcl).filter_by (taggable_id = resource.id)
    q.delete()
    # This is a *pile* of junk.. should be handled by mount_service but I cannot find a clean way to notify it.
    link = DBSession.query(Taggable).filter_by(resource_type = 'link', resource_value = resource.resource_uniq).first()
    if link:
        log.debug ('removing link %s %s from store', link.resource_name, link.resource_uniq)
        DBSession.delete(link)
        Resource.hier_cache.invalidate_resource (link, user = user_id)
    # Finally delete resource
    DBSession.delete(resource)
    DBSession.flush()

    log.debug('resource_delete %s:end' % resource)


def resource_types(user_id=None, wpublic=False):
    'return all toplevel resource types available to user'
    #names = [ x[0] for x in DBDBSession.query(Taggable.resource_type).distinct().all() ]
    query = DBSession.query(Taggable).filter_by(parent=None)
    query = prepare_permissions(query, user_id=user_id, with_public=wpublic)
    vsall = query.distinct(Taggable.resource_type).order_by(Taggable.resource_type).all()
    # for sqlite (no distinct on)
    try:
        vsall = unique(vsall, lambda x: x.resource_type)
        #log.debug ("tag_names query = %s" % sq1)
        return [ x.resource_type for x in vsall ]
    except (IndexError, StopIteration):
        return []
    return vsall


# def prepare_query_expr (query, resource_type, user_id, wpublic, parent, tag_query, **kw):
#     name, dbtype = resource_type
#     query = prepare_type (resource_type, query)
#     ## Check permission
#     welcome = kw.pop ('welcome', None)
#     if not welcome:
#         query = prepare_permissions(query, user_id, wpublic)
#     ## Parent check
#     ## TODO Consider renaming values and vertex 'id' field
#     ## to parent_id to better represent what they are and simplify
#     ## the parent check below
#     if parent:
#         if hasattr(dbtype.c, 'resource_parent_id'):
#             query = query.filter(dbtype.resource_parent_id == parent.id)
#         elif hasattr(dbtype.c, 'id'):
#             query = query.filter(dbtype.id == parent.id)
#     ## Subtag expressions
#     if tag_query:
#         query = prepare_tag_expr(query, tag_query)
#     return query


