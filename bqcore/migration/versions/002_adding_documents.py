from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata

    meta = MetaData()
    meta.bind = migrate_engine


    # document = Table('document', meta, 
    #                  Column('id', Integer, primary_key=True),
    #                  Column('uniq', String(40)),  # Same as Resource uniq
    #                  Column('content_hash', String(40)),
    #                  Column('document_type', Unicode (127)) # Top level resource_type
    #                  Column('owner_id', Integer, ForeignKey ('document.id')),
    #                  Column('perm', String(15)),
    #                  Column('ts', DateTime(timezone=False)),
    #                  )
    # document_acl = Table('document_acl', meta,
    #                  Column('document_id', Integer, ForeignKey('document.id'), primary_key=True),
    #                  Column('user_id', Integer, ForeignKey('document.id'),primary_key=True),
    #                  Column('permission', String (15)),
    #                  )

    #document.create()
    #document_acl.create()

    taggable = Table('taggable', meta, autoload=True)
    document_id = Column('document_id', Integer, ForeignKey('taggable.id')) # Unique Element
    document_id.create(taggable)

    values = Table('values', meta, autoload=True)
    document_id = Column('document_id', Integer, ForeignKey('taggable.id')) # Unique Element
    document_id.create(values)




def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
