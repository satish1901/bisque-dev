"""migrate resource ids

Revision ID: 1fd412bca00e
Revises: 33b00e22cb16
Create Date: 2014-10-10 12:14:14.604134

"""

# revision identifiers, used by Alembic.
revision = '1fd412bca00e'
down_revision = '33b00e22cb16'

import urlparse
import posixpath
from ConfigParser import ConfigParser
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy import and_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, MetaData
import sys
reload(sys)
sys.setdefaultencoding ('utf8')

def upgrade():
    "Find resource references in string and migrate to new resource_uniq id's"

    parser = ConfigParser ()
    parser.read ("config/site.cfg")
    bisque_root = parser.get ('servers', 'h1.url')
    print "ROOT", bisque_root
    root = urlparse.urlsplit(bisque_root)

    cntxt = context.get_context()
    SessionMaker = sessionmaker(bind=cntxt.bind)

    # toplevel = DBSession.query(Taggable).filter(Taggable.resource_parent_id == None, Taggable.resource_uniq == None)
    # for resource in toplevel:
    #     uid = make_short_uuid()
    #     #resource.resource_uniq = "00-%s" % uid
    #     print resource.resource_type, uid
    #     resource.resource_uniq = "00-%s" % uid

    Base = declarative_base()
    metadata = MetaData(bind=cntxt.bind)
    class Taggable(Base):
        __table__ = Table('taggable', metadata, autoload=True)
        def __str__(self):
            return u"<%s id=%s name=%s value=%s ts=%s document=%s>" % (self.resource_type, self.id, self.resource_name, self.resource_value, self.ts, self.document_id)

    DBSession = SessionMaker()
    Tag = Taggable

    alltags = DBSession.query(Tag).filter(and_(Tag.resource_type =='tag',  Tag.resource_value.like ('http%')))
    for tag in alltags:
        url = tag.resource_value
        parts = list ( urlparse.urlsplit(url) )
        # (scheme, host, path, ...)
        path = parts[2].split('/')
        ident = None
        try:
            while path:
                x = path.pop(0)
                if x and x[0].isdigit():
                    ident = int(x)
                    break
        except (ValueError, IndexError):

            print "bad value %s %s" % (x, url)
            continue
        if ident is None:
            print "bad value %s" % tag
            continue

        target = DBSession.query(Taggable).filter_by (id = ident).first()
        if target:
            if target.resource_uniq is None:
                print "Tag %s  points to  uniq=None %s" % (tag, target)
                continue
            #print "mapping %s -> %s  /data_service/%s/%s" % (ident, target, target.resource_uniq, "/".join(path))
            parts[0] = root[0]
            parts[1] = root[1]
            parts[2] = posixpath.join( "/data_service", target.resource_uniq, "/".join(path)).rstrip('/')
            newurl  = urlparse.urlunsplit ( parts )
            print "mapping %s -> %s" % (tag, newurl)
            tag.resource_value = newurl
        else:
            print "No mapping for %s" % tag



def downgrade():
    pass




