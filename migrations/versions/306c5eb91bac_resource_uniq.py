"""resource uniq

Revision ID: 306c5eb91bac
Revises: 156205cd1d39
Create Date: 2013-02-28 10:56:11.014148

"""

# revision identifiers, used by Alembic.
revision = '306c5eb91bac'
down_revision = '156205cd1d39'

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from bq.util.hash import make_uniq_code
from bq.data_service.model.tag_model import Taggable


def upgrade():
    "Ensure all top-level objects have resource_uniq and tag all resource_unique with generation code"

    cntxt = context.get_context()
    SessionMaker = sessionmaker(bind=cntxt.bind)


    # toplevel = DBSession.query(Taggable).filter(Taggable.resource_parent_id == None, Taggable.resource_uniq == None)
    # for resource in toplevel:
    #     uid = make_short_uuid()
    #     #resource.resource_uniq = "00-%s" % uid
    #     print resource.resource_type, uid
    #     resource.resource_uniq = "00-%s" % uid

    DBSession = SessionMaker()
    toplevel = DBSession.query(Taggable).filter(Taggable.resource_parent_id == None)
    for resource in toplevel:
        if resource.resource_uniq is None:
            uid = make_uniq_code()
            resource.resource_uniq =  uid
        elif resource.resource_uniq.startswith ('00-'):
            continue
        elif len(resource.resource_uniq) == 40:
            uid = make_uniq_code()
            resource.resource_uniq =  uid
        else:
            resource.resource_uniq = "00-%s" % resource.resource_uniq
        print "updating %s -> %s" % (resource.id, resource.resource_uniq)
    DBSession.flush()



def downgrade():
    #from bq.data_service.model.tag_model import Taggable, DBSession
    #toplevel = DBSession.query(Taggable).filter(Taggable.resource_parent_id == None).first()
    pass

