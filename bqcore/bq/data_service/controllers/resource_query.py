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

from tg import config, url
from datetime import datetime
from sqlalchemy.sql import select, func, exists, and_, or_, not_, asc, desc

from bq.core.model import DBSession as session
#from bq.image_service import image_service
#from bq.notify_service import notify_service


#from bq.data_service.model import UniqueName, names
from bq.data_service.model import Taggable, taggable, Image
from bq.data_service.model import TaggableAcl, BQUser
from bq.data_service.model import Tag
from bq.data_service.model import Value, values
from bq.core import identity
from bq.core.identity import get_admin
from bq.core.identity import get_user_id
from bq.util.mkdir import _mkdir
from bq.util.paths import data_path

from bq  import image_service
from bq.client_service.controllers import notify_service

log = logging.getLogger('bq.data_service.query')



PUBLIC=0
PRIVATE=1
RESOURCE_READ=0
RESOURCE_EDIT=1

report_errors = True

try:
    import ply.yacc as yacc
    import ply.lex as lex
except:
    import yacc as yacc
    import lex as lex
 
tokens = ('TAGVAL',  'SEP', 'AND', 'OR', 'LP', 'RP', 'QUOTED')
reserved = { 'and': 'AND', 'AND': 'AND',
             'or' : 'OR', 'OR' : 'OR', 
             }

#t_TAGVAL   = r'\w+\*?'
t_SEP   = r':'
t_AND   = r'\&'
t_OR    = r'\|'
t_LP    = r'\('
t_RP    = r'\)'
#t_REL   = r'<|>|<=|>='


#t_VALEXP= r'\w+\*'

t_ignore = r' '

def t_QUOTED(t):
    r'(?P<quote>["\'])(?:\\?.)*?(?P=quote)'
    t.type = 'TAGVAL'
    t.value = t.value[1:-1]
    return t

def t_TAGVAL(t):
    r'[^:\t\n\r\f\v()" ]+'
    t.type = reserved.get(t.value, 'TAGVAL')
    if t.type != 'TAGVAL':
        t.value = t.value.upper()
    return t
    
def t_error(t):
    global report_errors
    if (report_errors):
        print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1) 

lex.lex() 

#############


def p_query_simple(p):
    '''query : expr'''
    p[0] = p[1]
#def p_query_list(p):
#    '''query : query term'''
#    if p[2]:
#        p[0] = and_(p[1], p[2])
#    else:
#        p[0] = p[1]
#def p_query_empty(p):
#    '''query: '''
#    p[0] = None

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

def p_term_tagval(p):
    '''term : tagval SEP tagval'''
    vals= values.alias()
    tag = taggable.alias ()
    if p[1].count('*'):
        namexpr = tag.c.resource_name.ilike (p[1].replace('*', '%'))
    else:
        namexpr = tag.c.resource_name == p[1]
    
    v = p[3].lower()
    if p[3].count('*'):
        v = v.replace('*', '%')
        valexpr = tag.c.resource_value.ilike(v)
    else:
        valexpr = (func.lower(tag.c.resource_value) == v)

    p[0] = exists([tag.c.id]).where(
        and_(namexpr, valexpr, tag.c.document_id == taggable.c.id))
    

def p_term_tag(p):
    '''term : tagval'''
    #tag = tags.alias ()
    vals= values.alias()
    #resource = taggable.alias()
    tag = taggable.alias()
    #taggableobj = taggable.alias()

    v = p[1].lower()
    if p[1].count('*'):
        valexpr = (func.lower(tag.c.resource_value).ilike(v))
    else:
        #q1 = session.query(Tag).filter(and_(
        #        Tag.id == vals.c.parent_id, 
        #        func.lower(vals.c.valstr) == v))
        #q2 = session.query(Tag).filter(func.lower(Tag.resource_value) == 'f.tiff')
        #sq = q1.union(q2).subquery()
        # exists([taggable.id]).where(taggable.c.id == sq.c.taggable_document_id)
        valexpr = (func.lower(tag.c.resource_value) == v)
                                     
    p[0] = exists([tag.c.id]).where (and_(valexpr, tag.c.document_id == taggable.c.document_id))



def p_tagval_norm (p):
    '''tagval : TAGVAL'''
    p[0] = p[1]
def p_tagval_quote (p):
    '''tagval : QUOTED'''
    p[0] = p[1]


def p_error(p):
    print "Syntax error at token", p
    #yacc.errok()

#  We generate the table once and leave it in generated.  This should be 
#  move to some system directory like "/var/run/bisque" 
# http://www.dabeaz.com/ply/ply.html#ply_nn18
#_mkdir("generated")
yacc.yacc(outputdir=data_path(), debug= 0)


def prepare_permissions (query, user_id, with_public, action):
    # get system supplied user ID
    public_vals = { 'false': False, '0': False, 'private':False, 0:False,
                    'true': True, '1': True, 'public': True, 1:True
                    }
    with_public = public_vals.get(with_public, False)

    if not user_id:
        user_id = identity.get_user_id()

    if user_id == get_admin().id:
        return query

    # Check if logged in, else just check for public items.
    if user_id:
        visibility = ( Taggable.owner_id == user_id )
        if with_public and action == RESOURCE_READ:
            visibility = or_(visibility, Taggable.perm == PUBLIC)
        visibility = or_(visibility,
                         Taggable.acl.any(and_(TaggableAcl.user_id == user_id,
                                               TaggableAcl.permission >= action)))
                                                       
    else:
        visibility = (Taggable.perm == PUBLIC)
    
    return query.filter(visibility)


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


def prepare_type (resource_type, query = None):
    name, dbtype = resource_type
    ## Setup universal query type
    query_expr = None
    if not query:
        query = session.query(dbtype)

    if dbtype == Taggable:
        #query_expr = (Taggable.tb_id == UniqueName(name).id)
        query_expr = (Taggable.resource_type == name)
    else:
        if hasattr(dbtype, 'id'):
            query_expr = (dbtype.id == Taggable.id)

    return query.filter (query_expr)


def prepare_parent(resource_type, query, parent_query=None):
    name, dbtype = resource_type
    if parent_query:
        name, dbtype = resource_type
        subquery = parent_query.with_labels().subquery()
        #parent = parent_query.first()
        #log.debug ("subquery " + str(subquery))
        log.debug ( "parent %s %s " % ( name , dbtype))
        #query = session.query(dbtype).filter (dbtype.resource_parent_id == subquery.c.taggable_id)
        query  = query.filter(dbtype.resource_parent_id == subquery.c.taggable_id)
        #query  = query.filter(dbtype.resource_parent_id == parent.id)
    return query


def prepare_order_expr (query, tag_order, **kw):
    def ign (x): return x
    order_lookup = { 'asc': asc, 'desc': desc } 
    if tag_order:
        for order in tag_order.split(','):
            order, d, ordering = order.partition (':')
            ordering = order_lookup.get (ordering, ign)
            order = order.strip('"\'')

            log.debug ("tag_order: %s" % (order))
            
            if order.startswith('@'):
                query = query.order_by(ordering(getattr(Taggable, order[1:])))
                continue
            ordertags = taggable.alias()
            ordervals = values.alias()
            query_expr = and_ (#query_expr,
                               Taggable.id == ordertags.c.resource_parent_id,
                               ordertags.c.resource_type == 'tag', 
                               ordertags.c.resource_name == order,
                               ordertags.c.id == ordervals.c.resource_parent_id)
            query = query.filter(query_expr).order_by (ordering(ordervals.c.valstr))
    else:
        query = query.order_by(Taggable.id)
            
    return query

def count_special(**kw):
    if kw.pop('images2d', None):
        #vs = session.execute(select ([func.sum (Image.z * Image.t)])).fetchall()
        #count = vs[0][0]
        count = session.query(Image).count()
        if count:
            return count
    return None

def resource_count (resource_type, tag_query, **kw):
    count =   count_special(**kw)
    if count is None:
        query  =  resource_query(resource_type=resource_type,
                                 tag_query = tag_query,
                                 **kw)
        #count = query.distinct().count()
        count = query.count()
        #log.debug ('counted ' + str(query) + '=' + str(count))
    return count

class fobject(object):
    ''' A fake database object'''
    def __init__(self, xmltag = '', **kw):
        self.__class__.xmltag = xmltag
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

            

##   NOTE: Please examine for a better way of handling 
##   specilized attribute queries esp.  'name' and 'value' queries
##
def tags_special(dbtype, query, params):
    '''Specialized query for tags to support tag based browsing
       tag_names=1 :  names of all tags that can be found on the
                  queried objects

       tag_values=tag_name : all possible values for a particular tag name
       name=tag_name   : all tags have a name="tag_name" as an attribute
       value=tag_val   : all tags having a value attribute of tag_val
    '''
    
    if params.pop('tag_names', None):
        
        ### Return all tha available tag names for the given superquery
        sq1 = query.with_labels().subquery()
        # Fetch all name on all 'top' level tags from the query
        sq2 = session.query(Tag.resource_name).filter(Tag.document_id == sq1.c.taggable_document_id)
        sq3 = sq2.distinct().order_by(Tag.resource_name)
        #log.debug ("tag_names query = %s" % sq1)
        q = [ fobject (resource_type='tag', resource_name = tg[0]) for tg in sq3]
        #names = session.query(UniqueName).filter(UniqueName.id == sq2.c.name_id)
        #names = names.distinct().order_by(UniqueName.name)
        #log.debug ('names query = %s' % str(names))
        #q = [ fobject (xmltag='tag', name = str(tg.name)) for tg in names.all()]
        return q
    
    tv = params.pop('tag_values', None)
    if tv:
        ### Given a query and a tag_name, return all the possible values for the tag
        #valtags = tags.alias()
        #tv = UniqueName(tv)
        sq1 = query.with_labels().subquery()
        #sq2 = session.query(Tag).filter(and_(Tag.parent_id == sq1.c.taggable_id,
        #                                     Tag.name_id == tv.id)).with_labels().subquery()
        sq2 = session.query(Tag).filter(
            and_(Tag.resource_name == tv,
                 Tag.document_id == sq1.c.taggable_document_id)).with_labels().subquery()
        vs=session.query(Value.valstr).filter(Value.resource_parent_id == sq2.c.taggable_id).distinct()
        log.debug ('tag_values = %s' % vs)
        q = [ fobject (resource_type='tag', resource_name = tv, value = v[0])
              for v in vs.all() ]
        return q

    if params.has_key('name') and dbtype == Tag:
        ### Find tags with name
        ## Equiv .../tag[@name=param]
        sq1 = query.with_labels().subquery()
        return session.query(Tag).filter(
            and_(Tag.document_id == sq1.c.taggable_document_id,
                 Tag.resource_name == params.pop('name')))
    if params.has_key('value') and dbtype == Tag:
        ### Find tags with name
        ## Equiv .../tag[@value=param]
        return session.query(Tag).filter(
            and_(Tag.id == Value.resource_parent_id, 
                 Value.valstr == params.pop('value')))
                 
        

    #if params.has_key('name') and dbtype==Tag:
        ### Find tags with name
        ## Equiv .../tag[@name=param]
        #q  =  and_(Tag.name_id == names.c.id,
        #           names.c.name == params.pop('name'),
        #           Taggable.id == Tag.id)
        #return session.query(Tag).filter(q)
        


    #if params.has_key('value') and dbtype==Tag:
    #    ### Find tags with name
    #    ## Equiv .../tag[@name=param]
    #    q  = and_(Tag.id == Value.parent_id,
    #              Value.valstr == params.pop('value'),
    #              Taggable.id == Tag.id)
    #    
    #    return session.query(Tag).filter(q)
    
    return None

ATTR_EXPR = re.compile('([><=]*)([\w:-]+)')
def resource_query(resource_type,
                   tag_query=None,
                   tag_order=None,
                   parent=None,
                   user_id=None,
                   wpublic = True,
                   action = RESOURCE_READ,
                   **kw):
    '''Perform a query for the specified type, using the credentials user_id.
    tag_query will specify a set of tags that should be subordinate to the objects
    found.

    @type string:
    @param resource_type:  a database type
    @param tag_query: match the tag expression
    @param tag_order: order of the items to be returned
    @param parent:  The parent object (all results must be under this parent)
    @param user_id:
    @param **kw: All other keyword args are used as attribute value to be matched
    '''

    name, dbtype = resource_type
    
    log.debug ("query %s: %s order %s parent %s attributes %s" % (name, tag_query, tag_order, parent, str(kw)))

    query = prepare_type(resource_type)
    #query = session.query(Taggable)

    query = prepare_parent(resource_type, query, parent)

    if dbtype == Value:
        sq1 = query.with_labels().subquery()
        query = session.query (Taggable).filter (Taggable.id == sq1.c.values_valobj)
        wpublic = 1

    if not kw.pop('welcome', None):
        query = prepare_permissions(query, user_id, with_public = wpublic, action=action)
    # HACK
    #  If type of the query is a value then assume we are extracting
    #  objects from a dataset and apply and tag filter/ordering to the
    #  objects in the data set.
    #  THIS NEEDS MORE THOUGHT.

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

    ## Extra attributes
    legal_attributes= []
    for k,v in kw.items():
        #log.debug ("extra " + str(k) +'=' + str(v))
        if hasattr(dbtype, k):
            if not hasattr(v, '__iter__'):
                v = [v] 
            for val  in v:
                val  = val.strip('"\'')
                op, val = ATTR_EXPR.match(val).groups()
                if k=='ts': 
                    try:
                        val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
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
                    query =query.filter( getattr(dbtype, k)==val)
            del kw[k]

    #metadata.bind.echo=True
    #results = query.all()
    #log.debug ("RQ: count=%d" % len(results))
    #metadata.bind.echo=False
    #return results
    
    #taggable_query = query.with_labels().subquery()
    #log.debug ('taggable query %s' % taggable_query)
    #query = prepare_type(resource_type)
    
    #query = query.filter (taggable_query.c.taggable_id == dbtype.id)
    if kw.has_key('offset'):
        query = query.offset (int(kw.pop('offset')))
    if kw.has_key('limit'):
        query = query.limit (int(kw.pop('limit')))
    
    log.debug ("query = %s" % query)
    #query =  query.distinct()
    
    return query



def resource_load(resource_type, id,
                  user_id=None,
                  with_public=True,
                  action=RESOURCE_READ,
                  **kw):
    name, dbtype = resource_type
    resource = prepare_type (resource_type)
#    resource = prepare_permissions (resource, user_id, with_public = with_public, action=action)
    resource = resource.filter_by (id = int(id))

    return resource


def resource_permission(resource, action = RESOURCE_READ, user_id=None, with_public = True):
    resource = prepare_permissions (resource, user_id, with_public = with_public, action=action)
    return resource



def resource_auth (resource, parent, user_id=None, action=RESOURCE_READ, newauth=None):
    """View or edit authoization records associated the resource"""

    q = session.query (TaggableAcl).filter_by (taggable_id = resource.id)
    if not user_id:
        user_id = get_user_id()
    # If you are amin or have edit permission then you can see other
    # user that have permission over this resource
    if resource.owner_id != user_id and user_id != get_admin().id:
        q = q.filter (TaggableAcl.user_id == user_id)
        
    if action==RESOURCE_READ:
        return q
                          
    # setup for an edit of auth records
    # 
    if action==RESOURCE_EDIT:
        owner  = session.query(BQUser).get(user_id)
        owner_name = owner.user_name
        # Remove the previous ACL elements and replace with the provided xml

        log.debug ("RESOURCE EDIT %d %s" % (resource.id, resource.acl))
        new_shares = []
        previous_shares = []
        shares = []
        for acl in resource.acl:
            previous_shares.append (acl.user)
            
            
        #resource.acl = []
        #This flush is needed as otherwise SA Update and then deletes
        # the elements by user_id, resource.id.   This will delete
        # the elements we are updating if they existed in the acl before.
        image_service.set_file_acl (resource.src, owner_name, "remove")
        session.flush()  

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
            'owner_name' : owner.display_name,
            'owner_email' : owner.email_address,
            'image_url'  : url ('%s/client_service/view?resource=%s' % (bisque_root, "/data_service/%s" % (resource.uri))),
            'root'       : bisque_root,
            }

        for auth in newauth:
            email = auth.get ('email', None)
            action = auth.get ('action', RESOURCE_READ)
            log.debug ("AUTH : %s %s " % (email, action))
            if email is not None and action is not None:
                invite = None
                user = session.query(BQUser).filter_by(email_address=unicode(email)).first()

                if  user is None:
                    log.debug ('AUTH: no user %s sending invite' % email)

                    # Setup a temporary user so that we can add the ACL
                    # Also setup the pre-registration info they can
                    name = email.split('@',1)[0]
                    count = 1
                    check_name = name
                    while True:
                        user = session.query(BQUser).filter_by(
                            user_name=check_name).first()
                        if user is None:
                            name = check_name
                            break
                        check_name = name + str(count)
                        count += 1 
                        
                    
                    user = BQUser(create_tg=True,
                                  user_name = name,
                                  password  = 'bisque',
                                  email_address = email,
                                  display_name=name)

                    session.flush()
                    session.refresh(user)

                    invite = string.Template(textwrap.dedent(invite_msg)).substitute(
                        common_email,
                        name = name,
                        email = email)
                    
                    log.debug("AUTH: new user %s" % user)
                    new_shares.append (user)
                    
                elif user not in previous_shares:
                    
                    invite = string.Template(textwrap.dedent(share_msg)).substitute(
                                        common_email,
                                        email = email)


                ####################
                # User is now available modify ACL in DB
                log.debug ('AUTH: user = %s'% user)
                # Find acl or create
                try:
                    acl = (a for a in resource.acl if a.user == user).next()
                except StopIteration:
                    # Not found
                    acl = TaggableAcl()                    
                    acl.user_id = user.id

                shares.append(acl)
                acl.action = action
                image_service.set_file_acl(resource.src,
                                           user.user_name,
                                           action)

                try:
                    if invite is not None:
                        notify_service.send_mail (owner.email_address,
                                                  email,
                                                  "Invitation to view",
                                                  invite,
                                                  )
                except:
                    log.exception("Mail not sent")

        resource.acl = shares
    
    return []
    


def prepare_query_expr (query, resource_type, user_id, wpublic, parent, tag_query, **kw):
    name, dbtype = resource_type

    query = prepare_type (resource_type, query)

    ## Check permission 
    welcome = kw.pop ('welcome', None)
    if not welcome:
        query = prepare_permissions(query, user_id, wpublic)

    ## Parent check
    ## TODO Consider renaming values and vertex 'id' field
    ## to parent_id to better represent what they are and simplify
    ## the parent check below
    if parent:
        if hasattr(dbtype.c, 'resource_parent_id'):
            query = query.filter(dbtype.resource_parent_id == parent.id)
        elif hasattr(dbtype.c, 'id'):
            query = query.filter(dbtype.id == parent.id)
            

    ## Subtag expressions
    if tag_query:
        query = prepare_tag_expr(query, tag_query)
    return query


