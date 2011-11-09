from sqlalchemy import *
from migrate import *



#from sqlalchemy.ext.declarative import declarative_base
#DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
#Base = declarative_base()
#names = Table('names', meta, autoload=True)



def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    taggable = Table('taggable', meta, autoload=True)

    resource_uniq = Column('resource_uniq', String(40) ) # will be used for sha1
    resource_parent_id = Column('resource_parent_id', Integer, ForeignKey('taggable.id'))
    resource_index = Column('resource_index', Integer)
    resource_hidden = Column('resource_hidden', Boolean)
    resource_type =  Column('resource_type',Unicode(255))  # will be same as tb_id UniqueName
    resource_name =  Column('resource_name', Unicode (1023) )
    resource_user_type =  Column('resource_user_type', Unicode(1023) )
    resource_value = Column('resource_value', UnicodeText ) 
    
    resource_uniq.create(taggable)
    resource_parent_id.create(taggable)
    resource_index.create(taggable)
    resource_hidden.create(taggable)
    resource_type.create(taggable)
    resource_name.create(taggable)
    resource_user_type.create(taggable)
    resource_value.create(taggable)


    # Copy name from all objects
    # Removing  file and file_acl



def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
