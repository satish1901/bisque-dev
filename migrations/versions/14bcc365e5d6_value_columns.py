"""value columns

Revision ID: 14bcc365e5d6
Revises: 1fd412bca00e
Create Date: 2014-12-18 15:17:23.373858

"""

# revision identifiers, used by Alembic.
revision = '14bcc365e5d6'
down_revision = '1fd412bca00e'

from alembic import op
from alembic import context
import sqlalchemy as sa
from sqlalchemy import Column, Float, Integer, ForeignKey

from sqlalchemy import Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from bq.util.bisquik2db import parse_bisque_uri
from bq.util.hash import is_uniq_code

def upgrade():
    op.add_column('taggable', Column('resource_number', Float))
    op.add_column('taggable', Column('resource_obj',  Integer, ForeignKey ('taggable.id')))

    cntxt = context.get_context()
    SessionMaker = sessionmaker(bind=cntxt.bind)

    Base = declarative_base()
    metadata = MetaData(bind=cntxt.bind)
    class Taggable(Base):
        __table__ = Table('taggable', metadata, autoload=True)

    DBSession = SessionMaker()
    converted_numbers = 0
    converted_objs = 0
    for tv in DBSession.query(Taggable).filter(Taggable.resource_value != None):
        try:
            tv.resource_number  = float(tv.resource_value)
            converted_numbers += 1
            #print ",number ",
            continue
        except ValueError:
            pass

        try:
            service, clname, ida, rest = parse_bisque_uri(tv.resource_value)
            if ida and is_uniq_code (ida):
                #log.debug("loading resource_uniq %s" % ida)
                resource_link = DBSession.query(Taggable).filter_by(resource_uniq = ida).first()
                if resource_link:
                    tv.resource_obj = resource_link.id
                    #print ",linked:", resource_link.id,
                    converted_objs += 1
        except IndexError:
            pass

    print "converted %s numbers and %s objects" % (converted_numbers, converted_objs)
    DBSession.commit()
    DBSession.close()


def downgrade():
    op.drop_column('taggable', 'resource_number')
    op.drop_column('taggable', 'resource_obj')

