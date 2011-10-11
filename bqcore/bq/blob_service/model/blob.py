from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, backref
from sqlalchemy.types import Integer, Unicode, Boolean

from bq.core.model import DeclarativeBase, metadata, DBSession

__all__ = [ 'Blob', 'metadata' ]

class Blob(DeclarativeBase):
    __tablename__ = 'blobs'
    id = Column(Integer, primary_key=True)
    hash = Column(Unicode, nullable=False) 
    uri = Column(Unicode, nullable=False, unique = True, index = True )
    user_id = Column(Integer, ForeignKey('tg_user.user_id'), nullable=False)
    user = relation('User', foreign_keys=user_id)
    perms = Column(Integer, nullable=False)
    def __repr__(self):
        return (u"<Blob('%s','%s', '%s')>" % (
            self.hash, self.uri, self.user
        )).encode('utf-8')
