from sqlalchemy.sql import select, func, exists, and_, or_, not_, asc, desc, operators, cast
from sqlalchemy.orm import Query, aliased
from bq.data_service.model import Taggable, taggable, Image, LEGAL_ATTRIBUTES
from bq.data_service.model import TaggableAcl, BQUser
from bq.data_service.model import Tag, GObject
from bq.data_service.model import dbtype_from_tag
from bq.core.model import DBSession

try:
    import ply.yacc as yacc
    import ply.lex as lex
except Exception:
    import yacc as yacc
    import lex as lex

tokens = ('NAME', 'QUOTED')
literals = [ '[',']', '=' , ',' ]

def t_QUOTED(t):
    r'(?s)(?P<quote>["\'])(?:\\?.)*?(?P=quote)'
    t.type = 'QUOTED'
    t.value = t.value[1:-1]
    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.value = LEGAL_ATTRIBUTES.get (t.value, t.value)
    return t
t_ignore = r' '

def t_error(t):

    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

def p_expr(p):
    ''' expr : filter
             | expr ',' filter
    '''
    if len(p)>2:
        p[1].append (p[3])
        p[0] = p[1]
    else:
        p[0] = [ p[1] ]


def p_filter(p) :
    ''' filter : NAME '[' select_list ']' '''
    #print p[1]
    columns = [col[0] for col in p[3]][::-1]
    filters = [ col[1] for col in p[3][1:] ]
    filters.append (Taggable.resource_type == p[1])
    dbclass = dbtype_from_tag(p[1])[1]
    #p[0] = (p[1], DBSession.query (*columns).filter (*filters).group_by(*columns).order_by(*columns))
    p[0] = (dbclass, columns, filters)


def p_select_list(p):
    """ select_list : NAME
                    | NAME ',' filter_list
    """
    column = getattr(Taggable, p[1])
    if len(p) > 2:
        p[3].insert(0, (column, None) )
        p[0] = p[3]
    else:
        p[0] = [ (column, None) ]

def p_filter_list(p):
    """ filter_list : filter_expr
                    | filter_list ',' filter_expr
    """
    if len(p)>2:
        p[1].append (p[3])
        p[0] = p[1]
    else:
        p[0] = [ p[1] ]
    print "BEFORE", p[-1]

def p_filter_expr(p):
    """ filter_expr : NAME '=' NAME
    """
    column = getattr(Taggable, p[1])
    p[0] = (column,  operators.eq (column, p[3]))



def p_error(p):
    print "Syntax error at token", p
    #yacc.errok()

#  We generate the table once and leave it in generated.  This should be
#  move to some system directory like "/var/run/bisque"
# http://www.dabeaz.com/ply/ply.html#ply_nn18
#_mkdir("generated")
lexer = lex.lex()
parser  = yacc.yacc( debug= 0)


def filter_parse (text):
    return parser.parse (text, lexer = lexer)

def lexit (text):
    lexer.input(text)
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok


if __name__ == "__main__":
    text = 'tag[name],gobject[type,name=aa]'

    #lexit(text)
    qs =  filter_parse (text)

    for query in qs:
        print query





